# LangGraph Markdown 笔记检索 ReAct Agent 技术文档

> 文档用途：作为 AI Coding 工具的项目实现指导文件。  
> 项目定位：用最小工程量实现一个可运行、可观察、可测试的 LangGraph ReAct Demo。  
> 推荐项目名：`react-notes-agent`  
> 核心目标：让学习者通过本地 Markdown 笔记检索场景，真正看清 `Agent 节点 → 工具节点 → Observation → Agent 再推理 → 最终回答` 的完整循环。  
> 本版模型配置：优先支持千问 Qwen 与 DeepSeek V4 Pro，通过 OpenAI-compatible API 统一接入。

---

## 1. 项目背景

本项目来自 ReAct 范式学习阶段的最小实践 Demo。它不是完整 RAG 系统，也不是生产级知识库系统，而是一个用于理解 LangGraph 工具调用循环的教学项目。

项目聚焦三个问题：

1. LLM 如何判断是否需要调用工具；
2. LangGraph 如何用状态图表达 ReAct 循环；
3. 如何通过日志、messages 和测试验证工具调用确实发生。

本项目第一版只实现命令行版本，不做 Web 前端、不接数据库、不做向量检索、不做复杂 Memory。

---

## 2. 项目目标

### 2.1 功能目标

实现一个命令行学习助手，支持用户询问本地 Markdown 笔记中的内容。

用户输入示例：

```text
根据我的笔记，ReAct 的核心循环是什么？
```

系统执行流程：

```text
用户问题
  ↓
LangGraph agent 节点调用 LLM
  ↓
LLM 判断需要查询本地笔记
  ↓
生成 search_notes 工具调用
  ↓
ToolNode 执行 search_notes
  ↓
工具返回匹配片段 Observation
  ↓
回到 agent 节点
  ↓
LLM 根据 Observation 生成最终回答
```

### 2.2 学习目标

完成后应能理解：

1. `StateGraph` 如何组织 Agent 流程；
2. `MessagesState` 如何保存 HumanMessage、AIMessage、ToolMessage；
3. `ToolNode` 如何执行模型生成的工具调用；
4. `conditional_edges` 如何决定继续调用工具还是结束；
5. ReAct 循环在工程中如何被显式表达；
6. 如何用测试和 trace 验证 Agent 行为。

### 2.3 非目标

第一版不实现以下功能：

```text
不做向量数据库
不做 embedding
不做 PDF 解析
不做 Web UI
不做用户登录
不做多轮长期记忆
不做复杂权限控制
不做 Multi-Agent
不做自动写文件或修改笔记
```

---

## 3. 技术选型

### 3.1 核心依赖

```text
Python 3.11+
LangGraph
LangChain
langchain-openai
python-dotenv
pytest
```

说明：

1. 本项目优先通过 OpenAI-compatible API 接入千问和 DeepSeek V4 Pro，因此仍然使用 `langchain-openai` 的 `ChatOpenAI` 作为统一模型封装。
2. 千问 DashScope 和 DeepSeek API 都可以通过 `base_url + api_key + model` 的方式接入，主体 LangGraph 代码不需要因为换模型而改动。
3. 如后续希望直接使用 LangChain 的原生集成，也可以扩展 `langchain-community` 的 `ChatTongyi` 或 `langchain-deepseek` 的 `ChatDeepSeek`，但第一版不建议增加多套模型适配逻辑。

### 3.2 可选依赖

```text
LangSmith：用于可视化 trace
rich：用于美化命令行输出，第一版可不加
```

### 3.3 模型选择

本项目默认不使用 OpenAI 官方模型，而是优先支持下面两类模型：

```text
1. 千问 Qwen：通过阿里云 DashScope / Model Studio 的 OpenAI-compatible 接口调用
2. DeepSeek V4 Pro：通过 DeepSeek OpenAI-compatible 接口调用
```

推荐第一版采用统一配置方式：

```text
MODEL_PROVIDER=qwen 或 deepseek
LLM_API_KEY=模型平台 API Key
LLM_BASE_URL=模型平台 OpenAI-compatible base_url
LLM_MODEL=具体模型名
```

推荐默认配置：

```text
MODEL_PROVIDER=deepseek
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-v4-pro
```

千问示例配置：

```text
MODEL_PROVIDER=qwen
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
```

