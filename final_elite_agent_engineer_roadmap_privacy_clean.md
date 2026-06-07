# 精英 Agent 工程师最终学习路线

> 版本：Final 2026  
> 目标定位：面向大厂 Agent 工程师、AI 应用开发工程师、后端 AI 工程师岗位，建立从理论范式、系统架构、工程实现、业务落地、评估优化到长期维护的完整能力闭环。  

---

## 0. 总目标：你最终要成为哪类 Agent 工程师

你要成为的不是“会调用大模型 API 的开发者”，也不是“会写 LangChain Demo 的应用工程师”，而是具备完整 Agent 系统设计能力的工程型架构人才。

最终能力画像：

1. **范式判断能力**：看到一个业务场景，能判断该用普通 LLM、RAG、Workflow Agent、Tool-use Agent、Multi-Agent、Computer-use Agent，还是不该用 Agent。
2. **Harness 架构能力**：能把上下文、记忆、工具、规划、执行、反馈、安全、评估、观测组合成一个可运行、可维护的系统。
3. **工程实现能力**：能使用 Python / Java / FastAPI / LangGraph / LlamaIndex / OpenAI API / Claude API / MCP / Redis / PostgreSQL / Docker 等技术完成可部署系统。
4. **业务建模能力**：能把客服、交易履约、知识库、代码助手、数据分析等业务拆成流程、状态、工具、权限、异常和指标。
5. **评估优化能力**：能构建测试集、失败样本集、回归测试集、trace 分析和端到端指标体系。
6. **生产维护能力**：能进行 prompt / tool / memory / model / policy 的版本管理、灰度发布、线上排查、成本控制和持续优化。
7. **项目表达能力**：能把学习成果转化为 GitHub 项目、技术博客、简历亮点、面试叙事、软著和论文选题。

一句话总结：

> 精英 Agent 工程师 = 懂 LLM + 懂后端工程 + 懂业务流程 + 懂评估优化 + 懂长期维护。

---

## 1. 整体学习主线

这条路线分成 5 条并行主线，但学习时以项目驱动推进。

```text
主线 A：Agent 理论范式
Prompt Engineering → ReAct → Plan-and-Execute → Reflection → Workflow Agent → Agentic RAG → Multi-Agent → Computer-use Agent

主线 B：Agent Harness 架构
Input → Intent → Context → Memory → Tools → Planner → Executor → Guardrails → Evaluator → Observability → HITL

主线 C：Python 工程落地
FastAPI → Pydantic → LangGraph → Tool Calling → MCP → RAG → LiteLLM → Redis/PostgreSQL → Docker → AgentOps

主线 D：业务项目训练
PromptLab-Agent → SmartKB-Agent → OrderFlow-Agent → CodeFix-Agent → AgentOps-Platform

主线 E：求职与长期壁垒
README → 技术博客 → 评估报告 → 简历项目 → 面试表达 → 软著/论文/开源维护
```

学习原则：

- 不以“学框架”为目标，而以“能否解决业务闭环”为目标；
- 不先做复杂多 Agent，先做稳定的单 Agent 状态图闭环；
- 不只看最终回复，要看工具轨迹、状态变化、失败原因和成本；
- 不把 Prompt 当玄学，要做版本管理、测试和回归；
- 不把 RAG 做成普通问答，要做业务证据链和可验证决策；
- 不盲目微调，先做 Prompt / RAG / Tool / Eval，再判断是否需要微调。

---

## 2. 最终技术栈建议

### 2.1 核心工程栈

| 模块 | 推荐技术 | 学习目标 |
|---|---|---|
| 后端服务 | FastAPI / Spring Boot | 暴露 Agent 服务、工具服务、业务接口 |
| 数据建模 | Pydantic / dataclass / Java DTO | 定义状态、工具参数、结构化输出 |
| Agent 编排 | LangGraph | 构建状态图、条件路由、checkpoint、HITL |
| 模型调用 | OpenAI API / Claude API / LiteLLM | 结构化输出、工具调用、多模型路由、fallback |
| 工具协议 | Function Calling / MCP | 标准化工具注册、调用、权限与审计 |
| RAG | LlamaIndex / LangChain / Qdrant / Milvus / BM25 / rerank | 企业知识库、规则检索、证据链 |
| 存储 | PostgreSQL / MySQL / Redis | 业务数据、状态、缓存、队列 |
| 评估 | pytest / Ragas / LangSmith / 自定义 metrics | 节点级、工具级、端到端评估 |
| 观测 | OpenTelemetry / LangSmith / Langfuse / 日志系统 | trace、span、token、成本、延迟 |
| 部署 | Docker / docker-compose | 本地和服务器部署 |
| 微调 | Hugging Face TRL / LLaMA-Factory / LoRA / QLoRA | 小模型工具调用和领域适配实验 |

### 2.2 前沿增强模块

