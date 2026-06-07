# Prompt 设计

## parse_prompt
- 角色：旅行需求解析器
- 输入：用户自然语言
- 输出：TravelRequest (structured)
- 要求：不编造，缺失字段返回 null/空

## plan_prompt
- 角色：专业旅行规划师
- 输入：request + context
- 输出：TravelPlan (structured)
- 要求：严格围绕预算/天数/偏好，每天 3 个时段，不编造 mock 数据中不存在的事实

## reflection_prompt
- 角色：旅行计划审查员
- 输入：request + context + draft_plan + revision_count
- 输出：ReflectionResult (structured)
- 检查项：预算、行程密度、偏好匹配、天气/交通/数据风险、信息缺失

## revise_prompt
- 角色：旅行计划修正器
- 输入：request + context + draft_plan + reflection
- 输出：TravelPlan (structured)
- 要求：优先解决 blocking_issues，逐条处理 suggestions
