# 精英 Agent 工程师成长路线

> 版本：2026-05-15  
> 目标定位：面向大厂 Agent / AI 应用开发 / 后端 AI 工程师岗位，形成“理论理解 + 架构设计 + 工程落地 + 业务评估 + 长期维护 + 项目表达”的完整能力闭环。  
> 推荐主项目：**OrderFlow-Agent：面向电商交易履约场景的可验证多 Agent 决策系统**

---

## 先明确：什么是“精英 Agent 工程师”

我对“精英 Agent 工程师”的理解不是“会调 LangChain / 会写 prompt / 会接几个工具”，而是具备下面 6 种复合能力：

1. **范式理解能力**：能判断一个业务问题适合普通 RAG、Workflow Agent、Tool-use Agent、Multi-Agent，还是根本不该用 Agent。
2. **Harness 架构能力**：能把上下文、记忆、工具、规划、执行、反馈、约束、安全、评估、观测组合成可运行系统。
3. **工程实现能力**：能用 Python / Java / FastAPI / LangGraph / LlamaIndex / OpenAI API / Claude API / MCP 等技术实现可部署服务。
4. **业务建模能力**：能把客服、交易履约、知识库、代码助手、数据分析等场景拆成流程、状态、工具、权限、异常和评估指标。
5. **评估优化能力**：能构建 golden dataset、失败样本集、回归测试、Agent trace 分析和量化指标体系。
6. **长期维护能力**：能做 prompt / tool / memory / model / policy 的版本管理、线上问题排查、灰度发布、成本控制和持续迭代。

一句话总结：

> 精英 Agent 工程师 = 既懂 LLM，又懂后端工程，又懂业务流程，又能做评估和长期维护的人。

---

# Agent 工程师成长路线总览

## 学习周期建议

| 周期 | 目标 | 结果 |
|---|---|---|
| 3 个月 | 入门到可做完整项目 | 完成一个可运行的 OrderFlow-Agent MVP |
| 6 个月 | 形成工程竞争力 | 完成 2—3 个 Agent 项目，有评估、有文档、有部署 |
| 12 个月 | 形成架构和研究能力 | 能设计复杂 Agent 系统，具备论文/软著/开源项目包装能力 |

## 最终能力画像

学习完成后，你应该能做到：

- 看到业务需求后，能判断是否需要 Agent，以及需要哪种 Agent 架构；
- 能设计 Agent Harness：上下文、记忆、工具、规划、状态、安全、评估、观测；
- 能用 Python 实现单 Agent 状态图、多 Agent 协同、RAG、工具调用、评估系统；
- 能构建测试集并跑出任务成功率、工具调用准确率、规则召回率、成本和延迟；
- 能把 Demo 级系统改造成可部署、可维护、可回归测试的工程系统；
- 能在面试中讲清楚 Agent 系统的 trade-off，而不是只讲“我接了大模型 API”。

---

# 阶段 0：前置基础补齐

## 学习目标

补齐 Agent 工程落地必需的后端和 Python 工程基础，不追求大而全，只学到能支撑项目开发。

## 核心知识

| 基础能力 | 学到什么程度 |
|---|---|
| Python 工程化 | 会组织包结构、虚拟环境、依赖、配置、日志、异常、类型提示 |
| Web 后端基础 | 会用 FastAPI 写接口、定义请求响应、处理异常、生成 OpenAPI 文档 |
| LLM API 调用 | 会调用 chat、structured output、tool calling、streaming |
| RAG 基础 | 理解 chunk、embedding、retrieval、rerank、citation |
| 向量数据库 | 会用 Qdrant / Milvus / Chroma 任一工具完成向量检索 |
| Redis / MySQL | Redis 用于缓存、队列、会话；MySQL/PostgreSQL 用于业务数据 |
| GitHub 项目管理 | 会写 README、issue、目录结构、commit 规范 |
| Docker / 部署 | 会用 docker-compose 启动 API、数据库、Redis、向量库 |

## 推荐资料

- FastAPI 官方文档
- Pydantic 官方文档
- Docker 官方文档
- Python `typing` / `asyncio` 官方文档

## 实践任务

构建基础工程骨架：

```text
agent-system/
  app/
    api/
    core/
    schemas/
    services/
    agents/
    tools/
    rag/
    eval/
    tests/
  data/
  docs/
  docker-compose.yml
  README.md
```

## 项目产出

- FastAPI 服务可启动；
- `.env` 配置可读取；
- 日志可输出；
- `pytest` 可运行；
- Pydantic schema 可校验；
- Docker Compose 可启动 Redis / PostgreSQL / 向量库。

## 达标标准

你能从零搭建一个后端项目，并通过接口模拟订单、物流、规则、退款和工单服务。

---

# 阶段 1：LLM 与 Prompt Engineering 基础

## 学习目标

理解 Prompt 不是“玄学话术”，而是生产系统中的可版本化、可测试、可回归的指令层。

## 核心知识

### 1. Prompt 分层

| 类型 | 作用 |
|---|---|
| System Prompt | 定义模型身份、边界、长期规则 |
| Developer Prompt | 定义应用侧约束、工具使用规则、输出格式 |
| User Prompt | 用户当前请求 |
| Tool Result Context | 工具返回的事实和状态 |
| Memory Context | 经过筛选的历史偏好和任务记录 |

### 2. Prompt Engineering 核心原则

- 明确角色、任务、输入、输出、约束；
- 优先使用结构化输出，而不是让模型自由发挥；
- 对高风险动作使用确认和校验；
- 少用隐藏推理链，更多使用结构化中间状态；
- 对复杂任务使用计划、检查表、状态机；
- Prompt 必须版本化、可测试、可回滚。

### 3. Chain-of-thought 的替代设计

生产环境不要依赖模型长篇自我推理，可以改成：

```text
任务拆解表
证据列表
决策字段
置信度
风险标签
下一步动作
```

### 4. Prompt Injection 风险

需要区分：

```text
可信上下文：系统规则、平台规则、工具结果
不可信上下文：用户输入、网页内容、文档内容、搜索结果
```

## 推荐资料