| 模块 | 作用 | 放入路线的位置 |
|---|---|---|
| MCP | 标准化 Agent 与外部工具、资源、提示模板的连接 | 阶段 4：工具调用与外部系统集成 |
| Agent Skills / Skill Registry | 把工具、脚本、模板、说明文档打包成可复用能力包 | 阶段 4：工具与技能化封装 |
| GraphRAG / RuleRAG | 用图谱或规则结构增强 RAG 的证据组织能力 | 阶段 6：Agentic RAG |
| A2A / Agent-to-Agent 协议思想 | 多 Agent 跨系统通信与协作 | 阶段 8：Multi-Agent |
| Trace / Trajectory 级评估 | 不只评估最终答案，还评估每一步轨迹 | 阶段 11：评估与可观测性 |
| Eval as CI Gate | 把评估集接入 CI，防止 prompt/tool 版本更新导致退化 | 阶段 12：生产维护 |
| AgentOps | Agent 的监控、回放、失败归因、成本治理 | 阶段 12：生产部署与长期维护 |
| Computer-use / Browser-use Agent | 无 API 场景下通过浏览器或 GUI 操作系统 | 阶段 2 和阶段 13 |

---

# 第一部分：基础能力与核心范式

---

## 阶段 0：前置基础补齐

### 学习目标

补齐 Agent 工程落地所需的基础能力，但不要过度学习。所有基础都服务于后续项目。

### 核心知识

| 能力 | 学到什么程度 |
|---|---|
| Python 工程化 | 会组织项目结构、虚拟环境、依赖管理、配置、日志、异常、类型提示 |
| Web 后端 | 会用 FastAPI 写接口、请求响应、异常处理、OpenAPI 文档 |
| LLM API | 会调用 chat、structured output、tool calling、streaming |
| Pydantic | 会定义 schema、字段校验、嵌套模型、错误处理 |
| RAG 基础 | 理解 chunk、embedding、retrieval、rerank、citation |
| 向量数据库 | 会用 Qdrant / Milvus / Chroma 任意一个完成检索 |
| Redis | 会做缓存、限流、任务状态、队列 |
| PostgreSQL / MySQL | 会保存业务数据、测试集、日志 |
| GitHub | 会写 README、issue、commit、目录结构 |
| Docker | 会用 docker-compose 启动服务依赖 |

### 实践任务

搭建基础工程：

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
    memory/
    eval/
    tests/
  data/
  docs/
  docker-compose.yml
  README.md
```

### 项目产出

- FastAPI 服务能启动；
- `.env` 配置能读取；
- 日志能输出；
- `pytest` 能运行；
- Pydantic schema 能校验；
- Docker Compose 能启动 Redis / PostgreSQL / 向量库。

### 达标标准

你能从零搭建一个后端项目，并通过接口模拟订单、物流、规则、退款和工单服务。

---

## 阶段 1：LLM 与 Prompt Engineering 基础

### 学习目标

把 Prompt 从“临时话术”升级为生产系统里的可版本化、可测试、可回滚的指令资产。

### 核心知识

1. **Prompt 分层**
   - System Prompt：模型长期边界；
   - Developer Prompt：应用侧任务规则；
   - User Prompt：用户当前请求；
   - Tool Result Context：工具返回事实；
   - Memory Context：被筛选后的历史信息。

2. **生产级 Prompt 原则**
   - 明确任务、输入、输出、约束；
   - 优先结构化输出；
   - 对高风险动作增加确认；
   - 不依赖长篇 CoT，使用结构化中间字段；
   - Prompt 必须有版本号、测试集和变更记录。

3. **Chain-of-thought 替代设计**

```text
任务类型
证据列表
决策字段
置信度
风险标签
下一步动作
失败原因
```

4. **Prompt Injection 防护基础**
   - 区分可信上下文和不可信上下文；
   - 不让网页、文档、用户输入覆盖系统规则；
   - 对工具调用前做 policy check。

### 实践任务

为 OrderFlow-Agent 编写 5 类 Prompt：

1. 意图识别 Prompt；
2. 槽位抽取 Prompt；
3. 规则检索 Query Rewrite Prompt；
4. 责任归因 Prompt；
5. 客服回复生成 Prompt。

每个 Prompt 包含：

- 输入字段；
- 输出 schema；
- 正例；
- 反例；
- 测试样例；
- 版本号。

### 项目产出

```text
prompts/
  intent_v1.md
  slot_extract_v1.md
  policy_rewrite_v1.md
  responsibility_v1.md
  response_v1.md
tests/prompts/
  test_intent_prompt.py
  test_responsibility_prompt.py
docs/prompt_design_notes.md
docs/prompt_eval_report.md
```

### 达标标准

你能解释每个 Prompt 为什么这样设计，并能用测试集说明新版本是否优于旧版本。

---

## 阶段 2：Agent 基础范式与适用边界

### 学习目标

理解 Agent 范式的本质，不盲目套框架。重点是判断“什么场景适合什么范式”。

### 核心范式

| 范式 | 核心思想 | 适合场景 | 主要风险 |
|---|---|---|---|
| ReAct | Reason + Act 循环 | 搜索、查询、轻量工具使用 | 循环、成本高、动作不稳定 |
| Plan-and-Execute | 先规划再执行 | 多步骤任务、复杂流程 | 计划过时、执行偏离 |
| Reflection | 执行后反思修正 | 代码、写作、复杂判断 | 延迟和成本上升 |
| Tool-use Agent | 模型选择工具并生成参数 | 数据查询、业务操作 | 工具误用、越权 |
| Workflow Agent | 固定流程 + 局部 LLM | 交易履约、审批、售后 | 灵活性较低 |
| Router Agent | 路由到不同工具/专家 | 多意图系统 | 路由错误级联 |
| Agentic RAG | 检索、判断、追问、再检索 | 企业知识库、规则决策 | 检索链路复杂 |
| Code Agent | 读写代码、运行测试 | 编程助手、自动修复 | 沙箱和安全要求高 |
| Computer-use Agent | 操作浏览器/GUI | 无 API 的业务系统 | 慢、不稳定、难评估 |
| Multi-Agent | 多角色协作 | 复杂研究、评审、业务分工 | 成本、冲突、不可控 |

### 工程判断原则

- 高可靠业务流程：优先 Workflow Agent；
- 需要外部数据：Tool-use Agent + RAG；
- 需要规则依据：Agentic RAG / RuleRAG；
- 需要多角色评审：Multi-Agent；
- 无 API 系统自动化：Computer-use Agent；
- 简单问答：不要用复杂 Agent。

### 实践任务

针对“用户申请退款”实现 4 种版本：

1. 普通 LLM 回复；
2. ReAct 工具调用；
3. Workflow Agent 状态图；
4. Workflow + RAG + Tool Verification。

比较：

- 准确率；
- 工具调用次数；
- 是否可解释；
- 是否易测试；
- 延迟和成本；
- 是否能用于生产。

### 项目产出

```text
examples/
  refund_plain_llm.py
  refund_react_agent.py
  refund_workflow_agent.py
  refund_workflow_rag_verified.py
