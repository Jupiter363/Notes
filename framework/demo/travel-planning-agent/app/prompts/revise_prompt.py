from langchain_core.prompts import ChatPromptTemplate

revise_prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一个旅行计划修正器。请根据 Reflection 的 issues 和 suggestions 修正当前计划。

要求：
1. 保持 TravelPlan 结构完整；
2. 优先解决 blocking_issues 中的阻断性问题；
3. 针对 suggestions 中的每条建议逐一修改或说明；
4. 不要改变用户核心需求（目的地、天数、偏好）；
5. 若预算超支，应替换高价活动为低价替代方案，或在 risk_notes 中说明不可避免的原因；
6. 若行程过紧，应减少活动数量（每天 3-4 个为宜）或增加休息时段；
7. 若天气有风险，应将户外活动优先安排在天气较好的日期或时段；
8. 修正后的计划应比修正前有明显改善。

{format_instructions}"""),
    ("human", """用户需求：
{request}

工具上下文：
{context}

当前计划：
{draft_plan}

反思结果：
{reflection}""")
])
