# ReAct 范式学习指南：基于 LangChain 与 LangGraph

> 适用对象：已经了解 Prompt、Tool Calling、RAG 基础，准备系统学习 Agent 基础范式的学习者。  
> 学习目标：通过 ReAct 范式理解“模型如何边想边调用工具”，并分别用 LangChain 与 LangGraph 搭建一个最小可运行 Demo。  
> 文档风格：长期学习笔记，不追求概念堆砌，强调工程落地、适用边界和实践验证。

---

## 1. 学习目标

这一阶段不要急着做复杂 Agent，也不要一开始就堆 Multi-Agent、Memory、RAG、前端和数据库。你的核心目标只有一个：

> 理解 ReAct 为什么存在，以及它如何把 LLM、工具、状态、循环控制和最终回答串成一条可执行链路。

完成本阶段后，你应该能做到：

1. 能解释 ReAct 的 Thought / Action / Observation / Final Answer 循环。
2. 能区分 ReAct、普通 Prompt Chain、Tool Calling、Function Calling 的关系。
3. 能用 2—3 个简单工具搭建一个 ReAct Demo。
4. 能看懂 LangChain Agent 的基本执行过程。
5. 能用 LangGraph 显式表达“模型节点 → 工具节点 → 条件路由 → 结束”的 Agent 循环。
6. 能说清 ReAct 的适用边界：什么时候适合，什么时候不适合。
7. 能通过日志或 trace 判断 Agent 是否真的发生了工具调用和多轮观察。

---

## 2. ReAct 范式核心思想

### 2.1 ReAct 是什么

ReAct 是 Reasoning + Acting 的组合。

传统 LLM 只是在上下文里“想”和“回答”，但没有办法主动获取外部事实，也不能操作外部环境。ReAct 让模型在解决任务时交替执行两类动作：

```text
Reasoning：分析当前任务、判断下一步应该做什么
Acting：调用工具、查询外部环境、获得新信息
```

一个典型循环如下：

```text
用户问题
  ↓
Thought：我需要知道什么？
  ↓
Action：调用哪个工具？
  ↓
Observation：工具返回什么结果？
  ↓
Thought：根据结果还缺什么？
  ↓
Action：继续调用工具或停止
  ↓
Final Answer：给用户最终回答
```

### 2.2 Thought / Action / Observation / Final Answer

| 元素 | 含义 | 工程对应 |
|---|---|---|
| Thought | 模型对当前任务的内部分析 | 生产环境中不一定暴露，可替换为结构化决策日志 |
| Action | 模型决定调用的工具及参数 | tool call / function call |
| Observation | 工具执行后的返回结果 | tool result / ToolMessage |
| Final Answer | 模型基于已有信息给出的最终答案 | 面向用户的自然语言输出 |

注意：在现代 tool calling 框架里，你未必会看到显式的 `Thought:` 文本。很多模型会直接输出结构化 tool call。工程上更推荐记录：

```text
工具名
工具参数
工具返回
是否继续调用工具
最终答案
```

这样比暴露完整推理链更安全、可控，也更适合生产排查。

### 2.3 为什么要把 Reasoning 和 Acting 结合起来

ReAct 解决的是“模型只靠参数记忆不可靠”的问题。

比如用户问：

```text
请根据我的课程笔记，告诉我 ReAct 和普通 Chain 的区别。
```

如果模型不调用工具，它可能凭记忆回答，但无法保证和你的本地笔记一致。ReAct 的优势在于：

```text
先判断需要查资料
→ 调用本地笔记检索工具
→ 读取 Observation
→ 再基于工具结果回答
```

这让 Agent 的回答从“靠模型记忆”变成“基于外部证据”。

### 2.4 ReAct 与普通 Prompt Chain 的区别

普通 Prompt Chain 更像固定流水线：

```text
输入 → Prompt A → Prompt B → 输出
```

ReAct 更像动态循环：

```text
输入 → 模型判断是否需要工具
    → 如果需要，调用工具
    → 根据工具结果继续判断
    → 直到满足停止条件
```

普通 Chain 的步骤通常由开发者预先写死；ReAct 的关键在于：下一步调用什么工具，由模型根据当前上下文动态决定。

### 2.5 ReAct 与 Tool Calling / Function Calling 的关系

不要把它们混为一谈。

| 概念 | 关注点 | 说明 |
|---|---|---|
| ReAct | Agent 范式 | 强调 Reasoning 与 Acting 交替循环 |
| Tool Calling | 模型能力 / API 机制 | 模型生成结构化工具调用意图 |
| Function Calling | Tool Calling 的一种形式 | 模型输出函数名和 JSON 参数，由应用执行 |
| Agent Executor | 工程执行器 | 负责循环、解析、执行工具、返回结果 |

可以这样理解：