docs/paradigm_learning_notes.md
```

### 达标标准

你能在面试中讲清楚：为什么交易履约更适合 Workflow Agent + Tool-use + RuleRAG，而不是完全开放式 ReAct。

---

# 第二部分：Agent Harness 架构与核心模块

---

## 阶段 3：Agent Harness 架构设计

### 学习目标

把 Agent 看成一个由多个工程模块组成的系统，而不是一个大 Prompt。

### Harness 模块总览

| 模块 | 解决的问题 | 输入 | 输出 | 常见实现 | 如何测试 |
|---|---|---|---|---|---|
| 输入理解层 | 标准化用户输入 | query | normalized request | LLM / 规则 | 意图覆盖率 |
| 意图识别层 | 判断任务类型 | query + history | intent | classifier / LLM | intent accuracy |
| 槽位抽取层 | 提取业务参数 | query | slots | structured output | slot F1 |
| 任务规划层 | 决定执行步骤 | state | plan / next node | 状态机 / LLM | plan validity |
| 上下文管理层 | 控制模型看到的信息 | state + memory + tools | compact context | selector / summarizer | context precision |
| 短期记忆 | 维护当前任务状态 | conversation | AgentState | LangGraph state | state consistency |
| 长期记忆 | 保存跨会话信息 | events | retrievable memory | DB / vector DB | memory retrieval |
| 工具注册层 | 管理可用工具 | tool schema | tool registry | function calling / MCP | tool schema test |
| 工具执行层 | 安全执行动作 | tool call | tool result | executor | tool success rate |
| 状态管理层 | 记录流程进展 | node output | state update | StateGraph | replay test |
| 反思修正层 | 修复错误 | trace + error | repaired action | verifier / critic | repair success |
| 约束安全层 | 防止危险行为 | input/action | allow/deny | guardrails / policy | adversarial test |
| 人工接管层 | 高风险兜底 | uncertain state | human decision | HITL | handoff precision |
| 评估日志层 | 衡量质量 | trace | metrics | eval runner | golden dataset |
| 观测运维层 | 支持线上排查 | run metadata | trace / dashboard | OTel / LangSmith | failure replay |

### 实践任务

画出 OrderFlow-Agent Harness 架构图：

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
Policy RAG / RuleRAG
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

### 项目产出

```text
docs/agent_harness_architecture.md
docs/architecture_diagram.png
app/agents/state.py
app/agents/workflow.py
app/agents/router.py
app/agents/guardrails.py
```

### 达标标准

你能对任意业务需求拆出 Agent 的核心模块，并说清楚每个模块的输入、输出、风险和测试方式。

---

## 阶段 4：工具调用、MCP 与 Agent Skills

### 学习目标

掌握工具调用的工程本质：模型只生成结构化调用意图，真正执行业务的是受控工具层。

### 核心知识

1. **Function Calling / Tool Calling**
   - 工具名；
   - 工具描述；
   - 参数 schema；
   - 返回 schema；
   - 错误 schema；
   - 权限级别；
   - 是否有副作用；
   - 是否需要人工确认。

2. **MCP 思想**
   - MCP Client；
   - MCP Server；
   - Tools；
   - Resources；
   - Prompts；
   - tool registry；
   - 权限和审计；
   - 工具供应链安全。

3. **Agent Skills 思想**
   - 工具是单个动作；
   - Skill 是可复用能力包；
   - Skill 可以包含说明文档、脚本、模板、示例、资源文件；
   - 适合把“订单处理”“规则判断”“日报生成”“代码审查”封装成能力模块。

4. **工具调用失败处理**
   - 参数缺失 → 澄清或补全；
   - 网络失败 → 重试；
   - 权限不足 → 拒绝或人工；
   - 工具成功但状态未变 → verification；
   - 重复调用有副作用 → 幂等 key；
   - 高风险工具 → 二次确认。

### 实践任务

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

进一步封装成 Skill：

```text
skills/
  order_fulfillment_skill/
    SKILL.md
    tools.py
    schemas.py
    examples.jsonl
    tests/
```

### 项目产出

```text
app/tools/
  order_tool.py
  logistics_tool.py
  policy_tool.py
  refund_tool.py
  ticket_tool.py
  verification_tool.py