如果人在海外或使用国际版阿里云 Model Studio，可以把千问的 `LLM_BASE_URL` 改成：

```text
https://dashscope-intl.aliyuncs.com/compatible-mode/v1
```

AI Coding 时不要把模型名、API Key、base_url 写死在多个文件里，统一放在 `src/config.py` 和 `.env` 中。

注意：

1. `.env` 保存真实 API Key，不提交 GitHub。
2. `.env.example` 只写占位符，用于说明配置格式。
3. DeepSeek V4 Pro 的模型名统一写成 `deepseek-v4-pro`。
4. 千问模型名可先用 `qwen-plus`，后续可按账号权限替换为其他 Qwen 模型。
5. 由于本项目依赖工具调用能力，选择模型时必须优先确认该模型支持 tool calling / function calling。

### 3.4 模型接入策略

第一版采用“统一 OpenAI-compatible 接口”的原因：

```text
LangGraph 不关心你用哪个模型，它只关心 agent 节点是否返回 AIMessage，以及 AIMessage 里是否包含 tool_calls。

因此模型接入应该被封装在 src/config.py 的 get_chat_model() 中：

.env
  ↓
src/config.py 读取 MODEL_PROVIDER / LLM_API_KEY / LLM_BASE_URL / LLM_MODEL
  ↓
get_chat_model() 返回 ChatOpenAI 实例
  ↓
langgraph_agent.py 执行 get_chat_model().bind_tools(tools)
```

不要在 `src/langgraph_agent.py` 中直接写：

```python
ChatOpenAI(model="deepseek-v4-pro", api_key="sk-xxx")
```

正确方式是：

```python
model = get_chat_model().bind_tools(tools)
```

这样后续从 DeepSeek V4 Pro 切换到千问 Qwen，只需要改 `.env`，不需要改状态图、工具节点或路由逻辑。

---

## 4. 总体架构

### 4.1 架构图

```text
┌──────────────────┐
│ User CLI Input   │
└────────┬─────────┘
         ↓
┌──────────────────┐
│ LangGraph Graph  │
└────────┬─────────┘
         ↓
┌──────────────────┐
│ agent node       │
│ LLM + bind_tools │
└────────┬─────────┘
         ↓
┌──────────────────────────┐
│ should_continue router   │
└───────┬──────────┬───────┘
        │          │
        │ tool     │ no tool
        ↓          ↓
┌──────────────────┐   ┌─────┐
│ tools node       │   │ END │
│ ToolNode         │   └─────┘
└────────┬─────────┘
         ↓
┌──────────────────┐
│ search_notes     │
│ calculator       │
└────────┬─────────┘
         ↓
┌──────────────────┐
│ ToolMessage      │
└────────┬─────────┘
         ↓
   back to agent
```

### 4.2 ReAct 映射关系

| ReAct 概念 | LangGraph 实现 |
|---|---|
| Thought / 判断 | `agent_node` 中 LLM 基于 messages 做决策 |
| Action | LLM 输出 `tool_calls` |
| Observation | `ToolNode` 执行工具后生成 `ToolMessage` |
| Loop | `tools -> agent` 的回边 |
| Final Answer | 最后一条无 `tool_calls` 的 AIMessage |

注意：不要强制模型输出完整 Thought。工程上只需要记录工具选择、工具参数、工具返回和最终回答即可。

---

## 5. 项目目录结构

请 AI Coding 工具按照下面结构生成项目：

```text
react-notes-agent/
  README.md
  requirements.txt
  .env.example
  .gitignore

  data/
    notes/
      react.md
      langchain.md
      langgraph.md

  src/
    __init__.py
    config.py
    tools.py
    langgraph_agent.py
    run_langgraph.py
    trace_utils.py

  tests/
    __init__.py
    test_tools.py
    test_graph_flow.py

  docs/
    ai_coding_spec.md
    trace_examples.md
```

---

## 6. 文件职责说明

