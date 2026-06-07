# 阶段 2：Agent 基础范式理论学习笔记（2026 版）

> 主题：ReAct、Plan-and-Execute、Reflection、Workflow Agent、Router Agent、Agentic RAG、Multi-Agent  
> 定位：Agent 工程学习长期笔记  
> 目标：建立对主流 Agent 范式的系统理解，掌握不同范式的执行机制、适用边界、工程优缺点、业务选型方法和生产落地注意事项。  
> 核心结论：Agent 不是“让模型自由发挥”，而是用工程结构组织模型完成多步骤任务。成熟的 Agent 系统往往不是单一范式，而是 **Workflow 控制主链路 + 局部 ReAct 探索 + 局部 Reflection 复核 + Guardrails 约束 + Evaluation 回归** 的组合系统。

---

## 1. 阶段学习目标

### 1.1 为什么要学习 Agent 范式

Agent 范式解决的不是“如何调用一次大模型 API”的问题，而是解决：

> 当一个任务无法通过一次模型回复完成时，如何组织模型进行多步骤推理、工具调用、观察反馈、状态更新、错误恢复和最终交付。

普通 LLM 调用通常是：

```text
用户输入
→ 模型生成
→ 输出答案
```

Agent 系统更接近：

```text
用户任务
→ 任务理解
→ 状态初始化
→ 规划或路由
→ 工具调用
→ 获取观察结果
→ 更新状态
→ 检索证据
→ 决策或复核
→ 安全校验
→ 终止或继续
→ 输出结果
```

所以，Agent 的核心不是“模型更聪明”，而是“系统更会组织任务”。

---

### 1.2 学完本阶段后要具备的能力

学完本阶段后，你应该能够回答：

1. 一个任务适合普通 LLM、RAG、Workflow、ReAct、Plan-and-Execute、Reflection、Multi-Agent，还是根本不该用 Agent？
2. ReAct 为什么适合搜索、代码修复、浏览器操作、数据探索，但不适合裸用于高风险交易动作？
3. Plan-and-Execute 为什么适合目标明确的多步骤任务，但为什么计划必须可验证、可中断、可重规划？
4. Reflection 为什么能提升代码修复、报告生成、复杂决策的质量，但为什么不适合低延迟、高并发客服主链路？
5. Workflow Agent 为什么不是“低级写死流程”，反而是生产级 Agent 最常见的主控结构？
6. Multi-Agent 什么时候有价值，什么时候只是增加成本、延迟和调试难度？
7. 如何为一个真实业务系统选择合适的 Agent 范式组合，并设计终止条件、安全边界和评估指标？

---

### 1.3 本阶段的学习重点

本阶段不追求马上写复杂代码，而是先建立架构判断力。重点包括：

- 理解 Agent 与普通 LLM 调用的本质区别；
- 理解 Agent 与 Workflow 的边界；
- 掌握 ReAct、Plan-and-Execute、Reflection 的核心机制；
- 补充理解 Workflow Agent、Router Agent、Agentic RAG、Multi-Agent；
- 能根据任务的不确定性、风险、成本、延迟和可测试性选择范式；
- 能把范式落到真实业务链路中，而不是停留在论文概念。

---

## 2. Agent 范式的整体理解

### 2.1 什么是 Agent 范式

Agent 范式可以理解为：

> 大模型在复杂任务中组织“理解、规划、行动、观察、记忆、修正、终止”的控制结构。

它不是某一个框架，也不是某一个 Prompt，而是一种任务执行方式。

不同范式的差异主要体现在：

| 关键问题 | 不同范式的差异 |
|---|---|
| 是否先规划 | Plan-and-Execute 会先规划，ReAct 通常边执行边调整 |
| 是否动态选择工具 | ReAct、Tool-use Agent 更动态，Workflow 更固定 |
| 是否固定流程 | Workflow 固定主路径，Agent 动态决定局部路径 |
| 是否允许反思 | Reflection 显式检查和修正已有结果 |
| 是否多角色协作 | Multi-Agent 将任务拆给多个角色或专家 |
| 是否需要显式状态 | 生产级 Agent 通常需要状态管理、checkpoint 和 trace |
| 是否容易测试 | Workflow 最容易测试，自由 Agent 最难测试 |
| 是否适合高风险动作 | 高风险动作需要 Workflow、Guardrails、HITL，而不是裸 Agent |

---

### 2.2 Agent 与普通 LLM 调用的区别

普通 LLM 调用的目标是：

```text
生成一个答案
```

Agent 的目标是：

```text
完成一个任务
```

例如用户说：

```text
帮我处理一下这个退款申请
```

普通 LLM 可能只会生成一段客服话术。

Agent 则需要：

```text
识别退款意图
→ 获取订单号
→ 查询订单状态
→ 查询物流状态
→ 检索平台规则
→ 判断责任方
→ 判断是否符合退款条件
→ 请求用户确认
→ 调用退款工具
→ 校验退款状态
→ 回复用户
→ 记录 trace 和评估数据
```

因此，Agent 是“任务执行系统”，LLM 只是其中的一个能力组件。

---

### 2.3 Agent 与 Workflow 的区别

可以这样理解：

```text
Workflow：流程主要由开发者控制
Agent：流程中的一部分由模型动态决定
```

| 维度 | Workflow | Agent |
|---|---|---|
| 控制方式 | 开发者预定义流程 | 模型根据状态动态选择 |
| 稳定性 | 高 | 中等，取决于约束 |
| 灵活性 | 中等 | 高 |
| 可测试性 | 强 | 较弱 |
| 成本可控性 | 强 | 较弱 |
| 适合场景 | 审批、退款、履约、风控、工单 | 搜索、研究、代码、浏览器、开放工具探索 |
| 常见风险 | 流程僵硬、覆盖不全 | 循环、误调用、成本失控、越权执行 |

在真实系统中，Workflow 与 Agent 并不冲突。更常见的生产结构是：

```text
Workflow 控制主流程
+ Agent 在局部节点处理不确定性
+ Guardrails 约束工具与输出
+ Human-in-the-loop 兜底高风险动作
```

一句话：

> 让代码控制确定性，让模型处理不确定性。

---

### 2.4 Agent 的核心组成环节

一个完整 Agent 系统通常包含以下环节。

