# 开发进度记录

## 2026-05-27：项目初始化 + MVP 构建

### 已完成
- 项目目录结构搭建
- 4 个 Pydantic Schema（TravelRequest, TravelPlan, ReflectionResult, ToolResult）
- TravelState 分层设计
- 6 个 Mock 工具 + base 适配器（safe_tool_call, fallback）
- 4 套 Prompt 模板（parse, plan, reflection, revise）
- 4 条 LangChain Chain（PydanticOutputParser 方案）
- 9 个 Graph Node + 2 个条件 Router
- LangGraph 工作流组装（含 Reflection 循环）
- PlannerService + SessionService 服务层
- CLI 入口（app/main.py）
- 6 个测试文件，36 个测试用例
- 4 份文档（architecture, workflow, prompt_design, eval_plan）

### 修改文件
- 全部新建

### 技术决策
- 使用 PydanticOutputParser 代替 with_structured_output（DeepSeek 兼容性）
- RunnableLambda 延迟创建 model + LRU 缓存（修复 uvicorn 线程池挂死）

## 2026-05-28：DeepSeek 适配 + 性能优化

### 已完成
- DeepSeek API 配置（api.deepseek.com/v1, deepseek-v4-flash）
- Chain 改为 PydanticOutputParser 方案
- parse_request_node 从 LLM 改为 Python 关键词提取（省 ~16s）
- model 懒加载 + LRU 缓存
- Prompt 精简（减少输出 token）
- 默认快速模式（max_revision_count=0，跳过 reflection）
- 端到端响应时间从 81s 降至平均 24s

### 修改文件
- app/chains/*.py — RunnableLambda + lru_cache
- app/graph/nodes.py — _extract_request Python 解析器
- app/graph/workflow.py — route_after_generate 快速模式分支
- app/prompts/plan_prompt.py — 精简指令
- app/prompts/reflection_prompt.py — 精简指令
- app/services/planner_service.py — 默认 max_revision_count=0
- app/server.py — async endpoint + 延迟 import

## 2026-05-29：FastAPI + HTML 前端

### 已完成
- FastAPI 服务（app/server.py）：3 个 API 路由
- HTML 聊天界面（app/templates/index.html）：消息气泡、Markdown 渲染、多轮追问
- CSS 样式（app/static/style.css）
- 6 个 API 测试全部通过

### 修改文件
- pyproject.toml — 加 fastapi/uvicorn/jinja2 依赖
- app/server.py — 新建
- app/templates/index.html — 新建
- app/static/style.css — 新建

## 当前未完成
- 无特定待办项

## 下一步
- 等待用户提出具体需求
