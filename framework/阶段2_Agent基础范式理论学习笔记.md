# 阶段 2：Agent 基础范式理论学习笔记

> 主题：ReAct、Plan-and-Execute、Reflection  
> 定位：Agent 工程学习长期笔记  
> 重点：核心思想、执行机制、适用边界、工程优缺点、典型应用场景  
> 说明：本笔记聚焦理论理解，暂不展开代码实践和项目实现。

---

## 1. 阶段学习目标

### 1.1 为什么要学习 Agent 范式

Agent 范式解决的不是“如何调用一次大模型 API”的问题，而是解决：

> 当一个任务无法通过一次模型回复完成时，如何组织模型进行多步骤推理、工具调用、观察反馈、状态更新和错误修正。

普通 LLM 调用通常是：

```text
用户输入
→ 模型生成
→ 输出答案
```

而 Agent 更接近：

```text
用户任务
→ 理解任务
→ 规划步骤
→ 调用工具
→ 获取观察结果
→ 更新状态
→ 必要时反思修正
→ 判断是否终止
→ 输出结果
```

所以，Agent 的核心不是“模型更聪明”，而是“系统更会组织任务”。

---

### 1.2 为什么不能只会调用大模型 API

只会调用大模型 API，通常只能解决：

- 一次性问答；
- 文本改写；
- 简单分类；
- 简单抽取；
- 简单总结。

但真实业务经常需要：

- 查询数据库；
- 调用外部 API；
- 检索知识库；
- 多轮确认用户信息；
- 处理工具失败；
- 进行安全校验；
- 判断是否需要人工接管；
- 记录执行轨迹；
- 评估最终结果是否正确。

这时，如果没有 Agent 范式，你会把系统写成一堆“模型调用 + if else + 临时 prompt”，最后很难维护、测试和扩展。

---

### 1.3 为什么不能盲目套用 Agent 框架

LangChain、LangGraph、OpenAI Agents SDK、LlamaIndex、AutoGen、CrewAI、Google ADK、Microsoft Agent Framework 等框架都很有价值，但框架只能提供工程抽象，不能替你判断：

- 这个任务是否真的需要 Agent；
- 是否应该让模型自由规划；
- 是否应该固定成 Workflow；
- 哪些节点需要 LLM；
- 哪些节点应该用规则或代码；
- 工具调用是否安全；
- 如何设置终止条件；
- 如何避免循环、误调用和成本失控。

学习 Agent 范式的目的，是让你具备“架构判断力”，而不是只会照着框架模板写代码。

---

### 1.4 学完本阶段后应该具备的判断能力

学完本阶段后，你应该能够回答：

1. 一个任务适合普通 LLM、ReAct、Plan-and-Execute、Reflection，还是 Workflow Agent？
2. ReAct 为什么适合搜索、代码修复、开放式工具探索，但不适合高风险交易动作？
3. Plan-and-Execute 为什么适合多步骤任务，但为什么计划可能过时？
4. Reflection 为什么能提升复杂任务质量，但为什么不适合低延迟、高并发客服？
5. 生产系统中为什么常见的是“Workflow + 局部 ReAct + 局部 Reflection”，而不是完全自由的 Agent？

---

## 2. Agent 范式的整体理解

### 2.1 什么是 Agent 范式

Agent 范式可以理解为：

> 大模型在复杂任务中组织“思考、行动、观察、修正、终止”的控制结构。

它不是某一个框架，也不是某一个 prompt，而是一种任务执行方式。

不同范式的差异主要体现在：

| 问题 | 不同范式的差异 |
|---|---|
| 是否先规划？ | Plan-and-Execute 会先规划，ReAct 通常边执行边调整 |
| 是否调用工具？ | ReAct 和 Tool-use Agent 强依赖工具，普通 LLM 不一定 |
| 是否允许反思？ | Reflection 会显式检查和修正已有结果 |
| 是否固定流程？ | Workflow 固定路径，Agent 动态决定路径 |
| 是否记录状态？ | 生产级 Agent 通常需要显式状态 |
| 是否可测试？ | Workflow 更容易测试，自由 Agent 更难测试 |
| 是否安全可控？ | 取决于工具权限、状态约束和 guardrails |

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

这两个目标不同。

例如用户说：

```text
帮我处理一下这个退款申请
```

