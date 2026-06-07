"""测试用户补充信息后续跑流程。

注意：这些测试需要有效的 OPENAI_API_KEY 环境变量。
"""

import os
import pytest


@pytest.fixture
def requires_api_key():
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("需要 OPENAI_API_KEY 环境变量")


class TestFollowupAfterClarification:
    def test_prepare_followup_state(self):
        from app.services.planner_service import PlannerService

        svc = PlannerService()
        prev_state = {
            "user_input": "我想出去玩",
            "request": {},
            "missing_fields": ["destination", "days", "budget", "preferences"],
            "clarification_questions": ["你想去哪？"],
            "final_plan": "请先补充...",
            "stop_reason": "need_user_clarification",
        }
        new_state = svc._prepare_followup_state(prev_state, "去成都，3天，预算3000，喜欢美食")
        assert new_state["user_input"] == "去成都，3天，预算3000，喜欢美食"
        assert "clarification_questions" not in new_state
        assert "final_plan" not in new_state
        request_in_state = new_state.get("request")
        assert request_in_state is not None

    def test_followup_completes_plan(self, requires_api_key):
        from app.graph.workflow import build_graph

        graph = build_graph()

        result1 = graph.invoke({"user_input": "我想出去玩"})
        assert result1["stop_reason"] == "need_user_clarification"

        from app.services.planner_service import PlannerService
        svc = PlannerService()
        state2 = svc._prepare_followup_state(
            result1,
            "去成都，3天，预算3000，喜欢美食和轻松路线",
        )

        result2 = graph.invoke(state2)
        assert "final_plan" in result2
        assert "成都" in result2["final_plan"]

    def test_planner_service_continue_plan(self, requires_api_key):
        from app.services.planner_service import planner_service, session_service

        session_id = session_service.create_session()
        result1 = planner_service.plan("我想出去玩", session_id=session_id)

        if result1["status"] == "need_user_clarification":
            result2 = planner_service.continue_plan(
                session_id,
                "去成都，3天，预算3000，喜欢美食和轻松",
            )
            assert result2["status"] == "completed"
            assert "成都" in result2["final_plan"]
