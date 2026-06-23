"""
================================================================================
revise_chain.py —— 根据审查反馈修正旅行计划（修正后的 TravelPlan）
================================================================================

【在整个 Agent 工作流中的位置】

这是旅行规划 Agent 的**第四个阶段（Stage 4: Revision / Correction）**，
也是 Reflection 循环的"闭环"环节。

完整循环：
    plan_chain (生成初版)
      → reflection_chain (审查，找出问题)
        → route_node
          ├─ need_revision=False → final_output (计划合格，输出)
          └─ need_revision=True  → revise_chain (修正 ★ 你在这里 ★)
                                     → 修正后的 TravelPlan
                                     → 返回 final_output (修正完成，输出)

    revise_chain 只在 reflection_chain 判定"需要修正"时才会被调用。
    如果审查通过（accepted_as_final=True 或 need_revision=False），
    这个 chain 完全不会被触发。

【revise_chain 的输入端】

  revise_chain 接收三个关键输入：
    1. travel_plan: 原始计划（被审查为不合格的那个）
    2. reflection: 审查反馈（评分、问题列表、修正建议）
    3. original_request: 用户原始需求（确保修正不偏离用户意图）

  其中 reflection.suggestions 是 revise_chain 的"修正指南"，
  例如：
    "第2天安排了5个活动，建议把购物移到第3天上午"
    "总预算超出800元，建议替换晚餐餐厅或取消可选购物点"
    "第3天全天户外，但天气预报下雨，建议加入室内备选方案"

【revise_chain 和 plan_chain 的关键区别】

  plan_chain:      从零构建一个全新的旅行计划
  revise_chain:    基于已有计划做针对性修改（保持大部分内容不变）

  revise_chain 的 prompt 会强调：
  - 只修改有问题的地方，其他部分保持原样
  - 优先处理 blocking_issues（阻断性问题）
  - 修改后需要重新计算 total_estimated_cost 和 daily_estimated_cost
  - 保持原 plan 的风格和结构

【revise_chain 的输出端】

  输出是一个**修正后的 TravelPlan**，与 plan_chain 使用完全相同的 schema。
  这个设计非常巧妙 —— 修正后的计划在外观上和初版计划一样，
  使得修正后的 plan 可以被任何下游节点无缝消费。

  Stage 2 对应概念：§5 Reflection（Reflection 循环的修正步骤）
"""

import json
from functools import lru_cache

from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnableLambda

from app.config.settings import settings
from app.prompts.revise_prompt import revise_prompt
from app.schemas.travel_plan import TravelPlan


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║          SSE 流式推送的全局队列（Global Stream Queue）                    ║
# ║                                                                            ║
# ║  与其它 chain 相同的模式。                                                 ║
# ║                                                                            ║
# ║  在 revise 阶段进行流式推送的意义：                                        ║
# ║  - 用户看到 AI 在"修改"计划，而不是卡住了                                 ║
# ║  - 修正通常比全新生成快（只改部分内容），流式体验更流畅                    ║
# ║  - 前端可以高亮显示"正在修正..."的状态                                    ║
# ║                                                                            ║
# ║  详细解释见 parse_chain.py 同名注释块。                                    ║
# ╚════════════════════════════════════════════════════════════════════════════╝
_stream_queue = None