```text
Tool Calling / Function Calling 是“动作接口”
ReAct 是“什么时候动作、为什么动作、动作后如何继续”的范式
LangChain / LangGraph 是“把这个过程跑起来”的工程框架
```

---

## 3. ReAct 的工程组成

一个最小 ReAct Agent 通常包含以下模块：

```text
User Input
  ↓
Prompt / System Instruction
  ↓
LLM
  ↓
Parser / Tool Call Extractor
  ↓
Tool Executor
  ↓
Observation
  ↓
State / Scratchpad / Messages
  ↓
Loop Controller
  ↓
Final Answer
```

### 3.1 LLM

LLM 负责判断：

1. 当前问题是否可以直接回答；
2. 是否需要调用工具；
3. 调用哪个工具；
4. 工具参数是什么；
5. 工具结果是否足够；
6. 是否可以给出最终答案。

### 3.2 Prompt

Prompt 负责告诉模型：

```text
你能用哪些工具
什么时候应该用工具
什么时候不要用工具
工具返回结果如何使用
最多可以尝试几轮
如果没有合适工具该怎么办
最终回答格式是什么
```

一个简化提示词可以是：

```text
你是一个学习资料查询助手。
你可以使用 search_notes 查询本地 Markdown 笔记，使用 calculator 做简单计算。
当问题需要依据本地资料时，必须先调用 search_notes。
如果工具没有找到结果，不要编造，请说明没有找到依据。
最终回答要简洁，并说明依据来自哪个工具结果。
```

### 3.3 Tool

工具是 Agent 连接外部世界的接口。

一个好工具必须说明：

```text
工具做什么
什么时候调用
什么时候不要调用
需要哪些参数
参数格式是什么
返回结果代表什么
失败时返回什么
是否有副作用
是否需要权限或人工确认
```

示例：

```python
@tool
def search_notes(query: str) -> str:
    """Search local Markdown learning notes by keyword.
    Use this when the user asks about concepts that may appear in the local course notes.
    Do not use this for arithmetic or general chat.
    """
```

工具描述会直接影响模型选择工具。如果描述含糊，模型就容易误用工具。

### 3.4 Parser / Tool Call Extractor

早期 ReAct 常通过文本格式解析：

```text
Action: search_notes
Action Input: ReAct
```

现代框架更多使用结构化 tool calling：

```json
{
  "name": "search_notes",
  "arguments": {
    "query": "ReAct"
  }
}
```

结构化 tool calling 更稳定，也更容易做参数校验。

### 3.5 Executor

Executor 负责真正执行工具。模型不应该直接执行外部操作。

```text
模型：我想调用 refund(order_id=123)
执行器：校验权限、参数、幂等性、风险等级
工具层：真正调用退款 API
执行器：把结果作为 Observation 返回给模型
```

这点非常重要：模型只是提出调用意图，真正执行必须由代码控制。

### 3.6 Memory / State

ReAct 至少需要保存当前轮次的中间状态：

```text
用户问题
模型消息
工具调用
工具返回
当前迭代次数
是否结束
```

在 LangChain 里，这通常表现为 `messages` 或 agent scratchpad。  
在 LangGraph 里，这通常表现为 `State`，例如 `MessagesState` 或自定义 `TypedDict`。

### 3.7 Loop Controller

Loop Controller 用来防止死循环。

必须设置：

```text
最大迭代次数
最大工具调用次数
工具超时时间
异常重试次数
最终兜底策略
```

示例策略：

```text
如果连续两次调用同一个工具且参数相同，直接停止并说明当前无法获得更多信息。
如果工具返回空结果，不要继续盲目检索，改为询问用户补充关键词或给出未找到依据的回答。
如果达到最大迭代次数，输出当前已知信息和未完成原因。
```

---

## 4. ReAct 的适用边界与常见问题

### 4.1 适合 ReAct 的任务

ReAct 适合“需要边查边答、工具调用路径不完全固定”的任务：

1. 搜索型问答；
2. 文档查询助手；
3. 简单数据查询；
4. 需要计算器、时间、天气等工具的助手；
5. GitHub README 问答；
6. 简单订单状态查询；
7. 规则查询 + 解释类任务。

这些任务的共同点是：

```text
问题不一定需要工具
但如果需要工具，调用哪个工具可以由模型动态判断
工具调用失败的风险较低
最终动作多数是回答，而不是直接修改业务状态
```

### 4.2 不适合纯 ReAct 的任务

下面这些任务不适合完全开放式 ReAct：

1. 高风险退款、支付、删除、发货等有副作用操作；
2. 强流程业务，比如审批、售后、合规审核；
3. 步骤固定且必须满足业务状态机的任务；
4. 强约束输出任务，比如合同生成、医疗建议、金融交易；
5. 需要严格权限控制的企业系统。

这些任务更适合：