app/mcp/
  client.py
  server.py
  registry.py
skills/order_fulfillment_skill/
```

### 达标标准

不依赖 LLM，也能手动跑通：

```text
输入订单号
→ 查订单
→ 查物流
→ 检索规则
→ 创建退款
→ 校验退款状态
```

同时能解释：哪些工具允许自动执行，哪些工具必须人工确认。

---

## 阶段 5：Memory 与 Context Engineering

### 学习目标

理解上下文工程比单纯 Prompt Engineering 更重要。模型质量取决于：你给它看什么、不让它看什么、以什么结构给它看。

### 核心知识

| 类型 | 作用 | 项目示例 |
|---|---|---|
| Conversation Memory | 当前多轮对话 | 用户刚补充订单号 |
| Working Memory | 当前任务状态 | AgentState 中订单、物流、规则 |
| Episodic Memory | 事件记忆 | 用户之前多次投诉物流 |
| Semantic Memory | 稳定知识 | 平台规则、业务概念 |
| Vector Memory | 语义检索 | 历史工单、FAQ |
| Summary Memory | 压缩摘要 | 长对话摘要 |
| Long-term Memory | 跨会话持久化 | 用户偏好、常见问题 |
| Scratchpad | 临时中间状态 | 节点临时结果 |

### Context Engineering 关键问题

1. 哪些信息必须进入上下文？
2. 哪些信息应该压缩？
3. 哪些信息不能进入上下文？
4. 工具结果如何压缩？
5. 长对话如何分层摘要？
6. 记忆何时写入？
7. 记忆冲突如何解决？
8. 如何评估记忆是否有用？

### Memory Write Policy

```text
长期偏好 → 可写长期记忆
当前任务状态 → 写 AgentState
工具结果 → 写 trace，不一定写长期记忆
敏感信息 → 默认不写长期记忆
不确定信息 → 不写或标记低置信度
用户明确要求删除 → 必须删除
```

### 实践任务

为 OrderFlow-Agent 设计三层记忆：

```text
短期：当前会话状态 AgentState
中期：当前订单/工单处理历史
长期：用户偏好、投诉模式、规则命中历史
```

### 项目产出

```text
app/memory/
  short_term.py
  long_term.py
  context_builder.py
  memory_policy.py
  summarizer.py
  conflict_resolver.py
tests/memory/
```

### 达标标准

你能解释清楚：为什么某条信息进入上下文，为什么某条信息不进入上下文，以及记忆错误时如何修复。

---

# 第三部分：RAG、规划、多 Agent 与微调

---

## 阶段 6：Agentic RAG、GraphRAG 与 RuleRAG

### 学习目标

从普通知识库问答升级为业务决策证据系统，让 Agent 的判断有依据、可追溯、可验证。

### 核心知识

| 技术 | 作用 |
|---|---|
| Query Rewrite | 把口语问题改写成检索问题 |
| Query Decomposition | 把复杂问题拆成多个检索子问题 |
| Hybrid Retrieval | BM25 + dense vector |
| Rerank | 对召回内容重排序 |
| Citation | 给出证据来源 |
| Grounding | 回答必须基于证据 |
| Permission-aware RAG | 基于用户权限过滤文档 |
| RuleRAG | 面向规则条款、条件、动作的检索 |
| GraphRAG | 用实体、关系、社区摘要增强复杂知识检索 |
| RAG Evaluation | context recall、faithfulness、citation accuracy |

### OrderFlow-Agent 中的 RuleRAG

普通 RAG：

```text
用户问题 → 检索文档 → 生成回答
```

业务型 RuleRAG：

```text
订单状态 + 物流状态 + 用户诉求
→ 生成规则检索 query
→ 检索规则条款
→ 提取适用条件
→ 支撑责任判断
→ 支撑动作决策
→ 记录证据链
```

### 实践任务

构建规则库：

```text
R001：商家超过 48 小时未发货，用户可申请全额退款。
R002：物流超过 7 天无更新，优先判定物流异常。
R003：已签收超过 7 天，非质量问题不支持无理由退款。
R004：平台补偿金额不得超过实付金额的 10%。
```

### 项目产出

```text
data/policies.json
rag/index_builder.py
rag/retriever.py
rag/reranker.py
rag/policy_parser.py
rag/citation_checker.py
rag/rule_reasoner.py
```

### 达标标准

输入：

```text
订单已支付 72 小时未发货，用户要求退款
```

系统输出：

```text
命中规则：R001
责任方：merchant
建议动作：refund
证据：商家超过 48 小时未发货
```

---

## 阶段 7：Planning、Reflection、Verifier 与自我修正

### 学习目标

掌握规划和反思的适用边界。不是所有任务都需要 planner，也不是所有任务都值得 reflection。

### 核心机制

| 机制 | 适合场景 | 不适合场景 |
|---|---|---|
| Task Planning | 多步骤目标明确任务 | 简单 FAQ |
| Subtask Decomposition | 复杂任务拆解 | 原子任务 |
| Dynamic Planning | 环境状态变化 | 固定流程 |
| Reflection | 代码、写作、复杂判断 | 实时客服高并发 |
| Critic Model | 需要质量评审 | 低价值任务 |
| Verifier | 有明确规则或答案 | 主观开放问题 |
| Retry Policy | 工具失败、格式错误 | 有副作用的重复操作 |
| Plan Repair | 执行中断、工具失败 | 无状态任务 |

### 设计原则

```text
高可靠业务：优先状态机 + 局部规划
开放任务：可以使用 planner
高风险动作：必须 verifier + human-in-the-loop
低价值任务：不要反思，直接回答
工具失败：优先 plan repair，而不是重新开始
```

### 实践任务

为 OrderFlow-Agent 加入：

1. 初始计划生成；
2. 工具失败后的 plan repair；
3. 决策前 verifier；
4. 高风险退款 human approval；
5. 执行后 final state verification。

### 项目产出

```text
app/agents/planner.py
app/agents/verifier.py
app/agents/retry_policy.py
app/agents/plan_repair.py
docs/planning_strategy.md
```

### 达标标准

你能说明：哪些节点由 LLM 决策，哪些节点由代码状态机控制，哪些节点必须进入人工确认。

---

## 阶段 8：Multi-Agent 系统与 Agent-to-Agent 协作

### 学习目标

理解 Multi-Agent 的价值不是“Agent 数量多”，而是专业分工、协作协议、轨迹可评估。

### 核心模式

| 模式 | 说明 | 适合项目 |
|---|---|---|
| Supervisor-Worker | 一个主管分配任务给多个专家 | 客服分流、企业助手 |
| Planner-Executor | 一个负责规划，一个负责执行 | 长任务自动化 |
| Researcher-Writer-Reviewer | 研究、写作、审查分离 | 报告生成 |
| Critic-Reflector | 生成与批评分离 | 代码修复、内容审核 |
| Debate | 多个 Agent 辩论 | 决策评审，生产慎用 |
| Swarm | 多个轻量 Agent 协作 | 研究探索，生产慎用 |
| Blackboard | 共享状态板协作 | 复杂任务协同 |
| A2A 思想 | Agent 间协议化通信 | 跨系统 Agent 协作 |

### OrderFlow-Agent 多 Agent 设计

```text
Coordinator Agent：总控调度
Context Agent：意图识别、槽位补全、上下文整理
Business Agent：订单、物流、售后状态查询
Policy Agent：规则检索、规则解释、证据提取
Decision Agent：责任归因、退款/补偿/转人工决策
Execution Agent：退款、补偿、工单工具执行
Verification Agent：最终状态校验、风险检查
```

### 设计原则

不是每个 Agent 都必须调用 LLM：

```text
Context Agent：LLM
Business Agent：API + 规则代码
Policy Agent：RAG + LLM
Decision Agent：LLM + 规则约束
Execution Agent：纯工具调用
Verification Agent：规则代码 + 少量 LLM
Coordinator Agent：LangGraph 条件路由
```

### 项目产出

```text
app/multi_agent/
  coordinator.py
  context_agent.py
  business_agent.py
  policy_agent.py
  decision_agent.py
  execution_agent.py
  verification_agent.py
  shared_state.py