普通 LLM 可能只会生成一段客服话术。

Agent 则需要：

```text
理解退款意图
→ 获取订单号
→ 查询订单状态
→ 查询物流状态
→ 检索售后规则
→ 判断是否符合退款条件
→ 调用退款工具
→ 校验退款是否成功
→ 回复用户
```

所以 Agent 是“任务执行系统”，普通 LLM 调用只是其中的一个能力组件。

---

### 2.3 Agent 与 Workflow 的区别

根据 LangGraph 文档中的区分，Workflow 通常有预先确定的代码路径，并按照固定顺序运行；Agent 则更动态，会根据任务自行决定流程和工具使用。

可以这样理解：

```text
Workflow：流程由开发者控制
Agent：部分流程由模型动态决定
```

对比：

| 维度 | Workflow | Agent |
|---|---|---|
| 控制方式 | 开发者预定义流程 | 模型动态选择流程 |
| 稳定性 | 高 | 中等或不稳定 |
| 灵活性 | 中等 | 高 |
| 可测试性 | 强 | 较弱 |
| 适合场景 | 高可靠业务流程 | 开放式探索任务 |
| 典型例子 | 审批、退款、履约 | 搜索、代码修复、浏览器操作 |

在真实系统中，二者并不冲突。很多生产级 Agent 实际上是：

```text
Workflow 控制主流程
+ Agent 在局部节点中做智能决策
```

---

### 2.4 Agent 的核心环节

一个完整 Agent 系统通常包含以下环节。

#### 2.4.1 任务理解

将用户自然语言转化为结构化任务，例如：

```text
用户说：“我的订单三天没发货，我要退款”
系统理解：
intent = refund_request
reason = delayed_shipping
missing_slots = [order_id]
```

#### 2.4.2 规划

决定完成任务需要哪些步骤，例如：

```text
1. 获取订单号
2. 查询订单状态
3. 查询物流状态
4. 检索售后规则
5. 判断退款条件
6. 执行退款或转人工
```

#### 2.4.3 工具调用

模型不能直接操作真实业务系统，而是生成工具调用意图，由受控工具层执行。

例如：

```text
query_order(order_id)
query_logistics(order_id)
search_policy(query)
create_refund(order_id, amount, reason)
```

#### 2.4.4 观察反馈

工具执行后返回结果，Agent 根据结果继续判断。

```text
Observation:
订单已支付，72 小时未发货
```

#### 2.4.5 记忆

记忆包括：

- 当前任务状态；
- 多轮对话上下文；
- 历史工具结果；
- 用户偏好；
- 过往失败经验。

#### 2.4.6 反思修正

当执行失败或结果质量不足时，Agent 可以复盘：

```text
错误原因：没有先检查订单是否已签收
修正策略：后续退款前必须检查 delivery_status
```

#### 2.4.7 终止条件

Agent 必须知道什么时候停止。

常见终止条件：

- 已得到最终答案；
- 已完成工具执行；
- 达到最大步骤数；
- 缺少必要信息，需要追问；
- 触发安全风险，需要转人工；
- 多次失败，需要停止重试。

#### 2.4.8 安全约束

Agent 能调用工具后，风险显著增加。

因此必须有：

- 权限校验；
- 参数校验；
- 金额上限；
- 幂等控制；
- 高风险动作人工确认；
- 工具调用审计；
- Prompt injection 防御；
- 敏感信息过滤。

---

## 3. ReAct 范式详解

### 3.1 ReAct 的核心思想

ReAct 来自论文《ReAct: Synergizing Reasoning and Acting in Language Models》。它的核心思想是让大模型交替生成：

