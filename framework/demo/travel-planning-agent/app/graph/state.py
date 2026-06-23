"""
工作流状态（State）定义 —— Agent 的"共享记忆"。

State 是 LangGraph 最核心的概念。可以把它想象成一个文件夹在流水线上传：
每个节点从 State 读取需要的信息，处理完后再往 State 里写入新的信息，
下一个节点继续读、继续写。

TypedDict 是 Python 的类型提示工具，定义一个字典应该有哪些 key 和
对应的值类型。total=False 表示所有字段都是可选的（Optional），
这样初始状态可以只包含 user_input，其余字段随着流程逐步填充。

为什么 State 只存 dict 不存 Pydantic 对象？
- LangGraph 的 checkpoint 机制需要 JSON 序列化状态
- dict 可以直接 json.dumps()，Pydantic 对象需要 model_dump()
- 统一存 dict 避免代码里混用 dict[key] 和 object.attr

Stage 2 对应概念：§2.4 Agent 核心组成环节 — 状态管理
"""

from typing_extensions import TypedDict
from typing import Any, Dict, List


class TravelState(TypedDict, total=False):
    """
    旅行规划工作流的完整状态，贯穿所有 9 个节点。

    按职责分为 7 个区域，避免所有字段平铺在一起。
    每个节点只读写自己关心的区域。
    """

    # ── ① 用户输入区 ──
    # 原始的自然语言文本，如 "我想6月底去成都玩3天"
    user_input: str
    # 多轮对话时保存历史输入，如 ["我想出去玩", "去成都，3天，预算3000"]
    user_inputs: List[str]

    # ── ② 需求区（parse_request_node 写入）──
    # 存储 TravelRequest.model_dump() 后的 dict
    # 如 {"destination": "成都", "days": 3, "budget": 3000, "preferences": ["美食"]}
    request: Dict[str, Any]

    # ── ③ 信息检查区（check_info_node 写入）──
    # 缺失的必要字段列表，如 ["days", "budget"]
    missing_fields: List[str]
    # 追问的问题列表，如 ["你计划玩几天？", "你的预算大概是多少？"]
    clarification_questions: List[str]
    # 信息是否完整 → 决定路由：完整→工具，不完整→追问
    is_info_complete: bool

    # ── ④ 工具区（decide_tools + collect_context 写入）──
    # 需要调用哪些工具，如 ["weather", "attractions", "foods", "budget", "transport"]
    required_tools: List[str]
    # 工具返回的数据合集，如 {"weather": {...}, "attractions": {...}}
    context: Dict[str, Any]

    # ── ⑤ 计划区（generate_plan_node / revise_plan_node 写入）──
    # 存储 TravelPlan.model_dump() 后的 dict
    draft_plan: Dict[str, Any]

    # ── ⑥ 反思区（reflect_plan_node 写入）──
    # 存储 ReflectionResult.model_dump() 后的 dict
    reflection: Dict[str, Any]

    # ── ⑦ 输出区（final_output_node 写入）──
    # 最终渲染的 Markdown 文本，直接展示给用户
    final_plan: str

    # ── 流程控制区（各节点更新）──
    # 是否需要继续修正 → route_after_reflection 的判断依据
    need_revision: bool
    # 当前已修正的次数 → 用于限制无限循环
    revision_count: int
    # 最大允许修正次数 → 默认 2
    max_revision_count: int
    # 流程停止原因 → "accepted_by_reflection" / "max_revision_reached" / "need_user_clarification"
    stop_reason: str

    # ── 错误与追踪区 ──
    # 工具调用失败的记录列表
    tool_errors: List[Dict[str, Any]]
    # 系统级错误记录
    system_errors: List[Dict[str, Any]]
    # 轻量执行轨迹，每完成一个节点追加一条记录
    # 如 [{"node": "parse_request", "status": "ok"}, {"node": "reflect_plan", "score": 9}]
    # 用于调试和 SSE 流式推送进度
    trace: List[Dict[str, Any]]