- OpenAI Prompt / Structured Outputs / Function Calling 文档
- Anthropic Prompt Engineering 文档
- OWASP Top 10 for LLM Applications
- DSPy 官方文档

## 实践任务

为 OrderFlow-Agent 编写 4 类 Prompt：

1. 意图识别 Prompt；
2. 规则检索 Query Rewrite Prompt；
3. 责任归因 Prompt；
4. 客服回复生成 Prompt。

每个 Prompt 都要有：

- 输入字段；
- 输出 schema；
- 失败样例；
- 回归测试样例；
- 版本号。

## 项目产出

```text
prompts/
  intent_v1.md
  policy_rewrite_v1.md
  responsibility_v1.md
  response_v1.md
tests/prompts/
  test_intent_prompt.py
  test_responsibility_prompt.py
```

## 达标标准

你能解释为什么某个 Prompt 这样写，并能通过测试集证明它比上一版更稳定。

---

# 阶段 2：Agent 基础范式

## 学习目标

掌握主流 Agent 范式的适用边界，不盲目套框架。

## 核心范式对比

| 范式 | 核心思想 | 适用场景 | 优点 | 缺点 | 项目建议 |
|---|---|---|---|---|---|
| ReAct | Reason + Act 循环 | 搜索、工具查询、简单任务 | 实现简单，可解释 | 容易循环、成本高 | 搜索型问答、工具助手 |
| Plan-and-Execute | 先规划再执行 | 多步骤任务 | 结构清晰 | 计划可能过时 | 旅行规划、流程任务 |
| Reflection | 执行后反思修正 | 代码、写作、复杂判断 | 提升质量 | 成本和延迟增加 | 代码修复、报告生成 |
| Tool-use Agent | 模型选择并调用工具 | 数据查询、业务操作 | 能接真实系统 | 工具误用风险 | 客服、工单、订单系统 |
| Workflow Agent | 固定流程 + 局部 LLM | 高可靠业务流程 | 可控、易测试 | 灵活性较低 | 交易履约、审批、售后 |
| Router Agent | 路由到不同专家或工具 | 多意图系统 | 模块解耦 | 路由错误会级联 | 企业助手、客服分流 |
| Agentic RAG | 检索、判断、追问、再检索 | 企业知识库 | 减少幻觉 | 工程复杂 | 知识库问答、规则决策 |
| Code Agent | 读写代码、执行测试 | 编程助手 | 产出价值高 | 安全和沙箱要求高 | 代码审查、自动修复 |
| Computer-use Agent | 操作 GUI / 浏览器 | 无 API 的系统自动化 | 泛化强 | 不稳定、慢、难评估 | 浏览器自动化、办公助手 |

## 推荐资料

- ReAct 论文
- Reflexion 论文
- LangGraph 文档
- OpenAI Agents SDK 文档
- AutoGen / CrewAI / LlamaIndex Workflows 文档

## 实践任务

针对同一个任务“用户申请退款”，分别实现三种方式：

1. 普通 LLM 回复；
2. ReAct 工具调用；
3. Workflow Agent 状态图。

比较：

- 准确率；
- 工具调用次数；
- 是否可解释；
- 是否容易测试；
- 成本和延迟。

## 项目产出

```text
examples/
  refund_plain_llm.py
  refund_react_agent.py
  refund_workflow_agent.py
docs/paradigm_comparison.md
```

## 达标标准

你能在面试中讲清楚：为什么交易履约更适合 Workflow Agent，而不是完全开放式 ReAct。

---

# 阶段 3：Agent Harness 架构设计

## 学习目标

把 Agent 看成一个由多个工程模块组成的系统，而不是“一个大 prompt”。

## Harness 核心模块

| 模块 | 解决什么问题 | 输入 | 输出 | 常见实现 | 常见坑 | 如何测试 | 项目体现 |
|---|---|---|---|---|---|---|---|
| 输入理解层 | 理解用户问题 | user query | 标准化请求 | LLM / 规则 | 误解口语化表达 | intent set | 客服意图识别 |
| 意图识别层 | 判断任务类型 | query + history | intent | classifier / LLM | 多意图混淆 | intent accuracy | 退款/物流/投诉 |
| 任务规划层 | 决定执行步骤 | state | plan | LLM / 状态机 | 计划过度复杂 | plan match | 查订单→查规则 |
| 上下文管理层 | 控制输入信息 | memory + tool result | compact context | summarizer / selector | 上下文污染 | context precision | 只放必要证据 |
| 短期记忆 | 保持当前会话状态 | conversation | working state | state dict | 信息覆盖 | state consistency | AgentState |
| 长期记忆 | 保存跨会话知识 | user events | retrievable memory | vector DB / DB | 错误写入 | memory retrieval | 用户偏好 |
| 工具模块 | 连接外部系统 | tool schema | tool result | function calling / MCP | 乱调用、越权 | tool accuracy | 订单/退款工具 |
| 状态管理 | 记录流程进度 | node outputs | state | LangGraph state | 状态不一致 | replay test | workflow.py |
| 执行器 | 运行节点和工具 | plan + state | actions | graph executor | 死循环 | timeout test | LangGraph |
| 反思修正 | 修复失败步骤 | trace + error | revised action | verifier / critic | 过度反思 | repair success | 重试/转人工 |
| 安全约束 | 防止危险行为 | input/action | allow/deny | guardrails | 规则缺失 | adversarial test | 退款确认 |
| 评估日志 | 衡量质量 | trace | metrics | Ragas/LangSmith/custom | 只看主观效果 | golden set | eval runner |
| 人工接管 | 高风险兜底 | uncertain state | human decision | HITL | 接管条件不清 | handoff precision | 转人工节点 |
| 成本稳定性 | 控制生产风险 | run metadata | cost/latency | LiteLLM/缓存 | 成本失控 | latency/cost report | 模型路由 |

## 推荐资料

- LangGraph StateGraph / durable execution / human-in-the-loop
- OpenAI Agents SDK guardrails / handoffs / tracing
- MCP 文档
- OpenTelemetry GenAI 规范

## 实践任务

画出 OrderFlow-Agent 的 Harness 架构图：