```text
Reasoning trace
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

> 把模型的推理过程和外部环境交互过程结合起来。

论文中指出，Reasoning trace 可以帮助模型跟踪和更新行动计划、处理异常；Action 则允许模型与知识库或外部环境交互，获取额外信息。

---

### 3.2 Reasoning、Acting、Observation 分别是什么

#### Reasoning

Reasoning 是模型对当前任务状态的判断，例如：

```text
我需要先确认订单是否存在。
```

它回答的是：

```text
现在为什么要做这一步？
```

#### Acting

Acting 是模型决定调用某个工具，例如：

```text
query_order(order_id="123456")
```

它回答的是：

```text
现在要做什么动作？
```

#### Observation

Observation 是工具或环境返回的结果，例如：

```text
订单状态：已支付，未发货。
```

它回答的是：

```text
刚才的动作带来了什么新信息？
```

ReAct 的核心不是单独思考，也不是单独调用工具，而是把二者交替连接起来。

---

### 3.3 ReAct 与普通 Chain-of-Thought 的区别

普通 Chain-of-Thought 主要是：

```text
模型在内部一步步推理
```

但它不一定接触真实外部世界。

ReAct 是：

```text
模型一边推理
一边调用工具获取真实信息
再根据真实信息继续推理
```

对比：

| 维度 | Chain-of-Thought | ReAct |
|---|---|---|
| 是否调用工具 | 通常不调用 | 调用工具 |
| 信息来源 | 模型已有知识和输入上下文 | 模型 + 外部环境 |
| 是否动态更新 | 较弱 | 强 |
| 适合场景 | 数学、逻辑、解释型任务 | 搜索、问答、工具任务、交互任务 |
| 风险 | 可能一本正经地推错 | 可能工具循环或误调用 |

---

### 3.4 ReAct 与普通 Tool Calling 的区别

普通 Tool Calling 可以只是：

```text
模型判断需要某个工具
→ 调用一次工具
→ 生成答案
```

ReAct 则是：

```text
多轮推理
→ 多轮工具调用
→ 多轮观察
→ 动态调整
```

因此：

```text
Tool Calling 是能力
ReAct 是控制循环，ReAct = LLM 在工具集合中进行逐步动态决策
```

一个系统可以支持 Tool Calling，但不一定是 ReAct。只有当它存在“思考—行动—观察—再思考”的循环结构时，才更接近 ReAct。

---

### 3.5 ReAct 的典型执行流程

```text
用户任务
  ↓
模型理解当前目标
  ↓
模型生成 Thought：判断下一步需要什么信息
  ↓
模型生成 Action：选择并调用工具
  ↓
工具返回 Observation
  ↓
模型基于 Observation 更新判断
  ↓
继续调用工具或生成最终答案
  ↓
达到终止条件
```

---

### 3.6 ReAct 示例：退款申请

```text
用户：我的订单三天没发货，我要退款

Thought:
需要先确认订单状态。

Action:
query_order(order_id)

Observation:
订单已支付，商家未发货。

Thought:
还需要确认物流是否有揽收记录。

Action:
query_logistics(order_id)

Observation:
无揽收记录，距离付款已超过 72 小时。

Thought:
需要查询平台关于延迟发货退款的规则。

Action:
search_policy("付款后超过72小时未发货是否支持退款")

Observation:
命中规则：商家超时未发货，用户可申请退款。

Thought:
满足退款条件，但执行前需要确认退款金额和订单状态未发生变化。

Action:
verify_refund_precondition(order_id)

Observation:
订单仍未发货，未退款，金额一致。

Final Answer:
该订单满足超时未发货退款条件，可以为用户发起退款。
```

---

### 3.7 ReAct 的优势

#### 3.7.1 动态性强

ReAct 适合环境不确定的任务。

例如：

```text
搜索结果不够
→ 继续搜索

工具返回异常
→ 换工具