```text
Workflow Agent / State Machine
+ 局部 LLM 判断
+ Tool Calling
+ Guardrails
+ Human-in-the-loop
```

也就是说，在高可靠业务里，ReAct 可以作为局部能力，但不应该让模型完全自由决定流程。

### 4.3 常见问题

| 问题 | 表现 | 解决方案 |
|---|---|---|
| 工具误用 | 本来不用查工具，模型乱查 | 工具描述写清“什么时候不要调用” |
| 幻觉 Action | 模型调用不存在的工具 | 工具白名单 + 结构化 tool calling |
| 参数错误 | order_id、query 等参数缺失 | Pydantic 校验 + 缺参追问 |
| 循环失控 | 反复调用同一工具 | max_iterations + 重复调用检测 |
| Observation 理解错误 | 工具返回 A，模型解释成 B | 工具返回结构化 JSON + 结果摘要 |
| 过度依赖工具 | 简单问题也调用工具 | Prompt 加直接回答规则 |
| 最终答案不基于工具 | 查了资料但回答乱发挥 | 要求回答引用 Observation |
| 成本高 | 多轮 LLM + 多次工具调用 | 缓存、限制轮次、先规则路由 |

---

## 5. LangChain 中的 ReAct 实现

### 5.1 当前学习时要注意的版本变化

早期 LangChain 常见写法是：

```python
create_react_agent
AgentExecutor
```

但在 LangChain v1 之后，官方更推荐使用：

```python
from langchain.agents import create_agent
```

它仍然可以表达“模型调用工具直到停止”的 Agent 循环，但接口更统一，也更适合和中间件、结构化输出、状态等能力结合。

学习建议：

```text
先理解 create_react_agent / AgentExecutor 的经典思想
再用 create_agent 写当前版本 Demo
不要在入门阶段纠结所有历史 API
```

### 5.2 LangChain 适合做什么

LangChain 更适合快速搭建：

1. 单 Agent 工具助手；
2. 简单 RAG 问答；
3. 文档查询助手；
4. API 工具调用助手；
5. 原型验证 Demo。

它的优势是封装度高、上手快。  
局限是复杂状态管理、流程分支、人工审批、多 Agent 编排时不如 LangGraph 直观。

### 5.3 LangChain 最小代码结构

```text
react_notes_agent/
  data/
    notes/
      react.md
      langchain.md
      langgraph.md
  src/
    tools.py
    langchain_agent.py
  requirements.txt
  README.md
```

### 5.4 LangChain 工具定义示例

```python
# src/tools.py
from pathlib import Path
from langchain.tools import tool

NOTES_DIR = Path("data/notes")


@tool
def search_notes(query: str) -> str:
    """Search local Markdown notes by keyword.
    Use this when the user asks about ReAct, LangChain, LangGraph, Agent concepts,
    or anything that should be grounded in the local notes.
    Return matched note snippets. If nothing is found, return a clear empty result.
    """
    results = []
    for path in NOTES_DIR.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        if query.lower() in text.lower():
            snippet = text[:800]
            results.append(f"[{path.name}]\n{snippet}")
    return "\n\n".join(results) if results else "NO_MATCH_FOUND"


@tool
def calculator(expression: str) -> str:
    """Calculate a simple arithmetic expression.
    Use this only for arithmetic, such as 2+3*4.
    Do not use it for concept questions.
    """
    allowed = set("0123456789+-*/(). ")
    if not set(expression) <= allowed:
        return "ERROR: expression contains unsupported characters"
    try:
        return str(eval(expression, {"__builtins__": {}}, {}))
    except Exception as e:
        return f"ERROR: {e}"
```

### 5.5 LangChain Agent 示例

```python
# src/langchain_agent.py
from langchain.agents import create_agent
from src.tools import search_notes, calculator

SYSTEM_PROMPT = """
你是一个 ReAct 学习助手。
你可以使用工具查询本地 Markdown 笔记或进行简单计算。

规则：
1. 如果问题涉及本地学习笔记、ReAct、LangChain、LangGraph，请优先调用 search_notes。
2. 如果问题是简单计算，请调用 calculator。
3. 如果工具返回 NO_MATCH_FOUND，不要编造本地笔记内容。
4. 最终回答要说明你依据了哪个工具结果。
5. 不要无限尝试；如果信息不足，说明缺少什么。
"""

agent = create_agent(
    model="openai:gpt-5.4-mini",
    tools=[search_notes, calculator],
    system_prompt=SYSTEM_PROMPT,
)

if __name__ == "__main__":
    result = agent.invoke({
        "messages": [
            {"role": "user", "content": "根据我的笔记，ReAct 和普通 Chain 有什么区别？"}
        ]
    })

    for msg in result["messages"]:
        print(msg)
```

### 5.6 如何观察 LangChain 是否发生 ReAct 循环

你可以看三类信息：

