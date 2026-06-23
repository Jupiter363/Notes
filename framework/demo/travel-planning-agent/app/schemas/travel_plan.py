"""
旅行计划数据模型 —— 定义"AI 生成的旅行方案长什么样"。

这是整个 Agent 系统最核心的输出结构。LLM 不是输出一段自由文本，
而是输出这个严格结构的 JSON，然后代码可以逐层检查：
- 总预算超了吗？
- 某一天是不是太赶了（超过 4 个活动）？
- 每个活动的花费加起来对吗？

三层嵌套结构：TravelPlan → DayPlan → Activity
就像真实的旅行计划：一个方案包含多天，每天包含多个活动。

Stage 2 对应概念：§4 Plan-and-Execute（Plan 的结构化定义）
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class Activity(BaseModel):
    """
    一个具体活动。

    这是最底层的粒度——每天由 2-4 个 Activity 组成。
    每个 Activity 不仅有"做什么"，还有"为什么这样安排"（reason）、
    "怎么去"（transport_note）、"有什么风险"（risk_note）。

    这就是 Agent 和普通 Chatbot 的区别：
    Chatbot 说"上午去宽窄巷子"；
    Agent 说"上午去宽窄巷子，因为这是成都标志性景点且免费，
    坐地铁 4 号线直达，注意周末人多需要排队"。
    """

    # 时段：morning / afternoon / evening
    # 这里不用 Enum，因为 LLM 可能输出小写变体，String 更宽容
    time_slot: str = Field(description="morning/afternoon/evening")

    # 活动名称 —— 如"宽窄巷子"、"大熊猫基地"
    title: str

    # 地点 —— 可选，有些活动（如"自由探索"）不需要具体地址
    location: Optional[str] = None

    # ── 以下是 Agent 比 Chatbot 多出的结构化字段 ──

    # 安排理由 —— Agent 的"思考"，解释为什么选这个活动、这个时段
    reason: str = Field(description="为什么这样安排")

    # 预计花费 —— 用于累加计算总预算
    estimated_cost: float = 0

    # 持续时长（小时）—— 用于判断行程是否过满
    duration_hours: Optional[float] = None

    # 交通提示 —— 怎么去、坐几号线、大概多久
    transport_note: Optional[str] = None

    # 风险提示 —— 天气影响、排队、价格变动等
    risk_note: Optional[str] = None


class DayPlan(BaseModel):
    """
    一天的安排。

    每天有一个主题（theme），包含若干 Activity。
    pace_level 表示这一天是轻松、正常还是紧凑——
    reflection_chain 会检查 pace_level 是否合理。
    """

    # 第几天 —— 从 1 开始
    day: int

    # 当日主题 —— 如 "成都美食探索"、"首尔购物之旅"
    theme: str

    # 当天的活动列表
    activities: List[Activity]

    # 当天预计总花费 —— 由每日活动的 estimated_cost 累加
    daily_estimated_cost: float

    # 当天节奏 —— relaxed（轻松）/ normal（正常）/ tight（紧凑）
    pace_level: str = Field(description="relaxed/normal/tight")

    # 备注 —— 如 "这天是周日，有些店铺可能休息"
    notes: List[str] = Field(default_factory=list)


class TravelPlan(BaseModel):
    """
    完整的旅行方案。

    这是 generate_plan_node 调用 LLM 后的输出，也是 reflect_plan_node
    审查的对象。包含目的地、总天数、总预算、每日安排、偏好匹配度、
    风险提示和数据局限性说明。
    """

    # 目的地 —— 从 TravelRequest 继承
    destination: str

    # 总天数 —— 从 TravelRequest 继承
    total_days: int

    # 用户总预算 —— 从 TravelRequest 继承
    total_budget: float

    # 每日安排的列表
    days: List[DayPlan]

    # 总预计花费 —— 所有 DayPlan 的 daily_estimated_cost 之和
    total_estimated_cost: float

    # 预算状态 —— within_budget / slightly_over / over_budget / unknown
    # LLM 会根据 total_estimated_cost 和 total_budget 的比例自动判断
    budget_status: str = Field(
        description="within_budget/slightly_over/over_budget/unknown"
    )

    # ── 以下是 Agent 的"自检"字段 ──

    # 偏好匹配说明 —— LLM 解释为什么这个方案符合用户的偏好
    # 如 "3天安排了8种成都特色美食，每天节奏轻松，符合美食+轻松的偏好"
    preference_match_notes: List[str] = Field(default_factory=list)

    # 风险提示 —— 天气、交通、价格等方面的风险
    risk_notes: List[str] = Field(default_factory=list)

    # 数据局限性 —— 如果用的 mock 数据或低置信度信息，在这里说明
    # 如 "天气数据为 mock，实际出行前建议查询实时预报"
    data_limitations: List[str] = Field(default_factory=list)