信息缺失
→ 追问用户
```

#### 3.7.2 可解释性强

ReAct 会留下比较自然的执行轨迹：

```text
为什么调用这个工具
工具返回了什么
为什么下一步这么做
```

这对调试和评估非常有价值。

#### 3.7.3 适合外部工具接入

ReAct 天然适合：

- 搜索引擎；
- 数据库；
- API；
- 浏览器；
- 代码执行器；
- 知识库检索系统。

---

### 3.8 ReAct 的缺点

#### 3.8.1 容易循环

如果没有最大步数限制，模型可能不断搜索、不断调用工具。

#### 3.8.2 成本高

每一轮都需要模型推理和工具观察，复杂任务会产生较高 token 成本和延迟。

#### 3.8.3 可测试性较弱

因为每次路径可能不同，所以它比固定 Workflow 更难做严格回归测试。

#### 3.8.4 工具误用风险

模型可能：

- 调错工具；
- 传错参数；
- 重复调用有副作用的工具；
- 在证据不足时执行高风险动作。

---

### 3.9 ReAct 的适用场景

适合：

- 搜索型问答；
- 多跳问答；
- 事实核查；
- 数据查询；
- 编程助手；
- 浏览器自动化；
- 需要边查边判断的任务。

不适合直接裸用在：

- 支付；
- 退款；
- 删除数据；
- 订单修改；
- 高风险审批；
- 合规要求强的业务系统。

这些场景可以局部使用 ReAct，但主流程最好由 Workflow 或状态机控制。

---

### 3.10 工程落地建议

生产环境使用 ReAct 时，建议加入：

```text
max_steps
tool allowlist
tool schema validation
state check
idempotency key
risk guardrail
human approval
trace logging
fallback strategy
```

一句话总结：

> ReAct 适合“开放式探索”，但不适合“无限自由执行”。

---

## 4. Plan-and-Execute 范式详解

### 4.1 Plan-and-Execute 的核心思想

Plan-and-Execute 的核心是：

```text
先规划
再执行
```

它通常分成两个阶段：

```text
Planner：把任务拆成步骤
Executor：按步骤执行任务
```

Plan-and-Solve 论文中提出，先制定计划，把完整任务拆成子任务，再按照计划解决子任务，可以缓解 Zero-shot-CoT 中常见的 missing-step errors。

---

### 4.2 Plan-and-Execute 与 ReAct 的区别

ReAct 是：

```text
边做边想
```

Plan-and-Execute 是：

```text
先想清楚整体路线
再开始执行
```

对比：

| 维度 | ReAct | Plan-and-Execute |
|---|---|---|
| 控制方式 | 动态循环 | 先规划后执行 |
| 是否提前拆解 | 不一定 | 是 |
| 灵活性 | 强 | 中等 |
| 稳定性 | 中等 | 更高 |
| 是否容易测试 | 较难 | 更容易 |
| 适合任务 | 开放探索 | 多步骤目标明确任务 |

---

### 4.3 Plan-and-Execute 的典型执行流程

```text
用户任务
  ↓
Planner 生成任务计划
  ↓
系统检查计划是否合法
  ↓
Executor 执行第 1 步
  ↓
记录执行结果
  ↓
Executor 执行第 2 步
  ↓
必要时更新计划
  ↓
执行完所有步骤
  ↓
汇总结果并输出
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
5. 判断是否满足退款条件
6. 如果满足，执行退款前置校验
7. 生成退款建议或发起退款
8. 返回处理结果
```

这种范式的好处是：

```text
整体任务路径清晰
每一步职责明确
更适合做日志、测试和审计
```

---

### 4.5 Plan-and-Execute 的优势

#### 4.5.1 结构清晰

任务被拆成多个子步骤，便于：

- 观察；
- 调试；
- 复盘；
- 测试；
- 替换某个节点。

#### 4.5.2 适合长任务

例如：

- 旅行规划；
- 报告生成；
- 数据分析；
- 工单处理；
- 文档处理；
- 多步骤业务流程。

#### 4.5.3 更容易工程化

Plan 可以转化为：

- 状态机；
- DAG；
- Workflow；
- 多 Agent 协作任务；
- Human-in-the-loop 审批流程。

#### 4.5.4 有利于成本优化

Planner 可以使用强模型，Executor 的部分步骤可以使用便宜模型、规则或普通代码完成。

---

### 4.6 Plan-and-Execute 的缺点

#### 4.6.1 计划可能过时

规划时并不知道后续工具返回什么。

例如：

```text
计划第 6 步是退款
但第 2 步发现订单已经签收
```

这时原计划需要修改。

#### 4.6.2 Planner 可能规划错误

模型可能规划出：

- 不存在的工具；
- 不必要的步骤；
- 错误顺序；
- 违反业务规则的动作。

#### 4.6.3 对动态环境适应较弱

如果任务环境变化很快，固定计划会变得僵硬。

---

### 4.7 工程落地建议

生产环境不要完全相信 Planner。

建议做成：

```text
Planner
→ Plan Validator
→ Executor
→ Step Result
→ Replanner or Stop
```

关键控制点：

| 控制点 | 作用 |
|---|---|
| Plan schema | 限制计划格式 |
| Plan validator | 检查步骤是否合法 |
| Tool registry | 限制可用工具 |
| Step checkpoint | 每步保存状态 |
| Replanning | 工具结果改变时更新计划 |
| Human approval | 高风险计划必须确认 |
| Stop condition | 避免无限执行 |

一句话总结：

> Plan-and-Execute 适合“目标明确的多步骤任务”，但必须允许计划被验证和修正。

---

## 5. Reflection / Reflexion 范式详解

### 5.1 Reflection 的核心思想

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

Reflexion 论文提出，语言智能体可以不通过更新模型参数，而是通过语言反馈来强化自身表现。它会将反思内容保存到 episodic memory buffer 中，用于后续 trial 的决策。

---

### 5.2 Reflection 与 Reflexion 的关系

在工程语境中：

```text
Reflection：泛指反思、批评、修正机制
Reflexion：一篇代表性论文提出的具体框架
```

Reflection 可以很简单：

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

### 5.3 Reflection 的典型执行流程

```text
生成初始结果
  ↓
