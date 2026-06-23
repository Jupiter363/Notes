"""
旅行规划服务 —— 封装 LangGraph 工作流的调用，提供业务级 API。

这是"服务层"，在 LangGraph 图（底层引擎）和 Web/CLI（上层接口）之间
做一个中间层。好处：
- Web 和 CLI 不需要直接操作 graph.invoke()，只调 plan() / continue_plan()
- 响应格式化统一在这里处理（区分完成/追问/错误）
- 多轮对话的状态管理也在这里（_prepare_followup_state）

Stage 2 对应概念：§2.4 状态管理 + §6 Workflow Agent
"""

from typing import Optional
from app.graph.workflow import build_graph
from app.services.session_service import session_service


class PlannerService:
    """
    旅行规划服务。

    两个核心方法：
    - plan(): 新建规划 → 返回方案或追问
    - continue_plan(): 补充信息后继续 → 在上一轮状态基础上重新执行
    """

    def __init__(self):
        # 构建 LangGraph 图 —— 整个应用只需要构建一次
        # 同一张图可以被多次 invoke（每次传入不同的 state）
        self.graph = build_graph()

    def plan(
        self,
        user_input: str,
        session_id: Optional[str] = None,
        max_revision_count: int = 2,
    ) -> dict:
        """
        创建新的旅行规划。

        参数:
            user_input: 用户自然语言输入，如 "我想去成都玩3天"
            session_id: 会话ID，用于多轮对话。None 则不保存状态
            max_revision_count: Reflection 最大修正次数，默认 2

        返回:
            dict with keys: status, final_plan/message, session_id, clarification_questions, etc.
        """

        # 构造初始 State —— 只需要 user_input，其他字段由节点填充
        state = {
            "user_input": user_input,
            "max_revision_count": max_revision_count,
        }

        # ★ 核心调用：让 LangGraph 图执行整个工作流
        # graph.invoke(state) 会按图定义的顺序依次执行所有节点
        # 每个节点返回的 dict 会被合并到 state 中
        # 最终返回完整的 state（包含 final_plan）
        result = self.graph.invoke(state)

        # 保存状态到会话管理器（如果提供了 session_id）
        if session_id:
            session_service.update_state(session_id, result)

        # 格式化响应：区分"完成"和"需要追问"
        return self._format_response(result, session_id)

    def continue_plan(self, session_id: str, user_input: str) -> dict:
        """
        用户补充信息后继续规划。

        流程：
        1. 从会话管理器取出上一轮的 state
        2. 清理掉追问相关的临时字段（避免残留）
        3. 合并新的用户输入
        4. 重新 invoke 图

        这就是 Stage 2 §11 HITL 的简化版：
        信息不足时暂停（ask_clarification），等用户补充后继续。
        """

        # 取上一次的状态
        prev_state = session_service.get_state(session_id)
        if not prev_state:
            return {
                "status": "error",
                "message": f"会话 {session_id} 不存在或已过期",
                "need_user_input": False,
            }

        # 清理临时字段 + 合并新输入
        state = self._prepare_followup_state(prev_state, user_input)

        # 重新执行工作流
        result = self.graph.invoke(state)
        session_service.update_state(session_id, result)

        return self._format_response(result, session_id)

    def _prepare_followup_state(self, prev_state: dict, new_user_input: str) -> dict:
        """
        准备继续对话的 state。

        关键：清理上一轮产生的中间字段，但保留跨轮持久字段。
        - 清理：追问、输出、工具选择、计划、反思、流程控制
        - 保留：user_inputs 历史、request 已提取的需求
        """

        # copy() 创建浅拷贝，避免修改原始 state
        state = prev_state.copy()
        state["user_input"] = new_user_input  # 新输入覆盖旧输入

        # 清理上一轮的中间产物
        # 这些字段会由工作流重新生成
        for key in [
            "clarification_questions",
            "final_plan",
            "missing_fields",
            "is_info_complete",
            "required_tools",
            "context",
            "draft_plan",
            "reflection",
            "need_revision",
            "stop_reason",
        ]:
            # pop(key, None) 删除 key，如果不存在也不报错
            state.pop(key, None)

        return state

    def _format_response(self, result: dict, session_id: Optional[str]) -> dict:
        """
        把 LangGraph 的完整 state 格式化为前端需要的响应格式。

        区分两种情况：
        1. need_user_clarification → 返回追问问题和提示消息
        2. completed → 返回完整方案
        """

        stop_reason = result.get("stop_reason", "unknown")

        if stop_reason == "need_user_clarification":
            return {
                "status": "need_user_clarification",
                "need_user_input": True,
                "clarification_questions": result.get("clarification_questions", []),
                "message": result.get("final_plan", ""),  # 这里是追问消息文本
                "session_id": session_id,
            }

        return {
            "status": "completed",
            "final_plan": result.get("final_plan", ""),
            "stop_reason": stop_reason,
            "revision_count": result.get("revision_count", 0),
            "need_user_input": False,
            "clarification_questions": [],
            "session_id": session_id,
        }


# 全局单例
planner_service = PlannerService()