```text
User Input
  ↓
Input Normalizer
  ↓
Intent & Slot Layer
  ↓
Context Builder
  ↓
Planner / Router
  ↓
Tool Executor
  ↓
Policy RAG
  ↓
Decision Layer
  ↓
Guardrails
  ↓
Action Execution
  ↓
Verification
  ↓
Response + Trace + Evaluation
```

## 项目产出

```text
docs/agent_harness_architecture.md
docs/architecture_diagram.png
app/agents/state.py
app/agents/workflow.py
app/agents/guardrails.py
```

## 达标标准

你能对任意业务需求拆出 Agent 的 Harness 模块，并说清每个模块的输入、输出、风险和测试方式。

---

# 阶段 4：工具调用与外部系统集成

## 学习目标

掌握 function calling / tool calling 的本质：模型不直接执行业务，只生成结构化调用意图；真正执行由受控工具层完成。

## 核心知识

### Tool Schema 设计

每个工具必须定义：

- 工具名；
- 功能描述；
- 输入 schema；
- 输出 schema；
- 异常类型；
- 是否幂等；
- 是否有副作用；
- 权限级别；
- 是否需要人工确认；
- 是否允许自动重试。

### 工具描述原则

好的工具描述应该说明：

```text
什么时候调用
什么时候不要调用
需要哪些参数
参数从哪里来
返回值代表什么
失败时如何处理
```

### 工具失败处理

常见失败：

- 参数缺失；
- 业务对象不存在；
- 权限不足；
- 网络超时；
- 工具返回异常；
- 工具执行成功但状态未更新；
- 重复执行导致副作用。

对应策略：

- 参数补全；
- 重试；
- fallback 工具；
- 状态校验；
- 人工接管；
- 幂等 key；
- 审计日志。

## 推荐资料

- OpenAI Function Calling 文档
- MCP Tools / Resources / Prompts 文档
- LangGraph tool node 文档
- LlamaIndex tools 文档

## 实践项目

实现 OrderFlow-Agent 工具层：

```text
query_order(order_id)
query_logistics(order_id)
search_policy(query, context)
create_refund(order_id, amount, reason)
create_compensation(order_id, amount, reason)
create_ticket(order_id, reason, priority)
verify_final_state(order_id, expected_state)
```

## 项目产出

```text
app/tools/
  order_tool.py
  logistics_tool.py
  policy_tool.py
  refund_tool.py
  ticket_tool.py
  verification_tool.py
tests/tools/
```

## 达标标准

不需要 LLM，也能手动跑通：

```text
输入订单号
→ 查订单
→ 查物流
→ 检索规则
→ 创建退款
→ 校验退款状态
```

---

# 阶段 5：Memory 与 Context Engineering

## 学习目标

理解上下文工程比单纯 Prompt Engineering 更重要：模型输出质量主要取决于“你给它看了什么、没给它看什么、以什么结构给它看”。

## 核心知识

| 类型 | 作用 | 示例 |
|---|---|---|
| Conversation Memory | 当前多轮对话 | 用户刚才补充的订单号 |
| Working Memory | 当前任务状态 | AgentState 中的订单、物流、规则 |
| Episodic Memory | 事件记忆 | 用户上次投诉物流延迟 |
| Semantic Memory | 稳定知识 | 平台规则、业务概念 |
| Vector Memory | 语义检索 | 用户历史问题、FAQ |
| Summary Memory | 压缩摘要 | 长对话摘要 |
| Long-term Memory | 跨会话持久化 | 用户偏好、企业知识 |
| Scratchpad | 临时推理区 | 节点中间结果 |

## Context Engineering 关键问题

1. 哪些信息必须进入上下文？
2. 哪些信息应该压缩？
3. 哪些信息不能进入上下文？
4. 工具结果怎么摘要？
5. 记忆什么时候写入？
6. 记忆冲突怎么办？
7. 记忆如何评估？

## Memory Write Policy

推荐原则：

```text
用户明确表达长期偏好 → 可写入
短期任务状态 → 只写 AgentState
工具结果 → 写入 trace，不一定写长期记忆
敏感信息 → 默认不写长期记忆
不确定信息 → 不写入或标记低置信度
```

## 推荐资料

- LangGraph memory 文档
- LlamaIndex memory / chat engine 文档
- MemGPT / Letta 相关资料
- Context Engineering 相关博客

## 实践任务

为 OrderFlow-Agent 设计三层记忆：

```text
短期：当前会话状态 AgentState
中期：当前工单/订单处理历史
长期：用户偏好、常见投诉模式、规则命中历史
```

## 项目产出

```text
app/memory/
  short_term.py
  long_term.py
  context_builder.py
  memory_policy.py
tests/memory/
```

## 达标标准

你能解释清楚：为什么某条信息进入上下文，为什么某条信息不进入上下文。

---

# 阶段 6：Agentic RAG 与知识库问答系统

## 学习目标

从“普通知识库问答”升级到“能主动改写、拆解、检索、验证和引用证据的 Agentic RAG”。

## 核心知识

| 技术 | 作用 |
|---|---|
| Query Rewrite | 把口语问题改写为检索问题 |
| Query Decomposition | 把复杂问题拆成多个子问题 |
| Hybrid Retrieval | BM25 + dense vector |
| Rerank | 对召回结果重排序 |
| Citation | 给出证据来源 |
| Grounding | 回答必须基于证据 |
| Multi-turn RAG | 根据上下文补全省略信息 |
| Permission-aware RAG | 根据用户权限过滤文档 |
| RAG Evaluation | recall、precision、faithfulness、answer correctness |

## 企业级知识库 Agent 项目方案

项目名称：

```text
SmartKB-Agent：企业知识库可追溯问答与工单辅助系统
```

核心流程：

```text
用户问题
→ 意图识别
→ Query Rewrite
→ 权限过滤
→ Hybrid Retrieval
→ Rerank
→ Evidence Selection
→ Answer Generation
→ Citation Check
→ User Feedback
→ Eval Log
```

## 推荐资料

- LlamaIndex 官方文档
- LangChain RAG 文档
- Ragas RAG metrics
- BEIR / MIRACL / MTEB 检索 benchmark