docs/multi_agent_design.md
```

### 达标标准

你能记录每个 Agent 的输入、输出、工具调用、耗时、失败原因、最终贡献，并能评估多 Agent 是否真的比单 Agent 更好。

---

## 阶段 9：Agent 微调工程

### 学习目标

理解微调在 Agent 中的边界：微调不是第一选择，而是在 Prompt、RAG、工具、评估稳定之后的优化手段。

### 什么时候需要微调

适合微调：

- 固定格式输出不稳定；
- 领域术语和语气要求高；
- 工具调用选择有稳定模式；
- 有大量高质量轨迹数据；
- 希望用小模型降低成本。

不适合微调：

- 业务规则经常变化；
- 事实知识频繁更新；
- 数据少；
- 问题主要来自检索或工具设计；
- 没有评估集。

### 核心知识

| 技术 | 在 Agent 中的作用 |
|---|---|
| SFT | 学会格式、工具调用风格、领域话术 |
| DPO / Preference Learning | 学会偏好更好的决策或回复 |
| Tool-use Data | query、state、tool call、tool result、final answer |
| Trajectory Data | plan、action、observation、state、final |
| Rejection Sampling | 多次生成并筛选高质量样本 |
| Synthetic Data | 用强模型合成训练数据 |
| Domain Adaptation | 小模型领域适配 |
| Eval after FT | 微调前后任务成功率、格式错误率、成本对比 |

### 实践项目

```text
MiniToolAgent-SFT：面向客服工具调用的小模型微调实验
```

流程：

1. 构造 500—2000 条客服工具调用样本；
2. 样本包含 query、state、tool call、tool result、final answer；
3. 使用 LoRA / QLoRA 做小模型 SFT；
4. 与 prompt-only 大模型比较工具调用准确率；
5. 分析微调是否值得。

### 项目产出

```text
fine_tuning/
  data/tool_use_train.jsonl
  data/tool_use_eval.jsonl
  train_lora.py
  eval_tool_call.py
  report.md
