# 架构设计

## 分层架构

```
CLI / FastAPI
  ↓
LangGraph Workflow（流程编排）
  ├── parse_request → check_info → ask_clarification/decide_tools
  ├── collect_context → generate_plan → reflect_plan
  └── revise_plan → reflect_plan (循环) → final_output
  ↓
LangChain Capability Layer（节点能力）
  ├── parse_chain: Prompt + Model + TravelRequest
  ├── plan_chain: Prompt + Model + TravelPlan
  ├── reflection_chain: Prompt + Model + ReflectionResult
  └── revise_chain: Prompt + Model + TravelPlan
  ↓
Tool Adapter Layer（工具适配）
  ├── WeatherToolAdapter
  ├── AttractionToolAdapter
  ├── FoodToolAdapter
  ├── BudgetToolAdapter
  ├── TransportToolAdapter
  └── SearchToolAdapter
  ↓
Mock / Real API Providers
```

## 职责划分

- **LangGraph**: State 流转、节点连接、条件分支、循环控制
- **LangChain**: LLM 调用、Prompt 管理、Structured Output、Tool 封装
- **Tool Adapter**: 统一工具输入输出，屏蔽 mock 和真实 API 差异
