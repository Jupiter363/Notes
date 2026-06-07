from typing import Optional
from app.graph.workflow import build_graph
from app.services.session_service import session_service


class PlannerService:
    def __init__(self):
        self.graph = build_graph()

    def plan(self, user_input: str, session_id: Optional[str] = None, max_revision_count: int = 2) -> dict:
        state = {
            "user_input": user_input,
            "max_revision_count": max_revision_count,
        }
        result = self.graph.invoke(state)

        if session_id:
            session_service.update_state(session_id, result)

        return self._format_response(result, session_id)

    def continue_plan(self, session_id: str, user_input: str) -> dict:
        prev_state = session_service.get_state(session_id)
        if not prev_state:
            return {
                "status": "error",
                "message": f"会话 {session_id} 不存在或已过期",
                "need_user_input": False,
            }

        state = self._prepare_followup_state(prev_state, user_input)
        result = self.graph.invoke(state)
        session_service.update_state(session_id, result)

        return self._format_response(result, session_id)

    def _prepare_followup_state(self, prev_state: dict, new_user_input: str) -> dict:
        state = prev_state.copy()
        state["user_input"] = new_user_input

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
            state.pop(key, None)

        return state

    def _format_response(self, result: dict, session_id: Optional[str]) -> dict:
        stop_reason = result.get("stop_reason", "unknown")

        if stop_reason == "need_user_clarification":
            return {
                "status": "need_user_clarification",
                "need_user_input": True,
                "clarification_questions": result.get("clarification_questions", []),
                "message": result.get("final_plan", ""),
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


planner_service = PlannerService()
