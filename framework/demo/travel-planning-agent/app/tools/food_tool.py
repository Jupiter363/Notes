from datetime import date
from langchain_core.tools import tool


@tool
def search_foods(city: str, preferences: list | None = None) -> dict:
    """根据城市和偏好搜索当地美食。"""
    mock_data = {
        "成都": [
            {"name": "火锅", "category": "正餐", "avg_cost": 120, "note": "推荐蜀大侠、小龙坎，微辣即可体验地道风味"},
            {"name": "串串香", "category": "正餐", "avg_cost": 60, "note": "冷锅串串和热锅串串两种，人均实惠"},
            {"name": "担担面", "category": "小吃", "avg_cost": 15, "note": "成都名小吃，麻辣鲜香"},
            {"name": "龙抄手", "category": "小吃", "avg_cost": 20, "note": "皮薄馅大，红油或清汤均可"},
            {"name": "钟水饺", "category": "小吃", "avg_cost": 20, "note": "甜水面风格，红油加蒜泥"},
            {"name": "麻婆豆腐", "category": "正餐", "avg_cost": 30, "note": "陈麻婆豆腐总店最正宗"},
            {"name": "夫妻肺片", "category": "凉菜", "avg_cost": 35, "note": "牛肉牛杂加红油，经典凉菜"},
            {"name": "三大炮", "category": "甜品", "avg_cost": 10, "note": "糯米团加红糖，宽窄巷子随处可见"},
            {"name": "茶馆盖碗茶", "category": "饮品", "avg_cost": 30, "note": "人民公园鹤鸣茶社是经典去处"},
        ],
        "default": [
            {"name": f"{city}本地特色菜", "category": "正餐", "avg_cost": 80, "note": ""},
            {"name": f"{city}夜市小吃", "category": "小吃", "avg_cost": 40, "note": ""},
            {"name": f"{city}网红餐厅", "category": "正餐", "avg_cost": 100, "note": ""},
            {"name": f"{city}早餐", "category": "小吃", "avg_cost": 15, "note": ""},
        ],
    }

    data = mock_data.get(city, mock_data["default"])

    if preferences:
        food_prefs = [p for p in preferences if p in ("美食", "food")]
        if not food_prefs:
            data = data[:3]

    return {
        "data": data,
        "source": "mock_foods",
        "updated_at": str(date.today()),
        "confidence": "mock",
        "error": None,
    }