def set_stream_queue(queue):
    """
    注册本次请求的 SSE 推送队列。

    只有当工作流路由到 revise 分支时，FastAPI 路由才会调用此函数。
    如果 reflection 判定计划合格直接通过，revise_chain 不会被调用，
    set_stream_queue 也不会被触发。
    """
    global _stream_queue
    _stream_queue = queue


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║      @lru_cache(maxsize=1) —— 独立模型实例                               ║
# ║                                                                            ║
# ║  注意一个微妙之处：                                                        ║
# ║  revise_chain 和 plan_chain 使用相同的 temperature 参数。                  ║
# ║  这是有意为之 —— 保持生成风格的一致性。                                    ║
# ║                                                                            ║
# ║  但在某些场景下，修正阶段可能需要更低的 temperature：                      ║
# ║  - 生成阶段 (plan_chain): temperature=0.7，允许创造性                      ║
# ║  - 修正阶段 (revise_chain): temperature=0.3，强调精确性                     ║
# ║  当前实现没有做这种区分，值得未来优化。                                    ║
# ║                                                                            ║
# ║  详细解释见 parse_chain.py 同名注释块。                                    ║
# ╚════════════════════════════════════════════════════════════════════════════╝
@lru_cache(maxsize=1)
def _get_model():
    """
    懒加载模型实例。

    与 plan_chain / reflection_chain 使用完全相同的模型配置。
    四个 chain 各自独立缓存，但指向同一个 API endpoint。
    """
    return init_chat_model(
        settings.MODEL_NAME,
        model_provider="openai",
        openai_api_key=settings.OPENAI_API_KEY,
        openai_api_base=settings.OPENAI_BASE_URL,
        temperature=settings.TEMPERATURE,
    )


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║      LCEL 管道：revise_prompt → model → parser                            ║
# ║                                                                            ║
# ║  注意：revise_chain 输出的是 TravelPlan（与 plan_chain 相同 schema）      ║
# ║  而不是"只输出修改差异"。                                                  ║
# ║                                                                            ║
# ║  为什么输出完整计划而不是 diff？                                           ║
# ║  1. 下游消费者（如 final_output_node）只需要消费 TravelPlan 即可          ║
# ║     不需要知道"这是初版还是修正版"                                        ║
# ║  2. LLM 不擅长生成精确的 diff（JSON patch）                               ║
# ║  3. 完整输出更容易做 Pydantic 校验                                        ║
# ║  4. 前端可以直接渲染修正后的计划，无需应用 diff 逻辑                      ║
# ║                                                                            ║
# ║  详细解释见 parse_chain.py 同名注释块。                                    ║
# ╚════════════════════════════════════════════════════════════════════════════╝
def _build_revise_chain():
    """
    构建非流式 LCEL 管道：revise_prompt → LLM → PydanticOutputParser

    revise_prompt 的设计要点：
    - 入参包含 3 个字段：travel_plan（待修正）, reflection（修正建议）,
      original_request（原始需求，防止修正偏离用户意图）
    - system prompt 强调"只修改有问题的地方，保持其余不变"
    - 输出 schema 与 plan_chain 完全相同（TravelPlan）
    """
    parser = PydanticOutputParser(pydantic_object=TravelPlan)
    prompt_with_format = revise_prompt.partial(format_instructions=parser.get_format_instructions())
    return prompt_with_format | _get_model() | parser


def _invoke(input_dict: dict):
    """
    双模式分发：根据 _stream_queue 状态选择流式或非流式路径。

    参数 input_dict 示例：
        {
            "travel_plan": {...},        # 待修正的 TravelPlan dict
            "reflection": {...},         # ReflectionResult dict（包含问题&建议）
            "original_request": {...}    # TravelRequest dict（原始需求，防止偏离）
        }

    返回：TravelPlan —— 修正后的完整旅行计划

    注意：返回的 TravelPlan 和 plan_chain 的返回类型完全一样。
    下游节点不需要区分"这是初版还是修正版"。
    """
    q = _stream_queue
    if q is None:
        return _build_revise_chain().invoke(input_dict)

    model = _get_model()
    parser = PydanticOutputParser(pydantic_object=TravelPlan)
    prompt_with_format = revise_prompt.partial(format_instructions=parser.get_format_instructions())
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
# ║      RunnableLambda —— 四个 Chain 的统一出口                             ║
# ║                                                                            ║
# ║  revise_chain = RunnableLambda(_invoke)                                    ║
# ║                                                                            ║
# ║  至此，四个 chain 模块呈现出高度一致的架构模式：                            ║
# ║                                                                            ║
# ║   模块              输入                 输出                              ║
# ║   ─────────────────────────────────────────────────────                    ║
# ║   parse_chain       用户自由文本          TravelRequest                    ║
# ║   plan_chain        TravelRequest+工具    TravelPlan                       ║
# ║   reflection_chain  TravelPlan+Request    ReflectionResult                 ║
# ║   revise_chain      Plan+Reflection       TravelPlan（修正后）              ║
# ║                                                                            ║
# ║  所有 chain 共享：                                                         ║
# ║    ✓ RunnableLambda 延迟初始化                                            ║
# ║    ✓ @lru_cache(maxsize=1) 模型缓存                                       ║
# ║    ✓ set_stream_queue 双模式分发                                          ║
# ║    ✓ init_chat_model 统一模型入口                                         ║
# ║    ✓ PydanticOutputParser 结构化输出                                      ║
# ║    ✓ LCEL 管道 | 声明式组合                                              ║
# ║                                                                            ║
# ║  这种一致性降低了认知负担和学习成本。                                    ║
# ║                                                                            ║
# ║  详细解释见 parse_chain.py 末尾注释块。                                   ║
# ╚════════════════════════════════════════════════════════════════════════════╝
revise_chain = RunnableLambda(_invoke)