| 环节 | 作用 | 示例 |
|---|---|---|
| 输入理解 | 将用户自然语言转成结构化任务 | intent、slots、risk_tags |
| 状态管理 | 保存当前任务进度和上下文 | AgentState、checkpoint |
| 规划/路由 | 决定下一步做什么 | planner、router、conditional edge |
| 工具调用 | 连接外部系统 | 查询订单、搜索规则、执行退款 |
| 观察反馈 | 接收工具返回结果 | order_status、logistics_status |
| 检索增强 | 获取外部知识证据 | RAG、policy evidence |
| 决策判断 | 根据状态和证据给出建议 | refund_allowed、human_handoff |
| 复核修正 | 对复杂或高风险结果进行检查 | verifier、reflection |
| 安全约束 | 防止越权、泄露和误执行 | guardrails、policy engine |
| 人工接管 | 高风险或低置信度时转人工 | HITL approval |
| 可观测性 | 记录执行轨迹和指标 | trace、latency、cost、failure taxonomy |
| 终止条件 | 判断继续、结束、追问或转人工 | max_steps、done、need_more_info |

---

## 3. ReAct 范式

### 3.1 核心思想

ReAct 来自论文 **ReAct: Synergizing Reasoning and Acting in Language Models**。它的核心思想是让模型交替产生：

```text
Reasoning / Thought
Action
Observation
```

也就是：

```text
Thought
→ Action
→ Observation
→ Thought
→ Action
→ Observation
→ Final Answer
```

ReAct 的关键价值在于：

> 把模型的推理过程和外部环境交互过程结合起来，让模型可以边查证、边行动、边修正。

---

### 3.2 Reasoning、Action、Observation 分别是什么

| 元素 | 含义 | 示例 |
|---|---|---|
| Reasoning / Thought | 模型对当前状态的判断 | “需要先确认订单是否存在” |
| Action | 模型选择要调用的工具或执行的动作 | `query_order(order_id)` |
| Observation | 工具或环境返回的结果 | “订单已支付，未发货” |

ReAct 的重点不是“让模型输出很长的思考过程”，而是：

```text
每一步行动都要有当前状态依据；
每一次工具返回都要更新后续决策。
```

在生产环境中，通常不需要把完整隐藏推理链暴露给用户，而应将中间过程转成结构化状态、工具调用日志和证据列表。

---

### 3.3 ReAct 与普通 Chain-of-Thought 的区别

| 维度 | Chain-of-Thought | ReAct |
|---|---|---|
| 核心 | 模型内部逐步推理 | 推理与外部行动交替 |
| 是否调用工具 | 通常不调用 | 强依赖工具 |
| 信息来源 | 输入上下文 + 模型知识 | 输入上下文 + 工具/环境 |
| 是否能更新状态 | 较弱 | 强 |
| 适合场景 | 数学、逻辑、解释型任务 | 搜索、多跳问答、工具调用、代码调试 |
| 主要风险 | 推理看似合理但事实错误 | 工具误用、循环调用、成本高 |

一句话：

```text
CoT 是“想清楚”；
ReAct 是“边想边查边做”。
```

---

### 3.4 ReAct 与 Tool Calling 的区别

Tool Calling 是能力：

```text
模型可以生成工具调用参数
```

ReAct 是控制循环：

```text
模型在多轮 Thought-Action-Observation 中动态决定下一步
```

因此，一个系统支持 Tool Calling，不代表它一定是 ReAct。只有当它存在“思考—行动—观察—再思考”的循环结构时，才更接近 ReAct。

---

### 3.5 ReAct 执行流程

```text
用户任务
  ↓
模型理解目标
  ↓
判断下一步需要什么信息
  ↓
选择工具并生成参数
  ↓
工具返回观察结果
  ↓
模型更新状态
  ↓
继续调用工具或生成最终答案
  ↓
达到终止条件
```

---

### 3.6 ReAct 示例：退款申请

```text
用户：我的订单三天没发货，我要退款

Step 1:
需要先确认订单状态。
Action: query_order(order_id)

Observation:
订单已支付，商家未发货。

Step 2:
还需要确认物流是否有揽收记录。
Action: query_logistics(order_id)

Observation:
无揽收记录，距离付款已超过 72 小时。

Step 3:
需要查询延迟发货退款规则。
Action: search_policy("付款后超过72小时未发货是否支持退款")

Observation:
命中规则：商家超时未发货，用户可申请退款。

Step 4:
退款属于高风险动作，需要确认前置条件。
Action: verify_refund_precondition(order_id)

Observation:
订单仍未发货，未退款，金额一致。

Final:
当前信息支持进入退款处理流程，但执行退款前需要用户确认。
```

---

### 3.7 ReAct 的优势

| 优势 | 说明 |
|---|---|
| 动态性强 | 工具返回不同，下一步可以不同 |
| 适合不确定环境 | 适合搜索、浏览器、代码调试等开放任务 |
| 轨迹可解释 | 可以记录每一步工具选择和观察结果 |
| 能减少纯生成幻觉 | 可通过外部工具补充事实 |
| 容易接工具生态 | 搜索、数据库、API、文件系统、代码执行器都可接入 |

---

### 3.8 ReAct 的缺点

| 缺点 | 说明 |
|---|---|
| 容易循环 | 没有终止条件时可能反复搜索或调用工具 |
| 成本高 | 每一步都可能消耗模型调用和工具调用 |
| 延迟高 | 多轮循环不适合低延迟场景 |
| 可测试性弱 | 每次路径可能不同，回归测试难度大 |
| 工具误用风险 | 可能调错工具、传错参数、重复调用有副作用工具 |
| 安全风险高 | 如果工具权限过大，注入攻击可能诱导越权操作 |

---

### 3.9 ReAct 适用场景

适合：

- 搜索型问答；
- 多跳事实核查；
- 代码调试；
- 浏览器操作；
- 数据探索；
- 文档交叉验证；
- 工具结果会显著影响后续路径的任务。

不适合裸用在：

- 支付；
- 退款；
- 删除数据；
- 账号权限修改；
- 高风险审批；
- 强合规医疗/金融建议；
- 无步数限制的开放工具执行。

这些场景可以局部使用 ReAct，但主流程应由 Workflow 或状态机控制。

---

### 3.10 ReAct 工程落地 Checklist

