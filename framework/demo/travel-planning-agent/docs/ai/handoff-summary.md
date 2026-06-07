# 任务交接摘要

## 当前任务
旅行规划助手维护与优化 — 项目已完成 MVP，当前处于维护阶段。

## 已完成内容
- 完整 LangChain + LangGraph 旅行规划工作流（9 Nodes + 2 Routers + Reflection Loop）
- 6 个 Mock 工具 + 安全调用适配器
- Python 关键词需求解析（无 LLM）
- FastAPI Web 服务 + HTML 聊天界面
- 36 个测试全部通过
- DeepSeek API 适配（PydanticOutputParser 方案）
- 性能优化：parse 去 LLM 化、model LRU 缓存、快速模式跳过 reflection

## 修改过的文件（全项目文件清单）
- `app/graph/state.py` — TravelState 定义
- `app/graph/nodes.py` — 9 个节点（parse 用 Python 提取）
- `app/graph/routers.py` — 2 个条件路由
- `app/graph/workflow.py` — build_graph()，快速模式分支
- `app/chains/*.py` — RunnableLambda + lru_cache
- `app/prompts/*.py` — 4 套 Prompt
- `app/tools/*.py` — 6 个工具 + base
- `app/schemas/*.py` — 4 个 Schema
- `app/config/settings.py` — 环境变量配置
- `app/services/planner_service.py` — 业务逻辑
- `app/services/session_service.py` — 内存会话管理
- `app/server.py` — FastAPI + Jinja2
- `app/main.py` — CLI 入口
- `app/templates/index.html` — 聊天 UI
- `app/static/style.css` — 样式
- `tests/*.py` — 6 个测试文件
- `docs/*.md` — 架构/工作流/Prompt/评估文档
- `pyproject.toml`, `.env.example`, `README.md`

## 关键设计决策
1. **PydanticOutputParser 代替 with_structured_output** — DeepSeek V4 不支持 json_schema/tool_choice，用 text completion + parser 兼容所有 API
2. **RunnableLambda + LRU 缓存** — 修复 uvicorn 线程池中 httpx client 挂死，避免每次重复初始化 model
3. **parse 去 LLM 化** — Python 正则提取关键词，准确率够且省 16s
4. **默认快速模式** — max_revision_count=0 跳过 reflection，可从 81s 降到 24s
5. **State 只存 dict** — Pydantic 对象通过 model_dump() 后再写入 State
6. **工具失败不中断** — safe_tool_call 兜底 fallback

## 未解决问题
- DeepSeek API 响应时间波动大（13s-40s）
- 内存会话管理不持久化（重启丢失）
- 前端未显示当前处理阶段
- Mock 工具数据固定，未接真实 API

## 下一步建议
- 等待用户提出具体需求
- 可考虑：接入真实天气/景点 API
- 可考虑：会话持久化（Redis/文件）
- 可考虑：SSE 流式输出

## 不要重复做的事项
- 不要改回 with_structured_output（DeepSeek 不支持）
- 不要把 parse 改回 LLM 调用（性能倒退）
- 不要在 import 时创建 model（会导致 uvicorn 挂死）
- 不要默认开启 reflection（用户可手动设 max_revision_count=2）
- 不要删除 PydanticOutputParser 改用其他方案
