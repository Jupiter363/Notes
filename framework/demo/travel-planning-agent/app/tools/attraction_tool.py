from datetime import date
from langchain_core.tools import tool


@tool
def search_attractions(city: str, preferences: list | None = None) -> dict:
    """根据城市和偏好搜索景点。"""
    mock_data = {
        "成都": [
            {"name": "宽窄巷子", "type": "历史文化", "rating": 4.5, "estimated_cost": 0, "duration_hours": 2.5, "note": "免费，适合拍照和美食"},
            {"name": "锦里古街", "type": "历史文化", "rating": 4.4, "estimated_cost": 0, "duration_hours": 2, "note": "夜间更有氛围"},
            {"name": "大熊猫繁育研究基地", "type": "自然风光", "rating": 4.8, "estimated_cost": 55, "duration_hours": 3.5, "note": "建议早上去，熊猫更活跃"},
            {"name": "都江堰", "type": "自然风光", "rating": 4.6, "estimated_cost": 90, "duration_hours": 5, "note": "离市区约1小时车程"},
            {"name": "人民公园", "type": "轻松", "rating": 4.3, "estimated_cost": 0, "duration_hours": 1.5, "note": "喝盖碗茶，体验成都慢生活"},
            {"name": "春熙路/太古里", "type": "购物", "rating": 4.5, "estimated_cost": 0, "duration_hours": 2, "note": "成都核心商圈"},
            {"name": "武侯祠", "type": "历史文化", "rating": 4.4, "estimated_cost": 60, "duration_hours": 2, "note": "三国文化圣地"},
            {"name": "青羊宫", "type": "历史文化", "rating": 4.2, "estimated_cost": 10, "duration_hours": 1.5, "note": "道教名观"},
        ],
        "default": [
            {"name": f"{city}中心景区", "type": "自然风光", "rating": 4.0, "estimated_cost": 50, "duration_hours": 3, "note": ""},
            {"name": f"{city}博物馆", "type": "历史文化", "rating": 4.2, "estimated_cost": 30, "duration_hours": 2, "note": ""},
            {"name": f"{city}美食街", "type": "美食", "rating": 4.3, "estimated_cost": 0, "duration_hours": 2, "note": ""},
            {"name": f"{city}城市公园", "type": "轻松", "rating": 4.1, "estimated_cost": 0, "duration_hours": 1.5, "note": ""},
        ],
    }

    data = mock_data.get(city, mock_data["default"])

    if preferences:
        data = [item for item in data if any(p in item.get("type", "") for p in preferences)]

    return {
        "data": data,
        "source": "mock_attractions",
        "updated_at": str(date.today()),
        "confidence": "mock",
        "error": None,
    }