## 实践任务

实现一个企业知识库 Agent：

- 支持 Markdown/PDF 文档入库；
- 支持 hybrid retrieval；
- 支持答案引用；
- 支持“没有依据就拒答”；
- 支持评估集。

## 项目产出

```text
projects/smartkb-agent/
  ingestion/
  retriever/
  reranker/
  answerer/
  eval/
```

## 达标标准

能用 50 条测试问题评估：

- context recall；
- answer faithfulness；
- answer correctness；
- citation accuracy。

---

# 阶段 7：Planning、Reflection 与自我修正

## 学习目标

掌握规划和反思的边界：什么时候需要，什么时候会增加复杂度、成本和不稳定性。

## 核心知识

| 机制 | 适合场景 | 不适合场景 |
|---|---|---|
| Task Planning | 多步骤、目标清晰 | 简单 FAQ |
| Subtask Decomposition | 复杂任务拆解 | 原子任务 |
| Dynamic Planning | 环境状态变化 | 固定流程 |
| Reflection | 代码、写作、复杂判断 | 实时客服 |
| Critic Model | 需要质量评审 | 低成本高并发 |
| Verifier | 有明确标准答案 | 主观开放问题 |
| Retry Policy | 工具失败、格式错误 | 业务不允许重复执行 |
| Plan Repair | 执行中断、工具失败 | 无状态任务 |

## 设计原则

```text
高可靠业务：优先状态机 + 局部规划
开放任务：可以使用 planner
高风险动作：必须 verifier + human-in-the-loop
低价值任务：不要反思，直接回答
```

## 推荐资料

- Plan-and-Solve / ReAct / Reflexion 论文
- LangGraph conditional edge / checkpoint 文档
- OpenAI Agents SDK orchestration 文档

## 实践任务

为 OrderFlow-Agent 加入：

1. 初始计划生成；
2. 工具失败后的 plan repair；
3. 决策前 verifier；
4. 高风险退款 human approval。

## 项目产出

```text
app/agents/planner.py
app/agents/verifier.py
app/agents/retry_policy.py
docs/planning_strategy.md
```

## 达标标准

你能说明：为什么不是所有节点都需要 LLM 规划，哪些节点用代码状态机更可靠。

---

# 阶段 8：Multi-Agent 系统

## 学习目标

理解 Multi-Agent 的价值不是“Agent 多”，而是“专业角色分工 + 可控协作 + 可评估轨迹”。

## 核心模式

| 模式 | 说明 | 适合项目 |
|---|---|---|
| Supervisor-Worker | 一个主管分配任务给多个专家 | 客服分流、企业助手 |
| Planner-Executor | 一个负责规划，一个负责执行 | 长任务自动化 |
| Researcher-Writer-Reviewer | 研究、写作、审查分离 | 报告生成 |
| Critic-Reflector | 生成与批评分离 | 代码修复、内容审核 |
| Debate | 多个 Agent 辩论 | 决策评估，但成本高 |
| Swarm | 大量轻量 Agent 协作 | 研究探索多，生产慎用 |
| Blackboard | 共享状态板协作 | 复杂任务协同 |

## Multi-Agent 常见风险

- Agent 之间互相甩锅；
- 重复检索、重复调用工具；
- 成本指数级上升；
- 轨迹难调试；
- 角色边界不清；
- 最终责任不明确；
- 多 Agent 反而比单 Agent 不稳定。

## 求职展示项目

### 项目 1：OrderFlow-Agent

```text
Coordinator Agent
Context Agent
Business Agent
Policy Agent
Decision Agent
Execution Agent
Verification Agent
```

### 项目 2：Research-to-Report Agent

```text
Researcher → Evidence Extractor → Writer → Reviewer → Citation Checker
```

### 项目 3：Code Review Agent

```text
Repo Reader → Bug Finder → Test Generator → Patch Agent → Reviewer
```

## 推荐资料

- AutoGen 文档
- CrewAI 文档
- OpenAI Agents SDK handoffs
- LangGraph multi-agent examples

## 实践任务

把 OrderFlow-Agent 从单状态图升级为专业 Agent 协作：

```text
Coordinator Agent：总控调度
Policy Agent：规则检索与解释
Decision Agent：责任归因
Verification Agent：状态校验
```

## 项目产出

```text
app/multi_agent/
  coordinator.py
  policy_agent.py
  decision_agent.py
  verification_agent.py
  shared_state.py
docs/multi_agent_design.md
```

## 达标标准

你能记录每个 Agent 的输入、输出、调用工具、耗时、失败原因和最终贡献。

---

# 阶段 9：Agent 微调工程

## 学习目标

理解微调不是 Agent 的第一选择。先做 Prompt、RAG、工具、评估；当问题稳定、数据充足、模式可学习时，再考虑微调。

## 什么时候需要微调

适合微调：

- 固定格式输出不稳定；
- 专业术语和领域风格要求高；
- 工具调用选择有明显模式；
- 有大量高质量轨迹数据；
- 希望降低成本，用小模型替代大模型。

不适合微调：

- 业务规则经常变化；
- 事实知识需要频繁更新；
- 数据很少；
- 问题主要来自工具设计或检索质量；
- 没有评估集。

## 核心知识

| 技术 | 在 Agent 中的作用 |
|---|---|
| SFT | 学会标准格式、工具调用风格、领域话术 |
| DPO / Preference Learning | 学会偏好更好的回复或决策 |
| Tool-use Data | 输入、工具选择、参数、工具结果、最终答案 |
| Trajectory Data | 完整执行轨迹，包括 plan、action、observation、final |
| Rejection Sampling | 多次生成，筛掉差样本 |
| Synthetic Data | 用强模型合成训练样本 |
| Domain Adaptation | 让小模型适应垂直场景 |
| Eval after FT | 比较微调前后任务成功率、格式错误率、成本 |

## 推荐学习项目

```text
MiniToolAgent-SFT：面向客服工具调用的小模型微调实验
```

流程：

1. 构造 500—2000 条客服工具调用样本；
2. 格式包含 query、state、tool call、tool result、final answer；
3. 用开源小模型做 LoRA SFT；
4. 与 prompt-only 大模型比较工具调用准确率；
5. 分析什么时候小模型可替代大模型。

