"""
工作流节点 —— Agent 工作流的 9 个执行步骤。

每个节点是一个 Python 函数，签名为:
    def some_node(state: TravelState) -> dict

节点从 state 中读取需要的信息，处理后返回一个 dict。
LangGraph 会自动把这个 dict 合并回 state —— 这就是
"节点不直接修改 state，而是返回更新"的设计。

节点的职责划分原则（Stage 2 §2.3）：
- 能用代码判断的，不用 LLM（check_info、decide_tools、final_output）
- 需要理解和生成的，用 LLM（parse、plan、reflect、revise）
- 需要外部信息的，用 Tool（collect_context）
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


# ═══════════════════════════════════════════════════════════════
# 节点 1：parse_request_node —— 用 LLM 解析用户自然语言
# ═══════════════════════════════════════════════════════════════

def parse_request_node(state: TravelState) -> dict:
    """
    把用户的自然语言（"我想6月底去成都玩3天..."）转成结构化 TravelRequest。

    这是 Agent 和普通 Chatbot 的第一个区别：
    Chatbot 直接把用户的话发给 LLM 聊天；
    Agent 先解析出结构化需求（去哪、几天、多少预算），
    然后才能做后续的"信息完整性检查"、"工具选择"。

    多轮合并逻辑：如果用户之前已经说过一部分信息（如"我想出去玩"），
    本轮补充了更多（"去成都，3天，预算3000"），需要把新旧字段合并。
    新字段覆盖旧字段，但保留旧字段中本轮没说到的信息。
    """

    # 当前用户输入
    user_input = state["user_input"]

    # 保存历史输入（用于多轮对话的上下文追踪）
    user_inputs = state.get("user_inputs", []) + [user_input]

    # ★ 核心 LLM 调用：Prompt → Model → PydanticOutputParser → TravelRequest
    # parse_chain.invoke() 内部流程：
    #   1. 把 user_input 填入 Prompt 模板
    #   2. 发给 DeepSeek/OpenAI
    #   3. 把 LLM 返回的 JSON 解析成 TravelRequest 对象
    result: TravelRequest = parse_chain.invoke({"user_input": user_input})

    # 获取上一轮的解析结果（如果有），用于合并
    prev_request = state.get("request", {})

    # model_dump() 把 Pydantic 对象转成普通 Python dict
    new_request = result.model_dump()

    # 合并策略：新值覆盖旧值，但空值不覆盖（保留旧信息）
    # {**prev_request} 是 Python 的字典解包语法：创建一个新字典包含旧字典的所有键值
    merged_request = {**prev_request}
    for key, value in new_request.items():
        # 如果新值是 None、空字符串、空列表，说明 LLM 没能提取到
        # 保留旧值（可能是上一轮已经提取到的）
        if value not in [None, "", []]:
            merged_request[key] = value

    # 返回 dict —— LangGraph 会自动合并到 state
    return {
        "user_inputs": user_inputs,
        "request": merged_request,
        # 初始化控制字段（如果 state 中还没有这些值）
        "revision_count": state.get("revision_count", 0),
        "max_revision_count": state.get("max_revision_count", 2),
        # 保留已有的错误记录
        "tool_errors": state.get("tool_errors", []),
        "system_errors": state.get("system_errors", []),
        # 追踪日志：记录这个节点执行完成
        "trace": state.get("trace", []) + [{"node": "parse_request", "status": "ok"}],
    }


# ═══════════════════════════════════════════════════════════════
# 节点 2：check_info_node —— 检查信息是否完整（纯 Python，无 LLM）
# ═══════════════════════════════════════════════════════════════

def check_info_node(state: TravelState) -> dict:
    """
    检查 TravelRequest 的 4 个必要字段是否都有值。

    为什么这是纯 Python 而不是 LLM？
    —— Stage 2 §2.3 原则：能用代码判断的，不要浪费 LLM 调用。
    检查一个字段是否为 None/空，Python 一行代码搞定，不需要 LLM。
    """

    request = state.get("request", {})
    missing = []

    # 必要字段列表 —— 缺少任何一个都会触发追问
    required_fields = ["destination", "days", "budget", "preferences"]

    # 逐一检查：字段值为 None / "" / [] 都算缺失
    for field in required_fields:
        value = request.get(field)
        if value in [None, "", []]:
            missing.append(field)

    return {
        "missing_fields": missing,
        # is_info_complete = True → 继续工具流程
        # is_info_complete = False → 追问用户
        "is_info_complete": len(missing) == 0,
        "trace": state.get("trace", []) + [{"node": "check_info", "missing": missing}],
    }


# ═══════════════════════════════════════════════════════════════
# 节点 3：ask_clarification_node —— 生成追问（纯 Python）
# ═══════════════════════════════════════════════════════════════

def ask_clarification_node(state: TravelState) -> dict:
    """
    根据缺失字段生成对应的追问问题。

    这也是纯 Python —— 字段和问题的映射关系是确定的，
    不需要 LLM 来"想该问什么"。如果后续需要更智能的追问
    （如根据上下文调整措辞），可以升级为 LLM 节点。
    """

    # 字段 → 追问问题的硬编码映射
    field_to_question = {
        "destination": "你想去哪个城市或地区旅行？",
        "days": "你计划玩几天？",
        "budget": "你的总预算大概是多少？",
        "preferences": "你更偏好美食、自然风光、历史文化、购物，还是轻松休闲路线？",
    }

    # 只生成当前缺失字段对应的追问
    questions = [
        field_to_question[field]
        for field in state.get("missing_fields", [])
        if field in field_to_question
    ]

    return {
        "clarification_questions": questions,
        # stop_reason 标记 → planner_service 根据这个判断要不要等用户补充
        "stop_reason": "need_user_clarification",
        # final_plan 在这里用作追问消息（复用字段），最终输出时会被替换
        "final_plan": "为了更准确地规划行程，请先补充：\n" + "\n".join(f"- {q}" for q in questions),
    }


# ═══════════════════════════════════════════════════════════════
# 节点 4：decide_tools_node —— 动态选择工具（纯 Python）
# ═══════════════════════════════════════════════════════════════

def decide_tools_node(state: TravelState) -> dict:
    """
    根据用户需求决定需要调用哪些工具。

    不是一股脑调所有工具！基础 4 件套（天气、景点、预算、交通）
    总是需要；美食工具只在用户偏好"美食"时才调用；
    实时搜索只在用户指定了具体日期时才调用。

    这种"按需调用"减少了不必要的工具开销，也避免无关信息干扰 LLM。
    """

    request = state["request"]
    preferences = request.get("preferences", [])

    # 基础工具 —— 所有旅行规划都需要的 4 件套
    required_tools = ["weather", "attractions", "budget", "transport"]

    # 条件 1：用户喜欢美食 → 加查餐厅
    if "美食" in preferences:
        required_tools.append("foods")

    # 条件 2：有具体日期 → 搜索最新信息（营业时间、票价变动、临时通知等）
    if request.get("start_date"):
        required_tools.append("web_search")

    # dict.fromkeys() 技巧：用列表做 key 创建字典，再转回列表，实现去重
    # 等效于 list(set(required_tools)) 但保持顺序
    return {"required_tools": list(dict.fromkeys(required_tools))}


# ═══════════════════════════════════════════════════════════════
# 节点 5：collect_context_node —— 安全调用工具
# ═══════════════════════════════════════════════════════════════

def collect_context_node(state: TravelState) -> dict:
    """
    根据 required_tools 列表，逐一调用对应的工具。

    关键设计（Stage 2 §3.10 Checklist）：
    - 每个工具独立 try-except，一个工具挂了不影响其他工具
    - safe_tool_call 是统一的安全调用包装器
    - 失败工具返回 fallback 数据（confidence="low"，error=错误信息）
    - 错误记录到 tool_errors，供后续节点展示
    """

    request = state["request"]
    city = request.get("destination", "")
    days = request.get("days", 3)
    budget = request.get("budget", 0)
    preferences = request.get("preferences", [])
    date_range = request.get("start_date", "")
    required_tools = state.get("required_tools", [])

    context = {}        # 工具返回数据的合集
    errors = list(state.get("tool_errors", []))  # 保留之前累积的错误

    # ── 天气工具 ──
    if "weather" in required_tools:
        # safe_tool_call 返回 (result_dict, error_dict_or_None)
        result, err = safe_tool_call(
            get_weather,
            {"city": city, "date_range": date_range},
            "fallback_weather",  # 失败时的兜底数据标识
        )
        context["weather"] = result
        if err:
            errors.append(err)  # 记录错误但不中断

    # ── 景点工具 ──
    if "attractions" in required_tools:
        result, err = safe_tool_call(
            search_attractions,
            {"city": city, "preferences": preferences},
            "fallback_attractions",
        )
        context["attractions"] = result
        if err:
            errors.append(err)

    # ── 美食工具 ──
    if "foods" in required_tools:
        result, err = safe_tool_call(
            search_foods,
            {"city": city, "preferences": preferences},
            "fallback_foods",
        )
        context["foods"] = result
        if err:
            errors.append(err)

    # ── 预算工具 ──
    if "budget" in required_tools:
        result, err = safe_tool_call(
            estimate_budget,
            {"city": city, "days": days, "budget": budget},
            "fallback_budget",
        )
        context["budget_estimate"] = result
        if err:
            errors.append(err)

    # ── 交通工具 ──
    if "transport" in required_tools:
        result, err = safe_tool_call(
            search_transport,
            {"city": city, "start_date": date_range},
            "fallback_transport",
        )
        context["transport"] = result
        if err:
            errors.append(err)

    return {"context": context, "tool_errors": errors}


# ═══════════════════════════════════════════════════════════════
# 节点 6：generate_plan_node —— LLM 生成结构化旅行计划
# ═══════════════════════════════════════════════════════════════

def generate_plan_node(state: TravelState) -> dict:
    """
    调用 LLM 根据用户需求 + 工具上下文生成完整的 TravelPlan。

    这是整个工作流中消耗最大的 LLM 调用：
    - 输入：用户原始输入 + 结构化需求 + 5 个工具的查询结果
    - 输出：完整的 TravelPlan（目的地、预算、每天的活动安排）
    - 耗时：通常 15-40 秒（取决于 API 响应速度和输出复杂度）

    Stage 2 对应概念：§4 Plan-and-Execute 的 Execute 阶段
    """

    # 把用户原始输入也传进去，让 LLM 有更完整的上下文
    result: TravelPlan = plan_chain.invoke({
        "user_input": state["user_input"],
        "request": state["request"],
        "context": state.get("context", {}),
    })

    return {
        # model_dump() 把 Pydantic 对象转为 dict 存入 State
        "draft_plan": result.model_dump(),
        "trace": state.get("trace", []) + [{"node": "generate_plan", "status": "ok"}],
    }


# ═══════════════════════════════════════════════════════════════
# 节点 7：reflect_plan_node —— LLM 审查计划
# ═══════════════════════════════════════════════════════════════

def reflect_plan_node(state: TravelState) -> dict:
    """
    让 LLM 以"审查员"角色审视已生成的计划，输出 ReflectionResult。

    这就是 Stage 2 §5 的 Reflection 范式：
    Execute（generate_plan）→ Evaluate（reflect_plan）→ 决定是否修正。

    审查重点：
    1. 预算是否超支
    2. 行程密度是否合理（不能每天 >4 个活动）
    3. 是否匹配用户偏好
    4. 天气、交通、数据置信度风险是否标注
    5. 是否需要继续修正

    revision_count 传入给 LLM，让它知道"这是第几次审查了"，
    越往后越倾向于接受当前方案（避免无限修正）。
    """

    result: ReflectionResult = reflection_chain.invoke({
        "user_input": state["user_input"],
        "request": state["request"],
        "context": state.get("context", {}),
        "draft_plan": state["draft_plan"],           # 要审查的计划
        "revision_count": state.get("revision_count", 0),  # 已修正次数
        "max_revision_count": state.get("max_revision_count", 2),
    })

    # 生成 stop_reason —— 用于最终输出展示和调试
    stop_reason = "reflection_need_revision" if result.need_revision else "accepted_by_reflection"

    return {
        "reflection": result.model_dump(),
        "need_revision": result.need_revision,  # ← route_after_reflection 的判断依据
        "stop_reason": stop_reason,
        "trace": state.get("trace", []) + [{
            "node": "reflect_plan",
            "need_revision": result.need_revision,
            "score": result.score,  # 记录评分，用于 SSE 流式展示
        }],
    }


# ═══════════════════════════════════════════════════════════════
# 节点 8：revise_plan_node —— LLM 修正计划
# ═══════════════════════════════════════════════════════════════

def revise_plan_node(state: TravelState) -> dict:
    """
    根据 Review 的 issues 和 suggestions，让 LLM 修正计划。

    关键逻辑：revision_count += 1。
    这个计数器是限制无限循环的关键——每次修正后 +1，
    当 >= max_revision_count 时，即使还有问题也强制输出。
    （Stage 2 §5.8：max_reflection_rounds 限制反思次数）

    修正后的 draft_plan 会覆盖旧版，然后 flow 回到 reflect_plan
    再次审查——这就是 generate → reflect → revise → reflect 的循环。
    """

    result: TravelPlan = revise_chain.invoke({
        "user_input": state["user_input"],
        "request": state["request"],
        "context": state.get("context", {}),
        "draft_plan": state["draft_plan"],       # 当前有问题的计划
        "reflection": state["reflection"],       # 审查反馈（issues + suggestions）
    })

    # 修正计数器 +1 —— 这是 Agent 循环的"刹车"
    revision_count = state.get("revision_count", 0) + 1

    return {
        "draft_plan": result.model_dump(),
        "revision_count": revision_count,
        "need_revision": False,  # 重置，等待下次 reflect 重新判断
        "trace": state.get("trace", []) + [{
            "node": "revise_plan",
            "revision_count": revision_count,
        }],
    }


# ═══════════════════════════════════════════════════════════════
# 节点 9：final_output_node —— 把结构化计划渲染为 Markdown
# ═══════════════════════════════════════════════════════════════

def final_output_node(state: TravelState) -> dict:
    """
    把 TravelPlan dict 渲染成 Markdown 文本。

    为什么不是 LLM 节点？
    —— 结构化数据转 Markdown 是纯格式转换，不需要 LLM。
    用 Python 字符串拼接 100% 可控、可预测、没有幻觉风险。

    渲染内容包括：
    1. 行程概览（预算、花费、修正轮次）
    2. 每日安排（活动、地点、理由、交通、风险）
    3. 偏好匹配说明
    4. 风险提醒
    5. 自检结果（Reflection 评分和问题）
    6. 数据局限性（来源可信度、工具失败提示）
    """

    plan = state.get("draft_plan", {})
    reflection = state.get("reflection", {})
    tool_errors = state.get("tool_errors", [])
    revision_count = state.get("revision_count", 0)
    max_revision_count = state.get("max_revision_count", 2)

    lines = []

    # ── 标题 ──
    lines.append(f"# {plan.get('destination', '未知')}{plan.get('total_days', '?')}日旅行方案")
    lines.append("")

    # ── 一、行程概览 ──
    lines.append("## 一、行程概览")
    lines.append(f"- 总预算：{plan.get('total_budget', '未设定')} 元")
    lines.append(f"- 预计花费：{plan.get('total_estimated_cost', '未知')} 元")
    lines.append(f"- 预算状态：{plan.get('budget_status', 'unknown')}")
    lines.append(f"- 已完成修正轮次：{revision_count}/{max_revision_count}")
    lines.append("")

    # ── 每日安排 ──
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

    # ── 二、偏好匹配说明 ──
    if plan.get("preference_match_notes"):
        lines.append("## 二、偏好匹配说明")
        for note in plan["preference_match_notes"]:
            lines.append(f"- {note}")
        lines.append("")

    # ── 三、出行风险与提醒 ──
    if plan.get("risk_notes"):
        lines.append("## 三、出行风险与提醒")
        for note in plan["risk_notes"]:
            lines.append(f"- {note}")
        lines.append("")

    # ── 四、方案自检结果（Reflection 评分）──
    if reflection:
        lines.append("## 四、方案自检结果")
        lines.append(f"- 质量评分：{reflection.get('score', 'unknown')}/10")
        if reflection.get("issues"):
            lines.append("- 已识别问题：")
            for issue in reflection["issues"]:
                lines.append(f"  - {issue}")
        # 如果达到最大修正次数但还有问题 → 告知用户
        if revision_count >= max_revision_count and reflection.get("need_revision"):
            lines.append("- 说明：已达到最大修正次数，仍建议出行前人工确认关键细节。")
        lines.append("")

    # ── 五、数据限制说明 ──
    if plan.get("data_limitations") or tool_errors:
        lines.append("## 五、数据限制说明")
        for item in plan.get("data_limitations", []):
            lines.append(f"- {item}")
        if tool_errors:
            lines.append("- 部分工具调用失败或返回低置信度数据，建议出行前再次确认天气、景点开放时间、门票和交通情况。")

    return {
        # join() 把列表用换行符拼成完整的 Markdown 文本
        "final_plan": "\n".join(lines),
        "stop_reason": state.get("stop_reason", "final_output"),
    }
