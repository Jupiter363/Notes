"""
================================================================================
reflection_chain.py —— 审视生成的旅行计划，给出评分和修正建议（ReflectionResult）
================================================================================

【在整个 Agent 工作流中的位置】

这是旅行规划 Agent 的**第三个阶段（Stage 3: Reflection / Self-Critique）**。

工作流的完整链条：
    user_input
      → parse_chain         (Stage 1: 解析为 TravelRequest)
      → check_info_node     (信息完整性检查)
      → collect_info_node   (调用工具收集数据)
      → plan_chain          (Stage 2: 生成 TravelPlan)
      → reflection_chain    (Stage 3: 自我审查 ★ 你在这里 ★)
      → route_node          (根据 need_revision 决定下一步)
         ├─ need_revision=True  → revise_chain (修正)
         └─ need_revision=False → final_output (输出给用户)

【什么是 Reflection（自我反思）？】

Reflection 是 AI Agent 领域的一个重要范式（出自论文 "Reflexion: Language Agents
with Verbal Reinforcement Learning"）。核心思想是：
  - AI 不只生成结果，还会"审视"自己的结果
  - 发现问题 → 自我修正 → 再次审视 → 直到满意

在旅行规划场景中，reflection_chain 作为"审查员"，检查 plan_chain 的输出：
  - 预算超了吗？（total_estimated_cost vs total_budget）
  - 某一天行程太满了吗？（一天 5 个以上活动需要警惕）
  - 偏好匹配吗？（用户说"轻松"但安排了紧凑行程？）
  - 有逻辑错误吗？（下雨天安排了户外徒步？）

输出 ReflectionResult：
  - need_revision: True → 触发 revise_chain 修正
  - need_revision: False → 直接输出给用户
  - score: 1-10 的质量评分
  - suggestions: 具体修改建议

【与 plan_chain 的对比】

  plan_chain:      "生成者"角色 —— 创造性地构建旅行方案
  reflection_chain: "审查者"角色 —— 挑剔地检查方案的合理性

  两者用同一个基础 LLM，但通过不同的 system prompt 切换角色。
  plan_chain 的 prompt 说"你是旅行规划专家"；
  reflection_chain 的 prompt 说"你是严格的质量审核员"。

  Stage 2 对应概念：§5 Reflection / Reflexion
"""

import json
from functools import lru_cache

from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnableLambda

from app.config.settings import settings
from app.prompts.reflection_prompt import reflection_prompt
from app.schemas.reflection import ReflectionResult


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║          SSE 流式推送的全局队列（Global Stream Queue）                    ║
# ║                                                                            ║
# ║  与前两个 chain 完全相同的模式：                                           ║
# ║    1. 模块级全局变量 _stream_queue                                        ║
# ║    2. set_stream_queue(queue) 注册本次请求的队列                           ║
# ║    3. _invoke 中检测 queue 是否为 None，选择流式/非流式路径               ║
# ║                                                                            ║
# ║  注意：reflection_chain 的输出通常比 plan_chain 短得多。                  ║
# ║  plan_chain 输出完整的旅行计划（几百上千字），                             ║
# ║  reflection_chain 只输出评分和几条建议（几十到一百字）。                   ║
# ║  因此流式推送在 reflection 阶段的效果不那么"壮观"，                       ║
# ║  但仍然保持一致的 SSE 事件格式，前端可以复用同一套渲染逻辑。              ║
# ║                                                                            ║
# ║  详细解释见 parse_chain.py 同名注释块。                                    ║
# ╚════════════════════════════════════════════════════════════════════════════╝
_stream_queue = None