```

### 达标标准

你能回答：这个问题应该用 Prompt、RAG、工具工程还是微调解决，为什么？

---

# 第四部分：安全、评估、生产与维护

---

## 阶段 10：Agent 安全、约束与可靠性

### 学习目标

掌握生产级 Agent 的安全边界，不让模型越权、误操作、泄露数据或被注入攻击操控。

### 核心风险

| 风险 | 示例 | 防御 |
|---|---|---|
| Prompt Injection | 用户让模型忽略系统规则 | 指令分层、输入隔离、规则校验 |
| Jailbreak | 绕过安全策略 | policy engine、输出过滤 |
| Tool Misuse | 模型乱退款 | 权限、确认、业务校验 |
| Data Leakage | 泄露其他用户订单 | RBAC、数据过滤 |
| Unsafe Action | 高风险动作自动执行 | human-in-the-loop |
| Context Pollution | 文档内容污染系统指令 | 不可信内容隔离 |
| Memory Poisoning | 写入错误长期记忆 | memory write policy |
| MCP Tool Risk | 外部工具供应链风险 | 白名单、沙箱、审计 |
| Skill Supply Chain Risk | Skill 中脚本或说明不可信 | 签名、审核、权限边界 |

### 生产级安全设计

```text
输入层：内容分类 + 注入检测
上下文层：可信/不可信信息隔离
记忆层：写入策略 + 冲突处理 + 敏感信息过滤
工具层：权限控制 + 参数校验 + 幂等 + 审计
决策层：policy engine + verifier
执行层：高风险动作二次确认
输出层：敏感信息过滤 + 格式校验
观测层：全链路 trace + audit log
```

### 实践任务

为 OrderFlow-Agent 增加 6 类 guardrail：

1. Prompt injection 检测；
2. 退款金额上限；
3. 用户权限校验；
4. 高风险动作人工确认；
5. 输出敏感信息脱敏；
6. 工具和 Skill 白名单。

### 项目产出

```text
app/security/
  injection_detector.py
  permission.py
  policy_engine.py
  output_filter.py
  audit_log.py
  tool_sandbox.py
tests/security/
```

### 达标标准

通过 30—50 条 adversarial test case，系统不能越权退款、泄露订单或执行不合规工具调用。

---

## 阶段 11：Agent 评估、测试集构建与可观测性

### 学习目标

把 Agent 从“感觉效果不错”变成能量化、能回归、能定位失败原因的系统。

### 为什么 Agent 难评估

Agent 不是单次文本生成，而是多步骤系统：

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

每一步都可能错，因此要做 trace / trajectory / DAG 级评估。

### 完整评估体系

| 层级 | 指标 |
|---|---|
| 输入理解 | Intent Accuracy、Slot F1 |
| 检索层 | Recall@K、MRR、Citation Accuracy |
| 工具层 | Tool Selection Accuracy、Argument Accuracy、Tool Success Rate |
| 轨迹层 | Step Accuracy、Trajectory Match、DAG Validity |
| 规划层 | Plan Validity、Step Efficiency |
| 决策层 | Responsibility Accuracy、Action Accuracy |
| 安全层 | Unsafe Action Rate、Injection Defense Rate |
| 输出层 | Faithfulness、Helpfulness、Format Validity |
| 端到端 | Task Success Rate、Human Escalation Precision |
| 系统层 | Latency、Cost、Retry Rate、Fallback Rate |
| 用户层 | Satisfaction、Resolution Rate |

### 测试集类型

- Golden Dataset：标准业务样本；
- Adversarial Test Set：攻击和边界样本；
- Regression Test Set：历史失败样本；
- Scenario-based Evaluation：按业务流程设计样本；
- Synthetic Test Set：合成覆盖长尾场景；
- Online Eval：线上抽样评估；
- Human Review Set：人工标注困难样本。

### Failure Taxonomy

```text
F1 意图识别错误
F2 槽位缺失
F3 检索不到规则
F4 命中错误规则
F5 工具选择错误
F6 工具参数错误
F7 工具顺序错误
F8 责任判断错误
F9 动作决策错误
F10 工具执行失败
F11 状态校验失败
F12 输出不忠实
F13 安全违规
F14 成本或延迟超限
```

### 实践任务

为 OrderFlow-Agent 构建测试集：

```json
{
  "case_id": "C001",
  "user_query": "我的订单三天没发货，我要退款",
  "order_status": "paid",
  "logistics_status": "not_shipped",
  "expected_intent": "refund_request",
  "expected_policy_ids": ["R001"],
  "expected_responsible_party": "merchant",
  "expected_action": "refund",
  "expected_tool_sequence": ["query_order", "query_logistics", "search_policy", "create_refund", "verify_final_state"]
}
```

### 项目产出

```text
eval/
  datasets/golden.jsonl
  datasets/adversarial.jsonl
  datasets/regression.jsonl
  runner.py
  metrics.py
  trajectory_metrics.py
  failure_taxonomy.py
  report_generator.py
```

### 达标标准

你能跑出完整报告：

```text
Intent Accuracy
Policy Recall
Tool Call Accuracy
Trajectory Accuracy
Action Accuracy
End-to-End Success Rate
Avg Latency
Avg Cost
Failure Distribution
Regression Pass Rate
```

---

## 阶段 12：Agent 生产部署、AgentOps 与长期维护

### 学习目标

把 Demo 级 Agent 变成生产级 Agent：可部署、可监控、可灰度、可回滚、可持续优化。

### 生产架构

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
Tool / MCP Services
  ↓
Redis / PostgreSQL / Vector DB
  ↓
Observability + Eval + Audit + Failure Collector
```

### 核心能力