Evaluator 判断结果是否达标
  ↓
如果达标：输出
  ↓
如果不达标：Reflector 总结问题
  ↓
将反思内容加入上下文或记忆
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
修改代码

Evaluate:
运行测试，发现仍然失败

Reflect:
失败原因可能是只修复了输入校验，没有处理空列表边界条件

Retry:
重新修改代码，补充边界条件处理

Evaluate:
测试通过
```

这类任务非常适合 Reflection，因为有明确反馈信号：

```text
测试是否通过
```

---

### 5.5 示例：退款判断

```text
初次判断：
用户可以退款

Evaluator:
检查发现没有确认订单是否已签收

Reflect:
退款判断缺少 delivery_status 校验，高风险

Retry:
补充查询物流签收状态后再判断
```

在业务场景中，Reflection 更适合做“复核”和“纠错”，而不是让它无限重试执行真实退款动作。

---

### 5.6 Reflection 的优势

#### 5.6.1 提升复杂任务质量

尤其适合：

- 代码修复；
- 测试生成；
- 报告写作；
- 长推理；
- 复杂问答；
- 多步骤决策。

#### 5.6.2 能利用反馈信号

反馈可以来自：

- 单元测试；
- 编译器；
- 工具报错；
- 规则校验器；
- 人工评价；
- LLM-as-judge；
- 结构化评分。

#### 5.6.3 有助于沉淀失败经验

如果将反思内容写入短期或长期记忆，Agent 可以在后续尝试中避免重复错误。

---

### 5.7 Reflection 的缺点

#### 5.7.1 成本高

每次反思都需要额外模型调用。

如果有多轮重试，成本和延迟会明显上升。

#### 5.7.2 容易过度修正

模型可能把正确答案改坏。

因此需要明确：

```text
什么时候反思
什么时候停止
谁来判断是否真的有问题
```

#### 5.7.3 不适合所有任务

低价值、低风险、强实时任务不适合频繁反思。

例如：

- 简单 FAQ；
- 高并发客服闲聊；
- 实时推荐；
- 毫秒级风控。

---

### 5.8 工程落地建议

Reflection 更适合作为局部能力，而不是全局默认开启。

建议用于：

```text
高价值任务
高复杂任务
有明确反馈信号的任务
允许多轮迭代的任务
```

关键约束：

| 约束 | 作用 |
|---|---|
| max_reflection_rounds | 限制反思次数 |
| evaluator | 判断是否需要反思 |
| structured critique | 让反思输出结构化 |
| memory policy | 控制哪些反思能写入记忆 |
| rollback | 如果新结果更差，可以回退 |
| human review | 高风险场景需要人工复核 |

一句话总结：

> Reflection 不是让模型“想更多”，而是让系统在明确反馈下进行有限纠错。

---

## 6. 三种范式对比

### 6.1 核心区别

| 范式 | 核心思想 | 本质 |
|---|---|---|
| ReAct | 边思考边行动 | 动态探索 |
| Plan-and-Execute | 先规划再执行 | 任务拆解 |
| Reflection | 执行后反思修正 | 错误恢复 |

---

### 6.2 工程维度对比

| 维度 | ReAct | Plan-and-Execute | Reflection |
|---|---|---|---|
| 动态性 | 强 | 中等 | 中等 |
| 可控性 | 中等偏弱 | 强 | 中等 |
| 可解释性 | 强 | 强 | 强 |
| 可测试性 | 中等偏弱 | 强 | 中等 |
| 成本 | 高 | 中等 | 高到很高 |
| 延迟 | 高 | 中等 | 高 |
| 适合工具调用 | 很适合 | 适合 | 作为复核辅助 |
| 适合开放任务 | 很适合 | 一般 | 适合作为增强 |
| 适合高可靠业务 | 不适合裸用 | 适合 | 适合局部复核 |
| 主要风险 | 循环、误调用工具 | 计划过时、计划错误 | 过度反思、成本高 |

---

### 6.3 适用场景对比

| 场景 | 推荐范式 |
|---|---|
| 搜索问答 | ReAct |
| 多跳事实核查 | ReAct |
| 代码修复 | ReAct + Reflection |
| 数据分析报告 | Plan-and-Execute + Reflection |
| 旅行规划 | Plan-and-Execute |
| 企业审批流程 | Workflow + Plan-and-Execute |
| 电商退款/履约 | Workflow + 局部 ReAct + 局部 Reflection |
| 浏览器操作 | ReAct |
| 高风险金融/医疗建议 | Workflow + Guardrails + Human-in-the-loop |
| 简单 FAQ | 普通 LLM 或 RAG，不必 Agent |

---

## 7. 大厂与主流框架中的范式趋势

### 7.1 OpenAI Agents SDK

OpenAI Agents SDK 将 Agent 描述为能够规划、调用工具、跨专家协作，并保持足够状态以完成多步骤工作的应用。它强调的关键能力包括：

- orchestration；
- tool execution；
- approvals；
- state；
- handoffs；
- guardrails；
- tracing。

这说明生产级 Agent 不只是一个 prompt，而是包含状态、工具、审批、轨迹和安全约束的工程系统。

---

### 7.2 LangGraph / LangChain

LangGraph 明确区分 Workflows 和 Agents：

```text
Workflows：预定义代码路径，按特定顺序运行
Agents：动态决定流程和工具使用
```

这对工程实践非常关键：

- 高可靠流程适合 Workflow；
- 开放探索任务适合 Agent；
- 复杂系统常常混合使用二者。

---

### 7.3 LlamaIndex AgentWorkflow

LlamaIndex 的 AgentWorkflow 强调：

```text
创建和编排一个或多个带工具的 Agent 来执行特定任务
```

这说明 Agent 工程正在从单一 Agent，走向：

```text
Workflow orchestration
+ tools
+ state
+ multi-agent coordination
```

---

### 7.4 Microsoft AutoGen / Agent Framework

AutoGen 将 Agent 视为能够通过消息通信、维护自身状态，并根据消息或状态变化执行动作的软件实体。Microsoft Agent Framework 进一步强调：

- 单 Agent；
- 多 Agent；
- 工具调用；
- MCP；
- graph-based workflows；
- checkpointing；
- human-in-the-loop；
- telemetry。

同时，Microsoft 文档明确指出：

```text
如果一个任务可以用函数处理，就应该用函数，而不是 AI Agent。
```

这是非常重要的工程原则：不要为了 Agent 而 Agent。

---

### 7.5 Google ADK

Google ADK 强调从 prompts 和 tool calls 开始，逐步扩展到 multi-agent orchestration、graph-based workflows、performance evaluation 和 deployment。其 Workflow Agents 用于控制子 Agent 的执行流，核心角色是管理其他 Agent 如何、何时运行。

这与当前工业趋势一致：

```text
Agent 自主性需要被工程化编排和约束
```

---

## 8. 生产级 Agent 的常见组合方式

现实中很少使用单一范式解决所有问题。

更常见的是：

```text
主流程：Workflow / StateGraph
局部检索与工具探索：ReAct
复杂结果复核：Reflection
高风险动作：Human-in-the-loop
全链路：Tracing + Evaluation + Guardrails
```

例如电商退款任务：

```text
用户输入
  ↓
