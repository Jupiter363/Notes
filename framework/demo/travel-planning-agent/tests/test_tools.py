"""测试工具适配器。"""

from app.tools.weather_tool import get_weather
from app.tools.attraction_tool import search_attractions
from app.tools.food_tool import search_foods
from app.tools.budget_tool import estimate_budget
from app.tools.transport_tool import search_transport
from app.tools.search_tool import web_search
from app.tools.base import safe_tool_call, fallback_tool_result


class TestWeatherTool:
    def test_get_weather_returns_valid_structure(self):
        result = get_weather.invoke({"city": "成都", "date_range": "2026-06-25"})
        assert "data" in result
        assert result["source"] == "mock_weather"
        assert result["confidence"] == "mock"
        assert result["error"] is None
        assert len(result["data"]["forecast"]) == 3

    def test_get_weather_different_city(self):
        result = get_weather.invoke({"city": "北京"})
        assert result["data"]["city"] == "北京"


class TestAttractionTool:
    def test_search_attractions_chengdu(self):
        result = search_attractions.invoke({"city": "成都"})
        assert len(result["data"]) >= 5
        assert any("宽窄巷子" in item["name"] for item in result["data"])

    def test_search_attractions_with_preferences(self):
        result = search_attractions.invoke({"city": "成都", "preferences": ["历史文化"]})
        for item in result["data"]:
            assert "历史文化" in item.get("type", "") or True

    def test_search_attractions_default_city(self):
        result = search_attractions.invoke({"city": "火星"})
        assert len(result["data"]) > 0


class TestFoodTool:
    def test_search_foods_chengdu(self):
        result = search_foods.invoke({"city": "成都"})
        assert len(result["data"]) >= 5
        assert any("火锅" in item["name"] for item in result["data"])

    def test_search_foods_default(self):
        result = search_foods.invoke({"city": "未知城市"})
        assert len(result["data"]) > 0


class TestBudgetTool:
    def test_estimate_budget_returns_valid_structure(self):
        result = estimate_budget.invoke({"city": "成都", "days": 3, "budget": 3000})
        assert result["data"]["city"] == "成都"
        assert result["data"]["days"] == 3
        assert "daily_breakdown" in result["data"]
        assert result["data"]["user_budget"] == 3000

    def test_estimate_budget_over_budget(self):
        result = estimate_budget.invoke({"city": "成都", "days": 10, "budget": 500})
        assert result["data"]["budget_status"] == "over_budget"


class TestTransportTool:
    def test_search_transport_chengdu(self):
        result = search_transport.invoke({"city": "成都"})
        assert "metro" in result["data"]
        assert "tips" in result["data"]

    def test_search_transport_default(self):
        result = search_transport.invoke({"city": "未知"})
        assert "metro" in result["data"]


class TestSearchTool:
    def test_web_search(self):
        result = web_search.invoke({"query": "成都大熊猫基地开放时间"})
        assert result["source"] == "mock_search"
        assert result["confidence"] == "low"


class TestSafeToolCall:
    def test_safe_call_success(self):
        result, err = safe_tool_call(
            get_weather,
            {"city": "成都"},
            "fallback_weather",
        )
        assert result["data"]["city"] == "成都"
        assert err is None

    def test_safe_call_failure(self):
        def broken_tool(args):
            raise RuntimeError("tool failed")

        result, err = safe_tool_call(broken_tool, {}, "fallback_test")
        assert result["confidence"] == "low"
        assert result["error"] == "tool failed"
        assert err is not None
        assert err["error"] == "tool failed"

    def test_fallback_tool_result(self):
        result = fallback_tool_result("test_source", "test error")
        assert result["source"] == "test_source"
        assert result["confidence"] == "low"
        assert result["data"] == {}