def set_stream_queue(queue):
    """
    注册本次请求的 SSE 推送队列。

    每次调用 reflection_chain.invoke() 之前，FastAPI 路由调用此函数。
    因为每个 chain 模块有独立的 _stream_queue，所以同一个 HTTP 请求
    在调用 plan_chain 和 reflection_chain 之间需要分别 set_stream_queue。
    """
    global _stream_queue
    _stream_queue = queue


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║      @lru_cache(maxsize=1) —— 角色切换的本质                             ║
# ║                                                                            ║
# ║  注意：reflection_chain 和 plan_chain 用同一个模型实例吗？                 ║
# ║  在这个实现中 —— 不是。每个 chain 有独立的 @lru_cache，                   ║
# ║  所以 reflection_chain 首次调用时也会执行 init_chat_model。               ║
# ║                                                                            ║
# ║  但由于 init_chat_model 的参数完全相同，底层 httpx 连接池                  ║
# ║  可能会共享（取决于 provider 实现）。实际上两个 model 实例                 ║
# ║  指向同一个 API endpoint，只是 Python 层面上是两个对象。                  ║
# ║                                                                            ║
# ║  如果想让 plan_chain 和 reflection_chain 真正共享同一个模型实例，          ║
# ║  可以把 _get_model 提取到共享模块中。当前的设计选择了"独立"而非"共享"。  ║
# ║                                                                            ║
# ║  详细解释见 parse_chain.py 同名注释块。                                    ║
# ╚════════════════════════════════════════════════════════════════════════════╝
@lru_cache(maxsize=1)
def _get_model():
    """
    懒加载模型实例。

    虽然 reflection_chain 用的是和 plan_chain 完全相同的模型，
    但"审查"这个角色是通过 system prompt 切换的，不是通过模型参数。
    也就是说 —— 同一个模型，不同的 prompt，扮演不同的角色。

    这种"一个模型、多种角色"的做法在 Agent 开发中非常普遍：
    - 不需要为每个角色维护不同的模型配置
    - API key 和 endpoint 复用
    - 成本可控（所有调用都走同一个 API 账号）
    """
    return init_chat_model(
        settings.MODEL_NAME,
        model_provider="openai",
        openai_api_key=settings.OPENAI_API_KEY,
        openai_api_base=settings.OPENAI_BASE_URL,
        temperature=settings.TEMPERATURE,
    )


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║      LCEL 管道：reflection_prompt → model → parser                        ║
# ║                                                                            ║
# ║  输入端：                                                                 ║
# ║    - travel_request: 用户的原始需求（TravelRequest 的 dict）               ║
# ║    - travel_plan:     plan_chain 生成的方案（TravelPlan 的 dict）          ║
# ║                                                                            ║
# ║  输出端：ReflectionResult                                                  ║
# ║    - need_revision: bool     ← 路由节点据此决定下一步                      ║
# ║    - score: int (1-10)       ← 质量评分                                    ║
# ║    - suggestions: list[str]  ← 修正建议，传给 revise_chain                ║
# ║                                                                            ║
# ║  详细解释见 parse_chain.py 同名注释块。                                    ║
# ╚════════════════════════════════════════════════════════════════════════════╝
def _build_reflection_chain():
    """
    构建非流式 LCEL 管道：reflection_prompt → LLM → PydanticOutputParser

    reflection_prompt 的 system prompt 会指示 LLM 以"审查员"身份工作，
    逐项检查旅行计划的合理性，然后输出结构化的 ReflectionResult JSON。

    ReflectionResult 的关键字段 need_revision 决定了工作流的走向：
    - True  → 路由到 revise_chain 修正
    - False → 路由到 final_output 直接输出
    """
    parser = PydanticOutputParser(pydantic_object=ReflectionResult)
    prompt_with_format = reflection_prompt.partial(format_instructions=parser.get_format_instructions())
    return prompt_with_format | _get_model() | parser


def _invoke(input_dict: dict):
    """
    双模式分发：根据 _stream_queue 状态选择流式或非流式路径。

    参数 input_dict 示例：
        {
            "travel_request": {...},   # TravelRequest 的 dict
            "travel_plan": {...}       # TravelPlan 的 dict
        }

    返回：ReflectionResult 对象
      - reflection_result.need_revision  → bool: 是否需要修正
      - reflection_result.score          → int: 1-10 评分
      - reflection_result.suggestions    → list[str]: 修正建议
    """
    q = _stream_queue
    if q is None:
        return _build_reflection_chain().invoke(input_dict)

    model = _get_model()
    parser = PydanticOutputParser(pydantic_object=ReflectionResult)
    prompt_with_format = reflection_prompt.partial(format_instructions=parser.get_format_instructions())
    messages = prompt_with_format.invoke(input_dict)

    full_text = ""
    for chunk in model.stream(messages):
        token = chunk.content if hasattr(chunk, 'content') else str(chunk)
        if token:
            full_text += token
            try:
                q.put_nowait(json.dumps({"type": "token", "token": token}, ensure_ascii=False))
            except Exception:
                pass

    return parser.parse(full_text)


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║      RunnableLambda —— 统一的延迟初始化模式                              ║
# ║                                                                            ║
# ║  reflection_chain = RunnableLambda(_invoke)                                ║
# ║                                                                            ║
# ║  与其他三个 chain 完全相同：                                               ║
# ║  - import 时不创建模型，调用时才创建                                      ║
# ║  - 首次调用的模型实例被 lru_cache 缓存                                    ║
# ║  - 双路径分发（流式 / 非流式）在 _invoke 内部处理                         ║
# ║                                                                            ║
# ║  这种"四个 chain 共享同一套模式"的设计让代码高度一致，                     ║
# ║  新增一个 chain 时只需复制模板、改 prompt 和 schema 即可。                ║
# ║                                                                            ║
# ║  详细解释见 parse_chain.py 末尾注释块。                                   ║
# ╚════════════════════════════════════════════════════════════════════════════╝
reflection_chain = RunnableLambda(_invoke)
