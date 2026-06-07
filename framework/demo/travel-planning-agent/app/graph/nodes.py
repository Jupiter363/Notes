"""
工作流节点 —— 每个节点是 LangGraph 工作流中的一个执行步骤。
"""

from app.chains.parse_chain import parse_chain
from app.chains.plan_chain import plan_chain
from app.chains.reflection_chain import reflection_chain
from app.chains.revise_chain import revise_chain
from app.schemas.travel_request import TravelRequest
from app.schemas.travel_plan import TravelPlan
from app.schemas.reflection import ReflectionResult
from app.tools.base import safe_tool_call
from app.tools.weather_tool import get_weather
from app.tools.attraction_tool import search_attractions
from app.tools.food_tool import search_foods
from app.tools.budget_tool import estimate_budget
from app.tools.transport_tool import search_transport
from app.tools.search_tool import web_search
from app.graph.state import TravelState


# ── 1. parse_request_node (LLM 解析) ──

def parse_request_node(state: TravelState) -> dict:
    user_input = state["user_input"]
    user_inputs = state.get("user_inputs", []) + [user_input]

    result: TravelRequest = parse_chain.invoke({"user_input": user_input})

    prev_request = state.get("request", {})
    new_request = result.model_dump()

    merged_request = {**prev_request}
    for key, value in new_request.items():
        if value not in [None, "", []]:
            merged_request[key] = value

    return {
        "user_inputs": user_inputs,
        "request": merged_request,
        "revision_count": state.get("revision_count", 0),
        "max_revision_count": state.get("max_revision_count", 2),
        "tool_errors": state.get("tool_errors", []),
        "system_errors": state.get("system_errors", []),
        "trace": state.get("trace", []) + [{"node": "parse_request", "status": "ok"}],
    }


# ── 2. check_info_node ──

def check_info_node(state: TravelState) -> dict:
    request = state.get("request", {})
    missing = []

    for field in ["destination", "days", "budget", "preferences"]:
        value = request.get(field)
        if value in [None, "", []]:
            missing.append(field)

    return {
        "missing_fields": missing,
        "is_info_complete": len(missing) == 0,
        "trace": state.get("trace", []) + [{"node": "check_info", "missing": missing}],
    }


# ── 3. ask_clarification_node ──

def ask_clarification_node(state: TravelState) -> dict:
    field_to_question = {
        "destination": "你想去哪个城市或地区旅行？",
        "days": "你计划玩几天？",
        "budget": "你的总预算大概是多少？",
        "preferences": "你更偏好美食、自然风光、历史文化、购物，还是轻松休闲路线？",
    }

    questions = [
        field_to_question[field]
        for field in state.get("missing_fields", [])
        if field in field_to_question
    ]

    return {
        "clarification_questions": questions,
        "stop_reason": "need_user_clarification",
        "final_plan": "为了更准确地规划行程，请先补充：\n" + "\n".join(f"- {q}" for q in questions),
    }


# ── 4. decide_tools_node ──

def decide_tools_node(state: TravelState) -> dict:
    request = state["request"]
    preferences = request.get("preferences", [])

    required_tools = ["weather", "attractions", "budget", "transport"]

    if "美食" in preferences:
        required_tools.append("foods")

    if request.get("start_date"):
        required_tools.append("web_search")

    return {"required_tools": list(dict.fromkeys(required_tools))}


# ── 5. collect_context_node ──

def collect_context_node(state: TravelState) -> dict:
    request = state["request"]
    city = request.get("destination", "")
    days = request.get("days", 3)
    budget = request.get("budget", 0)
    preferences = request.get("preferences", [])
    date_range = request.get("start_date", "")
    required_tools = state.get("required_tools", [])

    context = {}
    errors = list(state.get("tool_errors", []))

    if "weather" in required_tools:
        result, err = safe_tool_call(get_weather, {"city": city, "date_range": date_range}, "fallback_weather")
        context["weather"] = result
        if err:
            errors.append(err)

    if "attractions" in required_tools:
        result, err = safe_tool_call(search_attractions, {"city": city, "preferences": preferences}, "fallback_attractions")
        context["attractions"] = result
        if err:
            errors.append(err)

    if "foods" in required_tools:
        result, err = safe_tool_call(search_foods, {"city": city, "preferences": preferences}, "fallback_foods")
        context["foods"] = result
        if err:
            errors.append(err)

    if "budget" in required_tools:
        result, err = safe_tool_call(estimate_budget, {"city": city, "days": days, "budget": budget}, "fallback_budget")
        context["budget_estimate"] = result
        if err:
            errors.append(err)

    if "transport" in required_tools:
        result, err = safe_tool_call(search_transport, {"city": city, "start_date": date_range}, "fallback_transport")
        context["transport"] = result
        if err:
            errors.append(err)

    return {"context": context, "tool_errors": errors}


