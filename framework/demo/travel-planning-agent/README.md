# 旅行规划助手 — LangChain + LangGraph 教学 Demo

> **前置课程：** [Stage 2 — Agent 基础范式理论学习](../stage2_agent_paradigms_2026_optimized.md)
>
> 学完 Stage 2 后，你已经理解了 ReAct、Plan-and-Execute、Reflection、Workflow Agent 等范式的概念。本 Demo 是这些概念的**代码落地**——用 LangChain + LangGraph 亲手构建一个完整的 Agent 项目。

---

## 这个 Demo 教会你什么

### 对应 Stage 2 的概念落地

| Stage 2 概念 | 本项目的对应实现 |
|---|---|
| **Workflow Agent** (§6) | `app/graph/workflow.py` — LangGraph 控制主流程，9 个节点按固定路由流转 |
| **Reflection / Reflexion** (§5) | `reflect_plan_node` → `revise_plan_node` → 再 `reflect_plan` 的真实循环 |
| **结构化输出** (§3 LLM 调用) | Pydantic Schema → `PydanticOutputParser` → LLM 输出被约束为结构化 JSON |
| **Tool Calling** (§3 ReAct) | 6 个 Mock 工具 + `safe_tool_call` 容错 + Tool Adapter 模式 |
| **Plan-and-Execute** (§4) | 解析需求 → 查工具 → 生成计划 → 审查修正 → 输出（隐式的计划-执行链） |
| **Verifier / Evaluator** (§10) | `reflect_plan_node` 打分 1-10，检查预算/行程/偏好，给出 blocking_issues |
| **Router Agent** (§7) | `routers.py` — `route_after_check` 根据信息完整性路由，`route_after_reflection` 根据审查结果路由 |
| **State 管理** (§2.4) | `TravelState` 分 7 个区域：用户输入、需求、工具上下文、计划、反思、控制、追踪 |
| **HITL 的思想** (§11) | 信息不足时 `ask_clarification_node` 暂停并向用户追问，补充后继续 |

### 用到的 LangChain / LangGraph 核心 API

| API | 在哪里用 |
|---|---|
| `ChatPromptTemplate` | `app/prompts/` — 4 套 Prompt 模板 |
| `PydanticOutputParser` | `app/chains/` — 约束 LLM 输出为 Pydantic 对象 |
| `init_chat_model` | `app/chains/` — 连接 DeepSeek / OpenAI |
| `@tool` 装饰器 | `app/tools/` — 把 Python 函数变成 LangChain Tool |
| `StateGraph` | `app/graph/workflow.py` — 构建有状态的工作流图 |
| `add_node` / `add_edge` | `app/graph/workflow.py` — 注册节点、连接节点 |
| `add_conditional_edges` | `app/graph/workflow.py` — 条件分支（if-else 路由） |
| `graph.stream()` | `app/server.py` — 流式执行，每完成一个节点就推送进度 |
| SSE（Server-Sent Events） | `app/server.py` — 实时推送 LLM token 到前端 |

---

## 架构全景图

```
浏览器 http://127.0.0.1:8000
  │ 用户输入："我想6月底去成都玩3天，预算3000，喜欢美食"
  │
  ▼
┌─────────────────────────────────────────────────────────────┐
│ FastAPI (app/server.py)                                     │
│   POST /api/travel-plan/stream → SSE 流式响应                │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ LangGraph StateGraph (app/graph/)                           │
│                                                             │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐               │
│  │① parse   │──→│② check   │──→│③ tools   │               │
│  │ LLM解析  │   │ 信息完整? │   │ 动态选择  │               │
│  └──────────┘   └────┬─────┘   └────┬─────┘               │
│                  不完整│        完整 │                       │
│               ┌───────▼──┐   ┌──────▼──────┐               │
│               │④ ask     │   │⑤ collect    │               │
│               │  追问→END│   │  调5个工具   │               │
│               └──────────┘   └──────┬──────┘               │
│                                     │                       │
│                              ┌──────▼──────┐               │
│                              │⑥ generate   │ ← ①号LLM调用  │
│                              │  生成计划    │               │
│                              └──────┬──────┘               │
│                                     │                       │
│                              ┌──────▼──────┐               │
│                              │⑦ reflect    │ ← ②号LLM调用  │
│                              │  审查评分    │←─────────┐    │
│                              └──────┬──────┘          │    │
│                                 通过│  需修正&未超次数  │    │
│                              ┌──────▼──┐ ┌─────────┴──┐    │
│                              │⑨ output │ │⑧ revise    │    │
│                              │ 渲染MD  │ │  修正→回到⑦│    │
│                              └────┬────┘ └────────────┘    │
│                                   │                         │
└───────────────────────────────────┼─────────────────────────┘
                                    │
                                    ▼
                           Markdown 旅行方案
```

### LangChain 与 LangGraph 的分工

