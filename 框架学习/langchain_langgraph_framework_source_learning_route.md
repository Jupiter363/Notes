# 从 Agent 范式到 LangChain / LangGraph 框架源码：学习路线

> 适用对象：已经理解 ReAct、Plan-and-Execute、Reflection、Workflow、Router、Agentic RAG 等 Agent 范式，并且已经完成一个基于 LangChain / LangGraph 的旅行规划助手，希望进一步从“会用框架”升级为“理解框架源码与设计思想”的学习者。  
> 核心目标：以已完成的旅行规划助手为样本工程，建立“Agent 范式 → 框架 API → 执行机制 → 源码结构 → 工程判断”的完整学习链路。  
> 学习原则：不再以堆功能为主，而是通过代码讲解、运行追踪、源码反查和框架设计复盘，深入掌握 LangChain 与 LangGraph 的核心抽象。

---

## 1. 学习定位

你当前已经完成了一个基于 LangChain 和 LangGraph 的旅行规划助手，因此接下来的目标不是继续改造项目，而是把这个项目当成一个“框架学习样本工程”。

这份路线的重点不是：

```text
再做一个旅行规划助手
再加几个工具
再接几个 API
再写几个 Prompt
```

而是：

```text
看到一段 Agent 代码，知道它对应哪个范式；
看到一个 LangChain API，知道它背后是哪个核心抽象；
看到一个 LangGraph 节点，知道它如何读写 state；
看到一次 Agent 执行，知道 invoke / stream / tool_call / checkpoint / interrupt 发生在哪里；
看到源码，知道应该从哪个类、哪个函数、哪个包开始读。
```

最终目标是达到：

```text
范式层：知道为什么这样设计；
框架层：知道用哪个 API 实现；
执行层：知道运行时发生什么；
源码层：知道底层为什么能这样运行；
工程层：知道真实业务里如何取舍。
```

---

## 2. 学习总主线

### 2.1 从范式语言到框架语言

| 范式语言 | 框架语言 | 源码语言 | 你要掌握的问题 |
|---|---|---|---|
| 普通 LLM Chain | `prompt \| model \| parser` | `RunnableSequence`、`invoke`、`stream` | 为什么链式组合可以运行 |
| Tool-use | `@tool`、`StructuredTool`、`ToolNode` | `BaseTool`、`args_schema`、`ToolMessage` | 函数如何变成模型可调用工具 |
| ReAct | `create_agent`、model-tool loop | `AIMessage.tool_calls`、tools node、agent graph | 模型与工具循环如何执行 |
| Workflow | `StateGraph`、`add_node`、`add_edge` | `CompiledStateGraph`、state update | 固定流程如何被图执行 |
| Router | `add_conditional_edges` | path function、branch mapping | 意图路由如何决定下一节点 |
| Plan-and-Execute | planner node、executor subgraph | structured plan、subgraph、checkpoint | 计划如何转成可执行流程 |
| Reflection | evaluator node、revise node、loop edge | conditional loop、max iteration | 反思如何成为有限循环 |
| Agentic RAG | retriever node、query rewrite node | Retriever、Document、Runnable | 检索如何成为 Agent 节点 |
| Memory | checkpointer、store、thread_id | checkpoint、StateSnapshot | 为什么能保存和恢复状态 |
| Human-in-the-loop | `interrupt()`、`Command(resume=...)` | interrupt、resume、checkpoint | 人工确认如何暂停/恢复图 |
| Observability | `stream`、events、LangSmith trace | callback、event stream、metadata | 如何观察每一步执行 |

---

## 3. 最新框架趋势校准

### 3.1 LangChain 的定位变化

LangChain v1 之后更强调“Agent 工程基础组件”和“可组合运行单元”，核心包括：

```text
ChatModel
Prompt
Message
Tool
OutputParser
Runnable
Retriever
Middleware
create_agent
```

需要重点理解：

```text
LangChain 不只是 Chain；
LangChain Core 的关键是 Runnable 抽象；
LangChain Agent 的关键是基于 LangGraph 的 agent runtime；
create_agent 成为构建 Agent 的标准入口之一；
middleware 成为模型调用、工具调用、上下文处理、安全控制的重要扩展点。
```

### 3.2 LangGraph 的定位变化

LangGraph 更像是 Agent 的底层编排运行时，核心包括：

```text
StateGraph
CompiledStateGraph
Node
Edge
Conditional Edge
Reducer
Checkpoint
Thread
Interrupt
Command
Subgraph
Durable Execution
Pregel Runtime
```

需要重点理解：

```text
LangGraph 不是普通流程图；
它是有状态、可恢复、可中断、可回放的 Agent / Workflow 执行框架；
生产级 Agent 的很多能力，如 memory、HITL、time travel、durable execution，都建立在 checkpoint 和 runtime 机制之上。
```

### 3.3 当前学习重点

不需要平均学习所有 API，而应该优先学习以下核心：

```text
1. Runnable
2. ChatPromptTemplate / Messages
3. BaseChatModel / AIMessage / ToolMessage
4. @tool / StructuredTool
5. create_agent
6. StateGraph
7. add_node / add_edge / add_conditional_edges
8. Reducer / Annotated state
9. Checkpointer / thread_id
10. interrupt / Command
11. stream / events / tracing
12. subgraph / multi-agent graph
```

---

## 4. 学习方法：四层拆解法

每学一个框架点，都按四层拆解。

### 4.1 范式层

先问：

```text
这个功能解决哪个 Agent 范式问题？
```

例如：

```text
add_conditional_edges 解决 Router / Workflow 分支问题；
checkpoint 解决长期状态、恢复执行和 HITL 问题；
@tool 解决模型连接外部能力的问题；
create_agent 解决 ReAct 式模型-工具循环问题。
```

### 4.2 代码层

再问：

```text
这个范式在 LangChain / LangGraph 中用哪个 API 表达？
```

例如：

```text
Tool-use → @tool / StructuredTool
Workflow → StateGraph
Router → add_conditional_edges
HITL → interrupt + Command
Memory → checkpointer + thread_id
```

### 4.3 执行层

继续问：

```text
运行时发生了什么？
```

例如：

```text
graph.invoke(input)
→ 初始化 state
→ 执行 START 指向的 node
→ node 返回 partial update
→ reducer 合并 state
→ edge 决定下一个节点
→ checkpoint 保存状态
→ 直到 END
```

### 4.4 源码层

最后问：

```text
源码为什么这样设计？
```

例如：