```text
[ ] 设置 max_steps，避免无限循环
[ ] 工具必须有 allowlist
[ ] 工具参数必须 schema 校验
[ ] 工具返回必须结构化
[ ] 有副作用工具需要幂等 key
[ ] 高风险工具需要用户确认或人工审批
[ ] 每一步记录 trace
[ ] 工具失败有 fallback 或停止策略
[ ] 用户输入和检索内容按不可信上下文处理
[ ] 最终答案必须基于工具结果和证据
```

一句话总结：

> ReAct 适合开放式探索，但不能无限自由执行。

---

## 4. Plan-and-Execute 范式

### 4.1 核心思想

Plan-and-Execute 的核心是：

```text
先规划，再执行
```

它通常分为两个角色或阶段：

```text
Planner：把任务拆成步骤
Executor：按步骤执行任务
```

Plan-and-Solve Prompting 提出的关键思想是：先制定计划，将完整任务拆成子任务，再按计划执行，以减少多步骤推理中的 missing-step errors。

---

### 4.2 Plan-and-Execute 与 ReAct 的区别

| 维度 | ReAct | Plan-and-Execute |
|---|---|---|
| 控制方式 | 边执行边决策 | 先规划再执行 |
| 任务拆解 | 动态隐式拆解 | 显式拆解 |
| 灵活性 | 强 | 中等 |
| 稳定性 | 中等 | 更高 |
| 可测试性 | 较弱 | 更强 |
| 成本 | 可能较高 | 可控性更好 |
| 适合任务 | 开放探索 | 目标明确的多步骤任务 |
| 主要风险 | 循环、误调用工具 | 计划过时、规划错误 |

一句话：

```text
ReAct 像“边走边看地图”；
Plan-and-Execute 像“先规划路线，再按路线执行”。
```

---

### 4.3 Plan-and-Execute 的执行流程

```text
用户任务
  ↓
Planner 生成任务计划
  ↓
Plan Validator 检查计划是否合法
  ↓
Executor 执行第 1 步
  ↓
保存 step result
  ↓
Executor 执行第 2 步
  ↓
必要时 Replanner 更新计划
  ↓
执行完所有步骤
  ↓
汇总结果
  ↓
输出或进入人工确认
```

---

### 4.4 示例：退款申请

```text
用户：我的订单三天没发货，我要退款

Plan:
1. 获取订单号
2. 查询订单状态
3. 查询物流状态
4. 检索延迟发货退款规则
5. 判断订单事实是否匹配规则
6. 如果满足条件，执行退款前置校验
7. 请求用户确认退款
8. 调用退款工具
9. 校验退款状态
10. 回复用户
```

这类范式的好处是：

```text
整体路径清晰；
每一步职责明确；
更适合日志、测试、审计和人工接管。
```

---

### 4.5 Plan-and-Execute 的优势

| 优势 | 说明 |
|---|---|
| 结构清晰 | 任务被拆成多个步骤，便于理解和复盘 |
| 适合长任务 | 报告、数据分析、文档处理、流程任务 |
| 易工程化 | 可转化为状态机、DAG、Workflow、多 Agent 协作 |
| 易测试 | 每一步都有输入输出，可单测和回归测试 |
| 成本可优化 | Planner 用强模型，Executor 可用弱模型、规则或代码 |
| 便于权限控制 | 高风险步骤可以提前识别并要求确认 |

---

### 4.6 Plan-and-Execute 的缺点

| 缺点 | 说明 |
|---|---|
| 计划可能过时 | 后续工具结果可能推翻原计划 |
| 计划可能错误 | Planner 可能编造不存在的工具或错误顺序 |
| 对动态环境适应较弱 | 环境变化大时，固定计划不够灵活 |
| 需要计划校验 | 不能直接相信模型生成的计划 |
| 可能过度规划 | 简单任务也规划很多步，增加成本 |

例如：

```text
计划第 6 步是退款
但第 2 步发现订单已经签收
```

这时必须中断原计划，进入重新规划或人工处理。

---

### 4.7 生产级 Plan-and-Execute 架构

推荐结构：

```text
Planner
  ↓
Plan Schema Validation
  ↓
Plan Policy Check
  ↓
Executor
  ↓
Step Checkpoint
  ↓
Verifier
  ↓
Replan / Continue / Stop / Human Review
```

关键控制点：

| 控制点 | 作用 |
|---|---|
| Plan schema | 限制计划格式，避免自由文本不可执行 |
| Tool registry | 限制 Planner 只能选择已有工具 |
| Plan validator | 检查步骤顺序、权限、风险 |
| Step checkpoint | 每步保存状态，支持恢复和审计 |
| Replanning | 工具结果改变时更新计划 |
| Human approval | 高风险计划需要人工确认 |
| Stop condition | 避免无限规划和无限执行 |

---

### 4.8 Plan-and-Execute 适用场景

适合：

- 旅行规划；
- 数据分析；
- 报告生成；
- 文档处理；
- 工单处理；
- 企业流程自动化；
- 代码仓库任务拆解；
- 电商履约任务规划。

不适合：

- 简单 FAQ；
- 单步工具查询；
- 环境变化极快的实时交互；
- 没有明确目标的开放探索；
- 高风险动作不经校验直接执行。

一句话总结：

> Plan-and-Execute 适合目标明确的多步骤任务，但计划必须被验证、可中断、可重规划。

---

## 5. Reflection / Reflexion 范式

### 5.1 核心思想

Reflection 的核心是：

```text
执行后检查结果
发现问题
总结错误
修正后再尝试
```

典型流程：

```text
Execute
→ Evaluate
→ Reflect
→ Retry
```

Reflexion 论文提出，语言智能体可以不通过更新模型参数，而是通过语言反馈强化自身表现：Agent 根据任务反馈产生反思文本，并将其保存在 episodic memory buffer 中，供后续尝试使用。

---

### 5.2 Reflection 与 Reflexion 的关系

| 概念 | 含义 |
|---|---|
| Reflection | 工程中的通用反思、批评、修正机制 |
| Reflexion | 代表性论文提出的具体框架，强调 verbal feedback + episodic memory |

工程中常说的 Reflection 可以很简单：

```text
生成答案
→ 自我检查
→ 修改答案
```

Reflexion 更强调：

```text
任务反馈
→ 语言反思
→ 写入记忆
→ 下一轮尝试使用反思经验
```

