"""测试工具失败不中断工作流。"""

import os
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def requires_api_key():
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("需要 OPENAI_API_KEY 环境变量")


def _make_broken_tool():
    """创建一个调用时会抛出异常的 mock 工具。"""
    mock = MagicMock()
    mock.invoke.side_effect = RuntimeError("tool api failed")
    mock.name = "broken_tool"
    return mock


class TestToolFailureDoesNotBreakWorkflow:
    def test_workflow_handles_broken_tool(self, requires_api_key):
        from app.graph.workflow import build_graph

        broken = _make_broken_tool()

        # Patch where the tool is USED (app.graph.nodes), not where it's defined
        with patch("app.graph.nodes.get_weather", broken):
            graph = build_graph()
            result = graph.invoke({
                "user_input": "我想6月底去成都玩3天，预算3000元，喜欢美食",
                "max_revision_count": 2,
            })

        assert "final_plan" in result
        assert len(result.get("tool_errors", [])) > 0

    def test_all_tools_fail_still_generates_plan(self, requires_api_key):
        from app.graph.workflow import build_graph

        broken = _make_broken_tool()

        with (
            patch("app.graph.nodes.get_weather", broken),
            patch("app.graph.nodes.search_attractions", broken),
            patch("app.graph.nodes.search_foods", broken),
            patch("app.graph.nodes.estimate_budget", broken),
            patch("app.graph.nodes.search_transport", broken),
        ):
            graph = build_graph()
            result = graph.invoke({
                "user_input": "我想6月底去成都玩3天，预算3000元，喜欢美食",
                "max_revision_count": 2,
            })

        assert "final_plan" in result
        assert len(result.get("tool_errors", [])) >= 1