```text
为什么 Runnable 要统一 invoke / stream / batch？
为什么 StateGraph node 返回 partial state？
为什么 checkpoint 要绑定 thread_id？
为什么 interrupt 必须依赖 checkpointer？
为什么 ToolMessage 要重新放回 messages？
```

---

## 5. 总体学习节奏

建议周期：4 到 6 周。

| 周次 | 学习主题 | 重点产出 |
|---|---|---|
| 第 1 周 | LangChain Core：Runnable / Prompt / Message / Model | 3 篇源码笔记 + 最小代码实验 |
| 第 2 周 | Tool Calling 与 create_agent | 2 篇源码笔记 + ReAct 执行链路图 |
| 第 3 周 | LangGraph 基础：StateGraph / Edge / Router / Reducer | 3 篇源码笔记 + 旅行助手 state 流转图 |
| 第 4 周 | LangGraph 进阶：Checkpoint / Interrupt / Subgraph / Streaming | 4 篇源码笔记 + checkpoint 时间线 |
| 第 5 周 | 旅行规划助手全链路框架复盘 | 1 篇综合复盘 + API 到源码映射表 |
| 第 6 周 | 框架设计复盘与工程判断 | 框架误区总结 + 面试表达稿 + 后续学习清单 |

---

# 第一部分：LangChain Core 源码学习路线

## 6. 第 1 篇：Runnable 源码解剖

### 6.1 学习目标

掌握 LangChain 中最核心的统一执行抽象：`Runnable`。

你需要理解：

```text
为什么 prompt | model | parser 可以组合；
为什么每个组件都能 invoke / stream / batch；
为什么普通函数可以变成 RunnableLambda；
为什么 LangChain 能把 Prompt、Model、Parser、Retriever、Tool 放在同一套执行协议下。
```

### 6.2 范式映射

```text
普通 LLM Chain
→ LangChain RunnableSequence
```

普通链路：

```text
User Input
→ Prompt
→ Model
→ Parser
→ Output
```

框架表达：

```python
chain = prompt | model | parser
```

### 6.3 最小代码

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.chat_models import init_chat_model

model = init_chat_model("openai:gpt-4.1-mini")

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个旅行规划助手。"),
    ("user", "请为 {destination} 规划 {days} 天行程。")
])

chain = prompt | model | StrOutputParser()

result = chain.invoke({
    "destination": "东京",
    "days": 5
})

print(result)
```

### 6.4 执行流程

```text
chain.invoke(input)
  ↓
ChatPromptTemplate.invoke(input)
  ↓
生成 PromptValue / messages
  ↓
ChatModel.invoke(messages)
  ↓
返回 AIMessage
  ↓
StrOutputParser.invoke(AIMessage)
  ↓
返回字符串
```

### 6.5 源码阅读入口

```text
langchain_core/runnables/base.py
langchain_core/runnables/config.py
langchain_core/runnables/utils.py
langchain_core/runnables/passthrough.py
langchain_core/runnables/branch.py
```

重点类：

```text
Runnable
RunnableSequence
RunnableParallel
RunnableLambda
RunnableConfig
```

### 6.6 源码阅读问题

```text
1. Runnable 的核心抽象方法有哪些？
2. invoke、ainvoke、stream、batch 的默认实现关系是什么？
3. `|` 运算符如何构造 RunnableSequence？
4. RunnableConfig 如何向下传递？
5. callbacks、tags、metadata 如何进入执行链？
6. RunnableSequence 如何逐个调用子 Runnable？
7. RunnableParallel 如何并行调用多个子 Runnable？
```

### 6.7 实践任务

在旅行规划助手中找到所有类似：

```python
prompt | model
prompt | model | parser
```

的代码，并标注：

```text
这是 RunnableSequence；
输入是什么；
中间输出是什么；
最终输出是什么；
是否支持 stream；
是否能加 with_retry / with_config。
```

### 6.8 产出

```text
01_langchain_runnable_源码解剖.md
```

---

## 7. 第 2 篇：Prompt / Message / ChatModel 源码解剖

### 7.1 学习目标

把对 Prompt 的理解从“字符串模板”升级为“结构化消息构造器”。

你需要掌握：

```text
PromptTemplate
ChatPromptTemplate
MessagesPlaceholder
SystemMessage
HumanMessage
AIMessage
ToolMessage
BaseChatModel
```

### 7.2 范式映射

```text
Context Engineering / Prompt Engineering
→ ChatPromptTemplate + Messages + ChatModel
```

### 7.3 最小代码

```python
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是旅行规划助手，需要根据用户偏好规划行程。"),
    MessagesPlaceholder("history"),
    ("user", "{input}")
])

messages = prompt.invoke({
    "history": [],
    "input": "我想去大阪玩 4 天，喜欢美食和城市漫步"
})

print(messages)
```

### 7.4 执行流程

```text
输入变量
  ↓
ChatPromptTemplate 格式化
  ↓
PromptValue
  ↓
messages list
  ↓
ChatModel 接收 messages
  ↓
返回 AIMessage
```

### 7.5 源码阅读入口

```text
langchain_core/prompts/
langchain_core/messages/
langchain_core/language_models/chat_models.py
```

重点类：

```text
BaseMessage
HumanMessage
SystemMessage
AIMessage
ToolMessage
BaseChatModel
ChatPromptTemplate
MessagesPlaceholder
```

### 7.6 源码阅读问题

```text
1. ChatPromptTemplate.invoke 返回的对象是什么？
2. PromptValue 如何转换为 messages？
3. AIMessage 为什么能携带 tool_calls？
4. response_metadata 和 usage_metadata 在哪里保存？
5. BaseChatModel.invoke 和 _generate 的关系是什么？
6. 不同模型供应商的返回值如何统一为 AIMessage？
```

### 7.7 实践任务

对旅行规划助手中的 Prompt 进行拆解：

| Prompt 名称 | 输入变量 | 输出类型 | 使用场景 | 是否进入 Agent State |
|---|---|---|---|---|
| 需求解析 Prompt | user_request | intent/slots | Router | 是 |
| 规划 Prompt | destination/preferences | plan_steps | Planner | 是 |
| 搜索 Query Prompt | plan/current_step | search_query | Tool-use | 是 |
| 最终回复 Prompt | full_state | final_answer | Response | 否 |

### 7.8 产出

```text
02_prompt_message_chatmodel_源码解剖.md
```

---

## 8. 第 3 篇：OutputParser 与结构化输出

### 8.1 学习目标

掌握模型输出从自然语言变成结构化对象的过程。

重点理解：

```text
StrOutputParser
JsonOutputParser
PydanticOutputParser
with_structured_output
schema validation
parser failure
retry / repair
```

### 8.2 范式映射

```text
意图识别 / 槽位抽取 / 计划生成 / 责任判断
→ 结构化输出
```

### 8.3 最小代码

```python
from pydantic import BaseModel, Field
from langchain.chat_models import init_chat_model

