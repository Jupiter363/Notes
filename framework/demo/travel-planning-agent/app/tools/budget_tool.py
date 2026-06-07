from datetime import date
from langchain_core.tools import tool


@tool
def estimate_budget(city: str, days: int, budget: float = 0) -> dict:
    """根据城市、天数和预算给出花费估算和分配建议。"""
    daily_estimates = {
        "成都": {"住宿": 250, "餐饮": 150, "交通": 50, "门票": 80, "其他": 70},
        "北京": {"住宿": 400, "餐饮": 180, "交通": 60, "门票": 120, "其他": 80},
        "上海": {"住宿": 450, "餐饮": 200, "交通": 50, "门票": 100, "其他": 80},
        "杭州": {"住宿": 300, "餐饮": 160, "交通": 50, "门票": 100, "其他": 70},
        "西安": {"住宿": 200, "餐饮": 120, "交通": 40, "门票": 100, "其他": 60},
        "大理": {"住宿": 200, "餐饮": 100, "交通": 40, "门票": 60, "其他": 50},
    }

    estimate = daily_estimates.get(city, {"住宿": 300, "餐饮": 150, "交通": 50, "门票": 80, "其他": 70})
    daily_total = sum(estimate.values())
    total_estimate = daily_total * days

    budget_status = "within_budget"
    if budget > 0:
        ratio = total_estimate / budget
        if ratio > 1.2:
            budget_status = "over_budget"
        elif ratio > 0.95:
            budget_status = "slightly_over"

    return {
        "data": {
            "city": city,
            "days": days,
            "daily_breakdown": estimate,
            "daily_total": daily_total,
            "total_estimate": total_estimate,
            "user_budget": budget,
            "budget_status": budget_status,
            "suggestion": f"建议每日住宿{estimate['住宿']}元，餐饮{estimate['餐饮']}元，总计约{total_estimate}元",
        },
        "source": "mock_budget",
        "updated_at": str(date.today()),
        "confidence": "mock",
        "error": None,
    }