1. 输出中是否出现 tool call；
2. 是否有 ToolMessage / tool result；
3. 最终回答是否基于工具返回内容。

建议开启 LangSmith tracing：

```bash
export LANGSMITH_TRACING=true
export LANGSMITH_API_KEY=你的_key
```

然后在 LangSmith 里观察：

```text
User input
→ Model call
→ Tool call: search_notes
→ Tool output
→ Model call
→ Final answer
```

---

## 6. LangGraph 中的 ReAct 实现

### 6.1 LangGraph 的核心优势

LangGraph 的重点不是“帮你少写代码”，而是让你显式控制 Agent 流程。

它更适合：

1. 多步骤状态机；
2. 复杂分支；
3. 多 Agent 编排；
4. 人工审批；
5. 长任务恢复；
6. 需要可观测 trace 的生产系统；
7. 高可靠业务流程。

LangGraph 的核心思想是：

```text
把 Agent 看成一个图
节点负责执行逻辑
边负责控制流转
状态负责保存上下文
条件边负责决定下一步
```

### 6.2 StateGraph / Node / Edge / Conditional Edge / State

| 概念 | 含义 | 类比 |
|---|---|---|
| StateGraph | 整个状态图 | 工作流定义 |
| State | 当前任务状态 | 全局上下文对象 |
| Node | 一个处理步骤 | 函数 / 服务节点 |
| Edge | 固定流转关系 | A 执行完一定到 B |
| Conditional Edge | 条件路由 | 如果有工具调用去工具节点，否则结束 |
| ToolNode | 工具执行节点 | 自动执行模型生成的 tool calls |

### 6.3 LangGraph 如何表达 ReAct 循环

最小结构如下：

```text
START
  ↓
agent_node：调用 LLM，判断是否需要工具
  ↓
conditional edge：
  ├─ 如果 AIMessage 里有 tool_calls → tools_node
  └─ 如果没有 tool_calls → END
  ↓
tools_node：执行工具，返回 ToolMessage
  ↓
agent_node：模型读取 Observation，继续判断
```

这正好对应 ReAct：

```text
Reasoning / Action：agent_node
Observation：tools_node
Loop：conditional edge + tools_node → agent_node
Final Answer：agent_node 输出无 tool_calls 的最终消息
```

### 6.4 LangGraph 最小代码示例

```python
# src/langgraph_agent.py
from typing import Literal
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from src.tools import search_notes, calculator

tools = [search_notes, calculator]

model = init_chat_model(
    "openai:gpt-5.4-mini",
    temperature=0
).bind_tools(tools)

SYSTEM_PROMPT = {
    "role": "system",
    "content": """
你是一个 ReAct 学习助手。
如果问题需要本地笔记依据，请调用 search_notes。
如果问题需要计算，请调用 calculator。
工具没有结果时不要编造。
"""
}


def agent_node(state: MessagesState):
    messages = [SYSTEM_PROMPT] + state["messages"]
    response = model.invoke(messages)
    return {"messages": [response]}


tool_node = ToolNode(tools)


def should_continue(state: MessagesState) -> Literal["tools", "__end__"]:
    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", None):
        return "tools"
    return "__end__"


graph_builder = StateGraph(MessagesState)
graph_builder.add_node("agent", agent_node)
graph_builder.add_node("tools", tool_node)

graph_builder.add_edge(START, "agent")
graph_builder.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        "__end__": END,
    },
)
graph_builder.add_edge("tools", "agent")

graph = graph_builder.compile()

if __name__ == "__main__":
    result = graph.invoke({
        "messages": [
            {"role": "user", "content": "根据我的笔记，ReAct 的核心循环是什么？"}
        ]
    })

    for msg in result["messages"]:
        print(msg)
```

### 6.5 为什么 LangGraph 更适合复杂 Agent

因为它让流程显式化。

如果你要做订单退款 Agent，流程可能是：

```text
识别意图
→ 补全订单号
→ 查订单
→ 查物流
→ 检索平台规则
→ 判断责任
→ 判断是否需要人工审批
→ 执行退款
→ 校验最终状态
→ 回复用户
```

这类流程不适合完全交给模型自由 ReAct。更好的做法是：

```text
LangGraph 控制主流程
LLM 只在局部节点做判断
工具执行由代码控制
高风险动作走人工确认
```

---

## 7. LangChain 与 LangGraph 对比

