"""
条件路由器 —— Agent 工作流的"路口交警"。

在 LangGraph 中，Router 是一个返回字符串的函数，字符串的值
决定下一步走哪个节点。这就是 Stage 2 §7 说的 Router Agent 思想——
根据当前状态动态决定下一步做什么。

和"自由 Agent 动态决策"的区别：
- 这里的路由逻辑是开发者写好的 Python 代码，不是 LLM 决定的
- 判断依据是 State 中的结构化字段（is_info_complete、need_revision 等）
- 可测试、可预测、不会"走错路"

两个路由器：
1. route_after_check —— 信息完整吗？完整走工具，不完整走追问
2. route_after_reflection —— 需要修正吗？需要且未超次数走修正，否则输出
"""

from typing import Literal
from app.graph.state import TravelState


def route_after_check(state: TravelState) -> Literal["ask_clarification", "decide_tools"]:
    """
    信息完整性检查后的路由。

    从 State 中读取 is_info_complete（由 check_info_node 设置），
    决定下一步是追问用户还是继续走工具选择。

    Literal[...] 是 Python 的类型提示，告诉 IDE 和类型检查器
    这个函数只能返回这两个字符串之一，不能返回其他值。
    """
    if state.get("is_info_complete"):
        # 用户的旅行需求信息齐全 → 进入工具选择和调用流程
        return "decide_tools"
    # 信息不全（如缺少目的地、天数、预算）→ 生成追问问题
    return "ask_clarification"


def route_after_reflection(state: TravelState) -> Literal["revise_plan", "final_output"]:
    """
    Reflection 审查后的路由 —— 实现修正循环的核心。

    这个函数决定了 Reflection 循环是否继续：
    - accepted_as_final=True → 直达输出
    - need_revision=True 且次数未超 → 走修正节点
    - 否则 → 直达输出

    退出条件（对应 Stage 2 §5.8 Reflection 工程约束）：
    1. LLM 判定质量合格（accepted_as_final=True）
    2. 不需要修正（need_revision=False）
    3. 达到最大修正次数（revision_count >= max_revision_count）
       → 即使还有问题也强制输出，并在输出中标注"建议人工确认"
    """
    # 从 State 中读取 Reflection 结果和控制字段
    # .get() 第二个参数是默认值：如果 key 不存在，返回默认值而不报错
    reflection = state.get("reflection", {})
    need_revision = reflection.get("need_revision", False)
    accepted_as_final = reflection.get("accepted_as_final", False)

    revision_count = state.get("revision_count", 0)
    max_revision_count = state.get("max_revision_count", 2)

    # 条件 1: LLM 一票通过，直接输出
    if accepted_as_final:
        return "final_output"

    # 条件 2: 需要修正且还有次数 → 进入修正循环
    if need_revision and revision_count < max_revision_count:
        return "revise_plan"

    # 条件 3: 不需要修正 或 次数用完 → 输出
    return "final_output"