class TravelIntent(BaseModel):
    destination: str | None = Field(description="目的地")
    days: int | None = Field(description="旅行天数")
    preferences: list[str] = Field(description="用户偏好")
    need_clarification: bool = Field(description="是否需要追问")

model = init_chat_model("openai:gpt-4.1-mini")
structured_model = model.with_structured_output(TravelIntent)

result = structured_model.invoke(
    "我想去东京玩 5 天，喜欢美食和城市漫步"
)

print(result)
```

### 8.4 执行流程

```text
Pydantic schema
  ↓
转换为模型可理解的结构化输出约束
  ↓
模型生成结构化结果
  ↓
框架解析并校验
  ↓
返回 Pydantic 对象或 dict
```

### 8.5 源码阅读入口

```text
langchain_core/output_parsers/
langchain_core/language_models/chat_models.py
langchain_core/utils/function_calling.py
```

### 8.6 源码阅读问题

```text
1. with_structured_output 底层如何绑定 schema？
2. Pydantic schema 如何转换为 JSON schema？
3. 结构化输出和 tool calling 有什么关系？
4. 解析失败时异常在哪里抛出？
5. parser 应该放在 chain 里，还是依赖模型原生 structured output？
```

### 8.7 实践任务

为旅行规划助手中的关键节点设计结构化输出：

```text
IntentResult
TravelPlan
SearchQuery
ReflectionResult
FinalResponse
```

每个结构化输出都要写：

```text
字段
含义
是否必填
失败样例
校验规则
```

### 8.8 产出

```text
03_structured_output_源码解剖.md
```

---

# 第二部分：Tool-use 与 Agent Loop

## 9. 第 4 篇：Tool Calling 源码解剖

### 9.1 学习目标

理解普通 Python 函数如何变成模型可调用工具。

你需要掌握：

```text
@tool
StructuredTool
BaseTool
args_schema
tool name
tool description
tool call
ToolMessage
tool error handling
```

### 9.2 范式映射

```text
Tool-use Agent
→ LangChain Tool / StructuredTool
```

### 9.3 最小代码

```python
from langchain.tools import tool

@tool
def search_attractions(city: str, preference: str) -> str:
    """Search attractions in a city based on user preference."""
    return f"{city} attractions for {preference}"

print(search_attractions.name)
print(search_attractions.description)
print(search_attractions.args)
```

### 9.4 执行流程

```text
Python function
  ↓
@tool 包装
  ↓
BaseTool / StructuredTool
  ↓
生成 name / description / args_schema
  ↓
绑定到模型
  ↓
模型输出 tool_calls
  ↓
工具执行层调用真实函数
  ↓
结果包装为 ToolMessage
  ↓
重新放回 messages
```

### 9.5 源码阅读入口

```text
langchain_core/tools/
langchain/tools/
langchain_core/messages/tool.py
```

重点类：

```text
BaseTool
StructuredTool
ToolException
ToolMessage
```

### 9.6 源码阅读问题

```text
1. @tool 装饰器如何读取函数名、参数和 docstring？
2. args_schema 如何从函数签名生成？
3. Tool.invoke 和普通函数调用有什么区别？
4. ToolMessage 如何保存 tool_call_id？
5. 工具异常如何被捕获并返回给模型？
6. 工具描述如何影响模型选择？
```

### 9.7 实践任务

对旅行规划助手中的工具建立工具表：

| 工具名 | 输入 schema | 输出 schema | 是否有副作用 | 是否需要确认 | 所属范式 |
|---|---|---|---|---|---|
| search_destination | city/query | documents | 否 | 否 | Tool-use / RAG |
| search_weather | city/date | weather | 否 | 否 | Tool-use |
| search_transport | from/to/date | routes | 否 | 否 | Tool-use |
| save_plan | plan/user_id | saved_status | 是 | 是 | HITL / Tool-use |

### 9.8 产出

```text
04_tool_calling_源码解剖.md
```

---

## 10. 第 5 篇：create_agent 与 ReAct 执行机制

### 10.1 学习目标

理解 LangChain Agent 如何通过模型-工具循环实现 ReAct 类行为。

需要掌握：

```text
create_agent
model node
tools node
middleware
tool loop
stop condition
iteration limit
structured response
```

### 10.2 范式映射

```text
ReAct
→ model call
→ tool call
→ ToolMessage
→ model call
→ final answer
```

现代框架不一定显式暴露 Thought，生产中更推荐观察结构化 trace：

```text
AIMessage
tool_calls
ToolMessage
final AIMessage
```

### 10.3 最小代码

```python
from langchain.agents import create_agent
from langchain.tools import tool

@tool
def search_city_info(query: str) -> str:
    """Search city information for travel planning."""
    return f"Search result for {query}"

agent = create_agent(
    model="openai:gpt-4.1-mini",
    tools=[search_city_info],
    system_prompt="你是一个旅行规划助手。"
)

result = agent.invoke({
    "messages": [
        {"role": "user", "content": "帮我规划东京 5 天行程，需要查一下热门景点"}
    ]
})

print(result)
```

### 10.4 执行流程

```text
用户 messages
  ↓
model node
  ↓
AIMessage 是否包含 tool_calls？
  ↓
如果有：tools node 执行工具
  ↓
ToolMessage 加入 messages
  ↓
回到 model node
  ↓
直到模型输出 final answer 或达到停止条件
```

### 10.5 源码阅读入口

```text
langchain/agents/
langchain/agents/factory.py
langgraph/prebuilt/
langchain_core/messages/
langchain_core/tools/
```

### 10.6 源码阅读问题

```text
1. create_agent 返回的是什么对象？
2. 它内部是否构建了 LangGraph graph？
3. model node 和 tools node 如何连接？
4. tool_calls 如何被识别？
5. 工具执行结果如何重新进入 messages？
6. middleware 在模型调用前后能做什么？
7. stop condition 在哪里判断？
```

### 10.7 实践任务

在旅行规划助手中选一次带工具调用的请求，记录完整 ReAct-like trace：

| 轮次 | 模型输出 | 是否有 tool_calls | 调用工具 | 工具结果 | 下一步 |
|---|---|---|---|---|---|
| 1 | 需要查询景点 | 是 | search_attractions | 返回候选景点 | 继续规划 |
| 2 | 需要查询天气 | 是 | search_weather | 返回天气 | 调整行程 |
| 3 | 输出最终计划 | 否 | 无 | 无 | 结束 |

### 10.8 产出

```text
05_create_agent与ReAct实现机制.md
```

---

# 第三部分：LangGraph Workflow 与状态图

## 11. 第 6 篇：StateGraph 源码解剖

### 11.1 学习目标

理解 LangGraph 如何用图结构承载 Workflow Agent。

重点掌握：

```text
StateGraph
State schema
add_node
add_edge
START
END
compile
CompiledStateGraph
partial state update
```

### 11.2 范式映射

```text
Workflow Agent
→ StateGraph + Node + Edge + State
```

### 11.3 最小代码

```python
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

