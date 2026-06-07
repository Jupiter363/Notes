"""端到端工作流测试。

注意：这些测试需要有效的 OPENAI_API_KEY 环境变量才能运行。
在没有 API key 的环境下，可通过 mock LLM 调用来测试。
"""

import os
import pytest


@pytest.fixture
def requires_api_key():
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("需要 OPENAI_API_KEY 环境变量")


class TestWorkflowSuccess:
    def test_complete_input_generates_plan(self, requires_api_key):
        from app.graph.workflow import build_graph

        graph = build_graph()
        result = graph.invoke({
            "user_input": "我想6月底去成都玩3天，预算3000元，喜欢美食和轻松路线",
            "max_revision_count": 2,
        })

        assert "final_plan" in result
        assert "成都" in result["final_plan"]
        assert result["revision_count"] <= 2

    def test_revision_count_within_limit(self, requires_api_key):
        from app.graph.workflow import build_graph

        graph = build_graph()
        result = graph.invoke({
            "user_input": "想去成都玩3天，预算3000，喜欢美食和自然风光",
            "max_revision_count": 2,
        })

        assert result["revision_count"] <= result.get("max_revision_count", 2)


class TestWorkflowMissingInfo:
    def test_missing_info_triggers_clarification(self, requires_api_key):
        from app.graph.workflow import build_graph

        graph = build_graph()
        result = graph.invoke({"user_input": "我想出去玩"})

        assert result["stop_reason"] == "need_user_clarification"
        assert len(result["clarification_questions"]) > 0

    def test_missing_info_output_has_message(self, requires_api_key):
        from app.graph.workflow import build_graph

        graph = build_graph()
        result = graph.invoke({"user_input": "帮我规划旅行"})

        assert "final_plan" in result
        assert "请先补充" in result.get("final_plan", "")