## 推荐资料

- OpenAI SFT / DPO 文档
- Hugging Face TRL
- Axolotl / LLaMA-Factory
- LoRA / QLoRA 论文与教程

## 项目产出

```text
fine_tuning/
  data/tool_use_train.jsonl
  data/tool_use_eval.jsonl
  train_lora.py
  eval_tool_call.py
  report.md
```

## 达标标准

你能回答：

> 这个问题应该用 Prompt、RAG、工具工程还是微调解决？为什么？

---

# 阶段 10：Agent 安全、约束与可靠性

## 学习目标

掌握生产级 Agent 的安全边界，不让模型越权、误操作、泄露数据或被注入攻击操控。

## 核心风险

| 风险 | 示例 | 防御 |
|---|---|---|
| Prompt Injection | 用户说“忽略之前规则” | 指令分层、输入隔离、规则校验 |
| Jailbreak | 绕过安全策略 | policy engine、输出过滤 |
| Tool Misuse | 模型乱退款 | 权限、确认、业务校验 |
| Data Leakage | 泄露其他用户订单 | RBAC、数据过滤 |
| Unsafe Action | 高风险操作自动执行 | human-in-the-loop |
| Context Pollution | 文档内容污染系统指令 | 不可信内容隔离 |
| Memory Poisoning | 写入错误长期记忆 | memory write policy |
| MCP Tool Risk | 外部工具供应链风险 | 白名单、沙箱、审计 |

## 生产级安全设计

```text
输入层：内容分类 + 注入检测
上下文层：可信/不可信信息隔离
工具层：权限控制 + 参数校验 + 幂等 + 审计
决策层：policy engine + verifier
执行层：高风险动作二次确认
输出层：敏感信息过滤 + 格式校验
观测层：全链路 trace + audit log
```

## 推荐资料

- OWASP Top 10 for LLM Applications
- OpenAI Agents SDK Guardrails
- Microsoft Responsible AI / Azure AI safety
- MCP 安全最佳实践

## 实践任务

为 OrderFlow-Agent 增加 5 类 guardrail：

1. Prompt injection 检测；
2. 退款金额上限；
3. 用户权限校验；
4. 高风险动作人工确认；
5. 输出敏感信息脱敏。

## 项目产出

```text
app/security/
  injection_detector.py
  permission.py
  policy_engine.py
  output_filter.py
  audit_log.py
tests/security/
```

## 达标标准

通过 30 条 adversarial test case，系统不能越权退款、泄露订单或执行不合规工具调用。

---

# 阶段 11：Agent 评估、测试集构建与可观测性

## 学习目标

把 Agent 从“感觉效果不错”变成“能量化、能回归、能定位失败原因”的系统。

## Agent 为什么难评估

因为 Agent 不是单次文本生成，而是：

```text
输入理解
→ 检索
→ 规划
→ 工具选择
→ 参数生成
→ 工具执行
→ 状态更新
→ 决策
→ 输出
```

每一步都可能错。

## 完整评估体系模板

| 层级 | 指标 |
|---|---|
| 输入理解 | Intent Accuracy、Slot F1 |
| 检索层 | Recall@K、MRR、Citation Accuracy |
| 工具层 | Tool Selection Accuracy、Argument Accuracy、Tool Success Rate |
| 规划层 | Plan Validity、Step Efficiency |
| 决策层 | Responsibility Accuracy、Action Accuracy |
| 安全层 | Unsafe Action Rate、Injection Defense Rate |
| 输出层 | Faithfulness、Helpfulness、Format Validity |
| 端到端 | Task Success Rate、Human Escalation Precision |
| 系统层 | Latency、Cost、Retry Rate、Fallback Rate |
| 用户层 | Satisfaction、Resolution Rate |

## 测试集类型

- Golden Dataset：标准业务样本；
- Adversarial Test Set：攻击和边界样本；
- Regression Test Set：历史失败样本；
- Scenario-based Evaluation：按业务流程设计样本；
- Online Eval：线上抽样评估；
- Human Review Set：人工标注困难样本。

## Failure Taxonomy

```text
F1 意图识别错误
F2 槽位缺失
F3 检索不到规则
F4 命中错误规则
F5 工具选择错误
F6 工具参数错误
F7 责任判断错误
F8 动作决策错误
F9 工具执行失败
F10 状态校验失败
F11 输出不忠实
F12 安全违规
```

## 推荐资料

- Ragas Agent Evaluation
- LangSmith Evaluation
- OpenTelemetry GenAI Semantic Conventions
- AgentBench / τ-bench / SWE-bench / GAIA

## 实践任务

为 OrderFlow-Agent 构建 100 条测试集：

```json
{
  "case_id": "C001",
  "user_query": "我的订单三天没发货，我要退款",
  "order_status": "paid",
  "logistics_status": "not_shipped",
  "expected_intent": "refund_request",
  "expected_policy_ids": ["R001"],
  "expected_responsible_party": "merchant",
  "expected_action": "refund"
}
```

## 项目产出

```text
eval/
  datasets/golden.jsonl
  datasets/adversarial.jsonl
  runner.py
  metrics.py
  failure_taxonomy.py
  report_generator.py
```

## 达标标准

你能跑出完整报告：

```text
Intent Accuracy
Policy Recall
Tool Call Accuracy
Action Accuracy
End-to-End Success Rate
Avg Latency
Avg Cost
Failure Distribution
```

---

# 阶段 12：Agent 生产部署与长期维护

## 学习目标

把 Demo 级 Agent 变成生产级 Agent：可部署、可监控、可灰度、可回滚、可持续优化。

## 核心架构

```text
Client
  ↓
API Gateway
  ↓
FastAPI Agent Service
  ↓
Model Gateway / LiteLLM
  ↓
LangGraph Workflow
  ↓
Tool Services
  ↓
Redis / PostgreSQL / Vector DB
  ↓
Observability + Eval + Audit
```

## 核心能力