| 维度 | LangChain | LangGraph |
|---|---|---|
| 上手难度 | 更低，适合快速 Demo | 稍高，需要理解状态图 |
| 适合场景 | 简单 Agent、RAG、工具助手、原型验证 | 复杂流程、多 Agent、长期任务、高可靠业务 |
| 流程控制能力 | 中等，依赖封装好的 Agent 执行器 | 强，可以显式定义节点、边、条件路由 |
| 状态管理能力 | 基础状态和消息历史较方便 | 强，适合自定义 State、checkpoint、memory |
| 可观测性 | 可接 LangSmith，适合快速调试 | 更适合观察状态转移和复杂轨迹 |
| 复杂 Agent 扩展能力 | 中等，复杂后容易黑盒 | 强，结构清晰，可拆模块 |
| 推荐学习顺序 | 先学，用来理解 Agent 基本链路 | 后学，用来构建工程级 Agent |
| 与 ReAct 的关系 | 快速搭建 ReAct / tool-use Agent | 显式表达 ReAct 循环和流程控制 |

学习建议：

```text
第一步：用 LangChain 跑通最小工具调用 Agent
第二步：用 LangGraph 手写同样的 ReAct 循环
第三步：对比两者 trace，理解封装与控制力的取舍
第四步：以后做生产级 Agent，优先用 LangGraph 控制流程
```

如果目标是成为 Agent 工程师，不要只会 LangChain 的高级封装。你必须理解 LangGraph 这种状态图思想，因为真实业务 Agent 最终一定会涉及：

```text
状态
分支
重试
异常
人工审批
权限
观测
评估
回放
```

---

## 8. 推荐学习资料与阅读顺序

### 8.1 必读资料

| 顺序 | 资料 | 链接 | 适合学习 | 是否必读 | 重点关注 |
|---|---|---|---|---|---|
| 1 | ReAct 原始论文 | https://arxiv.org/abs/2210.03629 | ReAct 的提出背景、Reason + Act 的基本思想 | 是 | Abstract、Introduction、方法图、HotpotQA/WebShop 示例 |
| 2 | Google Research ReAct 介绍 | https://research.google/blog/react-synergizing-reasoning-and-acting-in-language-models/ | 用更直观方式理解 ReAct | 是 | Reasoning trace 与 action trace 如何交替 |
| 3 | LangChain Agents 文档 | https://docs.langchain.com/oss/python/langchain/agents | 当前 LangChain Agent API | 是 | create_agent、tools、system_prompt、messages |
| 4 | LangChain v1 Migration | https://docs.langchain.com/oss/python/migrate/langchain-v1 | 理解 create_react_agent 到 create_agent 的变化 | 是 | Migrate to create_agent |
| 5 | LangGraph Overview | https://docs.langchain.com/oss/python/langgraph/overview | LangGraph 核心定位 | 是 | StateGraph、durable execution、memory、debugging |
| 6 | LangGraph Quickstart | https://docs.langchain.com/oss/python/langgraph/quickstart | 用图实现工具 Agent | 是 | calculator agent、Graph API、tool node |
| 7 | OpenAI Function Calling | https://developers.openai.com/api/docs/guides/function-calling | 理解工具调用的 API 机制 | 是 | tool calling flow、JSON schema、tool outputs |
| 8 | Anthropic Tool Use | https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview | 理解 Claude 的 tool_use / tool_result 流程 | 建议 | client tools 与 server tools 的区别 |
| 9 | LangSmith Evaluation | https://docs.langchain.com/langsmith/evaluation | 后续做 Agent 评估 | 建议 | dataset、evaluators、experiment |
| 10 | LangGraph GitHub Repo | https://github.com/langchain-ai/langgraph | 看源码结构和 examples | 建议 | README、examples、libs/prebuilt |

### 8.2 阅读顺序建议

不要按“资料发布日期”读，要按理解成本读：

```text
第 1 步：Google Research ReAct 博客
第 2 步：ReAct 论文 Abstract + Introduction + 示例
第 3 步：OpenAI Function Calling 文档
第 4 步：LangChain Agents 文档，跑通 create_agent
第 5 步：LangGraph Overview + Quickstart
第 6 步：用 LangGraph 重写同一个 Demo
第 7 步：接 LangSmith 看 trace
第 8 步：再读 ReAct 论文实验部分，理解适用边界
```

### 8.3 资料应该怎么看

读 ReAct 论文时，不要陷入公式或 benchmark。重点看：

```text
为什么只推理不够
为什么只行动不够
ReAct 如何把中间推理和外部观察结合
它在哪些任务上有效
它有哪些失败模式
```

读 LangChain 文档时，重点看：

```text
create_agent 如何接收 model、tools、system_prompt
工具如何定义
invoke 输入输出是什么
消息列表中如何体现 tool call
如何接 tracing
```

读 LangGraph 文档时，重点看：

```text
State 是什么
Node 如何读写 State
Edge 如何控制流程
Conditional Edge 如何决定是否继续
ToolNode 如何执行工具
为什么 graph.compile() 之后才能运行
```

---

## 9. 最小实践 Demo 设计

### 9.1 推荐 Demo 方向

推荐做：

```text
Markdown 笔记检索 ReAct 助手
```

它的功能是：