class TravelState(TypedDict):
    user_request: str
    destination: str | None
    days: int | None
    plan: str | None

def parse_request(state: TravelState):
    return {
        "destination": "东京",
        "days": 5
    }

def generate_plan(state: TravelState):
    return {
        "plan": f"为 {state['destination']} 生成 {state['days']} 天旅行计划"
    }

builder = StateGraph(TravelState)

builder.add_node("parse_request", parse_request)
builder.add_node("generate_plan", generate_plan)

builder.add_edge(START, "parse_request")
builder.add_edge("parse_request", "generate_plan")
builder.add_edge("generate_plan", END)

graph = builder.compile()

result = graph.invoke({
    "user_request": "我想去东京玩 5 天",
    "destination": None,
    "days": None,
    "plan": None
})

print(result)
```

### 11.4 执行流程

```text
StateGraph 构建阶段
  ↓
注册节点
  ↓
注册边
  ↓
compile 生成可执行图
  ↓
invoke 初始化 state
  ↓
按边执行节点
  ↓
节点返回 partial update
  ↓
合并 state
  ↓
到达 END
```

### 11.5 源码阅读入口

```text
langgraph/graph/state.py
langgraph/graph/graph.py
langgraph/pregel/
```

重点类：

```text
StateGraph
CompiledStateGraph
Pregel
```

### 11.6 源码阅读问题

```text
1. StateGraph 为什么是 builder，而不是执行器？
2. add_node 如何保存节点函数？
3. add_edge 如何保存图结构？
4. compile 做了哪些校验？
5. CompiledStateGraph 如何实现 Runnable？
6. node 返回 partial update 后如何合并到 state？
```

### 11.7 实践任务

为旅行规划助手画出真实 StateGraph：

```text
START
→ parse_user_request
→ route_by_intent
→ generate_plan
→ search_tools
→ optimize_plan
→ final_response
→ END
```

每个节点标注：

```text
输入 state
输出 partial update
是否调用 LLM
是否调用 tool
是否是路由节点
是否可能失败
```

### 11.8 产出

```text
06_langgraph_stategraph_源码解剖.md
```

---

## 12. 第 7 篇：Conditional Edge 与 Router

### 12.1 学习目标

理解意图路由、状态路由、错误路由如何在 LangGraph 中落地。

### 12.2 范式映射

```text
Router Agent / Workflow Branch
→ add_conditional_edges
```

### 12.3 最小代码

```python
from typing_extensions import TypedDict, Literal
from langgraph.graph import StateGraph, START, END

class TravelState(TypedDict):
    user_request: str
    intent: str | None
    result: str | None

def classify_intent(state: TravelState):
    text = state["user_request"]
    if "预算" in text:
        intent = "budget_planning"
    elif "景点" in text:
        intent = "attraction_planning"
    else:
        intent = "general_planning"
    return {"intent": intent}

def route_by_intent(state: TravelState) -> Literal[
    "budget_node",
    "attraction_node",
    "general_node"
]:
    if state["intent"] == "budget_planning":
        return "budget_node"
    if state["intent"] == "attraction_planning":
        return "attraction_node"
    return "general_node"
```

### 12.4 执行流程

```text
classify_intent 节点执行
  ↓
state.intent 被更新
  ↓
route_by_intent(state)
  ↓
返回下一个节点名
  ↓
LangGraph 进入对应节点
```

### 12.5 源码阅读入口

```text
langgraph/graph/state.py
langgraph/graph/branch.py
```

### 12.6 源码阅读问题

```text
1. add_conditional_edges 如何注册 path function？
2. path function 的返回值可以是什么？
3. 返回 END 时如何终止？
4. 返回多个节点时如何并行？
5. mapping 参数有什么作用？
6. Literal 类型提示对可视化和校验有什么帮助？
```

### 12.7 实践任务

给旅行规划助手补一张路由表：

| 路由类型 | 判断依据 | 路由函数 | 目标节点 | 风险 |
|---|---|---|---|---|
| 意图路由 | intent | route_by_intent | plan/search/clarify | 意图误判 |
| 信息缺失路由 | missing_slots | route_missing_info | ask_user/planner | 追问过多 |
| 工具失败路由 | tool_error | route_error | retry/fallback | 死循环 |
| 质量检查路由 | score | route_reflection | revise/final | 过度反思 |

### 12.8 产出

```text
07_conditional_edge与router实现机制.md
```

---

## 13. 第 8 篇：Reducer 与并行状态合并

### 13.1 学习目标

理解为什么 LangGraph 的 state 不只是普通字典，而是有合并规则的状态模型。

### 13.2 范式映射

```text
并行检索 / 多 Agent 协作 / 多工具结果聚合
→ Reducer
```

### 13.3 最小代码

```python
from typing import Annotated
from operator import add
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

class TravelState(TypedDict):
    user_request: str
    research_notes: Annotated[list[str], add]

def search_food(state: TravelState):
    return {"research_notes": ["推荐美食：寿司、拉面、居酒屋"]}

def search_attractions(state: TravelState):
    return {"research_notes": ["推荐景点：浅草寺、涩谷、上野公园"]}
```

### 13.4 执行流程

```text
START 同时触发 search_food 和 search_attractions
  ↓
两个节点都写 research_notes
  ↓
LangGraph 根据 Annotated[list, add] 合并
  ↓