---

### 5.3 Reflection 执行流程

```text
生成初始结果
  ↓
Evaluator 判断是否达标
  ↓
达标：输出
  ↓
不达标：Reflector 总结问题
  ↓
将反思内容加入短期上下文或经验库
  ↓
重新执行
  ↓
直到成功或达到最大重试次数
```

---

### 5.4 示例：代码修复

```text
任务：修复一个单元测试失败的 bug

Execute:
修改代码。

Evaluate:
运行测试，发现仍然失败。

Reflect:
失败原因可能是只修复了输入校验，没有处理空列表边界条件。

Retry:
重新修改代码，补充边界条件处理。

Evaluate:
测试通过。
```

这类任务非常适合 Reflection，因为有明确反馈信号：

```text
测试是否通过
```

---

### 5.5 示例：退款判断复核

```text
初次判断：
用户可以退款。

Evaluator:
检查发现没有确认订单是否已签收。

Reflect:
退款判断缺少 delivery_status 校验，高风险。

Retry:
补充查询物流签收状态后再判断。
```

在业务系统中，Reflection 更适合做“复核”和“纠错”，不适合让它无限重试执行真实退款动作。

---

### 5.6 Reflection 的优势

| 优势 | 说明 |
|---|---|
| 提升复杂任务质量 | 适合代码、写作、报告、复杂决策 |
| 能利用反馈信号 | 测试、编译、规则校验、人工评价、LLM-as-judge |
| 有助于失败经验沉淀 | 可将错误原因写入短期记忆或回归测试 |
| 可作为高风险复核 | 在执行前检查遗漏条件或风险 |
| 能提高鲁棒性 | 对工具失败、格式错误、低质量结果进行修复 |

---

### 5.7 Reflection 的缺点

| 缺点 | 说明 |
|---|---|
| 成本高 | 每轮反思都需要额外模型调用 |
| 延迟高 | 多轮重试不适合实时任务 |
| 可能过度修正 | 模型可能把正确结果改坏 |
| 评价器可能不可靠 | LLM-as-judge 也可能误判 |
| 不适合无标准任务 | 主观开放任务很难判断是否真的变好 |
| 可能形成错误记忆 | 错误反思写入长期记忆会污染后续任务 |

---

### 5.8 Reflection 工程约束

生产环境中，Reflection 应该是受控能力，而不是默认无限开启。

建议约束：

```text
[ ] max_reflection_rounds 限制反思次数
[ ] evaluator 明确判断标准
[ ] structured critique 输出结构化批评
[ ] retry policy 控制哪些错误可重试
[ ] rollback 允许回退到更好版本
[ ] memory policy 控制反思是否写入记忆
[ ] high-risk review 高风险动作转人工
```

一句话总结：

> Reflection 不是让模型“想更多”，而是让系统在明确反馈下进行有限纠错。

---

## 6. Workflow Agent

### 6.1 核心思想

Workflow Agent 的核心是：

```text
流程由开发者定义，模型只在局部节点发挥作用。
```

它不是“没有智能”，而是把智能限制在可控范围内。

典型结构：

```text
Input
→ Intent Node
→ Slot Node
→ Tool Node
→ RAG Node
→ Decision Node
→ Guardrail Node
→ Action Node
→ Verification Node
→ Response Node
```

---

### 6.2 Workflow Agent 与自由 Agent 的区别

| 维度 | Workflow Agent | 自由 Agent |
|---|---|---|
| 主流程 | 固定或半固定 | 动态生成 |
| 可测试性 | 高 | 较低 |
| 安全性 | 更容易控制 | 依赖约束 |
| 适合场景 | 高可靠业务流程 | 开放探索任务 |
| 可观测性 | 强 | 需要额外设计 |
| 工具调用 | 按节点受控调用 | 模型动态选择 |
| 失败恢复 | 可设计固定策略 | 容易不可预测 |

---

### 6.3 Workflow Agent 适用场景

特别适合：

- 电商退款；
- 交易履约；
- 审批流；
- 工单流转；
- 风控判断；
- 客服分流；
- 企业知识库问答；
- 医疗/金融等高约束场景。

原因是这些场景通常具备：

```text
固定业务阶段
明确权限边界
明确成功标准
明确审计要求
明确失败兜底路径
```

---

### 6.4 交易履约示例

```text
用户输入
  ↓
意图识别
  ↓
槽位补全
  ↓
订单查询
  ↓
物流查询
  ↓
规则检索
  ↓
责任归因
  ↓
动作建议
  ↓
高风险动作确认
  ↓
执行工具
  ↓
状态校验
  ↓
客服回复
  ↓
评估记录
```

在这个流程中：

- 意图识别可以用 LLM；
- 订单查询必须用工具；
- 规则匹配可以用 RAG；
- 责任归因可以用 LLM + 规则；
- 退款执行必须由后端工具控制；
- 最终回复不能承诺未执行动作；
- 全链路必须记录 trace。

---

### 6.5 Workflow Agent 的工程价值

| 价值 | 说明 |
|---|---|
| 稳定 | 主路径可预测 |
| 可测 | 每个节点可单独测试 |
| 可审计 | 每一步都有状态和日志 |
| 可灰度 | 可以逐节点替换 Prompt、模型或工具 |
| 可回滚 | 版本化流程更容易回退 |
| 可控成本 | 哪些节点用强模型、哪些用规则可明确配置 |
| 安全 | 高风险节点可插入审批、策略和权限校验 |

一句话总结：

> Workflow Agent 是生产级 Agent 的主干，不是 Agent 的反面。

---

## 7. Router Agent

### 7.1 核心思想

Router Agent 的核心是：

```text
根据用户输入、上下文和系统状态，将任务路由到合适的流程、工具或专家 Agent。
```

它解决的是：

```text
这个请求应该交给谁处理？
```

而不是：

```text
这个请求最终答案是什么？
```

---

### 7.2 静态路由与动态路由

| 类型 | 控制方式 | 示例 | 优点 | 缺点 |
|---|---|---|---|---|
| 静态路由 | 规则、关键词、意图树、配置表 | refund → refund_flow | 稳定、可控、便宜 | 泛化弱 |
| 动态路由 | LLM 根据上下文判断 | 判断是退款、投诉还是转人工 | 灵活、适合复杂表达 | 成本高、可能误判 |
| 混合路由 | 规则优先，LLM 兜底 | 高置信规则命中直接路由，模糊时问 LLM | 平衡稳定和灵活 | 需要评估体系 |

