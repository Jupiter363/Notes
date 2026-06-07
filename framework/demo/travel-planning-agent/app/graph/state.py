from typing_extensions import TypedDict
from typing import Any, Dict, List


class TravelState(TypedDict, total=False):
    # 当前用户输入
    user_input: str

    # 多轮场景下保存原始用户输入历史
    user_inputs: List[str]

    # 结构化需求，统一保存为 Pydantic model_dump() 后的 dict
    request: Dict[str, Any]

    # 信息完整性
    missing_fields: List[str]
    clarification_questions: List[str]
    is_info_complete: bool

    # 工具选择与上下文
    required_tools: List[str]
    context: Dict[str, Any]

    # 结构化计划，统一保存为 TravelPlan.model_dump() 后的 dict
    draft_plan: Dict[str, Any]

    # 最近一次反思结果，统一保存为 ReflectionResult.model_dump() 后的 dict
    reflection: Dict[str, Any]

    # 最终 Markdown 输出
    final_plan: str

    # 流程控制
    need_revision: bool
    revision_count: int
    max_revision_count: int
    stop_reason: str

    # 错误记录
    tool_errors: List[Dict[str, Any]]
    system_errors: List[Dict[str, Any]]

    # 轻量 trace，便于 debug 和测试
    trace: List[Dict[str, Any]]
