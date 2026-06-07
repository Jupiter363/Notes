from datetime import date
from langchain_core.tools import tool


@tool
def web_search(query: str) -> dict:
    """搜索最新的景点营业时间、票价、临时通知等实时信息。"""
    return {
        "data": {
            "query": query,
            "results": [
                {"title": f"关于「{query}」的搜索结果", "snippet": "此为 mock 搜索结果。实际部署时接入搜索 API 获取最新信息。", "url": ""},
            ],
            "note": "mock 数据，建议出行前在官方渠道确认最新信息",
        },
        "source": "mock_search",
        "updated_at": str(date.today()),
        "confidence": "low",
        "error": None,
    }