推荐生产方案：

```text
规则/分类器处理高频明确请求
LLM 处理模糊、多意图、长文本请求
低置信度转人工或追问
```

---

### 7.3 Router Agent 的典型输出

```json
{
  "route": "refund_workflow",
  "confidence": 0.91,
  "required_slots": ["order_id"],
  "risk_tags": ["high_risk_action_requested"],
  "fallback_route": "human_service"
}
```

---

### 7.4 Router Agent 适用场景

适合：

- 企业智能客服；
- 多业务线助手；
- 多工具平台；
- 多 Agent 协作系统；
- 企业微信/钉钉入口的统一 Agent；
- MCP 工具数量很大的系统。

需要注意：

```text
路由错误会导致后续全链路错误。
```

因此 Router Agent 必须评估：

- Route Accuracy；
- Fallback Accuracy；
- Multi-intent Recall；
- Human Handoff Precision；
- Tool/Flow Selection Accuracy。

一句话总结：

> Router Agent 是复杂 Agent 系统的入口调度层，核心不是回答，而是分发。

---

## 8. Agentic RAG

### 8.1 核心思想

普通 RAG 是：

```text
用户问题
→ 检索文档
→ 生成答案
```

Agentic RAG 是：

```text
理解问题
→ 判断是否需要检索
→ 改写 query
→ 拆解子问题
→ 多轮检索
→ 证据筛选
→ 判断证据是否足够
→ 必要时追问或再检索
→ 基于证据生成答案
→ 引用校验
```

它不是简单“接一个向量库”，而是让检索过程具有主动性和可控性。

---

### 8.2 Agentic RAG 与普通 RAG 的区别

| 维度 | 普通 RAG | Agentic RAG |
|---|---|---|
| 检索次数 | 通常一次 | 可多轮 |
| Query 处理 | 直接检索或简单改写 | 改写、拆解、扩展、约束 |
| 证据判断 | 较弱 | 显式判断证据是否足够 |
| 适合问题 | 简单知识问答 | 多跳问题、规则判断、复杂业务 |
| 风险控制 | 依赖 Prompt | 可加入证据校验和拒答策略 |
| 成本 | 较低 | 较高 |
| 可解释性 | 中等 | 强，能记录 evidence chain |

---

### 8.3 Agentic RAG 适用场景

适合：

- 企业制度问答；
- 平台规则决策；
- 售后责任判断；
- 合同条款查询；
- 代码库问答；
- 法规/政策辅助检索；
- 多文档报告生成。

不适合：

- 完全无需外部知识的任务；
- 一问一答的简单 FAQ；
- 文档质量极差且无来源标记的知识库；
- 不允许模型解释或综合的强规则执行场景。

---

### 8.4 Agentic RAG 工程流程

```text
用户问题
  ↓
Intent / Query Understanding
  ↓
Query Rewrite
  ↓
Query Decomposition
  ↓
Hybrid Retrieval
  ↓
Rerank
  ↓
Evidence Selection
  ↓
Evidence Sufficiency Check
  ↓
Answer / Decision Generation
  ↓
Citation Verification
  ↓
Safety Check
```

---

### 8.5 Agentic RAG 的关键指标

```text
Context Recall
Context Precision
Citation Accuracy
Faithfulness
Answer Correctness
Evidence Sufficiency Accuracy
Refusal Accuracy
Policy Recall@K
```

一句话总结：

> Agentic RAG 适合“需要主动查证和证据链”的任务，不适合把所有问题都复杂化。

---

## 9. Multi-Agent 范式

### 9.1 核心思想

Multi-Agent 的核心不是“Agent 越多越好”，而是：

```text
专业角色分工
+ 可控协作
+ 共享状态
+ 明确责任边界
+ 可评估轨迹
```

一个多 Agent 系统通常包含：

- Coordinator Agent；
- Planner Agent；
- Research Agent；
- Tool Agent；
- Decision Agent；
- Critic Agent；
- Verification Agent；
- Response Agent。

---

### 9.2 常见 Multi-Agent 模式

| 模式 | 说明 | 适合场景 |
|---|---|---|
| Supervisor-Worker | 一个主管分配任务给多个工作 Agent | 企业助手、客服分流 |
| Planner-Executor | 一个规划，一个执行 | 长任务自动化 |
| Researcher-Writer-Reviewer | 研究、写作、审查分离 | 报告生成、论文综述 |
| Critic-Reflector | 生成与批评分离 | 代码修复、内容审核 |
| Debate | 多 Agent 辩论 | 决策评估、观点比较 |
| Blackboard | 多 Agent 共享状态板 | 复杂任务协同 |
| Handoff | 一个 Agent 处理不了时移交另一个 Agent | 多技能助手、客服转接 |

---

### 9.3 Multi-Agent 的优势

| 优势 | 说明 |
|---|---|
| 专业分工 | 每个 Agent 负责更窄任务 |
| 易扩展 | 新业务可以新增专家 Agent |
| 可并行 | 独立子任务可并行执行 |
| 可复核 | Critic 或 Verifier 可检查结果 |
| 更接近组织协作 | 适合复杂企业任务和长流程 |

---

### 9.4 Multi-Agent 的风险

| 风险 | 说明 |
|---|---|
| 成本上升 | 多 Agent 意味着更多模型调用 |
| 延迟上升 | 串行协作会变慢 |
| 边界不清 | Agent 之间可能互相重复或冲突 |
| 状态污染 | 一个 Agent 的错误输出污染其他 Agent |
| 责任不清 | 最终错误由谁负责不明确 |
| 调试困难 | 多条消息、多轮协作难复现 |
| 过度设计 | 单 Agent 或 Workflow 能解决的问题被复杂化 |

---

### 9.5 Multi-Agent 工程建议

```text
[ ] 每个 Agent 只负责一个清晰角色
[ ] Agent 之间传递结构化数据，不传递任意自然语言指令
[ ] 共享状态中保留 source、trust_level、risk_tags
[ ] Coordinator 负责最终控制权
[ ] 高风险动作只能由受控执行层完成
[ ] 记录每个 Agent 的输入、输出、耗时、成本和贡献
[ ] 有失败归因和回归测试
```