| 文件 | 职责 |
|---|---|
| `README.md` | 项目介绍、安装方法、运行命令、测试问题 |
| `requirements.txt` | 依赖列表 |
| `.env.example` | 环境变量模板 |
| `.gitignore` | 忽略 `.env`、虚拟环境、缓存文件 |
| `data/notes/*.md` | 示例 Markdown 学习笔记 |
| `src/config.py` | 读取模型名、API Key、笔记路径等配置 |
| `src/tools.py` | 定义 `search_notes` 和 `calculator` 工具 |
| `src/langgraph_agent.py` | 构建 LangGraph 状态图 |
| `src/run_langgraph.py` | 命令行交互入口 |
| `src/trace_utils.py` | 打印 messages、tool_calls、ToolMessage 的辅助函数 |
| `tests/test_tools.py` | 工具单元测试 |
| `tests/test_graph_flow.py` | 图流程基础测试，可用 monkeypatch 或 mock model |
| `docs/trace_examples.md` | 保存典型运行轨迹 |

---

## 7. 环境变量设计

`.env.example` 内容：

```bash
# =========================================================
# LLM Provider
# =========================================================
# 可选值：qwen / deepseek / openai_compatible
MODEL_PROVIDER=deepseek

# 真实 API Key 写到本地 .env 中，不要提交 GitHub
LLM_API_KEY=your_model_api_key

# DeepSeek V4 Pro 默认配置
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-v4-pro

# 千问 DashScope 中国北京区域示例
# MODEL_PROVIDER=qwen
# LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
# LLM_MODEL=qwen-plus

# 千问 DashScope 国际站新加坡区域示例
# MODEL_PROVIDER=qwen
# LLM_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
# LLM_MODEL=qwen-plus

# =========================================================
# Local Notes
# =========================================================
NOTES_DIR=data/notes

# =========================================================
# Optional: LangSmith tracing
# =========================================================
LANGSMITH_TRACING=false
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=react-notes-agent
```

实现要求：

1. `.env` 不提交 Git；
2. `LLM_API_KEY` 缺失时，运行入口应给出清晰错误提示；
3. `LLM_BASE_URL` 缺失时，运行入口应给出清晰错误提示；
4. `LLM_MODEL` 缺失时，运行入口应给出清晰错误提示；
5. `NOTES_DIR` 默认值为 `data/notes`；
6. 模型名、API Key、base_url 都从环境变量读取，不要散落在业务代码中；
7. `MODEL_PROVIDER` 只作为语义标识和日志标识，真正调用参数以 `LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL` 为准。

---

## 8. 示例笔记内容

### 8.1 `data/notes/react.md`

```markdown
# ReAct

ReAct 是 Reasoning and Acting 的组合。
它通过 Thought、Action、Observation、Final Answer 的循环，
让模型在推理过程中调用外部工具，并根据工具结果继续更新判断。

ReAct 适合需要查询外部信息、调用工具、逐步观察环境结果的任务。
它不适合高风险、强流程约束、必须严格审批的业务动作完全自动化。
```

### 8.2 `data/notes/langchain.md`

```markdown
# LangChain

LangChain 适合快速构建 LLM 应用和简单 Agent。
它提供 Agent、Tool、Model、Prompt 等封装，适合快速原型验证。

对于复杂状态流转、人工审批、长期运行任务，单纯使用高级 Agent 封装可能会不够显式。
```

### 8.3 `data/notes/langgraph.md`

```markdown
# LangGraph

LangGraph 使用 StateGraph、Node、Edge 和 Conditional Edge 表达状态化 Agent 流程。
它适合复杂流程控制、多 Agent 编排、人工审批和长期运行任务。

在 ReAct 场景中，agent node 负责调用模型，tools node 负责执行工具，
conditional edge 根据最后一条 AIMessage 是否包含 tool_calls 决定继续调用工具还是结束。
```

---

## 9. 工具设计

第一版只实现两个工具：

```text
search_notes(query: str) -> str
calculator(expression: str) -> str
```

### 9.1 `search_notes`

#### 功能

从 `data/notes` 下读取 Markdown 文件，基于关键词做简单匹配，返回最相关片段。

#### 工具描述要求

工具描述必须清楚告诉模型：

```text
当用户问题涉及本地学习笔记、ReAct、LangChain、LangGraph 时使用。
不要把它用于通用聊天或数学计算。
如果没有匹配内容，返回 NO_MATCH_FOUND。
```

#### 检索逻辑

第一版使用简单关键词检索，不做 embedding。

实现建议：

1. 读取 `NOTES_DIR` 下所有 `.md` 文件；
2. 将 query 按空格、中文标点、英文标点切分；
3. 对每个文件统计关键词命中次数；
4. 返回命中分数最高的前 2 个片段；
5. 每个片段包含文件名和内容摘要；
6. 无命中返回 `NO_MATCH_FOUND`。