merge_plan 读取合并后的 research_notes
```

### 13.5 源码阅读入口

```text
langgraph/graph/state.py
langgraph/channels/
langgraph/pregel/
```

### 13.6 源码阅读问题

```text
1. State schema 如何解析 Annotated？
2. Reducer 是在什么时候被调用的？
3. 多节点写同一个 key 时如何判断是否冲突？
4. 覆盖式更新和追加式更新有什么区别？
5. messages 为什么通常需要特殊 reducer？
```

### 13.7 实践任务

检查旅行规划助手中哪些字段适合覆盖，哪些适合追加：

| State 字段 | 更新方式 | 是否需要 reducer | 原因 |
|---|---|---|---|
| destination | 覆盖 | 否 | 单一目的地 |
| preferences | 追加/覆盖 | 视场景 | 用户可能补充偏好 |
| search_results | 追加 | 是 | 多工具结果 |
| messages | 追加 | 是 | 对话历史 |
| final_plan | 覆盖 | 否 | 最终版本 |

### 13.8 产出

```text
08_reducer与并行状态合并.md
```

---

# 第四部分：计划、反思、记忆与人机协作

## 14. 第 9 篇：Plan-and-Execute 在 LangGraph 中的实现

### 14.1 学习目标

理解 Planner Node、Executor Node、Subgraph 如何表达 Plan-and-Execute。

### 14.2 范式映射

```text
Plan-and-Execute
→ planner node
→ plan validator
→ executor node / subgraph
→ step verifier
→ replan
```

### 14.3 推荐实现结构

```text
START
→ parse_request
→ planner_node
→ validate_plan
→ execute_step
→ check_step_result
→ route_next_step
  ├── continue_execute
  ├── replan
  └── final_response
```

### 14.4 最小代码骨架

```python
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

class PlanStep(TypedDict):
    step_id: int
    task: str
    status: str

class TravelState(TypedDict):
    user_request: str
    plan_steps: list[PlanStep]
    current_step_index: int
    final_answer: str | None

def planner_node(state: TravelState):
    return {
        "plan_steps": [
            {"step_id": 1, "task": "确认目的地和天数", "status": "pending"},
            {"step_id": 2, "task": "查询景点和交通信息", "status": "pending"},
            {"step_id": 3, "task": "生成每日行程", "status": "pending"},
        ],
        "current_step_index": 0
    }

def route_next_step(state: TravelState):
    if state["current_step_index"] >= len(state["plan_steps"]):
        return "final_response"
    return "execute_step"
```

### 14.5 源码阅读入口

```text
langgraph/graph/state.py
langgraph/graph/branch.py
langgraph/pregel/
```

### 14.6 源码阅读问题

```text
1. 计划列表应该存在 state 的哪个字段？
2. current_step_index 如何控制执行进度？
3. 每一步执行结果如何写回 state？
4. replan 是重新覆盖计划，还是追加修复步骤？
5. executor 应该直接调用工具，还是进入子图？
```

### 14.7 实践任务

对旅行规划助手的规划链路做一次标注：

```text
Planner 输出了什么？
Executor 每一步怎么选？
工具结果如何影响下一步？
什么时候需要 replan？
什么时候直接 final？
```

### 14.8 产出

```text
09_plan_and_execute在LangGraph中的实现.md
```

---

## 15. 第 10 篇：Reflection / Evaluator-Optimizer 在 LangGraph 中的实现

### 15.1 学习目标

理解 Reflection 如何从“让模型再想想”变成可控的评价-修改循环。

### 15.2 范式映射

```text
Reflection
→ generator node
→ evaluator node
→ revise node
→ conditional loop
```

### 15.3 推荐状态字段

```python
class TravelState(TypedDict):
    draft_plan: str | None
    critique: str | None
    quality_score: float | None
    revision_count: int
    final_plan: str | None
```

### 15.4 推荐流程

```text
generate_draft
→ evaluate_draft
→ route_by_score
  ├── revise_draft
  └── final_response
→ revise_draft
→ evaluate_draft
```

### 15.5 最小代码骨架

```python
MAX_REVISION = 2

def route_by_score(state):
    if state["quality_score"] >= 0.8:
        return "final_response"
    if state["revision_count"] >= MAX_REVISION:
        return "final_response"
    return "revise_draft"
```

### 15.6 源码阅读入口

```text
langgraph/graph/branch.py
langgraph/pregel/
```

### 15.7 源码阅读问题

```text
1. 反思循环如何避免无限执行？
2. revision_count 应该如何更新？
3. evaluator 输出应该结构化吗？
4. evaluator 和 generator 是否应该用不同模型？
5. 高风险任务中 Reflection 能不能替代 Policy / Verifier？
```

### 15.8 工程注意事项

```text
Reflection 适合质量优化，不适合替代规则校验；
必须设置 max_revision_count；
必须有明确评价指标；
如果新版本更差，需要保留旧版本或回滚；
高风险动作不能由 Reflection 自动放行。
```

### 15.9 产出

```text
10_reflection与evaluator_optimizer实现机制.md
```

---

## 16. 第 11 篇：Checkpoint / Thread / Durable Execution

### 16.1 学习目标

理解 LangGraph 生产级能力的核心：状态持久化与可恢复执行。

### 16.2 范式映射

```text
Memory / Long-running Agent / Durable Workflow / HITL
→ checkpoint + thread_id
```

### 16.3 最小代码

```python
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

class TravelState(TypedDict):
    user_request: str
    plan: str | None

def plan_node(state: TravelState):
    return {"plan": "生成旅行计划草稿"}

builder = StateGraph(TravelState)
builder.add_node("plan_node", plan_node)
builder.add_edge(START, "plan_node")
builder.add_edge("plan_node", END)

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "travel-thread-001"}}

graph.invoke({"user_request": "东京 5 天旅行", "plan": None}, config=config)

latest_state = graph.get_state(config)
history = list(graph.get_state_history(config))
```

### 16.4 执行流程

```text
graph.invoke(input, config)
  ↓
根据 thread_id 找到执行线程
  ↓
每个 super-step 后保存 checkpoint
  ↓
get_state 读取最新状态
  ↓
get_state_history 读取历史状态
```

### 16.5 源码阅读入口

```text
langgraph/checkpoint/
langgraph/pregel/
langgraph/types.py
```

重点概念：

```text
thread_id
checkpoint
StateSnapshot
super-step
writes
next
metadata
```

### 16.6 源码阅读问题

```text
1. checkpoint 保存了哪些信息？
2. thread_id 如何区分不同会话？
3. get_state 和 get_state_history 从哪里读数据？
4. super-step 的边界在哪里？
5. checkpoint 如何支持 time travel？
6. checkpoint 如何支持故障恢复？
```

### 16.7 实践任务

对旅行规划助手跑一次带 thread_id 的请求，记录：

| 时间点 | 节点 | state 变化 | checkpoint 是否产生 | 备注 |
|---|---|---|---|---|
| T1 | parse_request | 写入 destination/days | 是 | 初始化 |
| T2 | planner_node | 写入 plan_steps | 是 | 计划生成 |
| T3 | search_node | 写入 search_results | 是 | 工具结果 |
| T4 | final_node | 写入 final_plan | 是 | 结束 |

### 16.8 产出

```text
11_checkpoint与durable_execution源码解剖.md
```

---

## 17. 第 12 篇：Interrupt / Command / Human-in-the-loop

### 17.1 学习目标

理解人工确认如何从业务需求落到 LangGraph 运行机制。

### 17.2 范式映射

```text
Human-in-the-loop
→ interrupt()
→ checkpoint 保存
→ Command(resume=...)
```

### 17.3 最小代码

```python
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver

