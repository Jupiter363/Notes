from datetime import date
from langchain_core.tools import tool


@tool
def search_transport(city: str, start_date: str = "") -> dict:
    """查询市内交通建议和出行提示。"""
    transport_info = {
        "成都": {
            "metro": "地铁线路覆盖主城区，1/2/3/4/7号线可到达大多数景点",
            "bus": "公交线路密集，天府通卡通用",
            "taxi": "起步价8元，网约车方便",
            "bike": "共享单车覆盖全城，短距离推荐",
            "airport": "双流机场和天府机场，地铁可直达双流",
            "tips": ["高峰期（7:30-9:00, 17:30-19:00）地铁较拥挤", "去都江堰可在犀浦站坐城际列车"],
        },
        "default": {
            "metro": f"{city}地铁覆盖主城区",
            "bus": "公交线路可达主要景点",
            "taxi": "网约车方便快捷",
            "bike": "共享单车适合短途出行",
            "airport": f"{city}机场有公共交通连接市区",
            "tips": ["建议下载当地交通App查询实时信息"],
        },
    }

    return {
        "data": transport_info.get(city, transport_info["default"]),
        "source": "mock_transport",
        "updated_at": str(date.today()),
        "confidence": "mock",
        "error": None,
    }