Workflow 固定主流程
  ↓
订单/物流查询
  ↓
规则检索节点使用局部 ReAct
  ↓
责任判断
  ↓
Reflection / Verifier 复核高风险判断
  ↓
人工确认或自动执行
  ↓
状态校验
  ↓
回复用户
```

这类架构的核心思想是：

> 让代码控制流程，让模型处理不确定性。

---

## 9. 如何选择范式

### 9.1 选择 ReAct 的条件

适合：

```text
信息不完整
环境不确定
需要边查边判断
工具调用结果会影响下一步
```

典型任务：

- 搜索；
- 多跳问答；
- 代码调试；
- 浏览器操作；
- 数据探索。

不适合：

```text
高风险动作完全自动执行
强规则交易流程裸跑
没有步数限制的开放工具调用
```

---

### 9.2 选择 Plan-and-Execute 的条件

适合：

```text
任务目标明确
步骤较多
需要结构化拆解
需要过程可解释
```

典型任务：

- 报告生成；
- 数据分析；
- 行程规划；
- 文档处理；
- 复杂客服流程。

不适合：

```text
环境高度动态
工具结果经常推翻原计划
```

---

### 9.3 选择 Reflection 的条件

适合：

```text
任务价值高
允许多轮迭代
有明确反馈信号
第一次结果经常不完美
```

典型任务：

- 代码修复；
- 单元测试生成；
- 论文润色；
- 报告检查；
- 复杂决策复核。

不适合：

```text
低价值任务
强实时任务
高并发低延迟任务
没有评价标准的主观任务
```

---

## 10. 学习本阶段时最重要的认知

### 10.1 Agent 不是越自由越好

自由度越高，通常意味着：

- 更难测试；
- 更难控成本；
- 更难保证安全；
- 更容易出现不可预测路径。

生产系统追求的是：

```text
可控地使用智能
```

而不是：

```text
无限释放模型自由度
```

---

### 10.2 Workflow 不是低级，反而是生产核心

很多业务场景不是开放探索，而是强流程任务。

例如：

- 退款；
- 审批；
- 风控；
- 工单；
- 支付；
- 售后。

这些场景更适合：

```text
Workflow + 局部 LLM
```

而不是完全自由 Agent。

---

### 10.3 ReAct、Plan、Reflection 是可组合模块

它们不是互斥关系。

一个优秀 Agent 系统可以同时包含：

```text
Plan：先拆任务
ReAct：局部查证和工具探索
Reflection：失败后复盘修正
Workflow：控制整体执行路径
Guardrails：约束安全边界
```

---

## 11. 阶段小结

### 11.1 一句话理解三种范式

```text
ReAct：
边思考边行动，适合动态探索。