```text
用户问一个关于 ReAct / LangChain / LangGraph 的学习问题
Agent 判断是否需要查询本地 Markdown 笔记
如果需要，调用 search_notes 工具
工具返回匹配片段
Agent 根据片段回答
如果用户问计算问题，调用 calculator
如果没有依据，说明没有找到，不编造
```

### 9.2 为什么选这个方向

这个场景最适合作为入门 Demo，原因是：

1. 不需要数据库；
2. 不需要前端；
3. 不需要复杂 RAG；
4. 工具数量少；
5. 本地文件可控；
6. 非高风险操作；
7. 很容易观察 ReAct 循环；
8. 同一个工具层可以同时给 LangChain 和 LangGraph 使用。

它能完整体现：

```text
用户问题
→ 模型判断
→ 工具选择
→ 工具调用
→ Observation
→ 二次推理
→ 最终回答
```

### 9.3 Demo 功能边界

第一版不要做这些：

```text
不要做向量数据库
不要做 PDF 解析
不要做 Web 前端
不要做用户登录
不要做复杂 Memory
不要做 Multi-Agent
不要做自动写文件
```

第一版只做：

```text
读取本地 Markdown
关键词检索
简单计算器
命令行交互
打印消息轨迹
```

---

## 10. Demo 项目结构

推荐目录：

```text
react-notes-agent/
  README.md
  requirements.txt
  .env.example

  data/
    notes/
      react.md
      langchain.md
      langgraph.md

  src/
    __init__.py
    tools.py
    langchain_agent.py
    langgraph_agent.py
    run_langchain.py
    run_langgraph.py

  tests/
    test_tools.py

  docs/
    learning_log.md
    react_trace_examples.md
```

### 10.1 每个文件的作用

