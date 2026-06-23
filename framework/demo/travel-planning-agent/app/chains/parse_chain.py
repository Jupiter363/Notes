"""
================================================================================
parse_chain.py —— 用户原始消息 → 结构化旅行需求（TravelRequest）
================================================================================

【在整个 Agent 工作流中的位置】

这是整个旅行规划 Agent 的**第一个阶段（Stage 1: Parse）**。

用户输入自由文本，比如：
    "我想月底去成都玩3天，预算3000，喜欢美食和轻松"

parse_chain 的作用是把它解析成结构化的 TravelRequest 对象：
    TravelRequest(destination="成都", days=3, budget=3000, preferences=["美食", "轻松"], ...)

为什么需要这一步？
- LLM 的输出虽然是自然语言，但我们强制用 PydanticOutputParser 让它输出 JSON
- 代码拿到 TravelRequest 后可以精确判断"缺了什么信息"
- 如果 destination=None，后续 check_info_node 就知道要追问"你想去哪里？"

----

【本文件涉及的 LangChain 核心概念】

1. init_chat_model —— 统一的模型初始化入口
2. PydanticOutputParser —— 把 LLM 自由文本输出"掰"成严格的 Pydantic 结构
3. LCEL 管道运算符 | —— 声明式组合 Prompt → Model → Parser
4. @lru_cache(maxsize=1) —— 把模型实例缓存为"伪单例"，避免重复创建
5. RunnableLambda —— 延迟模型创建，避免 import 时就初始化模型
6. model.stream() —— 逐 token 流式生成，配合 SSE 推送到前端
7. set_stream_queue 全局模式 —— 在非流式 / 流式两种路径间切换

【参考 Stage 2 概念】
- §3 结构化输出（Structured Output）：PydanticOutputParser 把 LLM 输出约束为 Pydantic schema
- §2 管道与 LCEL：prompt | model | parser 的声明式组合
"""

import json
from functools import lru_cache

from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnableLambda

from app.config.settings import settings
from app.prompts.parse_prompt import parse_prompt
from app.schemas.travel_request import TravelRequest


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║              SSE 流式推送的全局队列（Global Stream Queue）                ║
# ╚════════════════════════════════════════════════════════════════════════════╝
#
# _stream_queue 是一个模块级全局变量，用于在 LLM 流式生成和 HTTP SSE 之间
# 建立"桥梁"。
#
# 【工作原理】
#   - FastAPI 路由在调用 plan_chain.invoke() 之前，先调用 set_stream_queue(q)
#     把一个 asyncio.Queue 注册到这里。
#   - _invoke 函数检测到 q 不为 None，就走流式路径：每拿到一个 token，
#     用 q.put_nowait() 推到队列里。
#   - FastAPI 的异步生成器从队列另一端读 token，包装成 SSE 格式发给浏览器。
#
# 【为什么用全局变量而不是传参？】
#   RunnableLambda 包装的 _invoke 签名是 (input_dict) → output，无法传入额外
#   的 queue 参数。用全局变量是最轻量的"旁路"方案，不需要修改 LangChain 的
#   标准调用接口。
#
# 【什么是 SSE？】
#   Server-Sent Events —— HTTP 长连接，服务器可以持续推送数据到客户端。
#   对用户来说就是"AI 一个字一个字往外蹦"的效果。
#
# 【关键点】
#   - q.put_nowait() 是非阻塞的 —— 队列满了就丢弃 token（用 except 兜底），
#     保证 LLM 生成不会因为前端断连而卡死。
#   - 每个请求有独立的 queue 实例，全局变量只是"指针"。并发场景下，
#     如果多个请求先后调用 set_stream_queue，后来的会覆盖前面的。
#     这是一个已知的限制，生产环境建议用 contextvars 替代。
#
_stream_queue = None


