# Task Plan: Travel Planning Agent (LangChain + LangGraph)

## Goal
Build a complete, runnable travel planning agent project based on the detailed engineering design document, implementing LangChain Structured Output + LangGraph workflow + Tool Adapter + Reflection loop.

## Current Phase
Complete

## Phases

### Phase 1: Project Scaffolding
- [ ] Create directory structure
- [ ] Write pyproject.toml with dependencies
- [ ] Write .env.example
- [ ] Write README.md
- **Status:** in_progress

### Phase 2: Schemas
- [ ] travel_request.py (TravelRequest, TravelPreference)
- [ ] travel_plan.py (Activity, DayPlan, TravelPlan)
- [ ] reflection.py (ReflectionResult)
- [ ] tool_result.py (ToolResult)
- **Status:** pending

### Phase 3: Config & State
- [ ] config/settings.py
- [ ] graph/state.py (TravelState)
- **Status:** pending

### Phase 4: Tools (Mock Providers)
- [ ] tools/base.py (ToolResult, safe_tool_call, fallback)
- [ ] tools/weather_tool.py
- [ ] tools/attraction_tool.py
- [ ] tools/food_tool.py
- [ ] tools/budget_tool.py
- [ ] tools/transport_tool.py
- [ ] tools/search_tool.py
- **Status:** pending

### Phase 5: Prompts
- [ ] prompts/parse_prompt.py
- [ ] prompts/plan_prompt.py
- [ ] prompts/reflection_prompt.py
- [ ] prompts/revise_prompt.py
- **Status:** pending

### Phase 6: Chains
- [ ] chains/parse_chain.py
- [ ] chains/plan_chain.py
- [ ] chains/reflection_chain.py
- [ ] chains/revise_chain.py
- **Status:** pending

### Phase 7: Nodes & Routers
- [ ] graph/nodes.py (all 9 nodes)
- [ ] graph/routers.py (2 conditional routers)
- **Status:** pending

### Phase 8: Graph Workflow Assembly
- [ ] graph/workflow.py (build_graph)
- **Status:** pending

### Phase 9: Services
- [ ] services/planner_service.py
- [ ] services/session_service.py
- **Status:** pending

### Phase 10: CLI Entry Point
- [ ] app/main.py
- [ ] app/__init__.py and all package __init__.py files
- **Status:** pending

### Phase 11: Tests
- [ ] tests/test_workflow.py
- [ ] tests/test_followup.py
- [ ] tests/test_tool_failure.py
- [ ] tests/test_reflection.py
- [ ] tests/test_parse.py
- [ ] tests/test_tools.py
- **Status:** pending

### Phase 12: Docs & Final Verification
- [ ] docs/architecture.md
- [ ] docs/workflow.md
- [ ] docs/prompt_design.md
- [ ] docs/eval_plan.md
- [ ] Run tests, verify everything works
- **Status:** pending

## Key Questions
1. Which LLM provider to configure? → Default to OpenAI-compatible, configurable via .env
2. Should we use interrupt/resume or simple re-invoke for clarification? → Start with simple re-invoke, document interrupt pattern

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| Mock tools first | Document specifies mock providers, real API later |
| Dict-based State | Document convention: model_dump() in state, not Pydantic objects |
| max_revision_count=2 | Document recommendation, balances quality and cost |
| OpenAI-compatible API | Works with OpenAI, DeepSeek, Qwen, Moonshot etc. |
