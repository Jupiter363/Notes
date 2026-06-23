"""
================================================================================
plan_chain.py —— 结构化旅行需求 → 结构化旅行方案（TravelPlan）
================================================================================

【在整个 Agent 工作流中的位置】

这是旅行规划 Agent 的**第二个阶段（Stage 2: Plan Generation）**。

调用链：
    parse_chain (用户输入 → TravelRequest)
        → check_info_node (检查信息完整性，不足则追问)
        → collect_info_node (收集天气、景点等工具数据)
        → plan_chain (TravelRequest + 工具数据 → TravelPlan)

plan_chain 是整个系统最核心的生成链条。它接收：
    1. 用户的 TravelRequest（想去哪、几天、预算...）
    2. 工具数据（天气、景点列表、酒店价格...）

输出一个层级化的 TravelPlan：
    TravelPlan
      └── DayPlan[] (每天的安排)
            └── Activity[] (上午/下午/晚上的具体活动)

【本文件与 parse_chain.py 的关系】
    parse_chain: 自由文本 → 结构化需求（TravelRequest）
    plan_chain:  结构化需求 + 上下文 → 结构化方案（TravelPlan）

两者共享完全相同的架构模式（RunnableLambda + 双路径 + 全局队列），
只是输入 schema 和输出 schema 不同。

【参考 Stage 2 概念】
- §4 Plan-and-Execute：plan_chain 是 "Plan" 步骤的核心
- §3 结构化输出：PydanticOutputParser 约束 LLM 输出为 TravelPlan schema
- §5 Reflection：plan_chain 的输出会送给 reflection_chain 做审查
"""

import json
from functools import lru_cache

from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnableLambda

from app.config.settings import settings
from app.prompts.plan_prompt import plan_prompt
from app.schemas.travel_plan import TravelPlan


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║          SSE 流式推送的全局队列（Global Stream Queue）                    ║
# ║                                                                            ║
# ║  每个 chain 模块都有自己独立的 _stream_queue。                             ║
# ║  这意味着一个 HTTP 请求需要依次调用 plan_chain 和 reflection_chain 时，    ║
# ║  FastAPI 路由需要在调用每个 chain 之前分别调用各自的 set_stream_queue。    ║
# ║                                                                            ║
# ║  详细解释见 parse_chain.py 同名注释块。                                    ║
# ╚════════════════════════════════════════════════════════════════════════════╝
_stream_queue = None


def set_stream_queue(queue):
    """
    注册本次请求的 SSE 推送队列。

    每次 HTTP 流式请求前，FastAPI 路由调用此函数把新创建的 asyncio.Queue
    绑定到模块全局变量。调用 plan_chain.invoke() 时，_invoke 函数检测到
    队列不为 None，自动走流式路径。

    Args:
        queue: asyncio.Queue 实例。传 None 可切换到非流式模式。
    """
    global _stream_queue
    _stream_queue = queue


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║      @lru_cache(maxsize=1) —— 模型实例的"懒加载单例"缓存                 ║
# ║                                                                            ║
# ║  为什么每个 chain 模块都有独立的 _get_model()？                            ║
# ║  理论上可以共享一个全局模型实例。但独立的好处是：                          ║
# ║    1. 每个 chain 可以独立配置不同的参数（temperature, model 等）          ║
# ║    2. 模块自包含，不需要额外的依赖注入                                     ║
# ║    3. 测试时模块可以独立 mock                                              ║
# ║  代价是每个 chain 第一次调用时都会创建一次模型实例（但因为 lru_cache，     ║
# ║  每个 chain 最多创建一次）。                                             ║
# ║                                                                            ║
# ║  详细解释见 parse_chain.py 同名注释块。                                    ║
# ╚════════════════════════════════════════════════════════════════════════════╝
@lru_cache(maxsize=1)
def _get_model():
    """
    懒加载模型实例。

    init_chat_model 是 LangChain 的统一模型初始化入口：
    - 支持 30+ 模型提供商（OpenAI, Anthropic, DeepSeek, Ollama...）
    - 自动处理 API key 的优先级：参数 > 环境变量 > .env 文件
    - 返回统一的 BaseChatModel 接口，调用方不需要关心底层 provider

    参数说明：
        settings.MODEL_NAME      → 模型标识，如 "deepseek-chat"
        model_provider="openai"  → 使用 OpenAI 兼容协议（绝大多数国产模型兼容）
        openai_api_key           → 从 settings 读取的 API 密钥
        openai_api_base          → 自定义 API 端点地址
        temperature              → 控制随机性（0.0～2.0，旅行场景一般 0.7 左右）

    Returns:
        BaseChatModel: 支持 invoke() 和 stream() 的统一模型接口
    """
    return init_chat_model(
        settings.MODEL_NAME,
        model_provider="openai",
        openai_api_key=settings.OPENAI_API_KEY,
        openai_api_base=settings.OPENAI_BASE_URL,
        temperature=settings.TEMPERATURE,
    )


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║      LCEL 管道：prompt → model → parser                                  ║
# ║                                                                            ║
# ║  plan_prompt.partial(format_instructions=...) → _get_model() → parser      ║
# ║                                                                            ║
# ║  TravelPlan 是一个三层嵌套结构，PydanticOutputParser 生成的                ║
# ║  format_instructions 会包含完整的 JSON Schema，告诉 LLM 按什么格式输出。  ║
# ║  例如：{"destination": "...", "total_days": 3, "days": [{"day": 1, ...}]}  ║
# ║                                                                            ║
# ║  详细解释见 parse_chain.py 同名注释块。                                    ║
# ╚════════════════════════════════════════════════════════════════════════════╝
def _build_plan_chain():
    """
    构建非流式 LCEL 管道：plan_prompt → LLM → PydanticOutputParser

    PydanticOutputParser 的工作流程：
    1. 调用 parser.get_format_instructions() 生成 JSON Schema 文本
    2. 通过 partial() 注入到 prompt 的 {format_instructions} 占位符
    3. LLM 看到 prompt 里的 JSON Schema 后会尝试按格式输出 JSON
    4. parser.invoke() 对 LLM 输出做 json.loads + Pydantic 校验
    5. 返回 TravelPlan 对象（强类型，.destination / .days[0].activities 可直接访问）
    """
    parser = PydanticOutputParser(pydantic_object=TravelPlan)
    prompt_with_format = plan_prompt.partial(format_instructions=parser.get_format_instructions())
    return prompt_with_format | _get_model() | parser