class TravelState(TypedDict):
    plan: str
    approved: bool | None

def approval_node(state: TravelState):
    approved = interrupt({
        "question": "是否确认使用该旅行计划？",
        "plan": state["plan"]
    })
    return {"approved": approved}

def final_node(state: TravelState):
    if state["approved"]:
        return {"plan": state["plan"] + "\n用户已确认。"}
    return {"plan": "用户未确认，需要重新规划。"}

builder = StateGraph(TravelState)
builder.add_node("approval_node", approval_node)
builder.add_node("final_node", final_node)
builder.add_edge(START, "approval_node")
builder.add_edge("approval_node", "final_node")
builder.add_edge("final_node", END)

graph = builder.compile(checkpointer=InMemorySaver())

config = {"configurable": {"thread_id": "travel-approval-001"}}

graph.invoke({"plan": "东京 5 天行程草案", "approved": None}, config=config)

graph.invoke(Command(resume=True), config=config)
```

### 17.4 执行流程

```text
执行到 approval_node
  ↓
调用 interrupt(payload)
  ↓
图暂停
  ↓
checkpoint 保存当前 state
  ↓
外部系统展示 payload
  ↓
用户确认
  ↓
graph.invoke(Command(resume=True), config)
  ↓
interrupt 返回 True
  ↓
图继续执行 final_node
```

### 17.5 源码阅读入口

```text
langgraph/types.py
langgraph/pregel/
langgraph/checkpoint/
```

### 17.6 源码阅读问题

```text
1. interrupt 如何让图暂停？
2. 暂停时 state 保存在哪里？
3. Command(resume=...) 如何把值传回 interrupt？
4. 为什么 interrupt 必须依赖 checkpointer？
5. 多个 interrupt 同时存在时如何恢复？
```

### 17.7 实践任务

检查旅行规划助手中哪些场景适合 HITL：

| 场景 | 是否需要 HITL | 原因 |
|---|---|---|
| 保存行程 | 需要 | 有状态写入 |
| 预订酒店 | 必须 | 高风险外部动作 |
| 修改日程 | 视情况 | 影响用户计划 |
| 查询天气 | 不需要 | 只读工具 |
| 生成建议 | 不需要 | 无副作用 |

### 17.8 产出

```text
12_interrupt与human_in_the_loop实现机制.md
```

---

# 第五部分：Streaming、Observability 与源码调试

## 18. 第 13 篇：Stream 与事件观察

### 18.1 学习目标

掌握如何观察 LangChain / LangGraph 的运行过程。

需要掌握：

```text
stream
astream
stream_mode="values"
stream_mode="updates"
stream_mode="messages"
event stream
metadata
callbacks
```

### 18.2 范式映射

```text
Agent Trace / Debugging / Observability
→ stream / events / tracing
```

### 18.3 最小代码

```python
for chunk in graph.stream(
    {"user_request": "东京 5 天旅行"},
    stream_mode="updates"
):
    print(chunk)
```

### 18.4 常见 stream 模式理解

| 模式 | 观察内容 | 适合场景 |
|---|---|---|
| values | 每步后的完整 state | 状态调试 |
| updates | 每个节点的增量更新 | 节点输出调试 |
| messages | 模型 token / message chunks | 流式回复 |
| custom | 自定义事件 | 工具进度、业务日志 |

### 18.5 源码阅读入口

```text
langgraph/pregel/
langchain_core/runnables/base.py
langchain_core/tracers/
```

### 18.6 源码阅读问题

```text
1. stream 与 invoke 的执行路径有什么不同？
2. stream_mode 如何影响输出？
3. token streaming 和 node update streaming 有什么区别？
4. callbacks 和 events 如何记录执行过程？
5. LangSmith trace 如何接入？
```

### 18.7 实践任务

为旅行规划助手做一份 trace 表：

| step | node | update | tool_calls | model_used | latency | cost |
|---|---|---|---|---|---|---|

### 18.8 产出

```text
13_stream与observability实现机制.md
```

---

## 19. 第 14 篇：源码阅读路线总表

### 19.1 LangChain Core 源码优先级

| 优先级 | 文件/目录 | 学习目标 |
|---|---|---|
| P0 | `langchain_core/runnables/base.py` | Runnable 抽象 |
| P0 | `langchain_core/messages/` | Message 体系 |
| P0 | `langchain_core/language_models/chat_models.py` | ChatModel 抽象 |
| P0 | `langchain_core/prompts/` | Prompt 构造 |
| P0 | `langchain_core/tools/` | Tool 抽象 |
| P1 | `langchain_core/output_parsers/` | 输出解析 |
| P1 | `langchain_core/retrievers.py` | Retriever 抽象 |
| P1 | `langchain_core/callbacks/` | 回调和追踪 |

### 19.2 LangChain Agent 源码优先级

| 优先级 | 文件/目录 | 学习目标 |
|---|---|---|
| P0 | `langchain/agents/` | create_agent 实现 |
| P0 | `langchain/agents/factory.py` | Agent graph 构建 |
| P1 | middleware 相关模块 | 中间件扩展点 |
| P1 | structured response 相关模块 | 结构化 Agent 输出 |

### 19.3 LangGraph 源码优先级

| 优先级 | 文件/目录 | 学习目标 |
|---|---|---|
| P0 | `langgraph/graph/state.py` | StateGraph |
| P0 | `langgraph/graph/graph.py` | 图基础结构 |
| P0 | `langgraph/pregel/` | 运行时 |
| P0 | `langgraph/checkpoint/` | 持久化 |
| P0 | `langgraph/types.py` | Command / interrupt |
| P1 | `langgraph/channels/` | 状态通道和 reducer |
| P1 | `langgraph/prebuilt/` | 预构建节点和 agent |
| P1 | `langgraph/store/` | 长期存储 |

### 19.4 源码阅读方法

不要从仓库第一行开始读，而是按调用链读。

推荐顺序：

```text
项目代码中的 API
  ↓
官方 reference
  ↓
核心类定义
  ↓
invoke / compile / stream 入口
  ↓
关键数据结构
  ↓
运行时调度
  ↓