| 能力 | 实现 |
|---|---|
| 队列 | Redis Queue / Celery |
| 缓存 | query cache、retrieval cache、tool result cache |
| 限流 | Redis token bucket |
| 熔断 | 模型或工具失败率过高自动切换 |
| 降级 | 强模型失败 → 弱模型 / 规则兜底 / 人工 |
| 多模型路由 | cheap / reasoning / fast / fallback |
| Prompt 版本管理 | prompt registry + version |
| Tool 版本管理 | tool schema version |
| Skill 版本管理 | skill registry + changelog |
| Memory 版本管理 | memory schema + write policy |
| Eval as CI Gate | 每次变更跑回归集 |
| 灰度发布 | 按用户/流量切分 |
| 反馈闭环 | 失败样本进入 eval dataset |
| AgentOps | trace、成本、延迟、失败率、回放 |

### 实践任务

为 OrderFlow-Agent 增加：

- Docker Compose；
- Redis 缓存；
- PostgreSQL 存储；
- LiteLLM 模型网关；
- trace_id；
- span 级记录；
- token / cost 统计；
- 失败样本自动沉淀；
- eval CI gate。

### 项目产出

```text
docker-compose.yml
app/llm/router.py
app/observability/tracing.py
app/ops/failure_collector.py
app/ops/eval_ci_gate.py
docs/deployment.md
docs/maintenance_playbook.md
```

### 达标标准

你能解释一次线上失败请求：

```text
从哪里查日志
如何定位失败节点
如何复现
如何修复
如何加入回归测试
如何评估修复是否有效
如何灰度上线
```

---

# 第五部分：业务项目、作品集与求职表达

---

## 阶段 13：业务场景落地训练

### 场景 1：电商客服 / 交易履约 Agent

| 项目 | 内容 |
|---|---|
| 业务流程 | 查订单、查物流、读规则、判断责任、退款/补偿/转人工 |
| 工具 | 订单 API、物流 API、规则检索、退款、工单 |
| 数据 | 订单、物流、售后规则、历史工单 |
| 风险 | 错误退款、越权查询、规则误判 |
| 指标 | 责任判断准确率、动作准确率、端到端成功率 |
| 项目 | OrderFlow-Agent |
| 简历表达 | 设计并实现面向交易履约场景的可验证 Agent 决策系统，支持规则 RAG、工具调用、状态校验和端到端评估 |

### 场景 2：企业知识库 Agent

| 项目 | 内容 |
|---|---|
| 业务流程 | 文档入库、权限过滤、检索、回答、引用、反馈 |
| 工具 | 文档解析、向量库、搜索、权限系统 |
| 数据 | FAQ、制度文档、产品文档 |
| 风险 | 幻觉、错误引用、越权访问 |
| 指标 | Context Recall、Faithfulness、Citation Accuracy |
| 项目 | SmartKB-Agent |
| 简历表达 | 构建企业级知识库 Agent，支持混合检索、引用校验、权限过滤和 RAG 自动评估 |

### 场景 3：代码开发 Agent

| 项目 | 内容 |
|---|---|
| 业务流程 | 读 issue、理解代码、定位 bug、生成 patch、运行测试 |
| 工具 | Git、文件系统、测试框架、静态分析 |
| 数据 | GitHub issue、repo、测试用例 |
| 风险 | 破坏代码、安全执行 |
| 指标 | Patch Pass Rate、Test Pass Rate |
| 项目 | CodeFix-Agent |
| 简历表达 | 实现面向代码仓库的自动修复 Agent，支持代码检索、测试生成、补丁验证和失败回放 |

### 场景 4：数据分析 Agent

| 项目 | 内容 |
|---|---|
| 业务流程 | 读表、理解指标、生成 SQL、执行分析、可视化 |
| 工具 | SQL、Python、BI、文件系统 |
| 数据 | CSV、数据库、指标定义 |
| 风险 | SQL 错误、指标误解、数据泄露 |
| 指标 | SQL Accuracy、Insight Quality、Execution Success |
| 项目 | DataAnalyst-Agent |
| 简历表达 | 构建数据分析 Agent，支持 NL2SQL、指标解释、图表生成和分析报告输出 |

### 场景 5：受限医疗 / 金融 Agent

| 项目 | 内容 |
|---|---|
| 业务流程 | 信息收集、资料检索、风险提示、人工转接 |
| 工具 | 权威资料库、规则引擎、人工审核 |
| 数据 | 指南、合规规则、案例 |
| 风险 | 高风险建议、合规问题 |
| 指标 | 安全拒答率、引用准确率、人工接管准确率 |
| 项目 | GuardedDomain-Agent |
| 简历表达 | 设计受限领域 Agent 安全架构，支持权限边界、引用证据、风险识别和人工接管 |

---


## 阶段 14：学习节奏与时间规划

### 3 个月计划：完成一个强项目

| 周期 | 学习重点 | 阶段成果 | 博客主题 |
|---|---|---|---|
| 第 1—2 周 | Python 工程化、FastAPI、Pydantic | 项目骨架、业务模拟接口 | Agent 工程项目如何搭骨架 |
| 第 3—4 周 | Prompt、structured output、tool calling | 工具层、结构化输出 | 为什么 Schema 比 Prompt 更重要 |
| 第 5—6 周 | LangGraph、Workflow Agent | 单 Agent 履约闭环 | 用 LangGraph 实现业务状态图 |
| 第 7—8 周 | RuleRAG、证据链 | 规则检索与责任判断 | 业务型 RAG 与普通 RAG 的区别 |
| 第 9—10 周 | 评估系统 | 100 条测试集和指标报告 | Agent 如何做端到端评估 |
| 第 11—12 周 | 多 Agent、部署、README | 完整 GitHub 项目 | OrderFlow-Agent 项目复盘 |

