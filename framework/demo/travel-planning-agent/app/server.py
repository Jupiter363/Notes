"""
FastAPI Web 服务 —— 为旅行规划助手提供 HTTP API + HTML 聊天界面。

这是 Agent 的"外包装"——把 LangGraph 工作流暴露为 Web 服务，
让用户通过浏览器使用。

三层职责：
1. 页面路由（GET /）→ 返回聊天 HTML 页面
2. API 路由（POST /api/travel-plan/...）→ 接收请求、调用 Agent、返回结果
3. SSE 流式推送 → 实时推送 LLM token 和执行进度到前端

SSE (Server-Sent Events) 是一种 HTTP 长连接技术：
- 服务器持续向客户端推送事件
- 客户端通过 EventSource 或 fetch + ReadableStream 接收
- 比 WebSocket 简单，适合"服务器→客户端"单向推送

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

# 创建 FastAPI 应用实例
# title 会显示在自动生成的 API 文档页（/docs）上
app = FastAPI(title="旅行规划助手", version="1.0.0")

# 基础路径 —— Path(__file__).resolve().parent 指向 app/ 目录
BASE_DIR = Path(__file__).resolve().parent

# os.fspath() 把路径对象转为操作系统能理解的字符串（Windows用反斜杠，Linux用正斜杠）
STATIC_DIR = os.fspath(BASE_DIR / "static")
TEMPLATES_DIR = os.fspath(BASE_DIR / "templates")

# mount() 把 /static/ 路径映射到 static/ 目录
# 浏览器请求 /static/style.css → 返回 static/style.css 文件内容
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Jinja2 模板引擎 —— 把 HTML 模板 + 数据 → 完整 HTML 页面
# auto_reload=True 开发模式下修改模板自动生效，无需重启
jinja_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), auto_reload=True)


def render_template(name: str, context: dict) -> HTMLResponse:
    """加载 Jinja2 模板并渲染为 HTML 响应。"""
    template = jinja_env.get_template(name)
    html = template.render(context)
    return HTMLResponse(content=html)


# ── 延迟加载函数 ──
# 为什么不是直接 import planner_service？
# 因为 planner_service 的 __init__ 会调用 build_graph()，
# build_graph() 导入 nodes.py，nodes.py 导入 chains，
# chains 创建 LLM model（httpx client）。
# 如果在 uvicorn 启动时（主线程事件循环）创建 httpx client，
# 后续在子线程中使用时可能死锁。
# 延迟到首次 API 请求时才导入，此时 model 在正确的线程上下文中创建。

def _get_planner():
    """延迟导入 PlannerService，确保 model 在请求线程中创建。"""
    from app.services.planner_service import planner_service
    return planner_service


def _get_session_service():
    """延迟导入 SessionService。"""
    from app.services.session_service import session_service
    return session_service


# ── Pydantic 请求模型 ──

class PlanRequest(BaseModel):
    """
    创建旅行规划的请求体。

    Pydantic 会自动校验：
    - user_input 必须是字符串
    - max_revision_count 必须是整数，默认 2
    """
    user_input: str
    max_revision_count: int = 2


class ContinueRequest(BaseModel):
    """继续对话的请求体。"""
    user_input: str


# ── 节点名称 → 用户可读消息映射 ──
# SSE 流式推送时，每个节点完成都会推送一条进度消息

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


# ═══════════════════════════════════════════════════════════════
# 页面路由
# ═══════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """返回聊天界面 HTML 页面。"""
    return render_template("index.html", {"request": request})


# ═══════════════════════════════════════════════════════════════
# SSE 流式规划 —— 核心功能
# ═══════════════════════════════════════════════════════════════

def _stream_graph(state: dict):
    """
    在独立线程中运行 LangGraph 工作流，通过 asyncio.Queue 向外推送事件。

    这是 SSE 流式推送的核心：工作流在子线程中运行，
    每完成一个节点 → 推送 progress 事件，
    LLM 每生成一个 token → 推送 token 事件，
    最终完成 → 推送 done 事件。

    返回 asyncio.Queue，事件消费者（_sse_generator）从队列中读取。
    """

    planner = _get_planner()
    session_service = _get_session_service()

    # asyncio.Queue 是协程安全的队列
    # 子线程用 put_nowait() 放入事件，主协程用 get() 取出
    queue = asyncio.Queue()

    def run():
        """在子线程中执行工作流。"""
        try:
            # ★ 注入流式队列到 chain 模块
            # 这样 LLM 调用时会把每个 token 推送到队列，
            # 前端就能看到打字机效果
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

            # ★ graph.stream(stream_mode="values")
            # 每完成一个节点，yield 当前完整 state
            # 我们通过比较 trace 长度来判断哪些节点是新完成的
            for chunk in planner.graph.stream(state, stream_mode="values"):
                final_state = chunk
                trace = chunk.get("trace", [])

                # 有新的 trace 条目 → 有节点刚完成
                if len(trace) > seen_trace_len:
                    new_nodes = trace[seen_trace_len:]
                    seen_trace_len = len(trace)

                    for entry in new_nodes:
                        node_name = entry["node"]
                        msg = NODE_MESSAGES.get(node_name, node_name)

                        # 为不同节点补充详细说明
                        extra = ""
                        if node_name == "reflect_plan" and "score" in entry:
                            extra = f" 评分 {entry['score']}/10"
                        elif node_name == "check_info":
                            missing = chunk.get("missing_fields", [])
                            extra = f" 发现 {len(missing)} 项信息待补充" if missing else " 信息完整"
                        elif node_name == "collect_context":
                            ctx = chunk.get("context", {})
                            if ctx:
                                extra = f" 已获取 {', '.join(ctx.keys())}"

                        # put_nowait 是线程安全的，不会阻塞
                        queue.put_nowait(json.dumps({
                            "type": "progress",
                            "node": node_name,
                            "message": msg + extra,
                        }, ensure_ascii=False))

            # ── 工作流执行完毕，格式化最终响应 ──
            session_id = state.get("_session_id", "")
            if session_id:
                session_service.update_state(session_id, final_state)

            formatted = planner._format_response(final_state, session_id)
            queue.put_nowait(json.dumps({
                "type": "done",
                "data": formatted,
            }, ensure_ascii=False))

        except Exception as e:
            # 异常也通过队列发送，前端可以展示错误信息
            queue.put_nowait(json.dumps({
                "type": "error",
                "message": str(e),
            }, ensure_ascii=False))

    # 启动子线程执行工作流
    # daemon=True 表示主进程退出时这个线程也会自动退出
    threading.Thread(target=run, daemon=True).start()

    return queue


async def _sse_generator(queue):
    """
    从 asyncio.Queue 中读取事件，转为 SSE 格式输出。

    SSE 格式：
        data: {"type": "progress", "node": "parse_request", ...}\n
        \n
        data: {"type": "token", "token": "{"}\n
        \n
        ...

    每个事件以 "data: " 开头，以 "\n\n" 结束。
    浏览器收到后触发 EventSource 的 onmessage 或 fetch ReadableStream。
    """
    while True:
        try:
            # await 等待队列中的下一个事件，超时 180 秒
            data = await asyncio.wait_for(queue.get(), timeout=180)
            yield f"data: {data}\n\n"

            # 检查是否是终止事件
            parsed = json.loads(data)
            if parsed.get("type") in ("done", "error"):
                break

        except asyncio.TimeoutError:
            # 超时 → 发送错误通知
            yield f"data: {json.dumps({'type': 'error', 'message': '请求超时'})}\n\n"
            break


@app.post("/api/travel-plan/stream")
async def create_plan_stream(req: PlanRequest):
    """
    流式创建旅行规划 —— SSE 端点。

    前端通过 fetch + ReadableStream 连接这个端点，
    实时收到：
    - progress 事件：每个节点完成时的进度消息
    - token 事件：LLM 生成的每个 token（打字机效果）
    - done 事件：最终格式化方案
    """
    session_service = _get_session_service()
    session_id = session_service.create_session()

    # 初始 State —— 只包含用户输入和审查模式设置
    state = {
        "user_input": req.user_input,
        "max_revision_count": req.max_revision_count,
        "_session_id": session_id,  # 内部使用，存储会话状态
    }

    queue = _stream_graph(state)

    # StreamingResponse 是 FastAPI 的流式响应
    # media_type="text/event-stream" 告诉浏览器这是 SSE
    return StreamingResponse(
        _sse_generator(queue),
        media_type="text/event-stream",
    )


@app.post("/api/travel-plan/{session_id}/continue/stream")
async def continue_plan_stream(session_id: str, req: ContinueRequest):
    """
    流式继续旅行规划 —— 用户补充信息后重新执行。
    """

    planner = _get_planner()
    session_service = _get_session_service()

    # 从会话管理器取上一轮的状态
    prev_state = session_service.get_state(session_id)
    if not prev_state:
        async def error_gen():
            yield f"data: {json.dumps({'type': 'error', 'message': f'会话 {session_id} 不存在'})}\n\n"
        return StreamingResponse(error_gen(), media_type="text/event-stream")

    # 清理临时字段 + 合并新输入
    state = planner._prepare_followup_state(prev_state, req.user_input)
    state["_session_id"] = session_id

    queue = _stream_graph(state)
    return StreamingResponse(_sse_generator(queue), media_type="text/event-stream")


# ═══════════════════════════════════════════════════════════════
# 非流式 API（向后兼容，供 CLI 或测试使用）
# ═══════════════════════════════════════════════════════════════

@app.post("/api/travel-plan")
async def create_plan(req: PlanRequest):
    """
    普通（非流式）创建规划。

    asyncio.to_thread() 把同步的 planner.plan() 调用放到线程池执行，
    避免阻塞 asyncio 事件循环。
    """
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
    """普通（非流式）继续规划。"""
    result = await asyncio.to_thread(
        _get_planner().continue_plan,
        session_id,
        req.user_input,
    )
    return result


@app.get("/api/travel-plan/{session_id}")
async def get_session(session_id: str):
    """查询会话状态。"""
    state = _get_session_service().get_state(session_id)
    if not state:
        return {"status": "error", "message": f"会话 {session_id} 不存在或已过期"}
    return {
        "status": "ok",
        "session_id": session_id,
        "stop_reason": state.get("stop_reason", ""),
        "revision_count": state.get("revision_count", 0),
    }


# ── 启动入口 ──

if __name__ == "__main__":
    import uvicorn
    # uvicorn 是 ASGI 服务器，FastAPI 是 ASGI 应用
    # --reload 开发模式：代码修改后自动重启
    uvicorn.run("app.server:app", host="0.0.0.0", port=8000, reload=True)
