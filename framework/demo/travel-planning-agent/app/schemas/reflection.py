"""
审查结果数据模型 —— 定义"AI 审查自己的计划后给出什么反馈"。

这是 Reflection 范式的核心数据结构。LLM 以"审查员"角色审视 TravelPlan，
输出结构化的评分、问题列表、修正建议，然后路由节点根据 need_revision
决定是修正还是输出。

审查不是让 LLM"随便说两句"，而是强制输出这个结构，这样：
- 代码可以判断 need_revision 决定走修正还是输出
- blocking_issues 和 issues 分开，修正时优先处理阻断性问题
- score 可以用于评估计划质量和监控 Agent 性能

Stage 2 对应概念：§5 Reflection / Reflexion
"""

from pydantic import BaseModel, Field
from typing import List


class ReflectionResult(BaseModel):
    """
    LLM 审查计划后的结构化反馈。

    核心字段是 need_revision —— 代码靠它决定下一步走 revise_plan
    还是 final_output。如果 need_revision=True，suggestions 里的
    每条建议都会传给 revise_chain 做针对性修正。
    """

    # 是否需要修正 —— 整个 Reflection 循环的开关
    # True → 走 revise_plan；False → 走 final_output
    need_revision: bool

    # 质量评分 1-10 —— Pydantic 自动校验范围
    # 9-10: 优秀，可直接采纳
    # 7-8: 有小问题，可接受
    # 5-6: 有明显问题，建议修正
    # 1-4: 严重问题，必须修正
    score: int = Field(ge=1, le=10)

    # 一般问题 —— 如 "第2天下午活动有点赶"
    issues: List[str] = Field(default_factory=list)

    # 修正建议 —— 如 "建议把第2天的购物移到第3天上午"
    suggestions: List[str] = Field(default_factory=list)

    # 阻断性问题 —— 严重到必须修正的问题
    # 如 "总花费超出预算 200%"、"第3天全是户外活动但那天暴雨"
    # revise_chain 会优先处理这些
    blocking_issues: List[str] = Field(default_factory=list)

    # 是否可以直接采纳 —— True 时跳过修正直达输出
    # 这个字段给了 LLM "一票通过"的权力：质量好就不折腾
    accepted_as_final: bool = False