#### 返回格式

有结果时：

```text
SOURCE: react.md
CONTENT:
ReAct 是 Reasoning and Acting 的组合。它通过 Thought、Action、Observation、Final Answer 的循环...

SOURCE: langgraph.md
CONTENT:
在 ReAct 场景中，agent node 负责调用模型，tools node 负责执行工具...
```

无结果时：

```text
NO_MATCH_FOUND
```

异常时：

```text
ERROR: notes directory not found: data/notes
```

### 9.2 `calculator`

#### 功能

执行简单数学表达式计算。

#### 安全要求

不要直接对任意字符串使用不受控 `eval`。

允许字符白名单：

```text
数字
空格
+ - * / % ** ( ) .
```

如果出现其他字符，返回：

```text
ERROR: invalid expression
```

#### 示例

输入：

```text
2 + 3 * 4
```

输出：

```text
14
```

---

## 10. LangGraph 实现设计

### 10.1 核心组件

`src/langgraph_agent.py` 需要包含：

```text
1. tools 列表
2. model 初始化
3. model.bind_tools(tools)
4. SYSTEM_PROMPT
5. agent_node(state)
6. ToolNode(tools)
7. should_continue(state)
8. StateGraph(MessagesState)
9. graph.compile()
```

### 10.2 节点定义

#### `agent_node`

职责：

1. 接收当前 `MessagesState`；
2. 在 messages 前加入 system prompt；
3. 调用绑定工具后的模型；
4. 返回新的 AIMessage。

伪代码：

```python
def agent_node(state: MessagesState):
    print(f"[NODE] agent | provider={MODEL_PROVIDER} | model={LLM_MODEL}")
    messages = [SYSTEM_PROMPT] + state["messages"]
    response = model.invoke(messages)
    return {"messages": [response]}
```

#### `tools_node`

职责：

1. 读取最后一条 AIMessage 中的 tool_calls；
2. 执行对应工具；
3. 将工具结果包装成 ToolMessage；
4. 写回 messages。

实现使用 LangGraph 预置：

```python
tool_node = ToolNode(tools)
```

#### `should_continue`

职责：

1. 读取最后一条消息；
2. 如果存在 `tool_calls`，返回 `tools`；
3. 否则返回 `__end__`。

伪代码：

```python
def should_continue(state: MessagesState) -> Literal["tools", "__end__"]:
    print("[ROUTER] should_continue")
    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", None):
        print("[ROUTER] route=tools")
        return "tools"
    print("[ROUTER] route=end")
    return "__end__"
```

### 10.3 图结构

```python
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
```

### 10.4 循环控制

第一版可以依赖 LangGraph 的默认递归限制，但建议在调用时显式设置：

```python
result = graph.invoke(
    {"messages": [{"role": "user", "content": query}]},
    config={"recursion_limit": 6},
)
```

目的：防止模型反复调用工具导致无限循环。

---

## 11. Prompt 设计

### 11.1 System Prompt

建议内容：

```text
你是一个 ReAct 学习助手，负责回答用户关于本地学习笔记的问题。

你可以使用以下工具：
1. search_notes：查询本地 Markdown 学习笔记。
2. calculator：执行简单数学计算。

规则：
1. 如果用户问题涉及 ReAct、LangChain、LangGraph 或“我的笔记”，必须优先调用 search_notes。
2. 如果用户问题是数学计算，调用 calculator。
3. 如果 search_notes 返回 NO_MATCH_FOUND，不要编造笔记内容，应明确说明没有在本地笔记中找到依据。
4. 如果工具返回 ERROR，应说明工具执行失败，并给出可操作的排查建议。
5. 最终回答必须简洁，并尽量说明依据来自哪个工具返回。
6. 不要为了同一个问题反复调用同一个工具超过 2 次。
```

### 11.2 输出风格

最终回答建议格式：

```text
根据本地笔记，...

依据：search_notes 返回的 react.md / langgraph.md 片段。
```

无结果时：

```text
我没有在本地 Markdown 笔记中找到这个问题的依据，因此不能根据笔记回答。你可以补充相关笔记后再查询。
```

---

## 12. 命令行入口设计

`src/run_langgraph.py` 需要实现：

1. 加载 `.env`；
2. 打印启动说明；
3. 循环读取用户输入；
4. 支持 `exit` / `quit` 退出；
5. 调用 graph；
6. 打印 trace messages；
7. 打印最终回答。