def set_stream_queue(queue):
    """
    注册本次请求的 SSE 推送队列。

    调用时机：FastAPI 路由在调用 chain.invoke() 之前。
    调用者：生成器路由函数内部，每次 HTTP 请求创建一个新的 asyncio.Queue。

    Args:
        queue: asyncio.Queue 实例。设置为 None 表示退回到非流式模式。

    注意：global 关键字告诉 Python "我不是在创建局部变量，我是在修改模块级变量"。
    没有 global，Python 会把 _stream_queue 当作函数内部的局部变量处理。
    """
    global _stream_queue
    _stream_queue = queue


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║              @lru_cache(maxsize=1) —— 模型实例缓存                       ║
# ╚════════════════════════════════════════════════════════════════════════════╝
#
# @lru_cache 是 Python 标准库 functools 提供的缓存装饰器。
# LRU = Least Recently Used（最近最少使用）。
#
# 【这里的具体效果】
#   @lru_cache(maxsize=1) 表示：
#   - 最多缓存 1 个结果（maxsize=1）
#   - 函数第一次被调用时，正常执行 init_chat_model(...)，返回模型实例
#   - 函数第二次被调用时，直接返回缓存的模型实例，不会再次初始化
#
# 【为什么 maxsize=1？】
#   _get_model() 是无参数函数，每次调用返回的应该是同一个模型实例。
#   maxsize=1 刚好够用 —— 多存也没意义，因为函数没有参数变化。
#   这本质上是一个"懒加载单例"（lazy singleton）模式。
#
# 【为什么需要缓存模型？】
#   init_chat_model 内部会：
#   1. 创建 HTTP 客户端（httpx 连接池）
#   2. 连接 OpenAI-compatible API endpoint
#   3. 初始化 tokenizer 等资源
#   如果不缓存，每次调用 _get_model() 都会重新做这些事，浪费内存和连接。
#   且同一个模型实例可以安全地并发调用（底层 httpx 连接池是线程安全的）。
#
# 【为什么不直接在模块顶层创建？】
#   看下一段 —— 这就是 RunnableLambda 解决的问题。
#
@lru_cache(maxsize=1)
def _get_model():
    """
    懒加载模型实例（伪单例模式）。

    init_chat_model 的参数说明：
    - settings.MODEL_NAME: 模型名，如 "deepseek-chat" 或 "gpt-4o"
    - model_provider="openai": 使用 OpenAI 兼容的 API 协议
    - openai_api_key: API 密钥，来自 settings
    - openai_api_base: 自定义 API 地址（可对接任何 OpenAI 兼容服务）
    - temperature: 生成温度，0=确定性强，1=创造性高

    Returns:
        BaseChatModel 实例 —— 可以被 invoke() 和 stream() 调用。
    """
    return init_chat_model(
        settings.MODEL_NAME,
        model_provider="openai",
        openai_api_key=settings.OPENAI_API_KEY,
        openai_api_base=settings.OPENAI_BASE_URL,
        temperature=settings.TEMPERATURE,
    )


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║              LCEL —— LangChain 表达式语言                                ║
# ╚════════════════════════════════════════════════════════════════════════════╝
#
# _build_parse_chain() 构建了一条 LCEL 管道：
#
#     parse_prompt → LLM 模型 → PydanticOutputParser
#
# 【LCEL 是什么？】
#   LangChain Expression Language —— 用 | 运算符把组件串成数据处理管道。
#   就像是 Unix 的 pipe（ls | grep | sort），数据从左边流到右边。
#
# 【这段管道的含义】
#   prompt_with_format | _get_model() | parser
#
#   等价于三个步骤：
#   ① prompt_with_format.invoke(input)  → 把用户输入注入 prompt 模板，得到消息列表
#   ② model.invoke(messages)            → 把消息发给 LLM，得到 AIMessage（文本回复）
#   ③ parser.invoke(ai_message)         → 把 LLM 的 JSON 文本解析成 TravelRequest 对象
#
# 【管道运算符 | 的实现原理】
#   LangChain 的 Runnable 类重载了 __or__ 方法。
#   当 Python 执行 a | b 时，实际调用 a.__or__(b)，返回一个新的 RunnableSequence。
#   这个 RunnableSequence 内部保存了 [a, b] 的列表，invoke 时依次调用。
#
# 【为什么这样写更好？】
#   1. 声明式：一眼就看出数据流向
#   2. 可组合：管道可以嵌套、复用
#   3. 自动批处理、异步、流式：RunnableSequence 自动支持这些高级功能
#   4. 可视化：可以打印管道图（chain.get_graph().print_ascii()）
#
def _build_parse_chain():
    """
    构建"普通模式"（非流式）的 LCEL 管道。

    管道：parse_prompt | LLM | PydanticOutputParser

    partial() 的作用：
    - parse_prompt 是一个 ChatPromptTemplate，里面有 {format_instructions} 占位符
    - parser.get_format_instructions() 返回 Pydantic schema 的文本描述
    - parse_prompt.partial(format_instructions=...) 把占位符填上，
      返回一个"只剩 {user_input} 待填"的新模板
    - 这样最终的管道只需要传入 {"user_input": "..."} 就能运行

    PydanticOutputParser 做的事情：
    1. 把 TravelRequest 的 JSON Schema 注入 prompt（告诉 LLM "按这个格式输出"）
    2. 拿到 LLM 的文本输出后，用 json.loads 解析
    3. 调用 TravelRequest.model_validate() 校验字段类型和约束（ge, le 等）
    4. 如果 JSON 格式错误或字段校验失败，抛出 OutputParserException
    """
    parser = PydanticOutputParser(pydantic_object=TravelRequest)
    prompt_with_format = parse_prompt.partial(format_instructions=parser.get_format_instructions())
    return prompt_with_format | _get_model() | parser


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║              _invoke —— 双模式分发函数                                    ║
# ╚════════════════════════════════════════════════════════════════════════════╝
#
# 【为什么有两个路径？】
#
#   路径 A（非流式，_stream_queue 为 None）：
#     input_dict → LCEL 管道 → TravelRequest
#     简洁高效，适合不需要实时推送的场景（如 CLI 调用、单元测试）。
#
#   路径 B（流式，_stream_queue 不为 None）：
#     input_dict → 手动拼接 prompt → model.stream() → 逐 token 推送 + 累积 → parser.parse()
#     适合 Web SSE 场景，用户在浏览器里看到逐字输出的体验。
#
# 【为什么流式路径不能直接用 LCEL 管道？】
#   LCEL 管道也支持 .stream()，但那是"组件到组件"的流式传递，
#   中间节点的输出需要先完成才能传到下一个节点。
#   而我们需要的"旁路"效果是：
#     模型每生成一个 token → ① 推送到 SSE 队列（旁路）
#                          → ② 累积到 full_text（主路）
#   这种"一边走主路一边走旁路"的效果，LCEL 原生不支持，需要手动展开循环。
#
# 【model.stream(messages) 是什么？】
#   它是 LLM 的**流式生成**接口。
#   - model.invoke(messages)  → 等待全部生成完 → 返回完整的 AIMessage
#   - model.stream(messages)  → 返回一个迭代器，每生成一个 token yield 一次
#
#   每次 yield 出来的是一个 AIMessageChunk，格式类似：
#     AIMessageChunk(content="宽", ...)
#     AIMessageChunk(content="窄", ...)  ← 注意：中文逐字输出
#     AIMessageChunk(content="巷", ...)
#     AIMessageChunk(content="子", ...)
#
#   chunk.content 是增量文本，hasattr(chunk, 'content') 是容错判断。
#
# 【queue.put_nowait 的行为】
#   put_nowait 是非阻塞的 put：
#   - 队列有空位 → token 入队，前端立即收到
#   - 队列满了（asyncio.Queue 默认 maxsize=0 即无限制，但也可以设上限）
#     → 抛出 QueueFull 异常 → except 捕获，丢弃这个 token
#   - 前端断开连接 → 队列可能被 GC 回收，put_nowait 也可能抛异常 → 静默丢弃
#
#   关键设计理念：**token 推送是 best-effort，绝不影响 LLM 主流程的完整性。**
#   宁可前端丢几个字，也不能让 LLM 生成中断导致最终解析失败。
#
def _invoke(input_dict: dict):
    """
    执行链的核心函数 —— 根据 _stream_queue 状态选择非流式 / 流式路径。

    参数 input_dict 格式：{"user_input": "我想去成都玩..."} 或 {"user_input": ..., "history": ...}

    返回：TravelRequest 对象
    """
    # ── 检查全局队列，决定走哪条路径 ──
    q = _stream_queue
    if q is None:
        # ═════════ 路径 A：非流式 ═════
        # 直接用 LCEL 管道的 invoke，一步到位。
        # _build_parse_chain() 每次会重新构建管道（包括新建 parser），
        # 但因为 _get_model() 有 lru_cache，模型实例是复用的。
        return _build_parse_chain().invoke(input_dict)

    # ═════════ 路径 B：流式（SSE 推送）═════
    # 手动展开 prompt → model.stream → parser 三步，
    # 在 model.stream 阶段把每个 token 旁路推送到 SSE 队列。

    # Step 1: 构建 prompt 消息
    # 注意：这里手动调用了 partial 和 invoke，
    # 是因为我们需要拿到 messages 对象来传给 model.stream()
    model = _get_model()
    parser = PydanticOutputParser(pydantic_object=TravelRequest)
    prompt_with_format = parse_prompt.partial(format_instructions=parser.get_format_instructions())
    messages = prompt_with_format.invoke(input_dict)

    # Step 2: 流式调用 LLM，逐 token 处理
    full_text = ""
    for chunk in model.stream(messages):
        # 从 AIMessageChunk 中提取增量文本
        # hasattr 容错：不同 provider 返回的 chunk 结构可能不同
        token = chunk.content if hasattr(chunk, 'content') else str(chunk)
        if token:
            full_text += token  # 主路：累积完整文本
            try:
                # 旁路：推送到 SSE 队列
                # json.dumps 把 token 包装成 {"type": "token", "token": "宽"}
                # ensure_ascii=False 保证中文不转义成 \uXXXX
                q.put_nowait(json.dumps({"type": "token", "token": token}, ensure_ascii=False))
            except Exception:
                pass  # 推送失败不阻塞主流程：队列满、前端断开等都静默忽略

    # Step 3: 把累积的完整文本解析为结构化对象
    # 注意：这里用的是 parser.parse(full_text)，不是 parser.invoke(ai_message)
    # parse() 接受原始字符串，内部做 json.loads + model_validate
    return parser.parse(full_text)


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║        RunnableLambda —— 为什么不在 import 时创建模型？                  ║
# ╚════════════════════════════════════════════════════════════════════════════╝
#
# 这是本模块最关键的架构决策。
#
# 【反模式：import 时创建模型】
#   # parse_chain.py 顶层
#   parser = PydanticOutputParser(pydantic_object=TravelRequest)
#   model = init_chat_model(...)                    # ← 问题在这里
#   chain = prompt | model | parser
#
# 问题：
#   1. import 时机不可控 —— Python 在 import 阶段执行顶层代码时，
#      settings 可能还没加载（pydantic-settings 的加载顺序不确定）
#   2. API key 可能还没设置 —— 如果 API key 来自环境变量或 .env 文件，
#      在 import 时可能还没读取
#   3. 测试困难 —— 单元测试想 mock 模型？已经创建完了，来不及拦截
#   4. 启动慢 —— 首次 import 就要做网络连接（虽然不一定连接，但初始化开销在）
#   5. 多进程问题 —— 如果用 gunicorn 多 worker，每个 worker import 时创建，
#      但不一定是好事（有些服务希望 worker fork 后再创建连接）
#
# 【正确模式：RunnableLambda(_invoke)】
#   parse_chain = RunnableLambda(_invoke)
#
# RunnableLambda 接受一个普通 Python 函数，把它包装成一个 LangChain Runnable 对象。
# 对外暴露的接口和普通 Runnable 完全一样：.invoke(), .batch(), .stream() 等。
#
# 关键区别：
#   - _invoke 内部调用 _get_model() 和 _build_parse_chain()
#   - 这两个函数都是**延迟调用**的 —— 什么时候 invoke，什么时候才创建模型
#   - import 时不需要 API key 就位，不需要网络连接
#   - 测试时可以在 _get_model 层面做 mock
#
# 【这解决了所有 import 时创建的问题】
#   ✓ import 时没有任何网络调用
#   ✓ API key 可以在运行时再设置
#   ✓ 单元测试容易 mock
#   ✓ 首次 invoke 时才真正初始化，启动零延迟
#   ✓ 结合 @lru_cache，首次初始化后模型被缓存，后续 invoke 复用同一个实例
#
# 【代价】
#   - 类型提示不够精确：RunnableLambda 的输入输出类型是 Any
#   - 调试稍复杂：trace 里看到的是 RunnableLambda，不是显式的管道结构
#   - 不能像纯 LCEL 管道那样自动生成可视化图
#
parse_chain = RunnableLambda(_invoke)