| 能力 | 实现 |
|---|---|
| 队列 | Redis Queue / Celery |
| 缓存 | query cache、retrieval cache、tool result cache |
| 限流 | Redis token bucket |
| 熔断 | 模型失败率过高自动切换 |
| 降级 | 强模型失败 → 弱模型/规则兜底/人工 |
| 多模型路由 | cheap / reasoning / fast / fallback |
| Prompt 版本管理 | prompt registry + version |
| Tool 版本管理 | tool schema version |
| Memory 版本管理 | memory schema + write policy |
| 灰度发布 | 按用户/流量切分 |
| 反馈闭环 | 失败样本进入 eval dataset |

## 推荐资料

- LiteLLM 文档
- OpenTelemetry 文档
- LangSmith / Langfuse / MLflow Tracing
- Docker / Kubernetes 基础

## 实践任务

为 OrderFlow-Agent 增加：

- Docker Compose；
- Redis 缓存；
- PostgreSQL 存储；
- LiteLLM 模型网关；
- trace_id；
- 成本统计；
- 失败样本自动沉淀。

## 项目产出

```text
docker-compose.yml
app/llm/router.py
app/observability/tracing.py
app/ops/failure_collector.py
docs/deployment.md
```

## 达标标准

你能解释一次线上失败请求从哪里查日志、如何复现、如何修复、如何加入回归测试。

---

# 阶段 13：业务场景落地训练

## 场景 1：电商客服 / 交易履约 Agent

| 项目 | 内容 |
|---|---|
| 业务流程 | 查订单、查物流、读规则、判断责任、退款/补偿/转人工 |
| 工具 | 订单 API、物流 API、规则检索、退款、工单 |
| 数据 | 订单、物流、售后规则、历史工单 |
| 风险 | 错误退款、越权查询、规则误判 |
| 指标 | 责任判断准确率、动作准确率、端到端成功率 |
| 项目 | OrderFlow-Agent |
| 简历描述 | 设计并实现面向交易履约场景的可验证 Agent 决策系统，支持规则 RAG、工具调用、状态校验和端到端评估 |

## 场景 2：企业知识库 Agent

| 项目 | 内容 |
|---|---|
| 业务流程 | 文档入库、权限过滤、检索、回答、引用、反馈 |
| 工具 | 文档解析、向量库、搜索、权限系统 |
| 数据 | FAQ、制度文档、产品文档 |
| 风险 | 幻觉、错误引用、越权访问 |
| 指标 | Context Recall、Faithfulness、Citation Accuracy |
| 项目 | SmartKB-Agent |
| 简历描述 | 构建企业级知识库 Agent，支持混合检索、引用校验、权限过滤和 RAG 自动评估 |

## 场景 3：代码开发 Agent

| 项目 | 内容 |
|---|---|
| 业务流程 | 读 issue、理解代码、定位 bug、生成 patch、运行测试 |
| 工具 | Git、文件系统、测试框架、静态分析 |
| 数据 | GitHub issue、repo、测试用例 |
| 风险 | 破坏代码、安全执行 |
| 指标 | Patch Pass Rate、Test Pass Rate |
| 项目 | CodeFix-Agent |
| 简历描述 | 实现面向代码仓库的自动修复 Agent，支持代码检索、测试生成、补丁验证和失败回放 |

## 场景 4：数据分析 Agent

| 项目 | 内容 |
|---|---|
| 业务流程 | 读表、理解指标、生成 SQL、执行分析、可视化 |
| 工具 | SQL、Python、BI、文件系统 |
| 数据 | CSV、数据库、指标定义 |
| 风险 | SQL 错误、指标误解、数据泄露 |
| 指标 | SQL Accuracy、Insight Quality、Execution Success |
| 项目 | DataAnalyst-Agent |
| 简历描述 | 构建数据分析 Agent，支持 NL2SQL、指标解释、图表生成和分析报告输出 |

## 场景 5：受限医疗 / 金融 Agent

| 项目 | 内容 |
|---|---|
| 业务流程 | 信息收集、资料检索、风险提示、人工转接 |
| 工具 | 权威资料库、规则引擎、人工审核 |
| 数据 | 指南、合规规则、案例 |
| 风险 | 高风险建议、合规问题 |
| 指标 | 安全拒答率、引用准确率、人工接管准确率 |
| 项目 | GuardedDomain-Agent |
| 简历描述 | 设计受限领域 Agent 安全架构，支持权限边界、引用证据、风险识别和人工接管 |

---

# 阶段 14：项目作品集规划

## 项目 1：PromptLab-Agent

| 项目 | 内容 |
|---|---|
| 定位 | Prompt 与结构化输出实验平台 |
| 技术栈 | FastAPI + Pydantic + OpenAI API + pytest |
| 核心模块 | Prompt registry、structured output、eval runner |
| 指标 | Format Validity、Accuracy、Latency |
| 亮点 | Prompt 版本管理和回归测试 |
| 简历描述 | 构建 Prompt 工程实验平台，支持结构化输出、提示词版本管理和自动化回归评估 |
| 后续优化 | 接入 DSPy 自动优化 |

## 项目 2：SmartKB-Agent

| 项目 | 内容 |
|---|---|
| 定位 | 企业知识库 Agent |
| 技术栈 | FastAPI + LlamaIndex/LangChain + Qdrant + Ragas |
| 核心模块 | 文档入库、混合检索、rerank、citation、RAG eval |
| 指标 | Context Recall、Faithfulness、Citation Accuracy |
| 亮点 | 可追溯回答和权限过滤 |
| 简历描述 | 设计企业知识库 Agent，支持混合检索、证据引用、权限过滤与系统化 RAG 评估 |
| 后续优化 | 多轮 Agentic RAG 和反馈闭环 |

## 项目 3：OrderFlow-Agent

| 项目 | 内容 |
|---|---|
| 定位 | 电商交易履约 Agent |
| 技术栈 | FastAPI + Pydantic + LangGraph + PostgreSQL + Redis + Ragas |
| 核心模块 | 订单/物流工具、规则 RAG、责任判断、退款决策、状态校验 |
| 指标 | Tool Accuracy、Responsibility Accuracy、Action Accuracy、E2E Success |
| 亮点 | 可验证工具执行和业务状态校验 |
| 简历描述 | 实现面向电商履约的多 Agent 决策系统，支持订单/物流/规则联动、退款决策、工具执行校验和端到端评估 |
| 后续优化 | 多模型路由、人工接管、灰度发布 |

