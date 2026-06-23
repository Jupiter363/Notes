# 旅行规划助手技术教程

> 本文是 `travel-planning-agent` 的完整技术教程。它不只是告诉你怎么运行项目，更重要的是解释：这个 Demo 如何把 Stage 2 中的 Agent 范式落到代码里，LangChain 负责什么，LangGraph 负责什么，为什么要这样设计，以及你应该按什么顺序读源码和改造它。

---

## 目录

1. [项目目标](#项目目标)
2. [快速运行](#快速运行)
3. [技术栈总览](#技术栈总览)
4. [整体架构](#整体架构)
5. [一次请求的完整生命周期](#一次请求的完整生命周期)
6. [源码阅读路线](#源码阅读路线)
7. [核心数据模型](#核心数据模型)
8. [State：工作流的共享记忆](#state工作流的共享记忆)
9. [Chain：一次 LLM 调用如何被封装](#chain一次-llm-调用如何被封装)
10. [Tool：工具调用与安全降级](#tool工具调用与安全降级)
11. [Node：9 个工作流步骤](#node9-个工作流步骤)
12. [Router：条件分支与循环退出](#router条件分支与循环退出)
13. [Workflow：LangGraph 如何编排 Agent](#workflowlanggraph-如何编排-agent)
14. [Web 服务与 SSE 流式输出](#web-服务与-sse-流式输出)
15. [多轮对话与 HITL](#多轮对话与-hitl)
16. [Reflection 循环详解](#reflection-循环详解)
17. [测试体系](#测试体系)
18. [扩展练习](#扩展练习)
19. [深度源码拆解](#深度源码拆解)
20. [调试与排错](#调试与排错)
21. [常见问题](#常见问题)

---

## 项目目标

这个项目是一个教学型 Agent Demo：用户输入旅行需求，系统自动解析需求、检查信息完整性、调用 mock 工具收集上下文、生成旅行计划、审查计划、必要时修正计划，最后输出 Markdown 格式的旅行方案。

它重点展示这些 Agent 工程概念：

| 概念 | 项目中的落地位置 |
|---|---|
| Workflow Agent | `app/graph/workflow.py` 使用 `StateGraph` 明确编排流程 |
| Structured Output | `app/chains/` 中使用 `PydanticOutputParser` |
| Tool Calling | `app/tools/` 中的 6 个 mock 工具 |
| Tool Adapter | `app/tools/base.py` 的 `safe_tool_call()` |
| Reflection | `reflect_plan_node` 和 `revise_plan_node` 构成审查修正循环 |
| Router | `app/graph/routers.py` 根据状态决定下一步 |
| HITL | 信息不足时进入 `ask_clarification_node`，等待用户补充 |
| State Management | `app/graph/state.py` 定义贯穿流程的共享状态 |
| SSE Streaming | `app/server.py` 将 token 和节点进度实时推给前端 |

一句话理解：

```text
LangChain 负责每个节点里如何调用 LLM / Prompt / Parser / Tool。
LangGraph 负责节点之间按什么顺序、分支和循环执行。
```

---

## 快速运行

### 1. 安装依赖

```bash
cd travel-planning-agent
pip install -e ".[dev]"
```

### 2. 配置环境变量

复制示例配置：

```bash
cp .env.example .env
```

编辑 `.env`：

```env
OPENAI_API_KEY=sk-xxxxxxxx
OPENAI_BASE_URL=https://api.deepseek.com/v1
MODEL_NAME=deepseek-chat
TEMPERATURE=0
MAX_REVISION_COUNT=2
```

项目使用 OpenAI 兼容协议，所以 DeepSeek、OpenAI、Qwen、Moonshot 等兼容服务都可以接入，只要设置好 `OPENAI_BASE_URL` 和 `MODEL_NAME`。

### 3. 启动 Web 服务

```bash
python -m app.server
```

浏览器打开：

```text
http://127.0.0.1:8000
```

### 4. 命令行运行

```bash
python -m app.main "我想6月底去成都玩3天，预算3000元，喜欢美食和轻松路线"
```

或进入交互模式：

```bash
python -m app.main
```

### 5. 推荐试验输入

完整输入：

```text
我想6月底去成都玩3天，预算3000元，喜欢美食和轻松路线
```

信息不完整输入：

```text
帮我规划旅行
```

这会触发追问流程，系统会要求补充目的地、天数、预算和偏好。

快速模式输入方式：在 Web 页面取消“深度审查”。前端会把 `max_revision_count` 设置为 `0`，工作流会跳过 Reflection。

---

## 技术栈总览

| 技术 | 用途 |
|---|---|
| Python 3.11+ | 项目语言 |
| LangChain | Prompt、LLM 调用、Parser、Tool 封装 |
| LangGraph | StateGraph 工作流编排、条件路由、循环控制 |
| Pydantic v2 | 数据模型、字段校验、结构化输出 |
| FastAPI | HTTP API、Web 服务 |
| Uvicorn | ASGI 服务运行器 |
| Jinja2 | HTML 模板渲染 |
| SSE | 后端向前端推送 token 和进度事件 |
| pytest | 单元测试和端到端测试 |

---

## 整体架构

项目可以分成 7 层：

```text
浏览器 / CLI
  |
  v
FastAPI / PlannerService
  |
  v
LangGraph Workflow
  |
  +-- parse_request
  +-- check_info
  +-- ask_clarification / decide_tools
  +-- collect_context
  +-- generate_plan
  +-- reflect_plan
  +-- revise_plan
  +-- final_output
  |
  v
LangChain Chains
  |
  +-- parse_chain
  +-- plan_chain
  +-- reflection_chain
  +-- revise_chain
  |
  v
Prompt + LLM + PydanticOutputParser
  |
  v
Tools / Mock Providers
```

职责划分：

| 层 | 文件 | 职责 |
|---|---|---|
| 配置层 | `app/config/settings.py` | 读取 `.env` 中的模型配置 |
| Schema 层 | `app/schemas/` | 定义输入、输出、审查结果、工具结果结构 |
| Prompt 层 | `app/prompts/` | 定义 LLM 的角色、任务和输出格式要求 |
| Chain 层 | `app/chains/` | 组合 Prompt、Model、Parser，形成可调用对象 |
| Tool 层 | `app/tools/` | 提供天气、景点、美食、预算、交通、搜索等工具 |
| Graph 层 | `app/graph/` | 定义 State、节点、路由和完整 LangGraph |
| 服务层 | `app/services/`, `app/server.py`, `app/main.py` | 对外提供 Web、API、CLI |

---

## 一次请求的完整生命周期

以这句输入为例：

```text
我想6月底去成都玩3天，预算3000元，喜欢美食和轻松路线
```

完整执行流程：

```text
1. 前端 POST /api/travel-plan/stream
2. server.py 创建 session_id 和初始 state
3. LangGraph 从 START 进入 parse_request
4. parse_chain 把自然语言解析为 TravelRequest
5. check_info_node 检查必填字段是否完整
6. route_after_check 决定继续或追问
7. decide_tools_node 根据偏好选择工具
8. collect_context_node 安全调用工具并合并上下文
9. generate_plan_node 调用 plan_chain 生成 TravelPlan
10. route_after_generate 判断是否进入审查模式
11. reflect_plan_node 调用 reflection_chain 评分和找问题
12. route_after_reflection 决定修正或输出
13. revise_plan_node 必要时修正 TravelPlan，并回到 reflect_plan
14. final_output_node 把结构化计划渲染为 Markdown
15. server.py 通过 SSE 返回 done 事件
16. 前端用 marked.js 渲染 Markdown
```

---

## 源码阅读路线

建议按这个顺序读源码：

### 第一遍：看结构

1. `README.md`
2. `docs/architecture.md`
3. `docs/workflow.md`
4. `app/graph/workflow.py`

目标：先知道项目由哪些层组成，工作流怎么走。

### 第二遍：看数据

1. `app/schemas/travel_request.py`
2. `app/schemas/travel_plan.py`
3. `app/schemas/reflection.py`
4. `app/schemas/tool_result.py`
5. `app/graph/state.py`

目标：理解 State 中每个字段什么时候产生、被谁消费。

### 第三遍：看能力

1. `app/prompts/`
2. `app/chains/`
3. `app/tools/base.py`
4. `app/tools/*_tool.py`

目标：理解 LangChain 如何封装 LLM 和工具调用。

### 第四遍：看编排

1. `app/graph/nodes.py`
2. `app/graph/routers.py`
3. `app/graph/workflow.py`

目标：理解每个节点的输入输出、分支和循环退出条件。

### 第五遍：看服务化

1. `app/services/planner_service.py`
2. `app/services/session_service.py`
3. `app/server.py`
4. `app/templates/index.html`

目标：理解 Web API、SSE、会话和多轮补充如何串起来。

---

## 核心数据模型

### TravelRequest：用户需求

文件：`app/schemas/travel_request.py`

`TravelRequest` 是自然语言解析后的结构化结果：

```python
class TravelRequest(BaseModel):
    destination: Optional[str]
    start_date: Optional[str]
    days: Optional[int]
    budget: Optional[float]
    preferences: List[str]
    companions: Optional[str]
    departure_city: Optional[str]
    pace: Optional[str]
```

关键点：

- 字段大多是 `Optional`，因为用户可能第一次没说全。
- `days` 有 `ge=1, le=30` 校验，避免离谱输入。
- `preferences` 用 `default_factory=list`，避免共享可变默认值。
- 解析阶段不强行补全信息，缺什么就让后续节点追问。

### TravelPlan：旅行方案

文件：`app/schemas/travel_plan.py`

它是三层嵌套结构：

```text
TravelPlan
  |
  +-- DayPlan[]
        |
        +-- Activity[]
```

`Activity` 包含活动名称、地点、理由、花费、持续时间、交通提示和风险提示。这个结构让最终方案不是泛泛而谈，而是可检查、可渲染、可修正。

### ReflectionResult：审查结果

文件：`app/schemas/reflection.py`

```python
class ReflectionResult(BaseModel):
    need_revision: bool
    score: int
    issues: List[str]
    suggestions: List[str]
    blocking_issues: List[str]
    accepted_as_final: bool
```

最关键的是 `need_revision` 和 `accepted_as_final`：

- `accepted_as_final=True`：直接输出。
- `need_revision=True` 且未超过最大修正次数：进入 `revise_plan`。
- 修正次数已用完：强制输出，避免无限循环。

### ToolResult：工具统一协议

文件：`app/schemas/tool_result.py`

```python
class ToolResult(BaseModel):
    data: dict | list
    source: str
    updated_at: Optional[str]
    confidence: str
    error: Optional[str]
```

统一协议的意义：今天工具是 mock，明天换真实 API，上游节点不需要改。只要仍返回这个结构，`collect_context_node` 和 `plan_chain` 就能继续工作。

---

## State：工作流的共享记忆

文件：`app/graph/state.py`

`TravelState` 是一个 `TypedDict`，贯穿整个 LangGraph。每个节点读取部分字段，并返回一个 dict 更新 State。

核心分区：

| 区域 | 字段 | 谁写入 |
|---|---|---|
| 用户输入区 | `user_input`, `user_inputs` | 初始请求、`parse_request_node` |
| 需求区 | `request` | `parse_request_node` |
| 检查区 | `missing_fields`, `is_info_complete`, `clarification_questions` | `check_info_node`, `ask_clarification_node` |
| 工具区 | `required_tools`, `context` | `decide_tools_node`, `collect_context_node` |
| 计划区 | `draft_plan` | `generate_plan_node`, `revise_plan_node` |
| 反思区 | `reflection` | `reflect_plan_node` |
| 输出区 | `final_plan` | `ask_clarification_node`, `final_output_node` |
| 控制区 | `revision_count`, `max_revision_count`, `stop_reason` | 多个节点 |
| 追踪区 | `trace`, `tool_errors`, `system_errors` | 多个节点 |

为什么 State 中存 dict，而不是 Pydantic 对象？

```python
result: TravelPlan = plan_chain.invoke(...)
return {"draft_plan": result.model_dump()}
```

原因：

- dict 更容易 JSON 序列化。
- LangGraph checkpoint 和服务层保存状态更自然。
- 避免后续节点一会儿用 `obj.attr`，一会儿用 `dict["key"]`。

---

## Chain：一次 LLM 调用如何被封装

文件：`app/chains/`

本项目有 4 条 Chain：

| Chain | 输入 | 输出 | 用途 |
|---|---|---|---|
| `parse_chain` | 用户自然语言 | `TravelRequest` | 抽取结构化需求 |
| `plan_chain` | `request + context` | `TravelPlan` | 生成旅行计划 |
| `reflection_chain` | `request + context + draft_plan` | `ReflectionResult` | 审查计划 |
| `revise_chain` | `request + context + draft_plan + reflection` | `TravelPlan` | 修正计划 |

### 标准结构

每个 chain 都遵循同一模式：

```python
parser = PydanticOutputParser(pydantic_object=TravelPlan)
prompt_with_format = plan_prompt.partial(
    format_instructions=parser.get_format_instructions()
)
chain = prompt_with_format | model | parser
```

这个管道的含义：

```text
输入 dict
  -> ChatPromptTemplate 填充变量
  -> init_chat_model 创建的模型生成文本
  -> PydanticOutputParser 解析为 Pydantic 对象
```

### 为什么用 RunnableLambda

当前代码没有在模块 import 时直接创建模型，而是：

```python
plan_chain = RunnableLambda(_invoke)
```

这样做有几个好处：

- import 模块时不需要 API Key 立即可用。
- 首次真正调用时才初始化模型。
- 配合 `@lru_cache(maxsize=1)` 缓存模型实例。
- `_invoke()` 内部可以根据是否设置 stream queue，选择普通模式或流式模式。

### 普通模式与流式模式

普通模式：

```text
_stream_queue is None
  -> 使用 LCEL 管道一次性 invoke
  -> 返回完整 Pydantic 对象
```

流式模式：

```text
_stream_queue is not None
  -> 手动 prompt.invoke()
  -> model.stream(messages)
  -> 每个 token 推入 SSE queue
  -> 同时累积 full_text
  -> 生成结束后 parser.parse(full_text)
```

这个设计让 Web 前端既能看到 token 流，又能在后端拿到完整结构化对象。

---

## Tool：工具调用与安全降级

文件：`app/tools/`

项目内置 6 个 mock 工具：

| 工具 | 文件 | 用途 |
|---|---|---|
| `get_weather` | `weather_tool.py` | 查询天气和天气风险 |
| `search_attractions` | `attraction_tool.py` | 查询景点 |
| `search_foods` | `food_tool.py` | 查询美食 |
| `estimate_budget` | `budget_tool.py` | 估算预算 |
| `search_transport` | `transport_tool.py` | 查询交通建议 |
| `web_search` | `search_tool.py` | 查询最新信息 |

### Tool Adapter

文件：`app/tools/base.py`

核心函数：

```python
def safe_tool_call(tool, args: dict, fallback_source: str) -> tuple[dict, dict | None]:
    try:
        if hasattr(tool, "invoke"):
            result = tool.invoke(args)
        else:
            result = tool(**args)
        return result, None
    except Exception as e:
        return fallback_tool_result(fallback_source, str(e)), error
```

它解决两个问题：

1. 工具可能是 LangChain `@tool` 包装后的对象，也可能是普通 Python 函数。
2. 工具可能失败，但失败不能让整个 Agent 崩溃。

工具失败时，系统会返回：

```python
{
    "data": {},
    "source": "fallback_weather",
    "updated_at": "...",
    "confidence": "low",
    "error": "错误原因"
}
```

最终方案会在“数据限制说明”中提醒用户自行确认低置信度信息。

---

## Node：9 个工作流步骤

文件：`app/graph/nodes.py`

节点函数统一签名：

```python
def some_node(state: TravelState) -> dict:
    ...
    return {"field": value}
```

LangGraph 会把返回的 dict 合并回 State。

### 1. parse_request_node

职责：调用 `parse_chain`，把自然语言解析成 `TravelRequest`。

额外逻辑：支持多轮合并。新一轮用户补充的信息会覆盖旧字段，但空值不会覆盖旧值。

例如：

```text
第一轮：帮我规划旅行
第二轮：去成都，3天，预算3000，喜欢美食
```

第二轮解析结果会和第一轮已有 State 合并。

### 2. check_info_node

职责：检查必要字段是否齐全。

必要字段：

```python
required_fields = ["destination", "days", "budget", "preferences"]
```

这是纯 Python 逻辑，不调用 LLM。原则是：能用确定性代码判断的，就不要花钱调模型。

### 3. ask_clarification_node

职责：根据缺失字段生成追问。

例如缺少 `budget`：

```text
你的总预算大概是多少？
```

它会设置：

```python
stop_reason = "need_user_clarification"
```

然后工作流结束，等待用户补充。

### 4. decide_tools_node

职责：根据用户需求选择工具。

默认工具：

```python
["weather", "attractions", "budget", "transport"]
```

条件工具：

- 偏好包含“美食”：增加 `foods`
- 有 `start_date`：增加 `web_search`

### 5. collect_context_node

职责：逐一调用 `required_tools` 中的工具，合并结果到 `context`。

关键设计：

- 每个工具独立安全调用。
- 一个工具失败不影响其他工具。
- 错误进入 `tool_errors`。
- 后续 LLM 仍能基于已有上下文生成计划。

### 6. generate_plan_node

职责：调用 `plan_chain` 生成初版 `TravelPlan`。

输入包括：

```python
{
    "user_input": state["user_input"],
    "request": state["request"],
    "context": state.get("context", {}),
}
```

输出写入：

```python
draft_plan = result.model_dump()
```

### 7. reflect_plan_node

职责：调用 `reflection_chain` 审查当前计划。

审查关注：

- 预算是否合理。
- 行程密度是否过高。
- 是否匹配用户偏好。
- 是否标注天气、交通、数据置信度风险。
- 是否需要修正。

### 8. revise_plan_node

职责：根据 Reflection 的 `issues`、`suggestions`、`blocking_issues` 修正计划。

修正后：

```python
revision_count += 1
```

然后工作流回到 `reflect_plan`，再次审查。

### 9. final_output_node

职责：把结构化 `TravelPlan` 渲染成 Markdown。

这是纯 Python 格式转换，不调用 LLM。这样输出格式稳定、可控、没有额外幻觉。

---

## Router：条件分支与循环退出

文件：`app/graph/routers.py`

### route_after_check

```python
def route_after_check(state):
    if state.get("is_info_complete"):
        return "decide_tools"
    return "ask_clarification"
```

如果信息完整，进入工具选择；否则追问用户。

### route_after_reflection

```python
def route_after_reflection(state):
    reflection = state.get("reflection", {})
    need_revision = reflection.get("need_revision", False)
    accepted_as_final = reflection.get("accepted_as_final", False)
    revision_count = state.get("revision_count", 0)
    max_revision_count = state.get("max_revision_count", 2)

    if accepted_as_final:
        return "final_output"

    if need_revision and revision_count < max_revision_count:
        return "revise_plan"

    return "final_output"
```

Reflection 循环的退出条件：

1. 审查器认为可直接采纳。
2. 审查器认为不需要修正。
3. 已达到最大修正次数。

第 3 条非常重要。没有最大次数，LLM 可能陷入“越改越挑剔”的无限循环。

---

## Workflow：LangGraph 如何编排 Agent

文件：`app/graph/workflow.py`

`build_graph()` 是整个 Agent 的总控：

```python
builder = StateGraph(TravelState)

builder.add_node("parse_request", parse_request_node)
builder.add_node("check_info", check_info_node)
builder.add_node("ask_clarification", ask_clarification_node)
builder.add_node("decide_tools", decide_tools_node)
builder.add_node("collect_context", collect_context_node)
builder.add_node("generate_plan", generate_plan_node)
builder.add_node("reflect_plan", reflect_plan_node)
builder.add_node("revise_plan", revise_plan_node)
builder.add_node("final_output", final_output_node)
```

固定边：

```python
START -> parse_request -> check_info
decide_tools -> collect_context -> generate_plan
revise_plan -> reflect_plan
final_output -> END
```

条件边：

```python
check_info -> ask_clarification / decide_tools
generate_plan -> final_output / reflect_plan
reflect_plan -> revise_plan / final_output
```

完整图：

```text
START
  |
  v
parse_request
  |
  v
check_info
  |
  +-- 信息不完整 -> ask_clarification -> END
  |
  +-- 信息完整 -> decide_tools
                    |
                    v
                collect_context
                    |
                    v
                generate_plan
                    |
                    +-- max_revision_count == 0 -> final_output -> END
                    |
                    +-- max_revision_count > 0 -> reflect_plan
                                                   |
                                                   +-- 需要修正 -> revise_plan
                                                   |                 |
                                                   |                 v
                                                   |             reflect_plan
                                                   |
                                                   +-- 通过/次数用完 -> final_output -> END
```

快速模式和审查模式的区别：

| 模式 | `max_revision_count` | 流程 |
|---|---:|---|
| 快速模式 | `0` | 生成计划后直接输出 |
| 深度审查 | `>0` | 生成计划后进入 Reflection 循环 |

---

## Web 服务与 SSE 流式输出

文件：`app/server.py`

### API 端点

| 端点 | 方法 | 用途 |
|---|---|---|
| `/` | GET | 返回聊天页面 |
| `/api/travel-plan/stream` | POST | 新建流式规划 |
| `/api/travel-plan/{session_id}/continue/stream` | POST | 流式继续对话 |
| `/api/travel-plan` | POST | 非流式规划 |
| `/api/travel-plan/{session_id}/continue` | POST | 非流式继续对话 |
| `/api/travel-plan/{session_id}` | GET | 查询会话状态 |

### SSE 事件类型

后端会推送三类事件：

```json
{"type": "progress", "node": "check_info", "message": "检查信息完整性... 信息完整"}
```

```json
{"type": "token", "token": "成"}
```

```json
{"type": "done", "data": {"status": "completed", "final_plan": "..."}}
```

出错时：

```json
{"type": "error", "message": "错误信息"}
```

### 为什么用子线程运行图

`_stream_graph(state)` 会启动一个 `threading.Thread` 执行 LangGraph：

```python
threading.Thread(target=run, daemon=True).start()
```

原因：

- FastAPI 路由是 async 的，不能长时间阻塞事件循环。
- LangGraph 和 chain 调用是同步逻辑。
- 子线程负责执行图，主协程负责从 `asyncio.Queue` 读事件并输出 SSE。

### token 如何从 LLM 到浏览器

数据路径：

```text
model.stream(messages)
  -> chain 模块中的 q.put_nowait({"type": "token", ...})
  -> server.py 的 _sse_generator(queue)
  -> StreamingResponse(text/event-stream)
  -> 前端 readStream()
  -> appendToken()
  -> 页面“思考中”区域逐字显示
```

注意：当前 `set_stream_queue()` 是模块级全局变量，教学上很直观，但并发场景下后来的请求可能覆盖前一个请求的 queue。生产环境可改成 `contextvars` 或请求级依赖注入。

---

## 多轮对话与 HITL

HITL 是 Human-in-the-loop，即需要人补充或确认时暂停自动流程。

本项目的 HITL 场景是“信息不足追问”：

```text
用户：帮我规划旅行
系统：请补充目的地、天数、预算、偏好
用户：去成都，3天，预算3000，喜欢美食
系统：继续从上一轮 State 合并信息并生成计划
```

关键文件：

- `app/services/session_service.py`
- `app/services/planner_service.py`

`SessionService` 用内存 dict 保存状态：

```python
self._sessions[session_id] = state
```

`PlannerService.continue_plan()` 的核心步骤：

1. 取出上一轮 State。
2. 用新输入替换 `user_input`。
3. 清理上一轮中间产物。
4. 重新执行 LangGraph。

需要清理的字段包括：

```python
[
    "clarification_questions",
    "final_plan",
    "missing_fields",
    "is_info_complete",
    "required_tools",
    "context",
    "draft_plan",
    "reflection",
    "need_revision",
    "stop_reason",
]
```

需要保留的字段：

- `request`：上一轮已解析出的需求。
- `user_inputs`：历史输入。
- `revision_count`、`max_revision_count` 等控制字段。

---

## Reflection 循环详解

Reflection 是本项目最有教学价值的部分。

普通生成链路：

```text
generate_plan -> final_output
```

带 Reflection 的链路：

```text
generate_plan
  -> reflect_plan
      -> 如果通过：final_output
      -> 如果不通过：revise_plan
            -> reflect_plan
                -> ...
```

### 为什么要 Reflection

旅行计划很容易出现这些问题：

- 总预算超支。
- 用户想轻松，但每天安排 5 个活动。
- 用户喜欢美食，但方案里没有美食安排。
- 室外活动过多，但天气有雨。
- mock 数据置信度低，却没有提醒用户确认。

`reflection_chain` 会强制输出结构化审查结果，而不是一段自由评论：

```json
{
  "need_revision": true,
  "score": 6,
  "issues": ["第2天行程过密"],
  "suggestions": ["将购物安排移到第3天上午"],
  "blocking_issues": [],
  "accepted_as_final": false
}
```

`route_after_reflection()` 读取这些字段决定下一步。

### 修正为什么输出完整 TravelPlan

`revise_chain` 的输出仍然是完整 `TravelPlan`，不是 diff。

这样做的好处：

- 下游 `final_output_node` 不需要知道这是初版还是修正版。
- Pydantic 可以完整校验。
- LLM 生成 diff 或 JSON Patch 更容易出错。
- 前端和测试都可以消费同一种结构。

---

## 测试体系

运行全部测试：

```bash
pytest tests/ -v
```

只运行不依赖 API Key 的测试：

```bash
pytest tests/test_parse.py tests/test_tools.py tests/test_reflection.py -v
```

需要真实模型调用的端到端测试：

```bash
pytest tests/test_workflow.py tests/test_followup.py tests/test_tool_failure.py -v
```

测试文件职责：

| 文件 | 覆盖内容 |
|---|---|
| `tests/test_parse.py` | Schema 校验、字段约束 |
| `tests/test_tools.py` | 工具返回结构、`safe_tool_call` 容错 |
| `tests/test_reflection.py` | Reflection schema 和路由逻辑 |
| `tests/test_workflow.py` | 完整工作流、缺失信息追问 |
| `tests/test_followup.py` | 用户补充后继续规划 |
| `tests/test_tool_failure.py` | 工具失败时流程不中断 |

学习建议：先跑不依赖 API 的测试，理解确定性逻辑；再配置 API Key 跑端到端测试。

---

## 扩展练习

### 练习 1：新增酒店工具

目标：新增 `search_hotels`，为计划提供住宿预算参考。

步骤：

1. 新建 `app/tools/hotel_tool.py`。
2. 返回统一 ToolResult dict。
3. 在 `decide_tools_node` 中加入 `"hotels"`。
4. 在 `collect_context_node` 中调用 `search_hotels`。
5. 修改 `plan_prompt`，要求考虑住宿预算。
6. 增加 `tests/test_tools.py` 对酒店工具的测试。

### 练习 2：接入真实天气 API

目标：把 `get_weather` 从 mock 替换为真实 API。

保持返回结构不变：

```python
{
    "data": {...},
    "source": "real_weather_api",
    "updated_at": "...",
    "confidence": "high",
    "error": None,
}
```

只要结构不变，上游流程不用改。

### 练习 3：增强追问逻辑

当前 `ask_clarification_node` 是纯 Python 映射。你可以改造成 LLM 节点，让追问更自然。

注意事项：

- 不要一次问太多无关问题。
- 仍然要基于 `missing_fields`。
- 输出最好仍是结构化 list，方便前端渲染。

### 练习 4：把 session 存到 Redis

当前会话存在内存中：

```python
self._sessions: Dict[str, dict] = {}
```

限制：

- 服务重启后丢失。
- 多进程不能共享。
- 没有 TTL。

可以改成 Redis：

- `create_session()` 写入 Redis。
- `get_state()` 从 Redis 读取 JSON。
- `update_state()` 序列化 State 后写入。
- 设置过期时间，例如 24 小时。

### 练习 5：加入 Eval 数据集

构造 20-30 条旅行需求，自动评估：

- 是否触发正确追问。
- 是否生成指定天数。
- 是否预算不超支。
- 是否包含用户偏好。
- Reflection 分数是否达到阈值。

---

## 深度源码拆解

前面的章节已经解释了项目分层和核心机制。这里进一步把关键源码拆开讲，目标是让你可以真正开始改这个项目，而不是只停留在“看懂了”的层面。

### 1. 项目文件地图

先从目录结构建立全局索引：

```text
travel-planning-agent/
  README.md
  pyproject.toml
  .env.example
  app/
    __init__.py
    main.py
    server.py
    config/
      settings.py
    schemas/
      travel_request.py
      travel_plan.py
      reflection.py
      tool_result.py
    prompts/
      parse_prompt.py
      plan_prompt.py
      reflection_prompt.py
      revise_prompt.py
    chains/
      parse_chain.py
      plan_chain.py
      reflection_chain.py
      revise_chain.py
    tools/
      base.py
      weather_tool.py
      attraction_tool.py
      food_tool.py
      budget_tool.py
      transport_tool.py
      search_tool.py
    graph/
      state.py
      nodes.py
      routers.py
      workflow.py
    services/
      planner_service.py
      session_service.py
    templates/
      index.html
    static/
      style.css
  docs/
    architecture.md
    workflow.md
    beginners-guide.md
    technical-tutorial.md
  tests/
    test_parse.py
    test_tools.py
    test_reflection.py
    test_workflow.py
    test_followup.py
    test_tool_failure.py
```

几个“入口文件”要先记住：

| 你想做什么 | 先看哪里 |
|---|---|
| 看 Web 服务如何启动 | `app/server.py` |
| 看命令行如何调用 | `app/main.py` |
| 看业务层如何调用图 | `app/services/planner_service.py` |
| 看完整 Agent 流程 | `app/graph/workflow.py` |
| 看每一步具体干什么 | `app/graph/nodes.py` |
| 看 LLM 调用怎么封装 | `app/chains/` |
| 看输出结构怎么定义 | `app/schemas/` |

### 2. 两条入口路径：CLI 和 Web

这个项目有两个入口：CLI 和 Web。它们最终都会调用同一个 `PlannerService`，所以业务逻辑没有重复。

CLI 路径：

```text
python -m app.main
  -> app/main.py:main()
  -> run_once()
  -> planner_service.plan()
  -> graph.invoke(state)
  -> 返回 final_plan 或 clarification message
```

Web 非流式路径：

```text
POST /api/travel-plan
  -> app/server.py:create_plan()
  -> asyncio.to_thread(_get_planner().plan, ...)
  -> planner_service.plan()
  -> graph.invoke(state)
  -> JSON response
```

Web 流式路径：

```text
POST /api/travel-plan/stream
  -> app/server.py:create_plan_stream()
  -> _stream_graph(state)
  -> 子线程运行 planner.graph.stream(state, stream_mode="values")
  -> asyncio.Queue 推送 progress/token/done
  -> StreamingResponse 输出 SSE
```

教学重点在这里：三条入口最终复用同一张 LangGraph 图，只是外层交互方式不同。

### 3. 配置层：settings 如何影响全局

文件：`app/config/settings.py`

配置从 `.env` 读取：

```python
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0"))
MAX_REVISION_COUNT = int(os.getenv("MAX_REVISION_COUNT", "2"))
```

这些配置主要被 `app/chains/` 使用：

```python
return init_chat_model(
    settings.MODEL_NAME,
    model_provider="openai",
    openai_api_key=settings.OPENAI_API_KEY,
    openai_api_base=settings.OPENAI_BASE_URL,
    temperature=settings.TEMPERATURE,
)
```

如果你要切换模型，一般只改 `.env`，不用改代码。

示例：

```env
# DeepSeek
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.deepseek.com/v1
MODEL_NAME=deepseek-chat
```

```env
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-4o-mini
```

注意：结构化输出任务建议先用 `TEMPERATURE=0`，因为解析、审查、修正更需要稳定性，而不是创造性。

### 4. Prompt 到 Pydantic 的完整链路

以 `parse_chain` 为例，它做了这件事：

```text
用户自然语言
  -> parse_prompt 注入 user_input
  -> 注入 parser.get_format_instructions()
  -> LLM 输出 JSON 文本
  -> PydanticOutputParser 解析
  -> TravelRequest 对象
```

核心代码模式：

```python
parser = PydanticOutputParser(pydantic_object=TravelRequest)
prompt_with_format = parse_prompt.partial(
    format_instructions=parser.get_format_instructions()
)
chain = prompt_with_format | _get_model() | parser
```

`format_instructions` 很关键。它会把 Pydantic schema 转成模型能理解的格式说明，告诉模型必须返回哪些字段、字段类型是什么。

如果没有这一步，模型可能返回：

```text
用户想去成都玩三天，预算三千，喜欢美食。我建议第一天...
```

这对人可读，但对程序不可控。

有了 `PydanticOutputParser`，模型被要求返回类似：

```json
{
  "destination": "成都",
  "start_date": "6月底",
  "days": 3,
  "budget": 3000,
  "preferences": ["美食", "轻松"],
  "companions": null,
  "departure_city": null,
  "pace": "轻松"
}
```

代码随后可以确定性地检查：

```python
if request.get("budget") in [None, "", []]:
    missing.append("budget")
```

这就是结构化输出的核心价值：把“模型说的话”变成“代码能判断的数据”。

### 5. 四条 Chain 的输入输出对照

这张表可以帮助你调试，也可以帮助你新增第五条 Chain：

| Chain | 调用位置 | 输入字段 | 输出对象 |
|---|---|---|---|
| `parse_chain` | `parse_request_node` | `{"user_input": str}` | `TravelRequest` |
| `plan_chain` | `generate_plan_node` | `{"user_input": str, "request": dict, "context": dict}` | `TravelPlan` |
| `reflection_chain` | `reflect_plan_node` | `{"user_input": str, "request": dict, "context": dict, "draft_plan": dict, "revision_count": int, "max_revision_count": int}` | `ReflectionResult` |
| `revise_chain` | `revise_plan_node` | `{"user_input": str, "request": dict, "context": dict, "draft_plan": dict, "reflection": dict}` | `TravelPlan` |

如果某条 Chain 报错，优先检查三件事：

1. Prompt 里需要的变量名，是否和传入 dict 的 key 一致。
2. Pydantic schema 是否要求了模型很难稳定输出的字段。
3. 模型返回的 JSON 是否包含 Markdown 代码块、注释、额外解释等干扰内容。

### 6. State 在每个节点后的样子

用一个完整输入举例：

```text
我想6月底去成都玩3天，预算3000元，喜欢美食和轻松路线
```

初始 State：

```json
{
  "user_input": "我想6月底去成都玩3天，预算3000元，喜欢美食和轻松路线",
  "max_revision_count": 2
}
```

`parse_request_node` 后：

```json
{
  "user_input": "...",
  "user_inputs": ["我想6月底去成都玩3天，预算3000元，喜欢美食和轻松路线"],
  "request": {
    "destination": "成都",
    "start_date": "6月底",
    "days": 3,
    "budget": 3000,
    "preferences": ["美食", "轻松"]
  },
  "revision_count": 0,
  "max_revision_count": 2,
  "tool_errors": [],
  "system_errors": [],
  "trace": [{"node": "parse_request", "status": "ok"}]
}
```

`check_info_node` 后：

```json
{
  "missing_fields": [],
  "is_info_complete": true,
  "trace": [
    {"node": "parse_request", "status": "ok"},
    {"node": "check_info", "missing": []}
  ]
}
```

`decide_tools_node` 后：

```json
{
  "required_tools": [
    "weather",
    "attractions",
    "budget",
    "transport",
    "foods",
    "web_search"
  ]
}
```

这里因为偏好包含“美食”，所以加入 `foods`；因为有 `start_date`，所以加入 `web_search`。

`collect_context_node` 后：

```json
{
  "context": {
    "weather": {"data": "...", "source": "mock_weather", "confidence": "mock"},
    "attractions": {"data": "...", "source": "mock_attractions", "confidence": "mock"},
    "budget_estimate": {"data": "...", "source": "mock_budget", "confidence": "mock"},
    "transport": {"data": "...", "source": "mock_transport", "confidence": "mock"},
    "foods": {"data": "...", "source": "mock_foods", "confidence": "mock"}
  },
  "tool_errors": []
}
```

`generate_plan_node` 后：

```json
{
  "draft_plan": {
    "destination": "成都",
    "total_days": 3,
    "total_budget": 3000,
    "days": [
      {"day": 1, "theme": "...", "activities": ["..."]},
      {"day": 2, "theme": "...", "activities": ["..."]},
      {"day": 3, "theme": "...", "activities": ["..."]}
    ],
    "total_estimated_cost": 2800,
    "budget_status": "within_budget"
  },
  "trace": [
    "...",
    {"node": "generate_plan", "status": "ok"}
  ]
}
```

`reflect_plan_node` 后：

```json
{
  "reflection": {
    "need_revision": false,
    "score": 9,
    "issues": [],
    "suggestions": [],
    "blocking_issues": [],
    "accepted_as_final": true
  },
  "need_revision": false,
  "stop_reason": "accepted_by_reflection",
  "trace": [
    "...",
    {"node": "reflect_plan", "need_revision": false, "score": 9}
  ]
}
```

`final_output_node` 后：

```json
{
  "final_plan": "# 成都3日旅行方案\n\n## 一、行程概览\n...",
  "stop_reason": "accepted_by_reflection"
}
```

理解这些中间状态后，调试会轻松很多。你只要知道“当前缺哪个字段”，就能定位是哪个节点没有正确写入。

### 7. 缺失信息场景的 State

输入：

```text
帮我规划旅行
```

`parse_request_node` 可能得到：

```json
{
  "request": {
    "destination": null,
    "start_date": null,
    "days": null,
    "budget": null,
    "preferences": []
  }
}
```

`check_info_node` 会写入：

```json
{
  "missing_fields": ["destination", "days", "budget", "preferences"],
  "is_info_complete": false
}
```

`route_after_check` 返回：

```text
ask_clarification
```

`ask_clarification_node` 写入：

```json
{
  "clarification_questions": [
    "你想去哪个城市或地区旅行？",
    "你计划玩几天？",
    "你的总预算大概是多少？",
    "你更偏好美食、自然风光、历史文化、购物，还是轻松休闲路线？"
  ],
  "stop_reason": "need_user_clarification",
  "final_plan": "为了更准确地规划行程，请先补充：\n- ..."
}
```

然后工作流结束，前端保存 `session_id`。用户补充后，`continue_plan()` 会在旧 State 基础上继续。

### 8. 为什么路由器不用 LLM

项目里的路由器是纯 Python：

```python
if state.get("is_info_complete"):
    return "decide_tools"
return "ask_clarification"
```

这是一个重要工程判断。不是所有“决策”都应该交给模型。

适合用代码的决策：

- 字段是否为空。
- 修正次数是否超过上限。
- 布尔字段是否为 true。
- 列表里是否包含某个偏好。

适合用 LLM 的决策：

- 用户输入到底表达了什么。
- 行程安排是否合理。
- 审查意见如何表达。
- 如何根据反馈重写计划。

如果把所有路由都交给 LLM，流程会变得不可预测，测试也更难写。Workflow Agent 的核心思想就是：把确定性交给代码，把不确定性交给模型。

### 9. 如何新增一个工具

以“酒店搜索工具”为例。

第一步，新建工具文件：

```python
# app/tools/hotel_tool.py
from datetime import date
from langchain_core.tools import tool


@tool
def search_hotels(city: str, days: int, budget: float) -> dict:
    """查询目的地酒店建议和住宿预算。"""
    return {
        "data": {
            "city": city,
            "nights": max(days - 1, 1),
            "options": [
                {
                    "name": "市中心经济型酒店",
                    "area": "市中心",
                    "price_per_night": 350,
                    "reason": "交通方便，适合首次到访游客"
                },
                {
                    "name": "景区附近舒适酒店",
                    "area": "热门景区周边",
                    "price_per_night": 520,
                    "reason": "节省通勤时间，但价格略高"
                }
            ]
        },
        "source": "mock_hotels",
        "updated_at": str(date.today()),
        "confidence": "mock",
        "error": None,
    }
```

第二步，在 `nodes.py` 导入：

```python
from app.tools.hotel_tool import search_hotels
```

第三步，在 `decide_tools_node` 加入：

```python
required_tools = ["weather", "attractions", "budget", "transport", "hotels"]
```

第四步，在 `collect_context_node` 调用：

```python
if "hotels" in required_tools:
    result, err = safe_tool_call(
        search_hotels,
        {"city": city, "days": days, "budget": budget},
        "fallback_hotels",
    )
    context["hotels"] = result
    if err:
        errors.append(err)
```

第五步，修改 `plan_prompt.py`，告诉 LLM：

```text
如果 context 中包含 hotels，请把住宿预算纳入 total_estimated_cost，
并在 data_limitations 中说明酒店价格为估算值。
```

第六步，增加测试：

```python
def test_search_hotels():
    result = search_hotels.invoke({"city": "成都", "days": 3, "budget": 3000})
    assert result["source"] == "mock_hotels"
    assert result["confidence"] == "mock"
    assert "options" in result["data"]
```

这个练习的重点不是酒店本身，而是学会新增工具的完整路径：Tool 文件、节点导入、工具选择、工具调用、Prompt 消费、测试覆盖。

### 10. 如何新增一个工作流节点

假设你想在生成计划前加一个“预算预检查”节点：如果预算太低，就先提醒 LLM 走极简路线。

第一步，在 `TravelState` 加字段：

```python
budget_level: str
budget_warning: str
```

第二步，在 `nodes.py` 新增节点：

```python
def precheck_budget_node(state: TravelState) -> dict:
    request = state.get("request", {})
    budget = request.get("budget") or 0
    days = request.get("days") or 1
    per_day = budget / days

    if per_day < 300:
        return {
            "budget_level": "low",
            "budget_warning": "用户日均预算较低，计划应优先选择免费景点和公共交通。"
        }

    if per_day < 800:
        return {
            "budget_level": "medium",
            "budget_warning": "用户预算适中，计划应平衡体验和成本。"
        }

    return {
        "budget_level": "high",
        "budget_warning": "用户预算较充足，可以安排更舒适的交通和餐饮。"
    }
```

第三步，在 `workflow.py` 注册节点：

```python
builder.add_node("precheck_budget", precheck_budget_node)
```

第四步，调整边：

```python
builder.add_edge("collect_context", "precheck_budget")
builder.add_edge("precheck_budget", "generate_plan")
```

原来的：

```python
builder.add_edge("collect_context", "generate_plan")
```

需要删除或替换。

第五步，把 `budget_warning` 传给 `plan_chain`：

```python
result: TravelPlan = plan_chain.invoke({
    "user_input": state["user_input"],
    "request": state["request"],
    "context": state.get("context", {}),
    "budget_warning": state.get("budget_warning", ""),
})
```

第六步，修改 `plan_prompt.py`，增加 `{budget_warning}` 占位符。

新增节点时最容易漏的地方：

- State 是否补了字段。
- workflow 是否注册了节点。
- edge 是否连接正确。
- prompt 是否需要新增变量。
- chain invoke 的输入 key 是否和 prompt 变量一致。
- 测试是否覆盖新路径。

### 11. 如何新增一条 Chain

如果追问逻辑想从纯 Python 改成 LLM，可以新增 `clarification_chain`。

需要新增：

```text
app/prompts/clarification_prompt.py
app/chains/clarification_chain.py
app/schemas/clarification.py
```

Schema 示例：

```python
from pydantic import BaseModel, Field
from typing import List


class ClarificationResult(BaseModel):
    questions: List[str] = Field(description="需要向用户追问的问题")
    reason: str = Field(description="为什么需要这些补充信息")
```

Prompt 示例：

```python
clarification_prompt = ChatPromptTemplate.from_messages([
    ("system", """你是旅行规划助手的追问模块。
请根据缺失字段生成简短、明确、不重复的问题。

{format_instructions}"""),
    ("human", "当前解析结果：{request}\n缺失字段：{missing_fields}")
])
```

Chain 示例：

```python
parser = PydanticOutputParser(pydantic_object=ClarificationResult)
prompt_with_format = clarification_prompt.partial(
    format_instructions=parser.get_format_instructions()
)
clarification_chain = prompt_with_format | _get_model() | parser
```

然后把 `ask_clarification_node` 从硬编码映射改为：

```python
result = clarification_chain.invoke({
    "request": state.get("request", {}),
    "missing_fields": state.get("missing_fields", []),
})

return {
    "clarification_questions": result.questions,
    "stop_reason": "need_user_clarification",
    "final_plan": "为了更准确地规划行程，请先补充：\n"
        + "\n".join(f"- {q}" for q in result.questions),
}
```

注意：这会多一次 LLM 调用。教学上可以展示 LLM 追问能力，但工程上要权衡成本和延迟。

### 12. SSE 前端如何消费事件

前端核心逻辑在 `app/templates/index.html`：

```javascript
const resp = await fetch('/api/travel-plan/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_input: userInput, max_revision_count: maxRev }),
});

await readStream(resp, true);
```

`readStream()` 做三件事：

1. 从 `resp.body.getReader()` 持续读取字节。
2. 按 SSE 的 `data: ...\n\n` 格式拆事件。
3. 根据 `event.type` 更新页面。

事件处理逻辑：

```javascript
if (event.type === 'token') {
    appendToken(event.token);
} else if (event.type === 'progress') {
    addProgressStep(event.message);
} else if (event.type === 'done') {
    handleResponse(event.data, isNew);
} else if (event.type === 'error') {
    addAssistantMessage(...);
}
```

这也是为什么后端事件要保持统一 JSON 格式。前端不需要知道 LangGraph 内部细节，只需要处理 `token`、`progress`、`done`、`error`。

### 13. `trace` 字段为什么重要

`trace` 是轻量执行轨迹。每个关键节点完成后追加一条：

```python
"trace": state.get("trace", []) + [{"node": "generate_plan", "status": "ok"}]
```

Web 流式服务会比较 `trace` 长度：

```python
if len(trace) > seen_trace_len:
    new_nodes = trace[seen_trace_len:]
    seen_trace_len = len(trace)
```

这意味着：

- 节点只要写入 trace，前端就能显示进度。
- 节点不写 trace，流程也能跑，但前端看不到这个步骤。
- 调试时可以直接看最终 State 的 trace 知道流程走过哪些节点。

如果你新增节点，建议也追加 trace：

```python
return {
    "some_field": value,
    "trace": state.get("trace", []) + [{"node": "your_node", "status": "ok"}],
}
```

### 14. Mock 工具如何升级为真实工具

替换工具时，尽量保持函数名、入参和返回结构不变。

例如天气工具从 mock 改真实 API：

```python
@tool
def get_weather(city: str, date_range: str = "") -> dict:
    """查询城市的天气信息与出行风险。"""
    response = real_weather_client.query(city=city, date_range=date_range)

    return {
        "data": {
            "city": city,
            "forecast": [
                {
                    "date": item.date,
                    "weather": item.condition,
                    "temp_high": item.high,
                    "temp_low": item.low,
                }
                for item in response.forecast
            ],
        },
        "source": "real_weather_api",
        "updated_at": response.updated_at,
        "confidence": "high",
        "error": None,
    }
```

不要让真实 API 的原始响应直接穿透到上游。原因是不同 API 的字段命名、嵌套层级和错误格式都不一样。工具层应该把它们转换为项目自己的稳定协议。

这就是 Adapter 的价值。

### 15. 生产化改造路线

这个项目适合教学，但如果要向生产靠近，可以按这个顺序改：

1. 把全局 `_stream_queue` 改成请求级上下文，避免并发覆盖。
2. 给工具调用增加 timeout、retry 和限流。
3. 把 `SessionService` 从内存 dict 改成 Redis。
4. 给每次请求生成 request_id，贯穿日志、trace、工具错误。
5. 给 LLM 调用增加成本统计和耗时统计。
6. 给 Prompt 增加版本号，便于 A/B 测试。
7. 建立 Eval 数据集，自动评估预算、偏好、天数、风险提示。
8. 增加鉴权，避免公开 API 被滥用。
9. 把 mock 工具逐步替换成真实 API。
10. 为端到端流程增加更多失败场景测试。

这条路线的原则是：先保证状态、并发和错误处理可靠，再追求工具真实性和体验优化。

---

## 调试与排错

这一节专门解决开发时最常见的问题。

### 1. LLM 返回无法解析的 JSON

常见报错：

```text
OutputParserException
```

可能原因：

- 模型输出了 Markdown 代码块外的额外解释。
- Prompt 没有明确要求只输出 JSON。
- Schema 太复杂，模型漏字段。
- temperature 太高，输出不稳定。

排查步骤：

1. 打印或记录模型原始输出。
2. 检查 prompt 中是否有 `{format_instructions}`。
3. 确认 `prompt.partial(format_instructions=...)` 已执行。
4. 把 `TEMPERATURE` 调成 `0`。
5. 简化 schema 或给字段增加更明确的描述。

改进 Prompt 的常用句式：

```text
只输出符合格式要求的 JSON，不要输出 Markdown，不要输出解释文字。
如果字段未知，请使用 null 或空列表，不要编造。
```

### 2. 信息完整却仍然触发追问

排查 `check_info_node`。

必要字段是：

```python
required_fields = ["destination", "days", "budget", "preferences"]
```

只要其中任何一个值是下面之一，就算缺失：

```python
[None, "", []]
```

例如模型解析出：

```json
{
  "destination": "成都",
  "days": 3,
  "budget": 3000,
  "preferences": []
}
```

虽然用户可能说“随便”，但 `preferences` 为空列表，所以会追问。

你可以选择两种改法：

1. 保持严格，要求用户明确偏好。
2. 放宽逻辑，把空偏好默认成 `["轻松"]` 或 `["经典路线"]`。

如果放宽，可以在 `check_info_node` 前或内部处理：

```python
if not request.get("preferences"):
    request["preferences"] = ["经典路线"]
```

但这会改变产品行为，教程项目默认选择更明确的追问。

### 3. Web 页面没有 token 流

先判断最终方案有没有返回。

如果最终方案正常，只是没有逐字显示，通常是 stream queue 没有注入或前端没有处理 token。

后端检查：

```python
import app.chains.plan_chain as pc
pc.set_stream_queue(queue)
```

需要确认四条 chain 都注入：

```python
prsc.set_stream_queue(queue)
pc.set_stream_queue(queue)
rc.set_stream_queue(queue)
rvc.set_stream_queue(queue)
```

前端检查：

```javascript
if (event.type === 'token') {
    appendToken(event.token);
}
```

还要注意：不是所有节点都会产生大量 token。`check_info_node`、`decide_tools_node`、`collect_context_node` 是纯 Python 节点，不会有 LLM token。

### 4. 工作流没有进入 Reflection

检查 `max_revision_count`。

`workflow.py` 中：

```python
def route_after_generate(state):
    if state.get("max_revision_count", 0) > 0:
        return "reflect_plan"
    return "final_output"
```

如果前端取消“深度审查”，会发送：

```json
{"max_revision_count": 0}
```

这时生成计划后直接输出，不会进入 `reflect_plan`。

### 5. 工作流一直修正

正常情况下不会无限修正，因为有：

```python
revision_count < max_revision_count
```

如果你看到多次修正，先检查：

- `revision_count` 是否在 `revise_plan_node` 中加 1。
- `max_revision_count` 是否被设置得太大。
- `reflection_chain` 是否总是返回 `need_revision=true`。
- `accepted_as_final` 是否很少为 true。

可以在 Reflection Prompt 中加规则：

```text
如果当前方案没有阻断性问题，且 score >= 8，请设置 accepted_as_final=true。
如果已接近最大修正次数，只保留真正影响出行的严重问题。
```

### 6. 工具失败后计划质量下降

这是预期现象，但不应该崩溃。

检查最终输出中是否有：

```text
部分工具调用失败或返回低置信度数据，建议出行前再次确认天气、景点开放时间、门票和交通情况。
```

如果没有，说明 `tool_errors` 没有正确传到 `final_output_node`。

工具失败路径应该是：

```text
safe_tool_call 捕获异常
  -> fallback_tool_result(...)
  -> errors.append(err)
  -> collect_context_node 返回 {"tool_errors": errors}
  -> final_output_node 读取 tool_errors
  -> Markdown 中显示数据限制说明
```

### 7. 新增 Prompt 变量后报 KeyError

例如你在 prompt 中写了：

```text
预算提醒：{budget_warning}
```

但调用 chain 时没有传：

```python
plan_chain.invoke({
    "user_input": state["user_input"],
    "request": state["request"],
    "context": state.get("context", {}),
})
```

就会报缺少变量。

修复方式：

```python
plan_chain.invoke({
    "user_input": state["user_input"],
    "request": state["request"],
    "context": state.get("context", {}),
    "budget_warning": state.get("budget_warning", ""),
})
```

记住：Prompt 里的每个 `{variable}`，都必须在 invoke 输入 dict 里有同名 key，除非它已经通过 `partial()` 预填。

### 8. 测试应该先从哪里写

新增功能时建议按风险分层写测试：

| 改动 | 最先写的测试 |
|---|---|
| 新增 Schema 字段 | schema 单元测试 |
| 新增工具 | 工具输出结构测试 |
| 新增路由条件 | router 单元测试 |
| 新增节点 | node 输入输出测试 |
| 改 workflow 边 | workflow 集成测试 |
| 改 prompt | 端到端测试或 eval case |

先测确定性逻辑，再测 LLM 逻辑。因为 LLM 测试慢、贵、波动大，不适合覆盖所有细节。

### 9. 建议的调试输出

开发阶段可以临时打印这些字段：

```python
print("request =", state.get("request"))
print("missing_fields =", state.get("missing_fields"))
print("required_tools =", state.get("required_tools"))
print("context keys =", list(state.get("context", {}).keys()))
print("reflection =", state.get("reflection"))
print("trace =", state.get("trace"))
```

不要长期保留大量 print。正式做法是接入结构化日志：

```json
{
  "request_id": "...",
  "node": "reflect_plan",
  "score": 8,
  "need_revision": false,
  "elapsed_ms": 1234
}
```

### 10. 最小复现技巧

如果端到端流程出错，不要一上来调整个 Web。按这个顺序缩小问题：

1. 直接调用 schema，确认字段校验没问题。
2. 单独调用 tool，确认返回结构没问题。
3. 单独调用 chain，确认 LLM 输出能解析。
4. 单独调用 node，确认 State 输入输出没问题。
5. 调用 `graph.invoke()`，确认工作流没问题。
6. 最后再调 Web SSE，确认只是传输和渲染问题。

从内到外调试，比从浏览器直接猜后端问题更快。

---

## 常见问题

### 1. 为什么不用 ReAct 让 LLM 自己决定下一步？

旅行规划的主流程比较固定：解析、检查、查资料、生成、审查、输出。固定流程用 Workflow Agent 更可控、更容易测试、更适合教学。LLM 负责理解和生成，代码负责流程控制。

### 2. 为什么工具都是 mock？

这是教学 Demo。mock 工具让学习者不需要申请多个外部 API，也能理解 Tool Calling、Tool Adapter、fallback 和上下文注入。真实项目中可以逐个替换为真实 provider。

### 3. 为什么 final_output_node 不调用 LLM？

因为它只是把结构化数据渲染为 Markdown。确定性格式转换用 Python 更稳定、更便宜，也不会引入额外幻觉。

### 4. 为什么用 PydanticOutputParser，而不是模型原生 structured output？

因为项目目标是兼容 OpenAI 协议下的多种模型服务。有些服务不支持 JSON Schema 原生约束，但都可以通过 prompt 要求模型输出 JSON，再由 `PydanticOutputParser` 校验。

### 5. 为什么会有 `max_revision_count`？

Reflection 是循环，如果没有上限，模型可能一直发现新问题、一直修正，造成成本和延迟失控。默认 2 次是教学场景中的平衡。

### 6. Web 页面为什么能逐字显示 LLM 输出？

因为 chain 在流式模式下使用 `model.stream(messages)` 获取 token，并把每个 token 放入 `asyncio.Queue`。FastAPI 的 `StreamingResponse` 再把队列事件以 SSE 格式推给浏览器。

### 7. 这个项目离生产环境还差什么？

主要差这些：

- 真实工具 API。
- 请求级 stream queue，避免全局变量并发问题。
- Redis/数据库持久化会话。
- 工具调用超时和重试。
- 更严格的日志、监控和成本统计。
- 更完整的 Eval 数据集。
- 鉴权和限流。

---

## 学习总结

这个 Demo 的核心价值在于：它把“让 LLM 自由发挥”改造成了“让代码控制确定性，让模型处理不确定性”。

确定性的部分：

- 信息是否缺失。
- 调哪些工具。
- 走哪个路由。
- 循环最多几次。
- 如何渲染 Markdown。

交给 LLM 的部分：

- 从自然语言中理解旅行需求。
- 基于上下文生成旅行方案。
- 审查计划质量。
- 根据反馈修正计划。

这就是一个工程化 Agent 的基本形态：不是一个无限自由的聊天机器人，而是一个有状态、有工具、有流程、有自检、有退出条件的可控系统。