```
┌─────────────────────────────────────────┐
│            LangGraph 负责                │
│   "节点之间怎么走"                        │
│   State 流转、条件分支、循环控制           │
│   StateGraph, Node, Edge, Router         │
├─────────────────────────────────────────┤
│            LangChain 负责                │
│   "每个节点里做什么"                      │
│   Prompt 管理、LLM 调用、工具封装、        │
│   结构化输出解析、Token 流式推送           │
│   ChatPromptTemplate, Chain, Tool,       │
│   PydanticOutputParser                   │
└─────────────────────────────────────────┘
```

---

## 快速开始

### 1. 安装依赖

```bash
cd travel-planning-agent
pip install -e ".[dev]"
```

### 2. 配置 API Key

```bash
cp .env.example .env
```

编辑 `.env`，填入你的 API Key：

```env
# DeepSeek（默认）
OPENAI_API_KEY=sk-xxxxxxxx
OPENAI_BASE_URL=https://api.deepseek.com/v1
MODEL_NAME=deepseek-chat

# 或用 OpenAI
# OPENAI_API_KEY=sk-xxxxxxxx
# OPENAI_BASE_URL=https://api.openai.com/v1
# MODEL_NAME=gpt-4o-mini
```

### 3. 启动 Web 服务

```bash
python -m app.server
```

浏览器打开 **http://127.0.0.1:8000**

### 4. 试试这些输入

```
我想6月底去成都玩3天，预算3000元，喜欢美食和轻松路线
```

```
我准备周日去韩国首尔，玩三天预算10000，我喜欢购物
```

```
帮我规划旅行
（触发追问：请补充目的地、天数、预算、偏好）
```

---

## 项目结构逐层解读

> **建议阅读顺序：** 从底层数据模型往上读到顶层服务，就像盖房子从地基到屋顶。

### 第一层：数据模型（app/schemas/）

| 文件 | 内容 | 对应 Stage 2 概念 |
|---|---|---|
| `travel_request.py` | 用户想要什么：目的地、天数、预算、偏好 | §3 结构化输出 |
| `travel_plan.py` | 生成的计划：每天安排、活动、花费、风险 | §4 Plan 的结构 |
| `reflection.py` | 审查结果：评分、问题、建议、是否需要修正 | §5 Reflection |
| `tool_result.py` | 工具统一输出格式：数据、来源、置信度 | §3 Tool Calling |

### 第二层：配置与状态（app/config/, app/graph/state.py）

| 文件 | 内容 |
|---|---|
| `config/settings.py` | 从 `.env` 读 API Key、模型名、温度参数 |
| `graph/state.py` | `TravelState` — 贯穿所有节点的共享上下文（7 个分区） |

### 第三层：工具层（app/tools/）

| 文件 | 内容 |
|---|---|
| `base.py` | `safe_tool_call` 安全调用 + `fallback_tool_result` 兜底 |
| `weather_tool.py` | Mock 天气查询 |
| `attraction_tool.py` | Mock 景点搜索 |
| `food_tool.py` | Mock 美食搜索 |
| `budget_tool.py` | Mock 预算估算 |
| `transport_tool.py` | Mock 交通建议 |
| `search_tool.py` | Mock 实时搜索 |

### 第四层：Prompt 与 Chain（app/prompts/, app/chains/）

| 文件 | 内容 |
|---|---|
| `prompts/*.py` | 4 套 `ChatPromptTemplate`：解析、规划、审查、修正 |
| `chains/parse_chain.py` | 解析链：Prompt → LLM → TravelRequest |
| `chains/plan_chain.py` | 规划链：Prompt → LLM → TravelPlan（支持流式） |
| `chains/reflection_chain.py` | 审查链：Prompt → LLM → ReflectionResult（支持流式） |
| `chains/revise_chain.py` | 修正链：Prompt → LLM → TravelPlan（支持流式） |

### 第五层：工作流（app/graph/）

| 文件 | 内容 |
|---|---|
| `nodes.py` | 9 个节点函数，每个节点做一件事 |
| `routers.py` | 2 个路由器，根据 State 决定走哪条分支 |
| `workflow.py` | `build_graph()` 把所有节点和路由组装成 StateGraph |

### 第六层：服务与界面（app/services/, app/server.py, app/templates/）

| 文件 | 内容 |
|---|---|
| `services/planner_service.py` | 业务逻辑：plan()、continue_plan() |
| `services/session_service.py` | 内存会话管理 |
| `server.py` | FastAPI + SSE 流式推送 |
| `templates/index.html` | 聊天 UI + 打字机效果 + 审查模式开关 |
| `static/style.css` | 样式 |

### 第七层：测试（tests/）

| 文件 | 测试内容 |
|---|---|
| `test_parse.py` | Schema 校验 |
| `test_tools.py` | 6 个工具 + safe_tool_call 容错 |
| `test_reflection.py` | ReflectionResult + 路由逻辑 |
| `test_workflow.py` | 端到端：完整输入生成、信息缺失追问 |
| `test_followup.py` | 用户补充后继续 |
| `test_tool_failure.py` | 工具挂了也不中断流程 |

