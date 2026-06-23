"""
================================================================================
阶段：规划（Plan）—— 工作流第二步
================================================================================
本 Prompt 属于"旅行计划生成"节点。在需求解析（Parse）完成后，结构化
的 TravelRequest 对象和工具查询结果（天气、景点、酒店等）一起传入此
Prompt，由 LLM 生成一份完整的旅行计划（TravelPlan）。

TravelPlan 包含每天的日程安排（morning/afternoon/evening），每个活动
附带花费、交通、理由等信息。这是整个 Agent 的核心输出物。

================================================================================
概念解释：ChatPromptTemplate 与 from_messages
================================================================================
ChatPromptTemplate 是 LangChain 中用于构建对话格式 Prompt 的模板类。
`from_messages()` 是一个类方法（classmethod），接受一个列表，列表中
每个元素是一个 (角色, 内容) 的元组。

运行时，ChatPromptTemplate 的 invoke() 方法会：
  1. 将 {变量名} 替换为传入的对应参数值
  2. 将每条 (role, content) 转换为 LangChain 的 BaseMessage 子类
     （SystemMessage / HumanMessage / AIMessage）
  3. 最终传给 LLM 的是一个消息列表（List[BaseMessage]），而非拼接字符串

这种设计的好处：
  - 语义清晰：一眼看出哪部分是"规则"，哪部分是"输入"
  - 角色隔离：system 的指令不会与 human 的数据混淆
  - 符合 OpenAI/Anthropic API 原生消息格式，减少格式转换损耗

================================================================================
角色详解：system vs human
================================================================================
system 消息（本文件第 4-16 行的内容）：
  - 定义了 LLM 的"专业身份"：专业旅行规划师
  - 列出了 6 条核心规则，这些规则是计划质量的硬约束
  - 大模型看到 system 消息时，会将其理解为"我必须遵守的行为准则"，
    其优先级高于 human 消息中的内容
  - 如果将规则写在 human 消息里，LLM 可能认为那只是"用户的建议"而非"系统要求"，
    存在被忽略的风险

human 消息（本文件第 17-21 行的内容）：
  - 携带三条动态数据：
    · {user_input}：用户的原始自然语言输入（保留用户原意）
    · {request}：上游 Parse 节点输出的结构化 TravelRequest 对象
    · {context}：工具调用返回的实测数据（天气、景点价格、酒店信息）

  为什么同时保留 user_input 和 request：
    - user_input 保留用户的语气、隐含意图，LLM 可以捕捉解析时遗漏的细节
    - request 是机器可读的结构化版本，用于精确匹配字段（目的地、天数等）
    - 两者互补，避免信息丢失——这对应 Agent 设计中"原始+解析双通道"的
      最佳实践

================================================================================
{format_instructions} 与 PydanticOutputParser
================================================================================
{format_instructions} 占位符由 LangChain 的 PydanticOutputParser 自动注入。

PydanticOutputParser 的工作流程：
  1. 绑定一个 Pydantic 模型（此处为 TravelPlan）
  2. 调用 parser.get_format_instructions() 生成如下形式的说明文本：

     "The output should be a JSON object with the following fields:
      - days (list): ... each day contains:
        - activities (list): ... each activity contains:
          - type (str): morning/afternoon/evening
          - description (str): ...
          - cost (float): ...
          - transport (str): ..."

  3. 运行时，LangChain 的链（Chain）自动将这段文本填入 {format_instructions}
  4. LLM 看到这段 JSON Schema 后，输出符合格式的 JSON
  5. Parser 将 JSON 反序列化为 TravelPlan 的 Pydantic 实例

这对应 Stage 2 笔记 §3 Structured Output 的核心思想：
  让 LLM 输出结构化数据（而非自由文本），通过 Pydantic 校验确保字段
  完整性和类型正确性，下游节点才能可靠消费。

================================================================================
核心规则的设计意图（逐条解析）
================================================================================

规则 1: "每天 2-3 个活动，留出休息和交通时间"
  来源：旅行规划的常识约束。如果 LLM 排满 8 个活动，实际用户在景点间
  奔走根本来不及，计划就不可执行。设置上限是防止 LLM 过度优化的关键。

规则 2: "每个活动写清：做什么、为什么、花多少钱、怎么去"
  每个活动都必须是"可执行单元"——用户看一眼就知道下一步该干嘛。

规则 3: "reason 控制在 20 字以内"
  防止 LLM 用长篇大论填充 token。简洁的 reason 用户阅读更快。

规则 4: "transport_note/risk_note 有就写，没有就省略"
  避免 LLM 在"没有风险"时强行编造风险说明（如"今天天气很好故无风险"）。
  这也是一种反幻觉约束。

规则 5: "confidence=mock 的数据，在 data_limitations 中提一句即可"
  工具返回的数据标记了置信度。mock = 低置信度（假数据），必须在计划中
  明确告知用户"这个信息不准确"。这是负责任 AI 的体现——不掩饰数据来源。

规则 6: "总花费 = 活动花费 + 住宿交通估算"
  住宿 250 元/天、交通 50 元/天 是硬编码的默认估算值，在没有真实酒店
  数据时提供合理的下限。budget_status 的百分比阈值（95%、120%）给
  反射节点（Reflection）提供明确的判断标准。

================================================================================
约束说明：为什么写"不要编造"（隐式约束）
================================================================================
虽然本 Prompt 没有显式写"不要编造"，但规则 4 和规则 5 本质上就是
反幻觉约束：
  - 规则 4：不知道就说不知道（省略字段）
  - 规则 5：mock 数据要标注（不把低质量数据当真实数据呈现）

这对应 Stage 2 笔记 §5 Reflection 中的关键原则：
  输出必须可溯源。每个数字、每条建议都有明确来源（用户输入 / 工具数据）。
  无法溯源的信息 → 不可信 → Reflection 无法有效审查。
"""

from langchain_core.prompts import ChatPromptTemplate

plan_prompt = ChatPromptTemplate.from_messages([
    ("system", """你是专业旅行规划师。根据用户需求和工具信息生成旅行计划。要求简洁实用。

核心规则：
1. 每天 2-3 个活动（morning/afternoon/evening），留出休息和交通时间
2. 每个活动写清：做什么、为什么、花多少钱、怎么去
3. reason 控制在 20 字以内，直说理由
4. transport_note/risk_note 有就写，没有就省略
5. 工具数据标注了 confidence=mock 的信息，在 data_limitations 中提一句即可
6. 总花费 = 活动花费 + 住宿交通估算（住宿约250元/天，交通约50元/天）

budget_status: within_budget(<=95%) / slightly_over(95-120%) / over_budget(>120%) / unknown

{format_instructions}"""),
    ("human", """用户说：{user_input}

已提取的需求：{request}

查到的信息：{context}""")
])