示例输出：

```text
React Notes Agent started.
Type exit or quit to stop.

User: 根据我的笔记，ReAct 的核心循环是什么？

[NODE] agent
[ROUTER] should_continue
[ROUTER] route=tools
[NODE] tools
[NODE] agent
[ROUTER] should_continue
[ROUTER] route=end

--- Trace Messages ---
HumanMessage: 根据我的笔记，ReAct 的核心循环是什么？
AIMessage tool_calls: search_notes({"query": "ReAct 核心循环"})
ToolMessage: SOURCE: react.md ...
AIMessage: 根据本地笔记，ReAct 的核心循环是...

--- Final Answer ---
根据本地笔记，ReAct 的核心循环是 Thought、Action、Observation、Final Answer...
```

---

## 13. Trace 打印要求

`src/trace_utils.py` 实现一个函数：

```python
def print_messages(messages: list) -> None:
    ...
```

打印规则：

1. HumanMessage：打印用户内容；
2. AIMessage：如果有 `tool_calls`，打印工具名和参数；否则打印 content；
3. ToolMessage：打印工具返回内容前 500 字符；
4. 其他消息类型：打印类型名和摘要。

目标是让学习者清楚看到：

```text
HumanMessage
AIMessage(tool_calls)
ToolMessage
AIMessage(final answer)
```

---

## 14. 测试设计

### 14.1 工具测试

`tests/test_tools.py`

必须覆盖：

1. `search_notes("ReAct")` 能返回 `react.md`；
2. `search_notes("LangGraph")` 能返回 `langgraph.md`；
3. `search_notes("不存在的概念 xyz")` 返回 `NO_MATCH_FOUND`；
4. `calculator("2 + 3 * 4")` 返回 `14`；
5. `calculator("__import__('os').system('rm -rf /')")` 返回错误。

### 14.2 图流程测试

`tests/test_graph_flow.py`

第一版可以只做轻量测试：

1. graph 对象能成功 import；
2. `should_continue` 在 AIMessage 有 tool_calls 时返回 `tools`；
3. `should_continue` 在 AIMessage 无 tool_calls 时返回 `__end__`。

不要在单元测试中强依赖真实 LLM API。真实模型调用放到手动集成测试。

---

## 15. 验收标准

### 15.1 基础验收

项目必须满足：

```text
能安装依赖
能通过 pytest
能启动命令行
能查询本地 Markdown
能进行简单计算
能打印 ReAct trace
无匹配结果时不编造
```

### 15.2 ReAct 行为验收

输入：

```text
根据我的笔记，ReAct 的核心循环是什么？
```

必须观察到：

```text
HumanMessage
AIMessage with tool_calls: search_notes
ToolMessage with react.md content
AIMessage final answer
```

输入：

```text
2 + 3 * 4 等于多少？
```

应该观察到：

```text
AIMessage with tool_calls: calculator
ToolMessage: 14
AIMessage final answer
```

输入：

```text
根据我的笔记，量子退火和 ReAct 有什么关系？
```

应该观察到：

```text
AIMessage with tool_calls: search_notes
ToolMessage: NO_MATCH_FOUND
AIMessage: 没有在本地笔记中找到依据
```

---

## 16. AI Coding 实现步骤

请 AI Coding 工具按顺序实现，不要一次性加入复杂功能。

### Step 1：生成项目骨架

创建目录、空文件、`.env.example`、`.gitignore`、`requirements.txt`。

### Step 2：写入示例 Markdown 笔记

创建：

```text
data/notes/react.md
data/notes/langchain.md
data/notes/langgraph.md
```

### Step 3：实现配置模块

实现 `src/config.py`：

```text
读取 MODEL_PROVIDER
读取 LLM_API_KEY
读取 LLM_BASE_URL
读取 LLM_MODEL
读取 NOTES_DIR
提供默认值
检查路径
提供 get_chat_model() 工厂函数
```

### Step 4：实现工具模块

实现 `src/tools.py`：

```text
search_notes
calculator
```

并先写测试通过。

### Step 5：实现 LangGraph Agent

实现 `src/langgraph_agent.py`：

```text
model 初始化
bind_tools
action node
tool node
conditional router
graph compile
```

### Step 6：实现命令行入口

实现 `src/run_langgraph.py`，支持交互输入和 trace 打印。