Plan-and-Execute：
先规划再执行，适合多步骤任务。

Reflection：
执行后反思修正，适合复杂任务纠错。
```

---

### 11.2 最重要的工程判断

```text
开放探索任务：
优先 ReAct。

目标明确的多步骤任务：
优先 Plan-and-Execute 或 Workflow。

高价值复杂任务：
局部加入 Reflection。

高风险业务动作：
必须 Workflow + Guardrails + Human-in-the-loop。

简单任务：
不要 Agent，普通 LLM / RAG / 函数即可。
```

---

### 11.3 最终结论

Agent 工程的核心不是“堆框架”，而是：

```text
根据任务的不确定性、风险、成本、延迟和可测试性，
选择合适的任务控制范式。
```

一个成熟的 Agent 工程师应该能做到：

```text
该自由探索时使用 ReAct；
该结构化拆解时使用 Plan-and-Execute；
该复核纠错时使用 Reflection；
该稳定可靠时使用 Workflow；
该不用 Agent 时坚决不用 Agent。
```

---

## 12. 参考资料

### 12.1 核心论文

1. Yao, S. et al. ReAct: Synergizing Reasoning and Acting in Language Models. ICLR 2023.
2. Shinn, N. et al. Reflexion: Language Agents with Verbal Reinforcement Learning. NeurIPS 2023.
3. Wang, L. et al. Plan-and-Solve Prompting: Improving Zero-Shot Chain-of-Thought Reasoning by Large Language Models. ACL 2023.
4. Wu, Q. et al. AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation. arXiv 2023.
5. Hong, S. et al. MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework. arXiv 2023.

### 12.2 官方与主流技术文档

1. OpenAI Agents SDK Documentation.
2. LangGraph Workflows and Agents Documentation.
3. LlamaIndex Agent Workflows Documentation.
4. Microsoft AutoGen Documentation.
5. Microsoft Agent Framework Documentation.
6. Google Agent Development Kit Documentation.
7. Google Research Blog: ReAct.
8. LangChain Blog: Reflection Agents.
9. LangChain Blog: Plan-and-Execute Agents.
