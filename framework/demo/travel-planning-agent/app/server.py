"""
FastAPI 服务 —— 为旅行规划助手提供 Web API + HTML 聊天界面。

启动方式:
    python -m app.server
    或
    uvicorn app.server:app --reload --port 8000
"""

import asyncio
import json
import os
import threading
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel

app = FastAPI(title="旅行规划助手", version="1.0.0")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = os.fspath(BASE_DIR / "static")
TEMPLATES_DIR = os.fspath(BASE_DIR / "templates")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

jinja_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), auto_reload=True)


def render_template(name: str, context: dict) -> HTMLResponse:
    template = jinja_env.get_template(name)
    html = template.render(context)
    return HTMLResponse(content=html)


def _get_planner():
    from app.services.planner_service import planner_service
    return planner_service


def _get_session_service():
    from app.services.session_service import session_service
    return session_service


# ── Pydantic models ──

class PlanRequest(BaseModel):
    user_input: str
    max_revision_count: int = 2


class ContinueRequest(BaseModel):
    user_input: str


# ── 节点 → 用户可读消息映射 ──

NODE_MESSAGES = {
    "parse_request":       "解析你的旅行需求...",
    "check_info":          "检查信息完整性...",
    "ask_clarification":   "整理追问问题...",
    "decide_tools":        "选择需要的查询工具...",
    "collect_context":     "查询目的地天气、景点、美食、交通信息...",
    "generate_plan":       "正在生成旅行计划（这一步最耗时，约 15-40 秒）...",
    "reflect_plan":        "正在审查方案质量...",
    "revise_plan":         "正在修正计划...",
    "final_output":        "正在整理最终方案...",
}

# ── Page routes ──

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return render_template("index.html", {"request": request})


# ── SSE 流式规划端点 ──

def _stream_graph(state: dict) -> dict:
    """
    在独立线程中运行 graph.stream()，通过 queue 向外发送进度事件。
    返回最终 state（格式化后的响应 dict）。
    """
    planner = _get_planner()
    session_service = _get_session_service()

    queue = asyncio.Queue()

    def run():
        try:
            # 注入流式队列到 chain 模块，让 LLM 调用的 token 逐字推送
            import app.chains.parse_chain as prsc
            import app.chains.plan_chain as pc
            import app.chains.reflection_chain as rc
            import app.chains.revise_chain as rvc
            prsc.set_stream_queue(queue)
            pc.set_stream_queue(queue)
            rc.set_stream_queue(queue)
            rvc.set_stream_queue(queue)

            seen_trace_len = 0
            final_state = None

            for chunk in planner.graph.stream(state, stream_mode="values"):
                final_state = chunk
                trace = chunk.get("trace", [])
                if len(trace) > seen_trace_len:
                    new_nodes = trace[seen_trace_len:]
                    seen_trace_len = len(trace)
                    for entry in new_nodes:
                        node_name = entry["node"]
                        msg = NODE_MESSAGES.get(node_name, node_name)
                        extra = ""
                        if node_name == "reflect_plan" and "score" in entry:
                            extra = f" 评分 {entry['score']}/10"
                        elif node_name == "check_info":
                            missing = chunk.get("missing_fields", [])
                            if missing:
                                extra = f" 发现 {len(missing)} 项信息待补充"
                            else:
                                extra = " 信息完整"
                        elif node_name == "collect_context":
                            ctx = chunk.get("context", {})
                            if ctx:
                                tools_done = list(ctx.keys())
                                extra = f" 已获取 {', '.join(tools_done)}"
                        queue.put_nowait(json.dumps({
                            "type": "progress",
                            "node": node_name,
                            "message": msg + extra,
                        }, ensure_ascii=False))

            # 流完成后，格式化最终结果
            session_id = state.get("_session_id", "")
            if session_id:
                session_service.update_state(session_id, final_state)

            formatted = planner._format_response(final_state, session_id)
            queue.put_nowait(json.dumps({
                "type": "done",
                "data": formatted,
            }, ensure_ascii=False))

        except Exception as e:
            queue.put_nowait(json.dumps({
                "type": "error",
                "message": str(e),
            }, ensure_ascii=False))

    threading.Thread(target=run, daemon=True).start()
    return queue


async def _sse_generator(queue):
    """从 queue 读取事件，转为 SSE 格式输出。"""
    while True:
        try:
            data = await asyncio.wait_for(queue.get(), timeout=180)
            yield f"data: {data}\n\n"
            parsed = json.loads(data)
            if parsed.get("type") in ("done", "error"):
                break
        except asyncio.TimeoutError:
            yield f"data: {json.dumps({'type': 'error', 'message': '请求超时'})}\n\n"
            break


@app.post("/api/travel-plan/stream")
async def create_plan_stream(req: PlanRequest):
    session_service = _get_session_service()
    session_id = session_service.create_session()

    state = {
        "user_input": req.user_input,
        "max_revision_count": req.max_revision_count,
        "_session_id": session_id,
    }

    queue = _stream_graph(state)
    return StreamingResponse(_sse_generator(queue), media_type="text/event-stream")


@app.post("/api/travel-plan/{session_id}/continue/stream")
async def continue_plan_stream(session_id: str, req: ContinueRequest):
    planner = _get_planner()
    session_service = _get_session_service()

    prev_state = session_service.get_state(session_id)
    if not prev_state:
        async def error_gen():
            yield f"data: {json.dumps({'type': 'error', 'message': f'会话 {session_id} 不存在'})}\n\n"
        return StreamingResponse(error_gen(), media_type="text/event-stream")

    state = planner._prepare_followup_state(prev_state, req.user_input)
    state["_session_id"] = session_id

    queue = _stream_graph(state)
    return StreamingResponse(_sse_generator(queue), media_type="text/event-stream")


# ── 非流式 API（向后兼容） ──

@app.post("/api/travel-plan")
async def create_plan(req: PlanRequest):
    session_service = _get_session_service()
    session_id = session_service.create_session()
    result = await asyncio.to_thread(
        _get_planner().plan,
        req.user_input,
        session_id=session_id,
        max_revision_count=req.max_revision_count,
    )
    return result


@app.post("/api/travel-plan/{session_id}/continue")
async def continue_plan(session_id: str, req: ContinueRequest):
    result = await asyncio.to_thread(
        _get_planner().continue_plan,
        session_id,
        req.user_input,
    )
    return result


@app.get("/api/travel-plan/{session_id}")
async def get_session(session_id: str):
    state = _get_session_service().get_state(session_id)
    if not state:
        return {"status": "error", "message": f"会话 {session_id} 不存在或已过期"}
    return {
        "status": "ok",
        "session_id": session_id,
        "stop_reason": state.get("stop_reason", ""),
        "revision_count": state.get("revision_count", 0),
    }


# ── Main ──

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.server:app", host="0.0.0.0", port=8000, reload=True)