一句话总结：

> Multi-Agent 的价值来自“清晰分工和可控协作”，不是来自“堆更多 Agent”。

---

## 10. Verifier / Evaluator 范式

### 10.1 为什么需要 Verifier

在生产系统中，Agent 生成结果后不能直接相信。尤其是以下场景：

- 退款、赔偿、取消订单；
- 代码补丁；
- 医疗/金融建议；
- 合同条款解释；
- 数据分析结论；
- 自动发送邮件或消息；
- 自动执行外部工具。

这时需要一个 Verifier / Evaluator 节点检查：

```text
结果是否符合格式？
是否有证据支持？
是否违反业务规则？
是否存在安全风险？
是否需要人工确认？
```

---

### 10.2 Verifier 与 Reflection 的区别

| 维度 | Verifier | Reflection |
|---|---|---|
| 目标 | 判断结果是否达标 | 总结问题并尝试修正 |
| 输出 | pass/fail/risk/retry | critique/revision_plan |
| 是否修改结果 | 通常不修改 | 可能修改 |
| 适合位置 | 执行前、输出前、工具调用前 | 失败后或质量不够时 |
| 风险 | 误判 | 过度修正 |

---

### 10.3 Verifier 输出示例

```json
{
  "pass": false,
  "risk_level": "high",
  "blocking_reasons": [
    "missing_policy_evidence",
    "refund_tool_not_confirmed"
  ],
  "next_action": "human_review"
}
```

---

### 10.4 常见评估指标

```text
Format Validity
Evidence Coverage
Decision Accuracy
Unsafe Action Rate
Tool Argument Accuracy
Regression Pass Rate
Task Success Rate
Human Review Precision
```

一句话总结：

> Verifier 是生产级 Agent 的刹车系统，Reflection 是修理系统。

---

## 11. Human-in-the-loop 范式

### 11.1 核心思想

Human-in-the-loop（HITL）的核心是：

```text
让人类在关键节点拥有确认权、否决权和最终责任。
```

它不是 Agent 能力弱的表现，而是生产系统负责的表现。

---

### 11.2 什么时候必须 HITL

以下情况建议或必须人工介入：

```text
高金额退款或补偿
账号权限修改
对外发送正式邮件
删除或覆盖重要数据
合规/法律/医疗/金融建议
模型置信度低
证据冲突
工具结果异常
用户强烈投诉
疑似 Prompt Injection
```

---

### 11.3 HITL 在 Agent 中的位置

```text
Plan Review：执行前审核计划
Tool Approval：调用高风险工具前确认
Decision Review：高风险决策前复核
Output Review：对外输出前审核
Exception Handling：异常或冲突时接管
```

---

### 11.4 HITL 输出示例

```json
{
  "approval_required": true,
  "approval_type": "refund_action",
  "reason": "high_risk_action_with_financial_impact",
  "review_payload": {
    "order_id": "O123",
    "suggested_action": "create_refund",
    "evidence_ids": ["R001"]
  }
}
```

一句话总结：

> 生产级 Agent 不是完全无人参与，而是让人在最该出现的位置出现。

---

## 12. 范式总览对比

### 12.1 核心区别

| 范式 | 核心思想 | 本质 |
|---|---|---|
| 普通 LLM | 一次输入，一次输出 | 文本生成 |
| RAG | 检索增强生成 | 外部知识注入 |
| ReAct | 边思考边行动 | 动态探索 |
| Plan-and-Execute | 先规划再执行 | 任务拆解 |
| Reflection | 执行后反思修正 | 错误恢复 |
| Workflow Agent | 固定流程 + 局部智能 | 可控编排 |
| Router Agent | 动态分发任务 | 调度入口 |
| Agentic RAG | 主动检索、验证、引用 | 证据链构建 |
| Multi-Agent | 多角色协作 | 专业分工 |
| Verifier | 判断结果是否合格 | 质量与安全检查 |
| Human-in-the-loop | 人类关键节点介入 | 风险兜底 |

---

### 12.2 工程维度对比

| 维度 | ReAct | Plan-and-Execute | Reflection | Workflow | Multi-Agent |
|---|---|---|---|---|---|
| 动态性 | 高 | 中 | 中 | 低到中 | 高 |
| 可控性 | 中 | 中高 | 中 | 高 | 中 |
| 可测试性 | 中低 | 中高 | 中 | 高 | 中低 |
| 成本 | 高 | 中 | 高 | 可控 | 高 |
| 延迟 | 高 | 中 | 高 | 可控 | 高 |
| 适合开放任务 | 高 | 中 | 中 | 低 | 高 |
| 适合高风险业务 | 低 | 中 | 中 | 高 | 中 |
| 主要风险 | 循环、误调用 | 计划过时 | 过度反思 | 流程僵硬 | 协作混乱 |

---

### 12.3 场景选型表

| 场景 | 推荐范式 |
|---|---|
| 简单 FAQ | 普通 LLM / 普通 RAG |
| 企业知识库问答 | RAG / Agentic RAG |
| 多跳事实核查 | ReAct + RAG |
| 代码修复 | ReAct + Reflection + 测试工具 |
| 数据分析报告 | Plan-and-Execute + Tool-use + Reflection |
| 旅行规划 | Plan-and-Execute |
| 电商退款履约 | Workflow + 局部 ReAct + Verifier + HITL |
| 审批流 | Workflow + Policy Engine |
| 多业务智能客服 | Router + Workflow |
| 浏览器自动化 | ReAct + Computer-use + Guardrails |
| 高风险医疗/金融 | Workflow + 权威检索 + HITL + 审计 |
| 长周期企业流程 | Durable Workflow + HITL + Checkpoint |
| 多专家报告生成 | Multi-Agent + Reviewer |
| 简单确定性函数 | 不用 Agent，直接函数/规则 |

---

## 13. 生产级 Agent 的常见组合方式

现实中很少使用单一范式解决所有问题。更常见的是组合架构：

```text
主流程：Workflow / StateGraph
入口调度：Router
局部检索与工具探索：ReAct
复杂任务拆解：Plan-and-Execute
复杂结果复核：Reflection / Verifier
知识证据链：Agentic RAG
多角色协作：Multi-Agent
高风险兜底：Human-in-the-loop
全链路保障：Tracing + Evaluation + Guardrails
```