### Step 7：实现 trace 工具

实现 `src/trace_utils.py`，清晰打印消息轨迹。

### Step 8：补充 README

README 必须包含：

```text
项目目标
安装步骤
环境变量
运行命令
测试命令
示例问题
预期 trace
常见问题
```

### Step 9：跑测试和手动验证

执行：

```bash
pytest
python -m src.run_langgraph
```

---

## 17. 推荐核心代码骨架

### 17.1 `src/config.py`

```python
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "deepseek").strip().lower()
LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com").strip()
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-v4-pro").strip()
NOTES_DIR = Path(os.getenv("NOTES_DIR", "data/notes"))


def validate_llm_config() -> None:
    """Validate required LLM environment variables before running the agent."""
    missing = []
    if not LLM_API_KEY:
        missing.append("LLM_API_KEY")
    if not LLM_BASE_URL:
        missing.append("LLM_BASE_URL")
    if not LLM_MODEL:
        missing.append("LLM_MODEL")

    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(
            f"Missing required LLM config: {joined}. "
            "Please copy .env.example to .env and fill in your model API configuration."
        )


def get_chat_model() -> ChatOpenAI:
    """Create the chat model used by LangGraph.

    The project uses OpenAI-compatible APIs for both Qwen and DeepSeek V4 Pro.
    Therefore the graph code can stay unchanged when switching providers.
    """
    validate_llm_config()
    return ChatOpenAI(
        model=LLM_MODEL,
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        temperature=0,
    )
```

### 17.1.1 `.env` 配置示例

DeepSeek V4 Pro：

```bash
MODEL_PROVIDER=deepseek
LLM_API_KEY=sk-你的DeepSeekKey
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-v4-pro
NOTES_DIR=data/notes
```

千问 Qwen，DashScope 中国北京区域：

```bash
MODEL_PROVIDER=qwen
LLM_API_KEY=sk-你的DashScopeKey
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
NOTES_DIR=data/notes
```

千问 Qwen，DashScope 国际站新加坡区域：

```bash
MODEL_PROVIDER=qwen
LLM_API_KEY=sk-你的DashScopeKey
LLM_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
NOTES_DIR=data/notes
```

说明：

1. `MODEL_PROVIDER` 只是用于日志和可读性。
2. `LLM_BASE_URL` 决定请求发往哪个平台。
3. `LLM_MODEL` 决定具体使用哪个模型。
4. DeepSeek V4 Pro 默认使用 `deepseek-v4-pro`。
5. 千问默认使用 `qwen-plus`，后续可换成账号支持的其他 Qwen 模型。

### 17.2 `src/tools.py`

```python
import re
from pathlib import Path
from langchain_core.tools import tool
from src.config import NOTES_DIR


def _tokenize(text: str) -> list[str]:
    tokens = re.split(r"[\s,，。！？；;:.：、()（）\[\]{}]+", text.lower())
    return [t for t in tokens if t]


def _safe_preview(text: str, max_len: int = 500) -> str:
    text = " ".join(text.split())
    return text[:max_len]


@tool
def search_notes(query: str) -> str:
    """Search local Markdown learning notes by keyword.

    Use this tool when the user asks about local notes, ReAct, LangChain, or LangGraph.
    Do not use it for arithmetic or general chat.
    Return NO_MATCH_FOUND if no relevant note is found.
    """
    notes_dir = Path(NOTES_DIR)
    if not notes_dir.exists():
        return f"ERROR: notes directory not found: {notes_dir}"

    query_tokens = _tokenize(query)
    if not query_tokens:
        return "NO_MATCH_FOUND"

    candidates: list[tuple[int, str, str]] = []

    for path in notes_dir.glob("*.md"):
        content = path.read_text(encoding="utf-8")
        lowered = content.lower()
        score = sum(lowered.count(token) for token in query_tokens)
        if score > 0:
            candidates.append((score, path.name, _safe_preview(content)))

    if not candidates:
        return "NO_MATCH_FOUND"

    candidates.sort(key=lambda item: item[0], reverse=True)
    results = []
    for score, filename, preview in candidates[:2]:
        results.append(f"SOURCE: {filename}\nSCORE: {score}\nCONTENT:\n{preview}")
    return "\n\n".join(results)


@tool
def calculator(expression: str) -> str:
    """Calculate a simple arithmetic expression.

    Use this tool only for arithmetic expressions containing numbers and operators.
    """
    if not re.fullmatch(r"[0-9\s+\-*/%.()]+", expression):
        return "ERROR: invalid expression"
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as exc:
        return f"ERROR: calculation failed: {exc}"
```

