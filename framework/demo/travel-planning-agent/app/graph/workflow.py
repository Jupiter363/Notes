"""
LangGraph 工作流 —— 组装节点、边、条件分支和循环。

快速模式 (max_revision_count=0):
    parse → check → tools → generate_plan → final_output （仅 1 次 LLM 调用）

完整模式 (max_revision_count>0):
    parse → check → tools → generate_plan → reflect → [revise → reflect] → final_output
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
    """快速模式跳过 reflection，直接输出。"""
    if state.get("max_revision_count", 0) > 0:
        return "reflect_plan"
    return "final_output"


def build_graph(checkpointer=None):
    builder = StateGraph(TravelState)

    builder.add_node("parse_request", parse_request_node)
    builder.add_node("check_info", check_info_node)
    builder.add_node("ask_clarification", ask_clarification_node)
    builder.add_node("decide_tools", decide_tools_node)
    builder.add_node("collect_context", collect_context_node)
    builder.add_node("generate_plan", generate_plan_node)
    builder.add_node("reflect_plan", reflect_plan_node)
    builder.add_node("revise_plan", revise_plan_node)
    builder.add_node("final_output", final_output_node)

    builder.add_edge(START, "parse_request")
    builder.add_edge("parse_request", "check_info")

    builder.add_conditional_edges(
        "check_info",
        route_after_check,
        {"ask_clarification": "ask_clarification", "decide_tools": "decide_tools"},
    )

    builder.add_edge("ask_clarification", END)

    builder.add_edge("decide_tools", "collect_context")
    builder.add_edge("collect_context", "generate_plan")

    # 条件：快速模式跳过 reflection，完整模式走 reflection 循环
    builder.add_conditional_edges(
        "generate_plan",
        route_after_generate,
        {"final_output": "final_output", "reflect_plan": "reflect_plan"},
    )

    builder.add_conditional_edges(
        "reflect_plan",
        route_after_reflection,
        {"revise_plan": "revise_plan", "final_output": "final_output"},
    )

    builder.add_edge("revise_plan", "reflect_plan")
    builder.add_edge("final_output", END)

    return builder.compile(checkpointer=checkpointer)