## 项目 4：CodeFix-Agent

| 项目 | 内容 |
|---|---|
| 定位 | 代码修复 Agent |
| 技术栈 | Python + LangGraph + Git + pytest + sandbox |
| 核心模块 | Repo reader、bug locator、patch generator、test runner |
| 指标 | Test Pass Rate、Patch Validity、Regression Pass |
| 亮点 | 代码执行沙箱和自动验证 |
| 简历描述 | 构建代码修复 Agent，支持仓库理解、补丁生成、自动测试和失败回放 |
| 后续优化 | 对接 SWE-bench 风格任务 |

## 项目 5：AgentOps-Platform

| 项目 | 内容 |
|---|---|
| 定位 | Agent 评估与观测平台 |
| 技术栈 | FastAPI + OpenTelemetry + LangSmith/Langfuse + PostgreSQL |
| 核心模块 | Trace、eval、failure taxonomy、cost dashboard |
| 指标 | Latency、Cost、Failure Rate、Regression Pass |
| 亮点 | Agent 生产维护能力 |
| 简历描述 | 设计 AgentOps 观测与评估平台，支持 trace 采集、失败归因、回归测试和成本监控 |
| 后续优化 | 接入在线 A/B test |

---

# 阶段 15：论文 / 软著 / 科研价值包装

## 可包装方向

| 类型 | 适合方向 |
|---|---|
| 学术论文 | Agent 评估、业务型 Agentic RAG、可验证工具执行、多 Agent 协作效率 |
| 软件著作权 | 完整系统：OrderFlow-Agent / SmartKB-Agent / AgentOps |
| 开源项目 | 工程实现 + README + demo + eval dataset |
| 技术博客 | 架构设计、踩坑总结、评估方法、框架对比 |
| 求职项目 | 强调业务闭环、可量化指标、工程可靠性 |

## 更有科研价值的方向

1. 面向交易履约的 Agent 端到端评估 benchmark；
2. 规则 RAG + 工具执行 + 状态校验的可验证 Agent 架构；
3. 多 Agent 协同在客服决策链路中的效果与成本对比；
4. Agent 失败样本自动归因与持续优化框架；
5. 面向高风险业务操作的 human-in-the-loop 安全机制。

## 更偏工程落地的方向

1. 企业知识库问答；
2. 客服 Agent；
3. 工单辅助；
4. 数据分析助手；
5. 内部流程自动化。

---

# 阶段 16：学习节奏与时间规划

## 3 个月计划：做出一个强项目

| 周期 | 学习重点 | 阶段成果 | 博客 |
|---|---|---|---|
| 第 1—2 周 | Python 工程化、FastAPI、Pydantic | 项目骨架、业务模拟接口 | Agent 工程项目如何搭骨架 |
| 第 3—4 周 | Prompt、structured output、tool calling | 工具层、结构化输出 | 为什么 Schema 比 Prompt 更重要 |
| 第 5—6 周 | LangGraph、Workflow Agent | 单 Agent 履约闭环 | 用 LangGraph 实现业务状态图 |
| 第 7—8 周 | 规则 RAG、证据链 | 规则检索与责任判断 | 业务型 RAG 与普通 RAG 的区别 |
| 第 9—10 周 | 评估系统 | 100 条测试集和指标报告 | Agent 如何做端到端评估 |
| 第 11—12 周 | 多 Agent、部署、README | 完整 GitHub 项目 | OrderFlow-Agent 项目复盘 |

达标标准：

- GitHub 有完整项目；
- README 有架构图、流程图、运行方法、评估结果；
- 面试能讲 15 分钟。

## 6 个月计划：形成岗位竞争力

| 月份 | 目标 |
|---|---|
| 第 1 月 | 完成 PromptLab + FastAPI 工程基础 |
| 第 2 月 | 完成 SmartKB-Agent |
| 第 3 月 | 完成 OrderFlow-Agent MVP |
| 第 4 月 | 升级多 Agent、评估、观测 |
| 第 5 月 | 学习微调，做 MiniToolAgent-SFT |
| 第 6 月 | 项目包装、博客、简历、模拟面试 |

达标标准：

- 2—3 个完整项目；
- 至少 6 篇技术博客；
- 掌握 Agent 评估和维护表达；
- 能投 AI 应用开发、Agent 工程、后端 AI 岗位。

## 12 个月计划：形成长期壁垒

| 阶段 | 目标 |
|---|---|
| 1—3 月 | 完成核心工程能力 |
| 4—6 月 | 完成多项目作品集 |
| 7—9 月 | 深入微调、评估、AgentOps |
| 10—12 月 | 论文/软著/开源维护/实习求职 |

达标标准：

- 有一个长期维护的 Agent 项目；
- 有评估数据集和实验报告；
- 有论文/软著/开源贡献；
- 能独立设计一个生产级 Agent 系统。

---

# 阶段 17：推荐资料清单

## 官方文档

- OpenAI API：Structured Outputs、Function Calling、Fine-tuning、Agents SDK
- LangGraph：StateGraph、Durable Execution、Human-in-the-loop、Memory
- LangSmith：Evaluation、Datasets、Tracing
- LlamaIndex：Workflows、Agents、RAG
- AutoGen：Multi-Agent Framework
- CrewAI：Role-based Multi-Agent
- MCP：Tools、Resources、Prompts
- OpenTelemetry：GenAI Semantic Conventions
- Ragas：RAG / Agent Evaluation
- DSPy：Prompt / Program Optimization

## 经典论文

- ReAct: Synergizing Reasoning and Acting in Language Models
- Reflexion: Language Agents with Verbal Reinforcement Learning
- Toolformer
- Self-Refine
- Plan-and-Solve Prompting
- Voyager
- Generative Agents
- SWE-bench
- AgentBench
- WebArena
- GAIA

## Benchmark / Evaluation

- Ragas
- LangSmith Eval
- AgentBench
- SWE-bench
- GAIA
- τ-bench
- WebArena
- BEIR
- MTEB