---

### 13.1 OrderFlow-Agent 示例架构

```text
用户输入
  ↓
Input Safety Check
  ↓
Intent & Slot Router
  ↓
Workflow 主流程
  ↓
Order Tool / Logistics Tool
  ↓
Policy Agentic RAG
  ↓
Responsibility Decision
  ↓
Verifier / Reflection
  ↓
Human Approval（高风险动作）
  ↓
Refund / Ticket Tool
  ↓
State Verification
  ↓
Customer Response
  ↓
Trace + Eval + Failure Dataset
```

这里每个范式的作用是：

| 范式 | 在系统中的位置 |
|---|---|
| Router | 判断用户是退款、物流、投诉还是转人工 |
| Workflow | 控制订单处理主流程 |
| ReAct | 在规则检索或异常排查中局部探索 |
| Plan-and-Execute | 对复杂售后任务生成步骤 |
| Agentic RAG | 检索规则并构建证据链 |
| Verifier | 检查责任判断和退款建议是否有证据 |
| HITL | 高风险退款或证据冲突时人工确认 |
| Reflection | 工具失败或判断不一致时复盘修正 |

---

### 13.2 生产原则

```text
确定性流程交给代码；
不确定性判断交给模型；
事实查询交给工具；
知识依据交给 RAG；
高风险执行交给受控后端；
异常和低置信度交给人工；
质量和安全交给评估与监控。
```

---

## 14. 范式选择决策树

可以按以下问题选择范式。

### 14.1 是否需要 Agent

```text
任务能不能用一个确定性函数完成？
  ├─ 能：不用 Agent
  └─ 不能：
      是否需要外部知识？
        ├─ 是：考虑 RAG / Agentic RAG
        └─ 否：
            是否需要多步骤执行？
              ├─ 否：普通 LLM
              └─ 是：继续判断
```

---

### 14.2 是否需要动态工具调用

```text
工具调用路径是否固定？
  ├─ 固定：Workflow
  └─ 不固定：
      工具结果是否会影响下一步？
        ├─ 是：ReAct
        └─ 否：Plan-and-Execute
```

---

### 14.3 是否需要反思修正

```text
任务是否高价值、允许多轮迭代、有明确反馈信号？
  ├─ 是：加入 Reflection / Verifier
  └─ 否：不默认加入 Reflection
```

---

### 14.4 是否需要 Multi-Agent

```text
单 Agent 是否已经能清晰完成任务？
  ├─ 是：不要 Multi-Agent
  └─ 否：
      是否存在清晰专家分工？
        ├─ 是：可以 Multi-Agent
        └─ 否：先优化 Workflow / Router
```

---

### 14.5 是否需要 HITL

```text
是否涉及资金、权限、隐私、对外发送、删除、合规？
  ├─ 是：必须加入 HITL 或强策略校验
  └─ 否：可根据置信度和风险决定是否人工接管
```

---

## 15. 常见误区

### 15.1 误区一：Agent 越自由越强

自由度越高，通常意味着：

- 更难测试；
- 更难控成本；
- 更难审计；
- 更难保证安全；
- 更容易出现不可预测路径。

生产系统追求的不是“最大自由度”，而是：

```text
在可控边界内释放模型能力。
```

---

### 15.2 误区二：Workflow 不算 Agent

Workflow 不是低级方案。很多生产级 Agent 都是 Workflow 主控，因为真实业务要求：

- 可测试；
- 可审计；
- 可回放；
- 可回滚；
- 可灰度；
- 可监控；
- 可人工接管。

---

### 15.3 误区三：所有复杂任务都要 Multi-Agent

Multi-Agent 会显著增加：

- 成本；
- 延迟；
- 上下文管理难度；
- 状态一致性问题；
- 调试复杂度。

如果角色边界不清，Multi-Agent 反而会让系统更差。

---

### 15.4 误区四：Reflection 一定提升质量

Reflection 只有在以下条件成立时更有价值：

```text
有明确评价标准；
允许多轮迭代；
任务价值足够高；
有停止条件；
有回滚机制。
```

否则它可能只是增加成本和延迟。

---

### 15.5 误区五：只要接了工具就是 Agent

工具调用只是 Agent 的一部分。生产 Agent 还需要：

- 状态管理；
- 权限控制；
- 工具校验；
- 终止条件；
- 失败恢复；
- 安全防护；
- trace；
- eval；
- deployment。

---

## 16. 学习路径与实践任务

### 16.1 学习顺序

建议顺序：

```text
1. 普通 LLM 调用与结构化输出
2. Tool Calling
3. ReAct
4. Plan-and-Execute
5. Workflow / StateGraph
6. Agentic RAG
7. Reflection / Verifier
8. Router Agent
9. Multi-Agent
10. Guardrails、HITL、Tracing、Evaluation
```

---

### 16.2 阶段实践任务

围绕同一个任务“用户申请退款”，实现以下版本：

| 版本 | 目标 |
|---|---|
| V0 普通 LLM | 直接生成客服回复 |
| V1 结构化输出 | 输出 intent、slots、next_action |
| V2 Tool Calling | 查询订单和物流 |
| V3 ReAct | 根据工具结果动态决定下一步 |
| V4 Workflow | 用状态图固定主流程 |
| V5 Agentic RAG | 检索平台规则并输出证据 |
| V6 Verifier | 检查是否允许退款建议 |
| V7 HITL | 高风险退款需要用户或人工确认 |
| V8 Eval | 用测试集评估端到端成功率 |

---

### 16.3 评估指标

```text
Intent Accuracy
Slot F1
Tool Selection Accuracy
Tool Argument Accuracy
Policy Recall@K
Evidence Citation Accuracy
Decision Accuracy
Unsafe Action Rate
Human Handoff Precision
End-to-End Success Rate
Average Latency
Average Cost
Regression Pass Rate
```

---

### 16.4 推荐项目目录

```text
agent-paradigm-lab/
  app/
    agents/
      react_agent.py
      planner.py
      workflow.py
      verifier.py
      router.py
    tools/
      order_tool.py
      logistics_tool.py
      policy_tool.py
      refund_tool.py
    rag/
      retriever.py
      reranker.py
      evidence_selector.py
    safety/
      guardrails.py
      policy_engine.py
      approval.py
    eval/
      datasets/
      runner.py
      metrics.py
  docs/
    paradigm_notes.md
    architecture.md
    eval_report.md
  tests/
    test_router.py
    test_workflow.py
    test_tools.py
```