def _invoke(input_dict: dict):
    """
    双模式分发：根据 _stream_queue 状态选择流式或非流式路径。

    参数 input_dict 示例：
        {
            "destination": "成都",
            "days": 3,
            "budget": 3000,
            "preferences": ["美食", "轻松"],
            "weather_data": "...",
            "attraction_data": "...",
            ...
        }

    返回：TravelPlan 对象（完整的三层嵌套结构）
    """
    q = _stream_queue

    # ═══════ 路径 A：非流式 ═══════
    # 用于不需要实时推送的场景：
    #   - CLI 调试
    #   - 单元测试
    #   - 需要完整结果再处理的中间步骤
    if q is None:
        return _build_plan_chain().invoke(input_dict)

    # ═══════ 路径 B：流式（SSE） ═══════
    # 用于 Web 场景：用户浏览器实时看到计划逐字生成。
    #
    # 手动展开 LCEL 管道的三步：
    #   Step 1: prompt.invoke(input)        → 构建消息列表
    #   Step 2: model.stream(messages)      → 逐 token 生成 + 旁路推送
    #   Step 3: parser.parse(full_text)     → 解析完整文本为 TravelPlan

    # Step 1: 手动构建 prompt
    model = _get_model()
    parser = PydanticOutputParser(pydantic_object=TravelPlan)
    prompt_with_format = plan_prompt.partial(format_instructions=parser.get_format_instructions())
    messages = prompt_with_format.invoke(input_dict)

    # Step 2: 流式生成——旁路每个 token 到 SSE 队列
    # full_text 累积完整的 LLM 输出（用于最终解析），
    # 同时每个 token 被包装成 JSON 推送到 q 里（用于前端 SSE 显示）
    full_text = ""
    for chunk in model.stream(messages):
        # chunk 是 AIMessageChunk 对象，.content 是本次生成的增量文本
        # 例如中文 "旅行" 可能分两次 yield："旅" → "行"
        token = chunk.content if hasattr(chunk, 'content') else str(chunk)
        if token:
            full_text += token
            try:
                # json.dumps 序列化为 {"type": "token", "token": "旅"}
                # ensure_ascii=False 防止中文变 旅
                q.put_nowait(json.dumps({"type": "token", "token": token}, ensure_ascii=False))
            except Exception:
                # 推送失败不阻塞主流程：
                # - asyncio.Queue 满了 → QueueFull → 跳过
                # - 前端断开导致队列异常 → 跳过
                # - 无论如何，full_text 不受影响，最终结果完整
                pass

    # Step 3: 解析累积的完整文本
    # parser.parse() 内部流程：
    #   a. 尝试从 full_text 中提取 JSON（处理 markdown code block 等格式）
    #   b. json.loads 解析
    #   c. TravelPlan.model_validate() Pydantic 校验
    #   d. 返回 TravelPlan 实例
    return parser.parse(full_text)


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║      RunnableLambda —— 延迟初始化架构                                    ║
# ║                                                                            ║
# ║  plan_chain = RunnableLambda(_invoke)                                      ║
# ║                                                                            ║
# ║  RunnableLambda 是一个"适配器"：把普通 Python 函数包装成 Runnable 对象。  ║
# ║  这使得 _invoke 可以被当作 LangChain chain 来使用：                       ║
# ║    - plan_chain.invoke(input_dict)          → 同步调用                     ║
# ║    - plan_chain.batch([dict1, dict2])       → 批量调用                     ║
# ║    - plan_chain | another_runnable           → 继续组合管道                ║
# ║                                                                            ║
# ║  核心优势：                                                               ║
# ║  1. import 时不创建模型：import app.chains.plan_chain 不会触发             ║
# ║     init_chat_model，settings 可以稍后加载                                 ║
# ║  2. 测试友好：可以 patch _get_model 或 _invoke 而不影响其他模块           ║
# ║  3. 灵活性：_invoke 函数内部可以做条件判断（如双路径分发）                ║
# ║                                                                            ║
# ║  详细解释见 parse_chain.py 末尾注释块。                                   ║
# ╚════════════════════════════════════════════════════════════════════════════╝
plan_chain = RunnableLambda(_invoke)