# ── 6. generate_plan_node ──

def generate_plan_node(state: TravelState) -> dict:
    result: TravelPlan = plan_chain.invoke({
        "user_input": state["user_input"],
        "request": state["request"],
        "context": state.get("context", {}),
    })

    return {
        "draft_plan": result.model_dump(),
        "trace": state.get("trace", []) + [{"node": "generate_plan", "status": "ok"}],
    }


# ── 7. reflect_plan_node ──

def reflect_plan_node(state: TravelState) -> dict:
    result: ReflectionResult = reflection_chain.invoke({
        "user_input": state["user_input"],
        "request": state["request"],
        "context": state.get("context", {}),
        "draft_plan": state["draft_plan"],
        "revision_count": state.get("revision_count", 0),
        "max_revision_count": state.get("max_revision_count", 2),
    })

    stop_reason = "reflection_need_revision" if result.need_revision else "accepted_by_reflection"

    return {
        "reflection": result.model_dump(),
        "need_revision": result.need_revision,
        "stop_reason": stop_reason,
        "trace": state.get("trace", []) + [{
            "node": "reflect_plan",
            "need_revision": result.need_revision,
            "score": result.score,
        }],
    }


# ── 8. revise_plan_node ──

def revise_plan_node(state: TravelState) -> dict:
    result: TravelPlan = revise_chain.invoke({
        "user_input": state["user_input"],
        "request": state["request"],
        "context": state.get("context", {}),
        "draft_plan": state["draft_plan"],
        "reflection": state["reflection"],
    })

    revision_count = state.get("revision_count", 0) + 1

    return {
        "draft_plan": result.model_dump(),
        "revision_count": revision_count,
        "need_revision": False,
        "trace": state.get("trace", []) + [{"node": "revise_plan", "revision_count": revision_count}],
    }


# ── 9. final_output_node ──

def final_output_node(state: TravelState) -> dict:
    plan = state.get("draft_plan", {})
    reflection = state.get("reflection", {})
    tool_errors = state.get("tool_errors", [])
    revision_count = state.get("revision_count", 0)
    max_revision_count = state.get("max_revision_count", 2)

    lines = []
    lines.append(f"# {plan.get('destination', '未知')}{plan.get('total_days', '?')}日旅行方案")
    lines.append("")
    lines.append("## 一、行程概览")
    lines.append(f"- 总预算：{plan.get('total_budget', '未设定')} 元")
    lines.append(f"- 预计花费：{plan.get('total_estimated_cost', '未知')} 元")
    lines.append(f"- 预算状态：{plan.get('budget_status', 'unknown')}")
    lines.append(f"- 已完成修正轮次：{revision_count}/{max_revision_count}")
    lines.append("")

    for day in plan.get("days", []):
        lines.append(f"## Day {day['day']}：{day['theme']}")
        lines.append(f"- 节奏：{day.get('pace_level', 'normal')}")
        lines.append(f"- 预计花费：{day['daily_estimated_cost']} 元")

        for activity in day.get("activities", []):
            lines.append(f"- {activity['time_slot']}：{activity['title']}")
            if activity.get("location"):
                lines.append(f"  - 地点：{activity['location']}")
            lines.append(f"  - 安排理由：{activity['reason']}")
            if activity.get("transport_note"):
                lines.append(f"  - 交通提示：{activity['transport_note']}")
            if activity.get("risk_note"):
                lines.append(f"  - 风险提示：{activity['risk_note']}")
        lines.append("")

    if plan.get("preference_match_notes"):
        lines.append("## 二、偏好匹配说明")
        for note in plan["preference_match_notes"]:
            lines.append(f"- {note}")
        lines.append("")

    if plan.get("risk_notes"):
        lines.append("## 三、出行风险与提醒")
        for note in plan["risk_notes"]:
            lines.append(f"- {note}")
        lines.append("")

    if reflection:
        lines.append("## 四、方案自检结果")
        lines.append(f"- 质量评分：{reflection.get('score', 'unknown')}/10")
        if reflection.get("issues"):
            lines.append("- 已识别问题：")
            for issue in reflection["issues"]:
                lines.append(f"  - {issue}")
        if revision_count >= max_revision_count and reflection.get("need_revision"):
            lines.append("- 说明：已达到最大修正次数，仍建议出行前人工确认关键细节。")
        lines.append("")

    if plan.get("data_limitations") or tool_errors:
        lines.append("## 五、数据限制说明")
        for item in plan.get("data_limitations", []):
            lines.append(f"- {item}")
        if tool_errors:
            lines.append("- 部分工具调用失败或返回低置信度数据，建议出行前再次确认天气、景点开放时间、门票和交通情况。")

    return {
        "final_plan": "\n".join(lines),
        "stop_reason": state.get("stop_reason", "final_output"),
    }