| 文件 | 作用 |
|---|---|
| README.md | 项目说明、运行方法、Demo 目标 |
| requirements.txt | Python 依赖 |
| .env.example | API Key 和 tracing 配置示例 |
| data/notes/*.md | 本地学习笔记 |
| src/tools.py | 工具定义，供两个版本复用 |
| src/langchain_agent.py | LangChain 版本 Agent |
| src/langgraph_agent.py | LangGraph 版本 Agent |
| src/run_langchain.py | 命令行运行 LangChain 版本 |
| src/run_langgraph.py | 命令行运行 LangGraph 版本 |
| tests/test_tools.py | 工具单元测试 |
| docs/learning_log.md | 学习记录 |
| docs/react_trace_examples.md | 保存典型 ReAct 轨迹 |

### 10.2 requirements.txt

```txt
langchain
langgraph
langchain-openai
langsmith
python-dotenv
pytest
```

如果你用 Anthropic 模型，可以加：

```txt
langchain-anthropic
```

---

## 11. LangChain 版本实现方案

### 11.1 实现目标

LangChain 版本的目标是：

```text
用最少代码跑通 Agent + tools
快速理解工具调用链路
观察 create_agent 的输入输出
```

### 11.2 运行入口

```python
# src/run_langchain.py
from dotenv import load_dotenv
from src.langchain_agent import agent

load_dotenv()

while True:
    query = input("\nUser: ")
    if query.lower() in {"exit", "quit"}:
        break

    result = agent.invoke({
        "messages": [{"role": "user", "content": query}]
    })

    print("\n--- Trace Messages ---")
    for msg in result["messages"]:
        print(msg)

    print("\n--- Final Answer ---")
    print(result["messages"][-1].content)
```

### 11.3 适合观察的问题

你可以测试：

```text
问题 1：根据我的笔记，ReAct 的核心循环是什么？
预期：调用 search_notes

问题 2：2 + 3 * 4 等于多少？
预期：调用 calculator

问题 3：你好，今天适合学习什么？
预期：可能不调用工具，直接回答

问题 4：根据我的笔记，量子退火和 ReAct 有什么关系？
预期：search_notes 可能返回 NO_MATCH_FOUND，最终说明没有依据
```

### 11.4 判断是否达标

LangChain 版本达标标准：

```text
能启动
能调用 search_notes
能调用 calculator
工具无结果时不编造
能打印中间消息
能说明最终答案来自工具结果
```

---

## 12. LangGraph 版本实现方案

### 12.1 实现目标

LangGraph 版本不是为了代码更短，而是为了看清楚 ReAct 循环：

```text
agent node
→ conditional edge
→ tools node
→ agent node
→ END
```

### 12.2 推荐实现方式

使用：

```python
StateGraph
MessagesState
ToolNode
conditional_edges
```

### 12.3 运行入口

```python
# src/run_langgraph.py
from dotenv import load_dotenv
from src.langgraph_agent import graph

load_dotenv()

while True:
    query = input("\nUser: ")
    if query.lower() in {"exit", "quit"}:
        break

    result = graph.invoke({
        "messages": [{"role": "user", "content": query}]
    })

    print("\n--- Trace Messages ---")
    for msg in result["messages"]:
        print(msg)

    print("\n--- Final Answer ---")
    print(result["messages"][-1].content)
```

### 12.4 判断是否达标

LangGraph 版本达标标准：

```text
能看到 agent 节点输出 tool_calls
能看到 tools 节点返回 ToolMessage
能看到 tools 节点之后再次回到 agent 节点
能在无 tool_calls 时进入 END
```

你也可以在节点里加日志：

```python
def agent_node(state):
    print("[NODE] agent")
    ...

def should_continue(state):
    print("[ROUTER] should_continue")
    ...
```

这样最直观。

---

## 13. 运行与验证方法

### 13.1 初始化项目

```bash
mkdir react-notes-agent
cd react-notes-agent
python -m venv .venv
```

Windows PowerShell：

```bash
.venv\Scripts\activate
```

macOS / Linux：

```bash
source .venv/bin/activate
```

安装依赖：

```bash
pip install -r requirements.txt
```

### 13.2 配置环境变量

创建 `.env`：

```bash
OPENAI_API_KEY=你的_api_key
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=你的_langsmith_key
```

如果暂时不用 LangSmith，可以先不配置 tracing。

### 13.3 准备笔记文件

`data/notes/react.md`：

```markdown
# ReAct

ReAct 是 Reasoning and Acting 的组合。
它通过 Thought、Action、Observation、Final Answer 的循环，
让模型在推理过程中调用外部工具，并根据工具结果继续更新判断。
```

`data/notes/langchain.md`：

```markdown
# LangChain

LangChain 适合快速构建 LLM 应用和简单 Agent。
当前版本推荐使用 create_agent 构建工具调用 Agent。
```

`data/notes/langgraph.md`：

```markdown
# LangGraph

LangGraph 使用 StateGraph、Node、Edge 和 Conditional Edge 表达状态化 Agent 流程。
它适合复杂流程控制、多 Agent 编排、人工审批和长期运行任务。
```

### 13.4 运行 LangChain 版本

```bash
python -m src.run_langchain
```

测试：

```text
根据我的笔记，ReAct 的核心循环是什么？
```

预期：

```text
模型调用 search_notes
工具返回 react.md 内容
模型总结 ReAct 核心循环
```

### 13.5 运行 LangGraph 版本

```bash
python -m src.run_langgraph
```

测试同样问题：

```text
根据我的笔记，LangGraph 为什么适合复杂 Agent？
```

预期：

```text
agent 节点判断需要 search_notes
tools 节点执行 search_notes
agent 节点根据 Observation 输出答案
```

### 13.6 如何验证 Agent 真的发生了 ReAct 循环

至少用三种方式验证：

#### 方法 1：打印 messages

看是否出现：

```text
AIMessage(tool_calls=[...])
ToolMessage(content=...)
AIMessage(content=最终回答)
```

#### 方法 2：节点日志

LangGraph 中打印：

```text
[NODE] agent
[ROUTER] tools
[NODE] tools
[NODE] agent
[ROUTER] end
```

#### 方法 3：LangSmith Trace

观察 trace 链路：

```text
Model
Tool
Model
```

如果只有一个 Model，没有 Tool，则说明没有发生工具调用。

---

## 14. 后续扩展方向

完成最小 Demo 后，可以按下面顺序扩展，不要一次全加。

### 14.1 第一层扩展：更好的检索

把关键词检索升级为：

```text
文档切分
embedding
向量检索
rerank
引用片段
```

技术选型：

```text
Chroma / FAISS / Qdrant
LangChain retriever
```

### 14.2 第二层扩展：结构化工具返回

当前工具返回字符串，后续可以改成 JSON：

```json
{
  "matched": true,
  "source": "react.md",
  "snippets": ["..."],
  "score": 0.82
}
```

这样模型更不容易误解 Observation。

### 14.3 第三层扩展：异常处理

加入：

```text
工具超时
文件不存在
无匹配结果
重复调用检测
max_iterations
兜底回答
```

### 14.4 第四层扩展：评估集

构造 20 条测试问题：

```json
{
  "case_id": "R001",
  "query": "ReAct 的核心循环是什么？",
  "expected_tool": "search_notes",
  "expected_source": "react.md",
  "expected_answer_points": ["Reasoning", "Acting", "Observation"]
}
```

评估指标：

```text
工具选择准确率
答案是否基于笔记
无依据拒答率
平均工具调用次数
平均延迟
```

### 14.5 第五层扩展：迁移到业务场景

把 Markdown 笔记助手迁移成简单订单查询助手：

```text
search_notes → search_policy
calculator → calculate_refund_amount
get_time → query_order_status
```

这样就能自然过渡到你的长期项目：

```text
OrderFlow-Agent：面向电商交易履约的可验证多 Agent 决策系统
```

---

## 15. 学习路线与检查清单

### 15.1 7 天学习安排

#### Day 1：理解 ReAct

任务：

```text
读 Google ReAct 博客
读 ReAct 论文 Abstract + Introduction
画出 Thought / Action / Observation 循环
```

产出：

```text
docs/react_basic_notes.md
```

检查：

```text
能用自己的话解释 ReAct 为什么要结合 Reasoning 和 Acting
```

#### Day 2：理解 Tool Calling

任务：

```text
读 OpenAI Function Calling 文档
读 Anthropic Tool Use 文档
写一个无框架 tool calling 伪代码
```

产出：

```text
docs/tool_calling_notes.md
```

检查：

```text
能解释模型为什么不直接执行工具
能解释 tool call 和 tool output 的关系
```

#### Day 3：LangChain 最小 Agent

任务：

```text
安装依赖
实现 tools.py
实现 langchain_agent.py
跑通 search_notes 和 calculator
```

产出：

```text
src/tools.py
src/langchain_agent.py
```

检查：

```text
能打印出 tool call 和最终回答
```

#### Day 4：LangGraph 最小 Agent

任务：

```text
学习 StateGraph / Node / Edge / Conditional Edge
用 LangGraph 重写同样 Demo
```

产出：

```text
src/langgraph_agent.py
```

检查：

```text
能说清 agent node、tools node、conditional edge 分别做什么
```

#### Day 5：对比两个版本

任务：

```text
记录同一问题在两个版本中的执行轨迹
比较代码复杂度、可控性、可扩展性
```

产出：

```text
docs/langchain_vs_langgraph_trace.md
```

检查：

```text
能说明为什么 LangGraph 更适合复杂流程
```

#### Day 6：加入异常和约束

任务：

```text
加入 NO_MATCH_FOUND 处理
加入重复工具调用检测思路
加入最大轮次说明
```

产出：

```text
docs/failure_cases.md
```

检查：

```text
Agent 不会在没有资料时编造答案
```

#### Day 7：整理 README 和学习复盘

任务：

```text
写 README
整理运行截图或 trace
写学习总结
```

产出：

```text
README.md
docs/learning_log.md
```

检查：

```text
别人能根据 README 跑通 Demo
你能在面试中讲清整个 ReAct 链路
```

### 15.2 能力检查清单

#### ReAct 理解

- [ ] 我能解释 ReAct 是什么。
- [ ] 我能解释 Reasoning 和 Acting 为什么要交替。
- [ ] 我能解释 Thought / Action / Observation / Final Answer。
- [ ] 我能说出 ReAct 相比普通 Chain 的优势。
- [ ] 我能说出 ReAct 的常见失败模式。

#### 工程实现

- [ ] 我能设计一个工具的名称、描述、输入和输出。
- [ ] 我能解释工具描述为什么会影响模型选择。
- [ ] 我能处理工具无结果、参数错误和异常。
- [ ] 我能设置最大迭代次数或设计停止条件。
- [ ] 我能让 Agent 在没有合适工具时拒绝编造。

#### LangChain

- [ ] 我能用 create_agent 构建最小工具 Agent。
- [ ] 我能解释 tools、system_prompt、messages 的作用。
- [ ] 我能打印并理解 Agent 的中间消息。
- [ ] 我知道 create_react_agent / AgentExecutor 是经典写法，但当前更推荐 create_agent。

#### LangGraph

- [ ] 我能解释 StateGraph、Node、Edge、Conditional Edge、State。
- [ ] 我能画出 ReAct 在 LangGraph 中的循环图。
- [ ] 我能用 ToolNode 执行工具。
- [ ] 我能写 should_continue 条件路由。
- [ ] 我能解释为什么 LangGraph 更适合复杂 Agent 编排。

#### Demo

- [ ] 我能运行 LangChain 版本。
- [ ] 我能运行 LangGraph 版本。
- [ ] 我能用同一个问题触发工具调用。
- [ ] 我能验证 Observation 被最终回答使用。
- [ ] 我能写出下一步扩展计划。

---

## 16. 最终建议

你现在的学习重点不是“框架 API 背熟”，而是建立 Agent 工程直觉：

```text
模型不是万能执行器
工具不是随便暴露的函数
ReAct 不是让模型无限自由发挥
Agent 的关键是：状态、工具、约束、循环、观测和兜底
```

本阶段最重要的产出不是代码量，而是下面三个东西：

1. 一个能跑通的 Markdown 笔记检索 ReAct Demo；
2. 一份 LangChain 与 LangGraph 的执行轨迹对比；
3. 一份你自己的 ReAct 适用边界总结。

如果这三个东西完成了，你就真正进入了 Agent 工程学习，而不是停留在“会调框架”的层面。
