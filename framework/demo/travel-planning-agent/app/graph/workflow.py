"""
LangGraph 工作流组装 —— 把节点和路由器串成完整的状态图。

这是整个 Agent 系统的"总控中心"。如果把 Agent 比作工厂流水线：
- 节点（Node）= 流水线上的每台机器（只做一道工序）
- 边（Edge）= 传送带（固定路线，A 做完一定送到 B）
- 条件边（Conditional Edge）= 分拣机（根据状态决定送到 B 还是 C）
- 状态（State）= 工件上贴的标签，随工件流转，每台机器读取和更新

工作流模式（对应 Stage 2 §6 Workflow Agent）：
- 快速模式 (max_revision=0): parse → check → tools → plan → output（1次LLM）
- 审查模式 (max_revision>0): ... → plan → reflect → [revise → reflect] → output

真实 Refletion 循环（§5）：
    generate_plan → reflect_plan → revise_plan → reflect_plan → ... → final_output
    退出条件: need_revision=False 或 revision_count >= max_revision_count
"""

from langgraph.graph import StateGraph, START, END
from app.graph.state import TravelState
from app.graph.nodes import (
    parse_request_node,
    check_info_node,
    ask_clarification_node,
    decide_tools_node,
    collect_context_node,
    generate_plan_node,
    reflect_plan_node,
    revise_plan_node,
    final_output_node,
)
from app.graph.routers import route_after_check, route_after_reflection


def route_after_generate(state: TravelState):
    """
    生成计划后的路由 —— 快速模式 vs 审查模式的分叉点。

    如果 max_revision_count=0（快速模式），跳过所有审查修正，
    直接生成最终输出。省 1-3 次 LLM 调用（每次 10-35s）。
    """
    if state.get("max_revision_count", 0) > 0:
        return "reflect_plan"    # 审查模式：生成 → 审查 → 修正循环
    return "final_output"         # 快速模式：生成 → 直接输出


def build_graph(checkpointer=None):
    """
    构建并编译 LangGraph 状态图。

    这是 Agent 的"施工图纸"——定义有哪些节点、它们怎么连接、
    在哪些路口根据什么条件选择路径。

    参数 checkpointer 预留用于持久化（保存状态到数据库），
    支持 interrupt/resume（暂停后从断点恢复）。
    """

    # ── 第1步：创建空白状态图，指定 State 类型 ──
    # StateGraph 是 LangGraph 的核心类，泛型参数 TravelState 约束了
    # 所有节点函数的输入输出类型
    builder = StateGraph(TravelState)

    # ── 第2步：注册所有节点（只是登记，还没有连接）──
    # 每个节点是一个 Python 函数，签名为 node(state) -> dict
    builder.add_node("parse_request", parse_request_node)       # ① LLM解析需求
    builder.add_node("check_info", check_info_node)             # ② 检查信息完整性
    builder.add_node("ask_clarification", ask_clarification_node) # ③ 生成追问
    builder.add_node("decide_tools", decide_tools_node)         # ④ 选择工具
    builder.add_node("collect_context", collect_context_node)   # ⑤ 调用工具
    builder.add_node("generate_plan", generate_plan_node)       # ⑥ LLM生成计划
    builder.add_node("reflect_plan", reflect_plan_node)         # ⑦ LLM审查
    builder.add_node("revise_plan", revise_plan_node)           # ⑧ LLM修正
    builder.add_node("final_output", final_output_node)         # ⑨ 渲染Markdown

    # ── 第3步：连接节点 —— 固定路线（Edge）──
    # START 和 END 是 LangGraph 的特殊节点，表示图的入口和出口

    # 入口 → 解析需求
    builder.add_edge(START, "parse_request")
    # 解析完 → 检查信息
    builder.add_edge("parse_request", "check_info")

    # ── 第4步：条件分支 —— 信息完整性路由 ──
    # add_conditional_edges 比 add_edge 多一个"路由器函数"参数
    # 路由器返回 "ask_clarification" 或 "decide_tools"
    # 第三个参数是映射表：返回值 → 目标节点名
    builder.add_conditional_edges(
        "check_info",                              # 从哪个节点出发
        route_after_check,                         # 用哪个路由器函数判断
        {
            "ask_clarification": "ask_clarification",  # 不完整 → 追问 → END
            "decide_tools": "decide_tools",            # 完整 → 继续工具流程
        },
    )

    # 追问后结束，等待用户补充信息后再重新 invoke
    builder.add_edge("ask_clarification", END)

    # ── 第5步：固定流程 —— 选工具 → 调工具 → 生成计划 ──
    builder.add_edge("decide_tools", "collect_context")
    builder.add_edge("collect_context", "generate_plan")

    # ── 第6步：条件分支 —— 快速模式 vs 审查模式 ──
    builder.add_conditional_edges(
        "generate_plan",                           # 从生成计划节点出发
        route_after_generate,                      # 检查 max_revision_count
        {
            "final_output": "final_output",         # 0 → 跳过审查，直接输出
            "reflect_plan": "reflect_plan",         # >0 → 进入审查循环
        },
    )

    # ── 第7步：审查 → 修正循环（Reflection Loop）──
    builder.add_conditional_edges(
        "reflect_plan",                            # 从审查节点出发
        route_after_reflection,                    # 检查 need_revision
        {
            "revise_plan": "revise_plan",           # 需要修正 → 去修正
            "final_output": "final_output",         # 不需要 → 去输出
        },
    )

    # ⚡ 关键：修正完不是直接输出，而是回到审查！
    # 这形成了真实循环：generate → reflect → revise → reflect → ...
    # 对应 Stage 2 §5：Execute → Evaluate → Reflect → Retry
    builder.add_edge("revise_plan", "reflect_plan")

    # ── 第8步：输出 → 结束 ──
    builder.add_edge("final_output", END)

    # ── 第9步：编译成可执行图 ──
    # compile() 会把图"冻结"为可执行对象，不可再添加节点
    # checkpointer 参数用于持久化中间状态（支持断点续跑）
    return builder.compile(checkpointer=checkpointer)
