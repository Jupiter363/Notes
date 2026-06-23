"""
预算估算工具 (Budget Estimation Tool)
======================================

在旅行规划 Agent 的架构中，本工具负责**根据目的地、天数、预算计算费用分配方案**。

Agent 调用链中的位置：
  用户："我有3000块预算，在成都玩3天够吗？"
       ↓
  LLM → 调用 estimate_budget(city="成都", days=3, budget=3000)
       ↓
  返回每日明细 + 总预算对比 + 是否超预算
       ↓
  LLM → "成都3天预计花费1800元，在您的3000元预算内，绰绰有余！"

核心功能：
  1. **城市差异化定价**：不同城市有不同的日均消费标准
  2. **预算对比**：将估算花费与用户预算做对比，给出 over_budget / within_budget 判断
  3. **分类明细**：住宿/餐饮/交通/门票/其他，让 LLM 知道钱花在哪里

相关概念（§3 Tool Calling）：
  - 工具参数的类型标注如何帮助 LLM 正确传参
  - 浮点数阈值判断与 Agent 决策逻辑
"""

from datetime import date
from langchain_core.tools import tool


@tool
def estimate_budget(city: str, days: int, budget: float = 0) -> dict:
    """
    根据城市、天数和预算给出花费估算和分配建议。

    LLM 调用时传三个参数：
      city   → 目的地城市
      days   → 旅行天数
      budget → 用户的总预算（元），默认 0 表示"无预算限制"

    返回的 budget_status 字段帮助 LLM 快速判断预算是否充足。

    Args:
        city:   城市名称
        days:   旅行天数
        budget: 用户预算（元），0 表示不设限

    Returns:
        dict: 符合 ToolResult 协议的预算分析
              - data.daily_breakdown: dict，分类别每日花费
              - data.budget_status:  "within_budget" / "over_budget" / "slightly_over"
              - data.total_estimate: int，预估总花费
    """  # noqa: D401
    # -----------------------------------------------------------------
    # 城市差异化定价表
    # -----------------------------------------------------------------
    # 为什么不同城市有不同定价？
    #   真实的旅行成本因城市而异：北京上海住宿贵、西安大理便宜。
    #   如果用统一价格，"成都玩3天500元"和"上海玩3天500元"
    #   给出相同预算估算，这就失去了工具的参考价值。
    #
    # 数据结构：dict of dict
    #   外层 key = 城市名
    #   内层 dict = 分类别日均花费（住宿/餐饮/交通/门票/其他）
    #
    # 为什么不细分住宿等级（如青旅/经济型/豪华）？
    #   这是 V1 的简化设计。后续版本可以让 budget 参数做更多事情：
    #   budget <= 2000 → 预算模式（青旅+小吃）
    #   budget > 5000  → 舒适模式（星级酒店+正餐）
    daily_estimates = {
        "成都": {"住宿": 250, "餐饮": 150, "交通": 50, "门票": 80, "其他": 70},
        "北京": {"住宿": 400, "餐饮": 180, "交通": 60, "门票": 120, "其他": 80},
        "上海": {"住宿": 450, "餐饮": 200, "交通": 50, "门票": 100, "其他": 80},
        "杭州": {"住宿": 300, "餐饮": 160, "交通": 50, "门票": 100, "其他": 70},
        "西安": {"住宿": 200, "餐饮": 120, "交通": 40, "门票": 100, "其他": 60},
        "大理": {"住宿": 200, "餐饮": 100, "交通": 40, "门票": 60, "其他": 50},
    }

    # dict.get() 兜底：未知城市用通用价格
    estimate = daily_estimates.get(city, {"住宿": 300, "餐饮": 150, "交通": 50, "门票": 80, "其他": 70})

    # -----------------------------------------------------------------
    # 费用计算
    # -----------------------------------------------------------------
    # sum(estimate.values()) → 将字典所有 value 相加，得到每日总花费
    # 例如成都：250+150+50+80+70 = 600 元/天
    daily_total = sum(estimate.values())

    # 总花费 = 每日花费 × 天数
    total_estimate = daily_total * days

    # -----------------------------------------------------------------
    # 预算对比逻辑
    # -----------------------------------------------------------------
    # budget_status 有三个取值，用阈值判断：
    #
    #   within_budget   → ratio <= 0.95（花费在预算的95%以内）
    #   slightly_over   → 0.95 < ratio <= 1.2（花费略超预算，在20%以内）
    #   over_budget     → ratio > 1.2（花费远超预算）
    #
    # 为什么阈值是 0.95 和 1.2 而不是精确的 1.0？
    #   旅行花费有波动（突发交通、意外消费），留出缓冲区间更符合实际情况。
    #   95%以内算"够"、120%以上算"超"、中间是"略超"，这是经验法则。
    #
    # 为什么 budget=0 时不触发 over_budget？
    #   因为 0 表示"用户没有设定预算"，此时 ratio 无意义，
    #   budget_status 保持初始值 "within_budget"。
    budget_status = "within_budget"
    if budget > 0:
        ratio = total_estimate / budget
        if ratio > 1.2:          # 超出预算 20% 以上
            budget_status = "over_budget"
        elif ratio > 0.95:       # 超出预算但不到 20%
            budget_status = "slightly_over"
        # else: ratio <= 0.95，保持 within_budget

    # -----------------------------------------------------------------
    # 返回 ToolResult 格式
    # -----------------------------------------------------------------
    return {
        "data": {
            "city": city,
            "days": days,
            "daily_breakdown": estimate,       # 分类别日均明细
            "daily_total": daily_total,         # 日均总花费
            "total_estimate": total_estimate,   # 全程预估总花费
            "user_budget": budget,              # 用户的预算（原样传回，方便 LLM 对比）
            "budget_status": budget_status,     # 预算充足度判断
            # suggestion 是预生成的人类可读建议
            # 用 f-string 直接嵌入数值，LLM 可以直接引用或改写
            "suggestion": f"建议每日住宿{estimate['住宿']}元，餐饮{estimate['餐饮']}元，总计约{total_estimate}元",
        },
        "source": "mock_budget",
        "updated_at": str(date.today()),
        "confidence": "mock",
        "error": None,
    }


# =============================================================================
# 为什么 estimate 是 dict 而不是 dataclass？
# =============================================================================
# 用 dict 的好处：
#   1. 不需要额外定义类，代码更简洁
#   2. 与 ToolResult 协议一致（data 字段本身就是 dict）
#   3. LLM 对 JSON-like 结构（dict/list）的解析比自定义对象更自然
#
# 用 dataclass 的好处（后续改进方向）：
#   1. 类型安全：IDE 自动补全，mypy 静态检查
#   2. 字段不可变（frozen=True）：防止意外修改
#   3. 文档化：字段定义即文档
#
# 当前选择 dict 是因为工具数量少、结构简单，引入 dataclass 是过度工程。
# 当工具数量增长到 10+ 时，建议迁移到 dataclass 或 Pydantic BaseModel。
# =============================================================================