异常和边界情况
```

例如读 `StateGraph.compile()`：

```text
你的代码：builder.compile()
  ↓
reference：compile 参数和返回值
  ↓
源码：StateGraph.compile
  ↓
CompiledStateGraph
  ↓
Pregel runtime
  ↓
invoke / stream
  ↓
checkpoint / interrupt
```

### 19.5 产出

```text
14_langchain_langgraph源码阅读路线总表.md
```

---

# 第六部分：旅行规划助手框架复盘

## 20. 第 15 篇：旅行规划助手完整执行链路拆解

### 20.1 学习目标

把已完成的旅行规划助手拆解成范式、框架组件、执行路径和源码入口。

### 20.2 拆解模板

| Step | 业务含义 | 范式 | LangGraph Node | LangChain Component | 输入 | 输出 | 源码入口 |
|---|---|---|---|---|---|---|---|
| 1 | 用户需求解析 | Router / Slot Extraction | parse_node | prompt \| model \| parser | user_request | intent/slots | Runnable / Prompt |
| 2 | 生成旅行计划步骤 | Plan-and-Execute | planner_node | structured output | state | plan_steps | ChatModel / Parser |
| 3 | 查询景点/天气/交通 | Tool-use / ReAct | tool_node | Tool | query | tool_result | BaseTool / ToolMessage |
| 4 | 路由下一步 | Workflow / Router | route_fn | conditional edge | state | next_node | add_conditional_edges |
| 5 | 质量检查 | Reflection | evaluator_node | model/parser | draft_plan | score/critique | Runnable |
| 6 | 修改计划 | Reflection | revise_node | model | critique/state | revised_plan | Runnable |
| 7 | 最终回复 | Response Generation | final_node | prompt \| model | full_state | answer | ChatModel |
| 8 | 状态保存 | Memory | checkpointer | checkpoint | state | snapshot | checkpoint / Pregel |

### 20.3 执行 trace 模板

```text
输入：
我想去东京玩 5 天，喜欢美食、城市漫步，预算中等。

Trace：
1. parse_user_request
   - 写入 destination=东京
   - 写入 days=5
   - 写入 preferences=[美食, 城市漫步, 预算中等]

2. planner_node
   - 生成 plan_steps
   - 每一步包含 task、需要的工具、预期输出

3. search_attractions_node
   - 调用 search_attractions
   - 写入 search_results

4. search_weather_node
   - 调用 search_weather
   - 写入 weather_info

5. optimize_route_node
   - 根据景点和交通优化日程顺序

6. evaluate_plan_node
   - 输出 score、issues、suggestions

7. revise_plan_node
   - 根据 critique 修改计划

8. final_response_node
   - 生成面向用户的最终计划
```

### 20.4 框架组件标注

在项目代码中为关键函数补充注释：

```python
def planner_node(state: TravelState):
    """
    LangGraph Node:
    - 范式角色：Plan-and-Execute 中的 Planner
    - 输入：完整 TravelState
    - 输出：partial state update，包含 plan_steps
    - LangGraph 机制：返回值会被合并到全局 state
    - LangChain 组件：内部使用 prompt | model | parser
    - 源码入口：StateGraph node execution + RunnableSequence
    """
    ...
```

### 20.5 产出

```text
15_旅行规划助手完整执行链路复盘.md
```

---

## 21. 第 16 篇：框架误区与工程判断

### 21.1 常见误区

#### 误区一：把 LangChain 当作 Prompt 拼接工具

正确理解：

```text
LangChain 的核心是 Runnable 抽象和 Agent 组件化，不只是 PromptTemplate。
```

#### 误区二：把 LangGraph 当成流程图工具

正确理解：

```text
LangGraph 是有状态、可恢复、可中断的 Agent runtime，不是普通 DAG 工具。
```

#### 误区三：所有节点都用 LLM

正确理解：

```text
确定性逻辑用代码；
语义判断用模型；
高风险决策用规则和人工；
复杂开放任务才用 Agent loop。
```

#### 误区四：会用 create_agent 就等于懂 ReAct

正确理解：

```text
create_agent 是 ReAct-like agent loop 的工程实现之一；
真正要懂的是 model call、tool call、ToolMessage、stop condition 的循环机制。
```

#### 误区五：Checkpoint 等于普通 memory

正确理解：

```text
checkpoint 是图执行状态快照；
memory 是上下文管理概念；
长期记忆还需要 store、retrieval、write policy。
```

#### 误区六：Reflection 可以替代验证器

正确理解：

```text
Reflection 适合质量优化；
Verifier / Policy 负责硬约束；
HITL 负责高风险兜底。
```

### 21.2 工程判断清单

| 问题 | 判断 |
|---|---|
| 这个逻辑是否确定？ | 确定则用代码，不要用 LLM |
| 这个流程是否稳定？ | 稳定则用 Workflow |
| 是否需要根据工具结果动态决策？ | 需要则用 conditional edge / ReAct |
| 是否涉及副作用？ | 需要权限校验和 HITL |
| 是否需要多轮恢复？ | 需要 checkpoint |
| 是否需要人工审批？ | 使用 interrupt |
| 是否需要质量复核？ | 使用 evaluator / reflection |
| 是否需要多工具并行？ | 使用 reducer 合并状态 |
| 是否需要长期记忆？ | 使用 store + memory policy |

### 21.3 产出

```text
16_langchain_langgraph框架误区与工程判断.md
```

---

# 第七部分：最终产出规划

## 22. 最终笔记目录

建议最终形成如下目录：

```text
langchain_langgraph_source_notes/
  00_学习路线.md
  01_langchain_runnable源码解剖.md
  02_prompt_message_chatmodel源码解剖.md
  03_structured_output源码解剖.md
  04_tool_calling源码解剖.md
  05_create_agent与ReAct实现机制.md
  06_langgraph_stategraph源码解剖.md
  07_conditional_edge与router实现机制.md
  08_reducer与并行状态合并.md
  09_plan_and_execute在LangGraph中的实现.md
  10_reflection与evaluator_optimizer实现机制.md
  11_checkpoint与durable_execution源码解剖.md
  12_interrupt与human_in_the_loop实现机制.md
  13_stream与observability实现机制.md
  14_langchain_langgraph源码阅读路线总表.md
  15_旅行规划助手完整执行链路复盘.md
  16_langchain_langgraph框架误区与工程判断.md
```

## 23. 每篇笔记固定模板

每篇文章都使用同一模板：

```markdown
# 标题

## 1. 本节解决什么问题

## 2. 对应 Agent 范式

## 3. 最小可运行代码

## 4. 代码逐行讲解