---

## 核心设计决策（为什么这样设计）

| 决策 | 原因 | 对应 Stage 2 |
|---|---|---|
| Workflow 控制主流程 | 旅行规划的步骤是确定的，不需要 LLM 动态决定"下一步做什么" | §6 Workflow Agent |
| 节点内 LLM 负责理解和生成，节点间 LangGraph 负责流转 | 确定性交给代码，不确定性交给模型 | §2.3 Agent vs Workflow |
| Reflection 循环有硬上限（max_revision=2） | 避免无限反思、成本失控 | §5.8 Reflection 工程约束 |
| 工具失败不中断 | fallback 兜底，确保系统鲁棒性 | §3.10 ReAct Checklist |
| 快速模式默认开启审查 | 展示 Reflection 范式，用户可关 | §5 Reflection |
| PydanticOutputParser | DeepSeek 不支持 json_schema，兼容所有 API | §3 结构化输出 |
| SSE 流式 + 打字机效果 | 用户等待时可见 LLM 思考过程，提升体验 | — |

---

## 学习路线

### 第一步：理解"它做了什么"

1. 启动服务，在浏览器里输入旅行需求
2. 观察右侧进度面板：解析 → 检查 → 生成 → 审查 → 输出
3. 点开"思考中"折叠块，看 LLM 吐出的原始 token

### 第二步：理解"数据怎么流"

1. 从 `app/schemas/` 开始，看懂 4 个 Pydantic 模型
2. 读 `app/graph/state.py`，理解 TravelState 的 7 个分区
3. 读 `app/graph/nodes.py`，追踪每个节点从 state 读什么、写什么

### 第三步：理解"流程怎么走"

1. 读 `app/graph/workflow.py` 的 `build_graph()`
2. 画一遍流程图：START → parse → check → ... → END
3. 理解两个条件路由：信息完整？要不要修正？

### 第四步：理解"LLM 怎么被调用"

1. 读 `app/prompts/parse_prompt.py` → 看 Prompt 模板怎么写
2. 读 `app/chains/parse_chain.py` → 看 Chain 怎么组装
3. 理解 `|` 管道符：`prompt | model | parser`
4. 理解 `PydanticOutputParser` 怎么把 LLM 文本变成 Pydantic 对象

### 第五步：理解"Agent 范式怎么落地"

对照 Stage 2 笔记：
- Workflow Agent → `workflow.py` 的 StateGraph 就是"开发者定义的主流程"
- Reflection → `reflect_plan_node` + `revise_plan_node` + `routers.py`
- Router → `routers.py` 的条件路由就是"根据状态走不同分支"
- Tool Calling → `tools/` + `collect_context_node`

### 第六步：改造实验

- 把 max_revision_count 从 2 改成 1，观察效果
- 新增一个工具（比如酒店搜索），加入 `collect_context_node`
- 修改 plan prompt，要求只输出 2 天的行程
- 把审查模式关掉（取消勾选），对比速度和输出质量

---

## 技术栈

| 技术 | 用途 |
|---|---|
| Python >= 3.11 | 语言 |
| LangChain >= 1.1 | Prompt 管理、LLM 调用、Tool 封装、Structured Output |
| LangGraph >= 1.0 | StateGraph 工作流编排、Node、Edge、条件路由 |
| FastAPI | Web 服务 + SSE 流式推送 |
| Jinja2 | HTML 模板渲染 |
| Pydantic >= 2.0 | 数据模型 + 校验 + JSON 解析 |
| DeepSeek / OpenAI | LLM API（OpenAI 兼容协议） |
| pytest >= 8.0 | 测试框架 |

---

## 运行测试

```bash
# 全部
pytest tests/ -v

# 不需要 API Key 的（秒级）
pytest tests/test_parse.py tests/test_tools.py tests/test_reflection.py -v

# 需要 API Key 的（分钟级，依赖 LLM 调用）
pytest tests/test_workflow.py tests/test_followup.py tests/test_tool_failure.py -v
```

---

## 后续可以做的扩展

1. **接真实 API** — 把 mock 工具换成高德地图、和风天气、美团 API
2. **加 Intent Router** — 用户说"帮我取消订单"时路由到订单模块，说"帮我规划旅行"时路由到旅行模块
3. **加 HITL** — 预算超支时弹窗要求用户确认，不自动继续
4. **持久化会话** — 用 Redis 存 session，服务重启不丢失
5. **加 Eval 测试集** — 构造 30 条旅行需求，评测端到端成功率

---

> **一句话总结：** 这个 Demo 不是"让 LLM 自由发挥"，而是用 LangGraph 搭好流程框架，让 LLM 在受控的节点内发挥理解和生成能力——这就是 Stage 2 里说的"让代码控制确定性，让模型处理不确定性"。
