"""
================================================================================
阶段：反思（Reflection）—— 工作流第三步
================================================================================
本 Prompt 属于"反思/审查"节点，对应 Stage 2 笔记 §5 Reflection 的核心概念。

Reflection 是 Agent 工作流中的"质量控制"环节。在 Plan 节点生成初步计划后，
Reflection 节点审查该计划的质量，输出两个关键结论：
  - need_revision: bool —— 计划是否需要修改
  - accepted_as_final: bool —— 计划是否可以直接交付

如果 need_revision=true，则下游的 Revise 节点会根据 Reflection 输出的
issues/suggestions 来修正计划。修正后的计划再次进入 Reflection 审查，
形成一个 **质检循环**（最多 max_revision_count 轮）。

这就是 LangGraph 中的"条件边"（conditional edge）模式：
  Reflection 节点 → 合格 → END（输出最终计划）
  Reflection 节点 → 不合格 → Revise 节点 → 回到 Plan → 再次 Reflection

================================================================================
概念解释：ChatPromptTemplate 与消息角色
================================================================================
ChatPromptTemplate.from_messages() 将 Prompt 组织为消息列表。

每条消息由 (角色, 内容) 元组定义，LangChain 在内部将其映射为：
  ("system", ...)  → SystemMessage  —— 定义 AI 的身份和规则
  ("human", ...)   → HumanMessage   —— 携带需要 AI 处理的具体数据

LLM 提供商（OpenAI / Anthropic）的 API 都原生支持这种多角色消息格式，
ChatPromptTemplate 只是做了 Python 侧的封装和占位符替换。

================================================================================
system 角色的审查看点（4 项检查）
================================================================================
本 system 消息定义了 4 项具体检查标准，而非模糊的"看看好不好"：

  检查 1: 预算是否超支
    → 与 plan_prompt 中 budget_status 的阈值（95%/120%）对齐
    → 这是客观指标，不应有模糊空间

  检查 2: 行程密度
    → 每天 >4 个活动 = 过满（用户赶场，体验差）
    → 每天 <2 个活动 = 过松（浪费天数，性价比低）
    → 2-4 个活动为合理区间，对应 plan_prompt 中"每天 2-3 个活动"的规则

  检查 3: 匹配用户偏好
    → 偏好来自 parse_prompt 的结构化输出
    → 例如：用户偏好"美食"但计划全是博物馆 → 不匹配 → 需要修正

  检查 4: 天气/交通风险标注
    → plan_prompt 规则 4 要求"有风险就标注"
    → Reflection 检查"标注了没有？"

评分体系（9-10 / 7-8 / 5-6 / 1-4）给了四个明确档位，
让 need_revision 的判断有据可依（≥7 分可接受 → accepted_as_final=true）。

================================================================================
human 角色的 4 个占位符
================================================================================
  {request}       —— 上游 Parse 节点的结构化需求（评估基准/锚点）
  {context}       —— 工具返回的实测数据（验证计划中的数字是否基于真实数据）
  {draft_plan}    —— 当前待审查的计划（Plan 节点的输出）
  {revision_count}/{max_revision_count}
                  —— 当前修改轮次和上限，Reflection 据此调整审查严格度
                     （例如：最后一轮可适当放宽标准，避免死循环）

================================================================================
{format_instructions} 与 PydanticOutputParser
================================================================================
{format_instructions} 的注入机制在所有 4 个 Prompt 中一致：
  PydanticOutputParser 绑定 ReflectionResult 模型 →
  生成 JSON Schema 文本 →
  填入占位符 →
  LLM 输出符合 Schema 的 JSON →
  Parser 反序列化为 ReflectionResult 实例

ReflectionResult Pydantic 模型通常包含：
  - score: int          （评分 1-10）
  - need_revision: bool （是否需要修改）
  - accepted_as_final: bool （是否可交付）
  - issues: list[str]   （发现的问题列表）
  - suggestions: list[str] （修改建议列表）
  - blocking_issues: list[str] （阻断性问题，必须解决）

LLM 看到 {format_instructions} 后，知道必须输出这个结构的 JSON，
否则 OutputParser 会抛出解析异常（ValidationError / OutputParserException）。

================================================================================
约束说明："不要编造"在 Reflection 中的体现
================================================================================
Reflection 的"不编造"体现在：
  1. 评分必须基于 {draft_plan} 的实际内容，不能凭印象
  2. issues 必须引用计划中的具体问题，不能写"似乎有些问题"这种模糊话
  3. 如果计划合格（≥7 分、无阻断问题），必须 accept_as_final=true，
     不能因为"感觉不够完美"就反复要求修改——这会进入无限修改循环

这对应 Stage 2 笔记 §5 Reflection 的原则：
  反思应该是"基于证据的评估"（evidence-based assessment），而非
  "审美判断"。每个 issue 都应对应到具体的检查项和评分扣分点。

================================================================================
与 Plan Prompt 的协作关系
================================================================================
Reflection 的 4 个检查项 → 分别对应 Plan Prompt 的 4 条规则：
  Reflection 检查预算  ↔  Plan 规则 6（总花费计算 + budget_status）
  Reflection 检查密度  ↔  Plan 规则 1（每天 2-3 个活动）
  Reflection 检查偏好  ↔  Parse 输出的结构化偏好（传递给 Plan）
  Reflection 检查风险  ↔  Plan 规则 4（risk_note 有就写）

这种"生成规则 → 审查标准"的对齐设计，保证了 Agent 内部逻辑一致：
规则定什么，就查什么；查什么问题，就修什么问题。
"""

from langchain_core.prompts import ChatPromptTemplate

reflection_prompt = ChatPromptTemplate.from_messages([
    ("system", """你是旅行计划审查员。快速检查计划质量，给出评分和建议。

检查项：
1. 预算是否超支
2. 行程是否过满（每天>4个活动）或过松（每天<2个活动）
3. 是否匹配用户偏好
4. 天气/交通风险是否标注

评分：9-10优秀 7-8可接受 5-6需修正 1-4严重问题
need_revision=true 时给出具体 suggestions；计划合格则 accepted_as_final=true。

{format_instructions}"""),
    ("human", """用户需求：{request}
工具信息：{context}
当前计划：{draft_plan}
修正次数：{revision_count}/{max_revision_count}""")
])
