from datetime import date
from langchain_core.tools import tool


@tool
def get_weather(city: str, date_range: str = "") -> dict:
    """查询城市的天气信息与出行风险。"""
    return {
        "data": {
            "city": city,
            "forecast": [
                {"date": "2026-06-25", "weather": "晴转多云", "temp_high": 29, "temp_low": 21, "rain_prob": "10%"},
                {"date": "2026-06-26", "weather": "多云", "temp_high": 30, "temp_low": 22, "rain_prob": "20%"},
                {"date": "2026-06-27", "weather": "阵雨", "temp_high": 28, "temp_low": 20, "rain_prob": "60%"},
            ],
            "risk": "第三天可能有阵雨，建议带雨具，户外景点安排在上午",
        },
        "source": "mock_weather",
        "updated_at": str(date.today()),
        "confidence": "mock",
        "error": None,
    }