---

## 17. 阶段达标检查清单

```text
[ ] 能解释普通 LLM、RAG、Agent、Workflow 的区别
[ ] 能解释 ReAct 的 Thought-Action-Observation 循环
[ ] 能说明 ReAct 和 Tool Calling 的区别
[ ] 能解释 Plan-and-Execute 为什么需要 Plan Validator
[ ] 能说明 Reflection 和 Verifier 的区别
[ ] 能判断什么任务不该用 Agent
[ ] 能判断什么时候用 Workflow 主控
[ ] 能设计 Router Agent 的输出 schema
[ ] 能说明 Agentic RAG 相比普通 RAG 的优势和成本
[ ] 能说明 Multi-Agent 的收益和风险
[ ] 能为高风险动作设计 HITL 节点
[ ] 能为 Agent 设计 max_steps、stop condition 和 retry policy
[ ] 能为不同范式设计评估指标
[ ] 能将退款场景拆成 Workflow + 局部 Agent 能力
```

---

## 18. 阶段总结

### 18.1 一句话理解核心范式

```text
ReAct：
边思考边行动，适合动态探索。

Plan-and-Execute：
先规划再执行，适合目标明确的多步骤任务。

Reflection：
执行后反思修正，适合有反馈信号的高价值任务。

Workflow Agent：
固定流程中嵌入局部智能，适合生产级高可靠业务。

Router Agent：
判断任务该交给哪个流程、工具或专家。

Agentic RAG：
让检索过程具备主动改写、拆解、验证和引用能力。

Multi-Agent：
通过专业分工解决单 Agent 难以覆盖的复杂任务。

Verifier：
检查结果是否合格，是质量和安全的刹车系统。

Human-in-the-loop：
让人在关键风险节点拥有确认权和最终责任。
```

---

### 18.2 最重要的工程判断

```text
开放探索任务：
优先 ReAct。

目标明确的多步骤任务：
优先 Plan-and-Execute 或 Workflow。

高可靠业务流程：
优先 Workflow + 局部 LLM。

复杂结果复核：
加入 Verifier / Reflection。

知识证据链任务：
使用 Agentic RAG。

多业务入口：
使用 Router Agent。

多专家复杂任务：
谨慎使用 Multi-Agent。

高风险动作：
必须 Guardrails + HITL + 状态校验。

简单确定性任务：
不要 Agent，直接函数或规则即可。
```

---

### 18.3 最终结论

Agent 工程的核心不是“堆框架”，而是：

```text
根据任务的不确定性、风险、成本、延迟和可测试性，
选择合适的任务控制范式。
```

一个成熟的 Agent 工程师应该能做到：

```text
该自由探索时使用 ReAct；
该结构化拆解时使用 Plan-and-Execute；
该稳定可靠时使用 Workflow；
该查证引用时使用 Agentic RAG；
该复核纠错时使用 Reflection / Verifier；
该分工协作时使用 Multi-Agent；
该人工兜底时使用 Human-in-the-loop；
该不用 Agent 时坚决不用 Agent。
```

---

## 19. 参考资料

### 19.1 核心论文

1. ReAct: Synergizing Reasoning and Acting in Language Models  
   https://openreview.net/forum?id=WE_vluYUL-X

2. Reflexion: Language Agents with Verbal Reinforcement Learning  
   https://proceedings.neurips.cc/paper_files/paper/2023/hash/1b44b878bb782e6954cd888628510e90-Abstract-Conference.html

3. Plan-and-Solve Prompting: Improving Zero-Shot Chain-of-Thought Reasoning by Large Language Models  
   https://arxiv.org/abs/2305.04091

4. AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation  
   https://arxiv.org/abs/2308.08155

5. MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework  
   https://arxiv.org/abs/2308.00352

6. Toolformer: Language Models Can Teach Themselves to Use Tools  
   https://arxiv.org/abs/2302.04761

7. Self-Refine: Iterative Refinement with Self-Feedback  
   https://arxiv.org/abs/2303.17651

8. From Agent Loops to Deterministic Graphs: Execution Lineage for Reproducible AI-Native Work  
   https://arxiv.org/abs/2605.06365

9. AgentTrace: A Structured Logging Framework for Agent System Observability  
   https://arxiv.org/abs/2602.10133

---

### 19.2 官方与主流框架文档

1. OpenAI Agents SDK  
   https://developers.openai.com/api/docs/guides/agents

2. OpenAI Agents SDK Python Docs  
   https://openai.github.io/openai-agents-python/agents/

3. OpenAI Agents SDK Tracing  
   https://openai.github.io/openai-agents-python/tracing/

4. LangGraph Overview  
   https://docs.langchain.com/oss/python/langgraph/overview

5. LangGraph Durable Execution  
   https://docs.langchain.com/oss/python/langgraph/durable-execution

6. LlamaIndex Agent Workflows  
   https://developers.llamaindex.ai/python/framework/module_guides/deploying/agents/

7. Microsoft Agent Framework Overview  
   https://learn.microsoft.com/en-us/agent-framework/overview/

8. Microsoft Agent Framework Workflows  
   https://learn.microsoft.com/en-us/agent-framework/workflows/

9. Google Agent Development Kit  
   https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/adk

10. Google ADK Evaluation Codelab  
   https://codelabs.developers.google.com/adk-eval/instructions

11. Model Context Protocol Security Best Practices  
   https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices

12. Anthropic Trustworthy Agents in Practice  
   https://www.anthropic.com/research/trustworthy-agents

13. Anthropic Prompt Injection Defenses for Browser Use  
   https://www.anthropic.com/research/prompt-injection-defenses

---

### 19.3 建议长期跟踪

- OpenAI Developers
- Anthropic Engineering / Research
- LangChain / LangGraph Blog
- LlamaIndex Blog
- Microsoft Agent Framework
- Google ADK / Gemini Enterprise Agent Platform
- Model Context Protocol
- OWASP Top 10 for LLM Applications
- Ragas / LangSmith / Langfuse
- SWE-bench / GAIA / WebArena / AgentBench / τ-bench