## 值得长期跟踪

- OpenAI Developers
- Anthropic Engineering
- LangChain Blog
- LlamaIndex Blog
- Microsoft Research AutoGen / Agent Framework
- Hugging Face Blog
- Stanford NLP / DSPy
- Berkeley Sky Computing / LMSYS
- OWASP LLM Security

---

# 阶段 18：最终能力检查清单

## 理论理解

- [ ] 能解释 ReAct、Plan-and-Execute、Reflection、Workflow Agent、Agentic RAG、Multi-Agent 的区别；
- [ ] 能判断一个业务场景是否需要 Agent；
- [ ] 能说明 Agent 相比普通 LLM 应用的核心差异。

## 架构设计

- [ ] 能画出 Agent Harness 架构；
- [ ] 能设计输入、状态、上下文、记忆、工具、规划、安全、评估模块；
- [ ] 能说明每个模块的输入、输出和风险。

## 工程实现

- [ ] 能用 FastAPI + Pydantic 搭建 Agent 后端；
- [ ] 能用 LangGraph 实现状态图；
- [ ] 能实现 tool calling、structured output、streaming；
- [ ] 能写单元测试和端到端测试。

## 工具调用

- [ ] 能设计 tool schema；
- [ ] 能做权限控制、参数校验、幂等控制；
- [ ] 能处理工具失败和重试；
- [ ] 能做工具调用日志和审计。

## RAG

- [ ] 能实现文档切分、embedding、检索、rerank、引用；
- [ ] 能做 query rewrite 和 query decomposition；
- [ ] 能评估 context recall 和 faithfulness。

## Memory

- [ ] 能区分短期、长期、语义、事件、向量、摘要记忆；
- [ ] 能设计 memory write policy；
- [ ] 能处理记忆冲突和上下文污染。

## Multi-Agent

- [ ] 能设计 supervisor-worker、planner-executor、critic-reflector；
- [ ] 能记录多 Agent trace；
- [ ] 能评估多 Agent 成本和收益；
- [ ] 能避免为了多 Agent 而多 Agent。

## 安全

- [ ] 能识别 prompt injection、tool misuse、data leakage；
- [ ] 能设计 guardrails、policy engine、human-in-the-loop；
- [ ] 能实现输出校验和审计日志。

## 评估

- [ ] 能构造 golden dataset；
- [ ] 能设计 adversarial test set；
- [ ] 能评估 tool accuracy、task success、latency、cost；
- [ ] 能做 failure taxonomy 和回归测试。

## 部署维护

- [ ] 能用 Docker 部署；
- [ ] 能接 Redis / PostgreSQL / 向量库；
- [ ] 能做模型 fallback、限流、缓存、trace；
- [ ] 能处理线上失败样本闭环。

## 项目表达

- [ ] GitHub README 有架构图、流程图、运行方法、评估结果；
- [ ] 简历能写出指标和架构亮点；
- [ ] 面试能讲清楚 trade-off；
- [ ] 能把项目包装成软著、博客或论文方向。

---

# 最终建议：你的主线项目应该怎么做

你最适合把学习路线落到这个主项目：

```text
OrderFlow-Agent：面向电商交易履约的可验证多 Agent 决策系统
```

最小闭环：

```text
用户：我的订单三天没发货，我要退款
  ↓
意图识别：退款申请
  ↓
槽位补全：订单号
  ↓
查订单：已支付，未发货
  ↓
查物流：无揽收记录
  ↓
规则 RAG：命中延迟发货规则
  ↓
责任判断：商家责任
  ↓
动作决策：允许退款
  ↓
工具执行：创建退款
  ↓
状态校验：退款状态已创建
  ↓
客服回复：说明处理结果
  ↓
评估记录：trace + metrics + failure taxonomy
```

这个项目能同时覆盖：

- Workflow Agent；
- Tool-use Agent；
- Agentic RAG；
- Multi-Agent；
- Guardrails；
- Evaluation；
- Observability；
- 业务系统集成；
- 简历和面试表达。

如果你只能选一个长期项目，就选它。


---

# 附录：推荐资料入口

## 官方与工程文档

- OpenAI Agents SDK: https://developers.openai.com/api/docs/guides/agents
- OpenAI Structured Outputs: https://developers.openai.com/api/docs/guides/structured-outputs
- OpenAI Function Calling: https://developers.openai.com/api/docs/guides/function-calling
- OpenAI SFT: https://developers.openai.com/api/docs/guides/supervised-fine-tuning
- OpenAI DPO: https://developers.openai.com/api/docs/guides/direct-preference-optimization
- LangGraph Overview: https://docs.langchain.com/oss/python/langgraph/overview
- LangGraph Durable Execution: https://docs.langchain.com/oss/python/langgraph/durable-execution
- LangSmith Evaluation: https://docs.langchain.com/langsmith/evaluation
- Ragas Agent Evaluation: https://docs.ragas.io/en/stable/tutorials/agent/
- OpenTelemetry GenAI Semantic Conventions: https://opentelemetry.io/docs/specs/semconv/gen-ai/
- DSPy: https://dspy.ai/
- LlamaIndex Agents / Workflows: https://developers.llamaindex.ai/python/framework/use_cases/agents/
- AutoGen: https://microsoft.github.io/autogen/stable/
- Model Context Protocol: https://modelcontextprotocol.io/docs/getting-started/intro
- MCP Specification: https://modelcontextprotocol.io/specification/2025-06-18/
- OWASP Top 10 for LLM Applications: https://owasp.org/www-project-top-10-for-large-language-model-applications/

## 经典论文关键词

- ReAct
- Reflexion
- Toolformer
- Self-Refine
- Plan-and-Solve
- Generative Agents
- Voyager
- SWE-bench
- AgentBench
- WebArena
- GAIA
- τ-bench

## 建议长期跟踪

- OpenAI Developers
- Anthropic Engineering
- LangChain Blog
- LlamaIndex Blog
- Microsoft Research AutoGen / Agent Framework
- Hugging Face Blog
- Stanford NLP / DSPy
- OWASP LLM Security