达标标准：

- GitHub 有完整项目；
- README 有架构图、流程图、运行方法、评估结果；
- 面试能讲 15 分钟。

### 6 个月计划：形成岗位竞争力

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

### 12 个月计划：形成长期壁垒

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

## 阶段 15：推荐资料清单

### 官方文档

- OpenAI API：Structured Outputs、Function Calling、Fine-tuning、Agents SDK、Evals；
- Anthropic Claude：Prompt Engineering、Tool Use、Agent Skills；
- LangGraph：StateGraph、Durable Execution、Human-in-the-loop、Memory；
- LangSmith：Evaluation、Datasets、Tracing；
- LlamaIndex：Workflows、Agents、RAG；
- AutoGen：Multi-Agent Framework；
- CrewAI：Role-based Multi-Agent、Flows；
- MCP：Tools、Resources、Prompts、Client/Server；
- OpenTelemetry：GenAI Semantic Conventions；
- Ragas：RAG / Agent Evaluation；
- DSPy：Prompt / Program Optimization。

### 经典论文关键词

- ReAct；
- Reflexion；
- Toolformer；
- Self-Refine；
- Plan-and-Solve；
- Generative Agents；
- Voyager；
- SWE-bench；
- AgentBench；
- WebArena；
- GAIA；
- τ-bench。

### Benchmark / Evaluation

- Ragas；
- LangSmith Eval；
- AgentBench；
- SWE-bench；
- GAIA；
- τ-bench；
- WebArena；
- BEIR；
- MTEB。

### 长期跟踪

- OpenAI Developers；
- Anthropic Engineering；
- LangChain Blog；
- LlamaIndex Blog；
- Microsoft AutoGen / Agent Framework；
- Hugging Face Blog；
- Stanford DSPy；
- OWASP LLM Security；
- MCP 社区与工具生态。

---

## 阶段 16：最终能力检查清单

### 理论理解

- [ ] 能解释 ReAct、Plan-and-Execute、Reflection、Workflow Agent、Agentic RAG、Multi-Agent 的区别；
- [ ] 能判断一个业务场景是否需要 Agent；
- [ ] 能说明 Agent 相比普通 LLM 应用的核心差异；
- [ ] 能解释为什么高可靠业务更适合 Workflow + Tool + Verification。

### 架构设计

- [ ] 能画出 Agent Harness 架构；
- [ ] 能设计输入、状态、上下文、记忆、工具、规划、安全、评估模块；
- [ ] 能说明每个模块的输入、输出、风险和测试方式；
- [ ] 能从业务流程倒推出 Agent 架构。

### 工程实现

- [ ] 能用 FastAPI + Pydantic 搭建 Agent 后端；
- [ ] 能用 LangGraph 实现状态图；
- [ ] 能实现 tool calling、structured output、streaming；
- [ ] 能写单元测试、节点测试和端到端测试；
- [ ] 能接 Redis、PostgreSQL 和向量库。

### 工具调用

- [ ] 能设计 tool schema；
- [ ] 能做权限控制、参数校验、幂等控制；
- [ ] 能处理工具失败、重试和状态校验；
- [ ] 能做工具调用日志和审计；
- [ ] 能理解 MCP 和 Skill Registry 的工程价值。

### RAG

- [ ] 能实现文档切分、embedding、检索、rerank、引用；
- [ ] 能做 query rewrite 和 query decomposition；
- [ ] 能实现 RuleRAG 或业务证据链；
- [ ] 能评估 context recall、faithfulness 和 citation accuracy。

### Memory

- [ ] 能区分短期、长期、语义、事件、向量、摘要记忆；
- [ ] 能设计 memory write policy；
- [ ] 能处理记忆冲突和上下文污染；
- [ ] 能评估记忆是否真正提升任务成功率。

### Multi-Agent

- [ ] 能设计 supervisor-worker、planner-executor、critic-reflector；
- [ ] 能记录多 Agent trace；
- [ ] 能评估多 Agent 的成本和收益；
- [ ] 能避免为了多 Agent 而多 Agent；
- [ ] 能设计 Agent 间共享状态和通信协议。

### 安全

- [ ] 能识别 prompt injection、tool misuse、data leakage；
- [ ] 能设计 guardrails、policy engine、human-in-the-loop；
- [ ] 能实现输出校验和审计日志；
- [ ] 能设计 MCP / Skill 安全边界。

### 评估

- [ ] 能构造 golden dataset；
- [ ] 能设计 adversarial test set；
- [ ] 能评估 tool accuracy、trajectory accuracy、task success、latency、cost；
- [ ] 能做 failure taxonomy 和回归测试；
- [ ] 能把 eval 接入 CI。

### 部署维护

- [ ] 能用 Docker 部署；
- [ ] 能接 Redis / PostgreSQL / 向量库；
- [ ] 能做模型 fallback、限流、缓存、trace；
- [ ] 能处理线上失败样本闭环；
- [ ] 能做 prompt / tool / skill / memory 版本管理。

### 项目表达

- [ ] GitHub README 有架构图、流程图、运行方法、评估结果；
- [ ] 简历能写出指标和架构亮点；
- [ ] 面试能讲清楚 trade-off；
- [ ] 能把项目包装成软著、博客或论文方向。