### 17.3 `src/langgraph_agent.py`

```python
from typing import Literal

from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode

from src.config import MODEL_PROVIDER, LLM_MODEL, get_chat_model
from src.tools import search_notes, calculator


tools = [search_notes, calculator]

model = get_chat_model().bind_tools(tools)

SYSTEM_PROMPT = {
    "role": "system",
    "content": """
你是一个 ReAct 学习助手，负责回答用户关于本地学习笔记的问题。

你可以使用以下工具：
1. search_notes：查询本地 Markdown 学习笔记。
2. calculator：执行简单数学计算。

规则：
1. 如果用户问题涉及 ReAct、LangChain、LangGraph 或“我的笔记”，必须优先调用 search_notes。
2. 如果用户问题是数学计算，调用 calculator。
3. 如果 search_notes 返回 NO_MATCH_FOUND，不要编造笔记内容，应明确说明没有在本地笔记中找到依据。
4. 如果工具返回 ERROR，应说明工具执行失败，并给出可操作的排查建议。
5. 最终回答必须简洁，并尽量说明依据来自哪个工具返回。
""".strip(),
}


def agent_node(state: MessagesState):
    print(f"[NODE] agent | provider={MODEL_PROVIDER} | model={LLM_MODEL}")
    messages = [SYSTEM_PROMPT] + state["messages"]
    response = model.invoke(messages)
    return {"messages": [response]}


tool_node = ToolNode(tools)


def should_continue(state: MessagesState) -> Literal["tools", "__end__"]:
    print("[ROUTER] should_continue")
    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", None):
        print("[ROUTER] route=tools")
        return "tools"
    print("[ROUTER] route=end")
    return "__end__"


def build_graph():
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
    return graph_builder.compile()


graph = build_graph()
```

### 17.4 `src/trace_utils.py`

```python
def print_messages(messages: list) -> None:
    for idx, msg in enumerate(messages, start=1):
        msg_type = msg.__class__.__name__
        print(f"\n[{idx}] {msg_type}")

        tool_calls = getattr(msg, "tool_calls", None)
        if tool_calls:
            print("tool_calls:")
            for call in tool_calls:
                print(f"  - name: {call.get('name')}")
                print(f"    args: {call.get('args')}")
            continue

        content = getattr(msg, "content", "")
        if content:
            content = str(content)
            if len(content) > 500:
                content = content[:500] + "..."
            print(content)
```

### 17.5 `src/run_langgraph.py`

```python
from dotenv import load_dotenv

from src.langgraph_agent import graph
from src.trace_utils import print_messages


def main() -> None:
    load_dotenv()
    print("React Notes Agent started.")
    print("Type exit or quit to stop.")

    while True:
        query = input("\nUser: ").strip()
        if not query:
            continue
        if query.lower() in {"exit", "quit"}:
            break

        result = graph.invoke(
            {"messages": [{"role": "user", "content": query}]},
            config={"recursion_limit": 6},
        )

        print("\n--- Trace Messages ---")
        print_messages(result["messages"])

        print("\n--- Final Answer ---")
        print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
```

---

## 18. README 必须包含的运行命令

