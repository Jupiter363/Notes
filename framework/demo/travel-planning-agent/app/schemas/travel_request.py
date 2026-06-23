"""
旅行需求数据模型 —— 定义"用户想要什么"。

在 Agent 系统里，用户输入的自然语言（"我想去成都玩3天"）需要被转成
结构化数据，代码才能判断"信息够不够"、"该调哪些工具"。

Pydantic 是 Python 的数据校验库：
- BaseModel: 定义一个结构化数据类，类似 dataclass 但更强
- Field: 给字段加约束和描述（如 ge=1 表示 >=1）
- Optional: 表示这个字段可以为 None（用户可能没说）

Stage 2 对应概念：§3 结构化输出（Structured Output）
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class TravelPreference(str, Enum):
    """
    旅行偏好的可选值。

    Enum 是一种枚举类型——变量的值只能是预设的几个选项之一。
    这里继承 str，所以 "美食" 既是 TravelPreference.food 也是字符串 "美食"。
    """
    food = "美食"
    relaxed = "轻松"
    nature = "自然风光"
    culture = "历史文化"
    shopping = "购物"
    parent_child = "亲子"
    photography = "拍照"


class TravelRequest(BaseModel):
    """
    从用户输入中解析出的结构化旅行需求。

    每个字段都是 Optional（可选），因为用户可能一次没说全。
    比如只说"我想出去玩"，那 destination/days/budget 都是 None，
    后续 check_info_node 会检测到缺失并触发追问。

    Field 参数说明：
    - default=None: 默认值，用户没提就是这个值
    - ge=1, le=30: 数值范围约束，Pydantic 会自动校验
    - description: 给 LLM 看的字段说明（会注入到 Prompt 里）
    """

    # 目的地 —— 如"成都"、"韩国首尔"、"东京"
    destination: Optional[str] = Field(
        default=None,
        description="目的地城市或地区"
    )

    # 出发日期 —— 如"6月底"、"7月15日"、"下周末"
    start_date: Optional[str] = Field(
        default=None,
        description="出发日期或时间范围，例如 6 月底"
    )

    # 旅行天数 —— 必须 >=1 且 <=30，Pydantic 自动校验
    days: Optional[int] = Field(
        default=None,
        ge=1,   # greater than or equal to 1
        le=30,  # less than or equal to 30
        description="旅行天数"
    )

    # 总预算 —— 单位元，必须 >=0
    budget: Optional[float] = Field(
        default=None,
        ge=0,
        description="总预算，单位元"
    )

    # 偏好列表 —— 如 ["美食", "轻松"]，可以为空列表
    # default_factory=list 是 Python 惯用法：每个实例独立的空列表
    preferences: List[str] = Field(
        default_factory=list,
        description="旅行偏好"
    )

    # 同行人 —— "独自"、"情侣"、"亲子" 等
    companions: Optional[str] = Field(
        default=None,
        description="同行人，例如独自、情侣、朋友、亲子"
    )

    # 出发城市 —— 可选，如果用户不提就默认不需要
    departure_city: Optional[str] = Field(
        default=None,
        description="出发城市，可选"
    )

    # 旅行节奏 —— "轻松"、"适中"、"紧凑"
    pace: Optional[str] = Field(
        default=None,
        description="旅行节奏，例如轻松、适中、紧凑"
    )