## 5. 执行流程图

## 6. 源码阅读入口

## 7. 核心源码问题

## 8. 结合旅行规划助手的复盘

## 9. 工程注意事项

## 10. 小结
```

## 24. 每篇代码讲解标准

每段代码都要讲清：

```text
这个对象是什么？
输入是什么？
输出是什么？
它属于 LangChain 还是 LangGraph？
它是构建阶段执行，还是运行阶段执行？
它是否读写 state？
它是否调用模型？
它是否调用工具？
它是否支持 stream？
它对应哪个源码入口？
```

## 25. 每篇源码讲解标准

每个源码点都要讲清：

```text
这个类解决什么抽象问题？
核心方法是什么？
谁调用它？
它调用谁？
输入输出是什么？
哪些参数最重要？
容易误解的地方是什么？
生产中如何使用？
```

---

# 第八部分：学习检查清单

## 26. LangChain 掌握标准

- [ ] 能解释 Runnable 的作用；
- [ ] 能解释 `prompt | model | parser` 为什么能运行；
- [ ] 能解释 PromptValue、Message、AIMessage 的关系；
- [ ] 能解释 AIMessage.tool_calls 的作用；
- [ ] 能解释 `@tool` 如何生成工具 schema；
- [ ] 能解释 ToolMessage 为什么要放回 messages；
- [ ] 能解释 create_agent 的模型-工具循环；
- [ ] 能解释 middleware 能拦截哪些阶段；
- [ ] 能解释 structured output 和 output parser 的区别；
- [ ] 能解释 Retriever 如何作为 Runnable 参与链路。

## 27. LangGraph 掌握标准

- [ ] 能解释 StateGraph 为什么是 builder；
- [ ] 能解释 compile 之后得到什么；
- [ ] 能解释 node 为什么返回 partial state；
- [ ] 能解释 reducer 的作用；
- [ ] 能解释 add_edge 和 add_conditional_edges 的区别；
- [ ] 能解释 START / END 的作用；
- [ ] 能解释 checkpoint 和 thread_id 的关系；
- [ ] 能解释 StateSnapshot 保存什么；
- [ ] 能解释 interrupt 和 Command(resume=...) 如何工作；
- [ ] 能解释 subgraph 如何复用；
- [ ] 能解释 stream 的不同模式；
- [ ] 能解释 Pregel runtime 的基本调度思想。

## 28. 范式到框架映射掌握标准

- [ ] 能用 StateGraph 实现 Workflow；
- [ ] 能用 conditional edge 实现 Router；
- [ ] 能用 create_agent 解释 ReAct-like loop；
- [ ] 能用 planner node + executor node 表达 Plan-and-Execute；
- [ ] 能用 evaluator node + loop edge 表达 Reflection；
- [ ] 能用 retriever node + answer node 表达 Agentic RAG；
- [ ] 能用 checkpoint 表达短期执行记忆；
- [ ] 能用 interrupt 表达人工确认；
- [ ] 能用 stream / trace 表达可观测性。

## 29. 源码阅读掌握标准

- [ ] 能定位 Runnable 源码；
- [ ] 能定位 ChatModel 源码；
- [ ] 能定位 Tool 源码；
- [ ] 能定位 create_agent 源码；
- [ ] 能定位 StateGraph 源码；
- [ ] 能定位 CompiledStateGraph / Pregel 源码；
- [ ] 能定位 checkpointer 源码；
- [ ] 能定位 interrupt / Command 源码；
- [ ] 能根据报错追踪到框架层问题。

---

# 9. 推荐资料

## 9.1 官方文档

- LangChain Agents  
  https://docs.langchain.com/oss/python/langchain/agents
- LangChain Runtime  
  https://docs.langchain.com/oss/python/langchain/runtime
- LangChain v1 Release Notes  
  https://docs.langchain.com/oss/python/releases/langchain-v1
- LangChain `create_agent` Reference  
  https://reference.langchain.com/python/langchain/agents/factory/create_agent
- LangChain Runnable Reference  
  https://reference.langchain.com/python/langchain-core/runnables
- LangGraph Overview  
  https://docs.langchain.com/oss/python/langgraph/overview
- LangGraph StateGraph Reference  
  https://reference.langchain.com/python/langgraph/graph/state/StateGraph
- LangGraph Durable Execution  
  https://docs.langchain.com/oss/python/langgraph/durable-execution
- LangGraph Interrupts  
  https://docs.langchain.com/oss/python/langgraph/interrupts
- LangGraph Subgraphs  
  https://docs.langchain.com/oss/python/langgraph/use-subgraphs
- LangGraph Runtime / Pregel  
  https://docs.langchain.com/oss/python/langgraph/pregel
- LangSmith Evaluation  
  https://docs.langchain.com/langsmith/evaluation

## 9.2 源码仓库

- LangChain GitHub  
  https://github.com/langchain-ai/langchain
- LangGraph GitHub  
  https://github.com/langchain-ai/langgraph

## 9.3 关联学习资料

- ReAct: Synergizing Reasoning and Acting in Language Models  
  https://arxiv.org/abs/2210.03629
- Reflexion: Language Agents with Verbal Reinforcement Learning  
  https://arxiv.org/abs/2303.11366
- Plan-and-Solve Prompting  
  https://aclanthology.org/2023.acl-long.147/
- Anthropic: Building Effective Agents  
  https://www.anthropic.com/engineering/building-effective-agents
- OpenAI Agents SDK  
  https://developers.openai.com/api/docs/guides/agents
- Model Context Protocol  
  https://modelcontextprotocol.io/docs/getting-started/intro

---

# 10. 最终总结

这条学习路线的核心不是“学会更多 API”，而是把 Agent 范式、框架实现和源码机制打通。

最终你应该形成三种能力：

```text
第一，范式映射能力：
看到 ReAct、Workflow、Router、Plan、Reflection，知道在 LangChain / LangGraph 中如何表达。

第二，源码理解能力：
看到 Runnable、Tool、StateGraph、Checkpoint、Interrupt，知道它们的执行机制和源码入口。

第三，工程判断能力：
知道哪些场景该用 Chain，哪些场景该用 Workflow，哪些场景该用 Agent loop，哪些场景必须加 checkpoint、HITL、Verifier 和 Guardrails。
```

学完这条路线后，你对 LangChain / LangGraph 的理解不应该停留在：

```text
我会用框架写一个 Agent
```

而应该升级为：

```text
我知道 Agent 范式如何被框架实现；
我知道框架运行时如何调度；
我知道源码该从哪里读；
我知道真实业务里该用哪一层抽象。
```