```bash
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

复制环境变量：

```bash
cp .env.example .env
```

运行测试：

```bash
pytest
```

运行项目：

```bash
python -m src.run_langgraph
```

---

## 19. 常见问题处理

### 19.1 没有触发工具调用

可能原因：

1. 用户问题没有明确提到“笔记”或相关概念；
2. system prompt 约束不够强；
3. 工具描述太模糊；
4. 模型认为自己可以直接回答；
5. 当前所选模型或接口没有正确返回 `tool_calls`；
6. 使用的模型不支持 tool calling / function calling。

解决方式：

1. 测试问题使用：`根据我的笔记，ReAct 的核心循环是什么？`；
2. 在 system prompt 中强调“涉及本地笔记必须调用 search_notes”；
3. 优化工具 docstring；
4. 打印 AIMessage，检查是否存在 `tool_calls`。

### 19.2 ToolMessage 没有回到模型

检查：

1. 是否添加了 `graph_builder.add_edge("tools", "agent")`；
2. tools 节点名称是否和 router 返回值一致；
3. `add_conditional_edges` 映射是否正确。

### 19.3 无限循环调用工具

解决方式：

1. 调用 graph 时设置 `recursion_limit`；
2. system prompt 中限制不要反复调用同一工具；
3. 后续版本可在 State 中增加 tool_call_count。

### 19.4 search_notes 找不到中文内容

第一版是关键词匹配，可能受分词影响。可以优化为：

1. 如果 query 子串在原文中出现，直接加分；
2. 人工维护关键词映射；
3. 后续再升级为向量检索。

### 19.5 千问或 DeepSeek V4 Pro API 调不通

优先检查：

1. `.env` 是否真实存在，且没有被命名成 `.env.txt`；
2. `LLM_API_KEY` 是否填成了对应平台的 Key；
3. `LLM_BASE_URL` 是否和平台区域匹配；
4. `LLM_MODEL` 是否是账号当前可调用的模型名；
5. 是否把真实 Key 写到了 `.env.example` 并误提交到 GitHub；
6. 当前模型是否支持 tool calling，否则 ReAct 工具循环可能无法触发。

推荐排查命令：

```bash
python -c "from src.config import MODEL_PROVIDER, LLM_BASE_URL, LLM_MODEL; print(MODEL_PROVIDER, LLM_BASE_URL, LLM_MODEL)"
```

如果配置能打印，但调用失败，说明问题大概率在 API Key 权限、模型名或 base_url 区域。

---

## 20. 后续扩展方向

按优先级扩展：

### 20.1 扩展一：更好的关键词检索

增加：

```text
标题加权
文件名加权
段落级切分
Top-K 返回
```

### 20.2 扩展二：向量检索

引入：

```text
Chroma / FAISS / Qdrant
embedding
chunking
rerank
citation
```

### 20.3 扩展三：自定义 State

从 `MessagesState` 升级为自定义状态：

```python
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    query: str
    retrieved_sources: list[str]
    tool_call_count: int
    final_answer: str
```

用于记录：

```text
检索来源
工具调用次数
错误信息
是否命中笔记
```

### 20.4 扩展四：FastAPI 服务化

增加：

```text
POST /chat
GET /health
trace_id
请求响应 schema
```

### 20.5 扩展五：评估集

构建 `eval/questions.jsonl`：

```json
{"query": "根据我的笔记，ReAct 的核心循环是什么？", "expected_tool": "search_notes", "expected_source": "react.md"}
```

指标：

```text
Tool Selection Accuracy
Source Recall
No Answer Correctness
End-to-End Success Rate
```

---

## 21. AI Coding 注意事项

请严格遵守：

1. 第一版保持简单，不要引入数据库、前端、向量库；
2. 工具层必须可单独测试；
3. 不要把 API Key 写入代码；
4. 不要直接暴露完整隐藏推理链；
5. trace 只打印消息类型、工具调用、工具返回和最终答案；
6. 所有异常都要返回清晰错误，而不是让程序直接崩溃；
7. README 必须能让新用户从零跑通；
8. 测试不要依赖真实 LLM API；
9. 真实 LLM 调用只在手动集成测试中执行；
10. 项目代码以教学清晰为第一目标，不追求复杂封装。

---

## 22. 最终交付物清单

AI Coding 完成后，项目至少应包含：

```text
[ ] 完整项目目录
[ ] requirements.txt
[ ] .env.example
[ ] 示例 notes
[ ] search_notes 工具
[ ] calculator 工具
[ ] LangGraph ReAct 图
[ ] CLI 运行入口
[ ] trace 打印工具
[ ] 工具单元测试
[ ] 基础图流程测试
[ ] README
[ ] docs/trace_examples.md
```

---

## 23. 推荐提交顺序

Git commit 可以按下面顺序：

```text
init: create react notes agent project structure
feat: add sample markdown notes and config module
feat: implement note search and calculator tools
test: add unit tests for tools
feat: build langgraph react agent loop
feat: add cli runner and trace printer
docs: add readme and trace examples
```

---

## 24. 一句话总结

这个项目的重点不是做一个强大的知识库，而是用最小代码看懂：

```text
LangGraph 如何把 ReAct 的 Reason → Act → Observe → Reason → Answer 变成一个可运行、可观察、可测试的状态图。
```
