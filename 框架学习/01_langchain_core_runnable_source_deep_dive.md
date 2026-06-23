# LangChain Core 源码学习路线：第 1 篇 Runnable 源码解剖

> 主题：从 `prompt | model | parser` 反推 LangChain Core 的统一执行协议  
> 主线：范式 → 框架表达 → 执行流程 → 源码机制 → 旅行规划助手实践标注  
> 适合阶段：已经理解 Agent 基础范式，希望从框架 API 深入到源码抽象和工程判断

---

## 0. 本篇在框架学习主线中的位置

在 LangChain / LangGraph 的学习中，很多人会先背 API：

```python
chain = prompt | model | parser
result = chain.invoke(input)
```

但源码级学习不能停留在“这样写能跑”。你真正要理解的是：

```text
为什么 Prompt、Model、Parser、Retriever、Tool、普通 Python 函数，都可以被放进同一条链路？
为什么这些组件都能 invoke / stream / batch / ainvoke？
为什么一个 `|` 运算符就能把多个对象组合成一个可执行对象？
为什么 chain 本身组合后仍然是一个 Runnable，还能继续被组合、重试、打标签、追踪、并行执行？
```

答案就是 LangChain Core 的最核心抽象：**Runnable**。

从 Agent 范式角度看，Runnable 不是一个具体 Agent 范式，而是 LangChain 里承载各种范式的“执行协议层”：

| 上层范式 / 能力 | LangChain Core 落点 |
|---|---|
| 普通 LLM Chain | `RunnableSequence` |
| Prompt → Model → Parser | `prompt | model | parser` |
| 函数式预处理 / 后处理 | `RunnableLambda` |
| 多路并行检索 / 多路模型调用 | `RunnableParallel` |
| 条件分支 | `RunnableBranch` |
| 原样透传输入 / 字典字段保留 | `RunnablePassthrough` |
| 统一配置、追踪、重试 | `RunnableConfig` / `with_config` / `with_retry` |

后面学习 Tool Calling、Retriever、Agent、LangGraph Node 时，都会反复遇到 Runnable。所以第一篇必须先把 Runnable 打透。

---

## 1. 学习目标

掌握 LangChain 中最核心的统一执行抽象：`Runnable`。

你需要理解：

1. 为什么 `prompt | model | parser` 可以组合；
2. 为什么每个组件都能 `invoke / ainvoke / stream / astream / batch / abatch`；
3. 为什么普通函数可以变成 `RunnableLambda`；
4. 为什么字典可以隐式变成 `RunnableParallel`；
5. 为什么 LangChain 能把 Prompt、Model、Parser、Retriever、Tool 放在同一套执行协议下；
6. `RunnableConfig` 如何把 `callbacks / tags / metadata / max_concurrency / configurable` 传给下游子调用；
7. `RunnableSequence` 如何逐个调用子 Runnable；
8. `RunnableParallel` 如何把同一个输入并行送给多个 Runnable；
9. `with_retry / with_config / with_types / assign / pick` 这些增强能力为什么能作用在整个 chain 上。

本篇目标不是让你“会写 chain”，而是让你看到这行代码背后的运行时结构：

```python
chain = prompt | model | parser
```

它本质上不是三段代码顺序执行，而是构造了一个新的对象：

```text
RunnableSequence(
  first=ChatPromptTemplate,
  middle=[ChatModel],
  last=StrOutputParser
)
```

这个 `RunnableSequence` 自己仍然是 Runnable，所以它又能继续：

```python
chain.with_config(...)
chain.with_retry(...)
chain.batch([...])
chain.stream(...)
chain | another_runnable
```

---

## 2. 范式映射

### 2.1 普通 LLM Chain → RunnableSequence

普通链路：

```text
User Input
  ↓
Prompt
  ↓
Model
  ↓
Parser
  ↓
Output
```

框架表达：

```python
chain = prompt | model | parser
```

源码抽象：

```text
ChatPromptTemplate  是 Runnable[dict, PromptValue]
ChatModel           是 Runnable[PromptValue/messages, AIMessage]
StrOutputParser     是 Runnable[AIMessage, str]

prompt | model | parser
= RunnableSequence(prompt, model, parser)
```

范式位置：

| 范式层语言 | 框架层语言 | 源码层语言 |
|---|---|---|
| 单步 LLM 调用 | Chain | RunnableSequence |
| 输入模板化 | Prompt | ChatPromptTemplate.invoke |
| 模型生成 | Model | BaseChatModel.invoke |
| 输出后处理 | Parser | StrOutputParser.invoke |
| 链式组合 | LCEL | Runnable.__or__ |

这说明：Runnable 是 LangChain 里最小的“可执行单元”，RunnableSequence 是最常见的“顺序编排单元”。

### 2.2 为什么这是学习 Agent 框架的第一站

在 Agent 系统里，即使你后来使用的是 LangGraph，节点内部仍然大量出现：

```python
intent_chain = intent_prompt | model | intent_parser
planner_chain = planner_prompt | model.with_structured_output(Plan)
reflection_chain = reflection_prompt | model | parser
```

这些链路本质上都是 RunnableSequence。

所以你在旅行规划助手里看到的：

```python
prompt | model
prompt | model | parser
retriever | formatter | prompt | model | parser
```

都应该被标注为：

```text
这是一个 RunnableSequence。
它的输入类型是什么？
每一步输出类型是什么？
最终输出类型是什么？
它是否支持 batch？
它是否支持 stream？
它是否能挂 callbacks / tags / metadata？
它是否可以加 with_retry？
```

---

## 3. 最小代码

### 3.1 标准 Prompt → Model → Parser 链

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

### 3.2 你应该如何读这段代码

不要只读成：

```text
先格式化 prompt，再调用模型，再转成字符串。
```

源码级读法应该是：

```text
1. ChatPromptTemplate 是一个 Runnable。
2. ChatModel 是一个 Runnable。
3. StrOutputParser 是一个 Runnable。
4. `|` 调用 Runnable.__or__。
5. __or__ 会调用 coerce_to_runnable，把右侧对象转成 Runnable。
6. __or__ 返回 RunnableSequence。
7. 第二个 `| parser` 继续构造更长的 RunnableSequence。
8. chain.invoke(input) 实际调用 RunnableSequence.invoke(input)。
9. RunnableSequence.invoke 按 steps 顺序调用每个子 Runnable。
10. 每一步输出成为下一步输入。
```

### 3.3 推荐增加调试代码

```python
print(type(prompt))
print(type(model))
print(type(StrOutputParser()))
print(type(chain))

print(chain.get_graph())
print(chain.input_schema.model_json_schema())
print(chain.output_schema.model_json_schema())
```

你关注的不是输出好不好看，而是验证三件事：

1. `chain` 的类型是不是 `RunnableSequence`；
2. `chain` 是否暴露 input_schema / output_schema；
3. `chain.get_graph()` 是否能把链路还原成图结构。

---

## 4. 执行流程

### 4.1 用户看到的执行流程

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

### 4.2 源码视角的执行流程

更接近源码的执行过程是：

```text
chain.invoke(input, config=None)
  ↓
RunnableSequence.invoke(input, config)
  ↓
ensure_config(config)
  ↓
创建 root run / callback manager
  ↓
遍历 steps：
    step_1 = ChatPromptTemplate
    step_2 = ChatModel
    step_3 = StrOutputParser
  ↓
每一步执行前 patch_config：
    为子步骤创建 child callback manager
    写入 seq:step:1 / seq:step:2 / seq:step:3
  ↓
output_1 = step_1.invoke(input, child_config)
  ↓
output_2 = step_2.invoke(output_1, child_config)
  ↓
output_3 = step_3.invoke(output_2, child_config)
  ↓
callback_manager.on_chain_end(output_3)
  ↓
return output_3
```

### 4.3 类型流转

以旅行规划助手为例，输入输出不是一直都是字符串：

```text
输入：dict
{
  "destination": "东京",
  "days": 5
}

ChatPromptTemplate 输出：PromptValue
PromptValue 可转 messages：
[
  SystemMessage(content="你是一个旅行规划助手。"),
  HumanMessage(content="请为 东京 规划 5 天行程。")
]

ChatModel 输出：AIMessage
AIMessage(content="以下是东京 5 天行程...")

StrOutputParser 输出：str
"以下是东京 5 天行程..."
```

所以你后面学习 Tool Calling 时要记住：

```text
模型输出不是普通字符串，而是 AIMessage。
AIMessage 既可以有 content，也可以有 tool_calls、usage_metadata、response_metadata。
Parser 只是把 AIMessage 进一步转成你需要的业务结构。
```

---

## 5. 源码阅读入口

### 5.1 核心文件

```text
langchain_core/runnables/base.py
langchain_core/runnables/config.py
langchain_core/runnables/utils.py
langchain_core/runnables/passthrough.py
langchain_core/runnables/branch.py
```

### 5.2 本篇重点类

```text
Runnable
RunnableSequence
RunnableParallel
RunnableLambda
RunnableConfig
```

### 5.3 扩展类

```text
RunnableSerializable
RunnableBinding
RunnablePassthrough
RunnableAssign
RunnablePick
RunnableBranch
RunnableGenerator
```

### 5.4 推荐阅读顺序

不要一上来从文件头读到文件尾。建议按问题倒推：

```text
第一轮：看 Runnable 的协议
  ↓
Runnable.invoke / ainvoke / stream / batch

第二轮：看 `|` 是怎么组合的
  ↓
Runnable.__or__ / __ror__ / pipe / coerce_to_runnable

第三轮：看 RunnableSequence 如何执行
  ↓
RunnableSequence.__init__ / invoke / batch / transform / stream

第四轮：看 RunnableLambda 如何包装普通函数
  ↓
RunnableLambda.__init__ / invoke / ainvoke

第五轮：看 RunnableConfig 如何传递
  ↓
ensure_config / patch_config / merge_configs / get_config_list

第六轮：看并行与分支
  ↓
RunnableParallel / RunnableBranch / RunnablePassthrough
```

### 5.5 推荐源码链接

- LangChain Core Runnable reference：`https://reference.langchain.com/python/langchain-core/runnables/`
- Runnable API：`https://reference.langchain.com/python/langchain-core/runnables/base/Runnable/`
- RunnableSequence API：`https://reference.langchain.com/python/langchain-core/runnables/base/RunnableSequence/`
- RunnableParallel API：`https://reference.langchain.com/python/langchain-core/runnables/base/RunnableParallel/`
- RunnableConfig API：`https://reference.langchain.com/python/langchain-core/runnables/config/RunnableConfig/`
- GitHub 源码：`https://github.com/langchain-ai/langchain/blob/master/libs/core/langchain_core/runnables/base.py`
- RunnableConfig 源码：`https://github.com/langchain-ai/langchain/blob/master/libs/core/langchain_core/runnables/config.py`

---

## 6. 源码核心概念一：Runnable 是统一执行协议

### 6.1 Runnable 的定位

源码中 `Runnable` 的核心定义可以概括为：

```text
Runnable 是一个可以被调用、批处理、流式输出、转换、组合的工作单元。
```

这句话有四层含义：

1. **可调用**：单输入单输出，`invoke(input)`；
2. **可异步调用**：`ainvoke(input)`；
3. **可批处理**：多输入多输出，`batch(inputs)`；
4. **可流式输出**：逐块输出，`stream(input)`；
5. **可组合**：通过 `|` 或 `pipe()` 组合成更大的 Runnable；
6. **可配置**：每次运行可携带 tags、metadata、callbacks、max_concurrency 等配置；
7. **可追踪**：通过 callback manager / LangSmith 记录中间步骤；
8. **可模式化**：暴露 input_schema、output_schema、config_schema。

### 6.2 Runnable 的核心方法

源码中最重要的方法可以分成四类。

#### 6.2.1 执行方法

```text
invoke(input, config=None, **kwargs) -> output
ainvoke(input, config=None, **kwargs) -> output
stream(input, config=None, **kwargs) -> Iterator[chunk]
astream(input, config=None, **kwargs) -> AsyncIterator[chunk]
batch(inputs, config=None, **kwargs) -> list[output]
abatch(inputs, config=None, **kwargs) -> list[output]
```

#### 6.2.2 组合方法

```text
__or__(other)
__ror__(other)
pipe(*others)
assign(**kwargs)
pick(keys)
```

其中 `__or__` 是 `prompt | model` 的根源。

#### 6.2.3 配置增强方法

```text
with_config(...)
with_retry(...)
with_fallbacks(...)
with_types(...)
with_listeners(...)
configurable_fields(...)
configurable_alternatives(...)
```

这些方法不是只给 LLM 用的，而是给所有 Runnable 用的。这就是为什么整个 chain 可以直接：

```python
chain = (prompt | model | parser).with_retry(stop_after_attempt=3)
```

#### 6.2.4 Schema / Trace 方法

```text
input_schema
output_schema
config_schema()
get_graph()
get_prompts()
```

这些方法让 Runnable 不只是可执行，还可以被：

```text
可视化
可验证
可追踪
可调试
可序列化
```

### 6.3 Runnable 的默认实现关系

Runnable 里最重要的设计是：**只要子类实现最核心的同步调用能力，框架就能给它补齐其他执行模式的默认实现。**

简化理解：

```text
ainvoke 默认：把 invoke 放到 executor 里运行
batch 默认：对多个输入并行调用 invoke
stream 默认：如果没有原生流式能力，就把 invoke 的最终结果作为一个 chunk 输出
abatch 默认：并发调用 ainvoke
```

因此，很多组件只需要实现 `invoke`，就天然拥有 `ainvoke / batch / stream` 的统一外观。

但是要注意：

```text
“支持 stream 方法”不等于“真正 token 级流式输出”。
```

如果某个组件没有实现原生 `transform` 或流式逻辑，它虽然也能被 `stream()` 调用，但可能只是等整个结果生成后一次性吐出。

这对旅行规划助手很关键：

```text
如果你希望前端 SSE 逐 token 展示最终行程，链路中的中间步骤不能随便放阻塞型 RunnableLambda。
否则流式输出会被阻塞在该步骤之后才开始。
```

---

## 7. 源码核心概念二：`|` 运算符如何构造 RunnableSequence

### 7.1 表面现象

你写：

```python
chain = prompt | model | parser
```

Python 实际执行顺序是：

```python
chain_1 = prompt.__or__(model)
chain_2 = chain_1.__or__(parser)
```

最终得到：

```text
RunnableSequence(prompt, model, parser)
```

### 7.2 源码关键逻辑

源码中 `Runnable.__or__` 的核心逻辑可以简化为：

```python
def __or__(self, other):
    return RunnableSequence(self, coerce_to_runnable(other))
```

`__ror__` 处理的是右结合场景，比如：

```python
{"context": retriever, "question": RunnablePassthrough()} | prompt
```

当左侧是 dict，不是 Runnable 时，Python 会尝试调用右侧对象的 `__ror__`。

### 7.3 coerce_to_runnable：为什么普通函数和 dict 也能进链

`coerce_to_runnable` 是理解 LCEL 的关键函数。

它的逻辑可以概括为：

```python
if thing is Runnable:
    return thing

if thing is generator function:
    return RunnableGenerator(thing)

if thing is callable:
    return RunnableLambda(thing)

if thing is dict:
    return RunnableParallel(thing)

else:
    raise TypeError
```

这解释了三个常见现象。

#### 现象一：普通函数可以直接写进链

```python
def format_plan(ai_message):
    return ai_message.content.strip()

chain = prompt | model | format_plan
```

本质是：

```python
chain = prompt | model | RunnableLambda(format_plan)
```

#### 现象二：dict 可以触发并行

```python
chain = {
    "food": food_chain,
    "attractions": attraction_chain,
} | merge_prompt | model
```

本质是：

```python
chain = RunnableParallel({
    "food": food_chain,
    "attractions": attraction_chain,
}) | merge_prompt | model
```

#### 现象三：不支持的类型会报错

```python
chain = prompt | "not runnable"
```

会报类似错误：

```text
Expected a Runnable, callable or dict.
Instead got an unsupported type: <class 'str'>
```

这个错误不是模型问题，而是 LCEL 组合阶段 `coerce_to_runnable` 不知道如何把字符串变成 Runnable。

### 7.4 工程理解

`|` 的本质不是“把 Python 函数拼起来”，而是做了两件事：

```text
1. 把每个对象统一包装成 Runnable；
2. 把多个 Runnable 注册进 RunnableSequence。
```

所以 `prompt | model | parser` 的工程含义是：

```text
声明一条可执行、可追踪、可批处理、可流式、可配置的执行管线。
```

---

## 8. 源码核心概念三：RunnableSequence 如何执行

### 8.1 RunnableSequence 的定位

`RunnableSequence` 是 LangChain 里最重要的组合算子之一。它的语义是：

```text
按顺序调用多个 Runnable，前一个 Runnable 的输出作为下一个 Runnable 的输入。
```

即：

```text
x0 = input
x1 = step1.invoke(x0)
x2 = step2.invoke(x1)
x3 = step3.invoke(x2)
return x3
```

### 8.2 构造阶段

当你写：

```python
chain = prompt | model | parser
```

构造阶段大致发生：

```text
1. prompt.__or__(model)
2. coerce_to_runnable(model)
3. RunnableSequence(prompt, model)
4. sequence.__or__(parser)
5. coerce_to_runnable(parser)
6. RunnableSequence(prompt, model, parser)
```

RunnableSequence 内部通常会维护：

```text
first
middle
last
```

这是为了类型推断和执行优化。你可以理解为：

```text
steps = [first, *middle, last]
```

### 8.3 invoke 执行阶段

简化伪源码：

```python
def invoke(self, input, config=None, **kwargs):
    config = ensure_config(config)
    callback_manager = get_callback_manager_for_config(config)
    run_manager = callback_manager.on_chain_start(...)

    try:
        for i, step in enumerate(self.steps):
            child_config = patch_config(
                config,
                callbacks=run_manager.get_child(f"seq:step:{i + 1}")
            )

            if i == 0:
                input = step.invoke(input, child_config, **kwargs)
            else:
                input = step.invoke(input, child_config)

        run_manager.on_chain_end(input)
        return input

    except BaseException as e:
        run_manager.on_chain_error(e)
        raise
```

这段逻辑解释了几个重要细节。

#### 细节一：kwargs 只传给第一个 step

如果你执行：

```python
chain.invoke(input, some_kwarg="value")
```

通常只有第一个 step 会接收额外 kwargs，后续 step 接收的是前一步输出。

#### 细节二：每个 step 都有 child callback

每一步都会通过：

```text
run_manager.get_child("seq:step:n")
```

生成子运行记录。

这就是为什么 LangSmith 或 ConsoleCallbackHandler 能看到：

```text
chain
  ├── seq:step:1 ChatPromptTemplate
  ├── seq:step:2 ChatModel
  └── seq:step:3 StrOutputParser
```

#### 细节三：异常会进入 on_chain_error

任何一步失败，都会：

```text
触发 callback on_chain_error
中断后续步骤
向外抛出异常
```

所以调试时你要定位：

```text
是 prompt 格式化失败？
是 model 调用失败？
是 parser 解析失败？
```

不要只看最终报错。

### 8.4 batch 执行阶段

`RunnableSequence.batch(inputs)` 的语义不是简单地：

```python
[chain.invoke(x) for x in inputs]
```

更准确的理解是：

```text
先把所有 inputs 批量送进 step1；
再把 step1 的所有 outputs 批量送进 step2；
再把 step2 的所有 outputs 批量送进 step3。
```

即：

```text
inputs_0 = [case1, case2, case3]
inputs_1 = step1.batch(inputs_0)
inputs_2 = step2.batch(inputs_1)
inputs_3 = step3.batch(inputs_2)
return inputs_3
```

这样设计的好处是：

```text
如果某个底层模型 API 支持真正 batch，它可以在自己的 batch 中优化；
如果不支持，Runnable 默认 batch 会用线程池并发执行 invoke。
```

这对评估很重要。比如你做旅行助手测试集：

```python
results = chain.batch([
    {"destination": "东京", "days": 5},
    {"destination": "大阪", "days": 3},
    {"destination": "京都", "days": 4},
])
```

你不是手写 for 循环，而是让每个 Runnable 自己决定是否优化 batch。

### 8.5 stream 执行阶段

`RunnableSequence.stream(input)` 更复杂，因为它要考虑链路中每个 step 是否支持流式转换。

源码层核心概念是 `transform`：

```text
transform: Iterator[InputChunk] -> Iterator[OutputChunk]
```

如果链路中每个组件都实现了 transform，那么数据可以像管道一样一边输入一边输出：

```text
input stream
  ↓
step1.transform
  ↓
step2.transform
  ↓
step3.transform
  ↓
output stream
```

但如果中间某个组件不支持 transform，例如普通 `RunnableLambda`，就可能阻塞流式输出：

```text
step1 支持流式
step2 不支持流式，需要等完整输入
step3 支持流式

结果：stream 会从 step2 完成后才开始继续往下游输出。
```

工程结论：

```text
如果你的旅行规划助手要做 SSE 流式响应，
不要在最终模型输出前随便插入阻塞型 RunnableLambda。
```

如果确实需要自定义流式逻辑，优先考虑：

```text
RunnableGenerator
或自定义 Runnable 并实现 transform / atransform
```

---

## 9. 源码核心概念四：RunnableLambda 如何包装普通函数

### 9.1 表面用法

```python
from langchain_core.runnables import RunnableLambda


def normalize_destination(input: dict) -> dict:
    return {
        **input,
        "destination": input["destination"].strip()
    }

normalize_node = RunnableLambda(normalize_destination)

chain = normalize_node | prompt | model | StrOutputParser()
```

也可以直接写：

```python
chain = normalize_destination | prompt | model | StrOutputParser()
```

因为 `coerce_to_runnable` 会把 callable 转成 `RunnableLambda`。

### 9.2 RunnableLambda 解决什么问题

它解决的是：

```text
如何把普通 Python 业务逻辑放进 LangChain 的统一执行协议？
```

比如：

```text
字段清洗
输入归一化
输出格式修正
日志补充
规则判断
轻量数据转换
```

这些逻辑不需要 LLM，但需要接入 chain 的执行、追踪、配置和批处理体系。

### 9.3 RunnableLambda 的源码机制

RunnableLambda 的核心行为：

```text
1. 接收一个 Python callable；
2. 检查它是同步函数、异步函数、生成器函数还是异步生成器函数；
3. invoke 时调用同步函数；
4. ainvoke 时优先调用异步函数，否则委托线程池；
5. batch 时继承 Runnable 默认 batch；
6. 如果函数返回另一个 Runnable，则继续调用返回的 Runnable。
```

简化伪源码：

```python
class RunnableLambda(Runnable):
    def __init__(self, func, afunc=None, name=None):
        self.func = func
        self.afunc = afunc
        self.name = name or func.__name__

    def invoke(self, input, config=None, **kwargs):
        config = ensure_config(config)
        output = call_func_with_variable_args(
            self.func,
            input,
            config,
            run_manager=...
        )

        if isinstance(output, Runnable):
            return output.invoke(input, config)

        return output
```

### 9.4 call_func_with_variable_args：函数为什么可以接收 config / run_manager

普通函数可能有不同签名：

```python
def f(x): ...

def f(x, config): ...

def f(x, run_manager): ...

def f(x, run_manager, config): ...
```

LangChain 会通过工具函数判断函数是否接受 `config` 或 `run_manager`，然后按需注入。

这让你可以写出更工程化的业务函数：

```python
from langchain_core.runnables import RunnableConfig


def normalize_request(input: dict, config: RunnableConfig) -> dict:
    metadata = config.get("metadata", {})
    trace_id = metadata.get("trace_id")

    return {
        **input,
        "trace_id": trace_id,
        "destination": input["destination"].strip()
    }
```

这样函数仍然是普通函数，但进入 RunnableLambda 后可以读取运行配置。

### 9.5 RunnableLambda 的流式限制

源码文档中明确提醒：`RunnableLambda` 更适合不需要流式处理的普通函数。如果需要 chunk-by-chunk 的流式转换，应使用 `RunnableGenerator` 或自定义 Runnable。

所以旅行规划助手里：

```python
chain = prompt | model | RunnableLambda(clean_text) | parser
```

如果 `model` 原本可以 token streaming，`RunnableLambda(clean_text)` 可能成为流式阻塞点。

更推荐：

```text
非流式预处理：放在 prompt 前
非流式后处理：放在最终输出后
需要流式处理：实现 transform / RunnableGenerator
```

---

## 10. 源码核心概念五：RunnableConfig 如何传递 callbacks、tags、metadata

### 10.1 RunnableConfig 是什么

`RunnableConfig` 是每次执行 Runnable 时携带的运行配置。

常见字段：

```text
tags: list[str]
metadata: dict[str, Any]
callbacks: callback handlers 或 callback manager
run_name: 当前运行名称
run_id: 当前运行 ID
max_concurrency: 最大并发数
recursion_limit: 最大递归深度
configurable: 运行时可配置字段
```

典型用法：

```python
result = chain.invoke(
    {"destination": "东京", "days": 5},
    config={
        "run_name": "travel_plan_chain",
        "tags": ["travel", "runnable-sequence", "demo"],
        "metadata": {
            "user_id": "u_001",
            "trace_id": "trace_20260608_001"
        },
        "max_concurrency": 5,
    }
)
```

### 10.2 RunnableConfig 为什么重要

在 Demo 里你可以忽略 config，但在生产 Agent 系统里它非常关键：

| 字段 | 作用 | 旅行助手例子 |
|---|---|---|
| `tags` | 给 trace 打标签 | `travel`, `planner`, `eval` |
| `metadata` | 记录业务元信息 | `user_id`, `session_id`, `request_id` |
| `callbacks` | 接入日志、LangSmith、自定义监控 | 输出每一步耗时 |
| `run_name` | 当前链路名称 | `itinerary_generation_chain` |
| `max_concurrency` | 控制 batch / parallel 并发 | 并发评估 100 条 case |
| `configurable` | 运行时切换模型、温度、策略 | `llm=openai` / `llm=qwen` |

### 10.3 ensure_config：为什么 config 可以自动继承

`ensure_config(config)` 做的事情可以理解为：

```text
1. 如果 config 为 None，创建默认配置；
2. 补齐 tags、metadata、callbacks、recursion_limit、configurable 等字段；
3. 从 ContextVar 中读取父 Runnable 的配置；
4. 合并父配置和当前配置；
5. 把未知普通字段放进 configurable；
6. 把部分 configurable 字段同步到 metadata，便于 trace。
```

这解释了为什么父 chain 设置的 tags / metadata 可以传给子步骤。

### 10.4 patch_config：为什么每个子步骤能有独立 callback

RunnableSequence 执行每个 step 时，会基于父 config 派生 child config：

```python
child_config = patch_config(
    config,
    callbacks=run_manager.get_child("seq:step:1")
)
```

这意味着：

```text
父运行：travel_plan_chain
  子运行：seq:step:1 prompt
  子运行：seq:step:2 model
  子运行：seq:step:3 parser
```

这些子运行共享父级 tags / metadata，但 callbacks 指向各自的 child run manager。

### 10.5 merge_configs：with_config 为什么能叠加

你可以这样写：

```python
base_chain = prompt | model | parser

chain = base_chain.with_config(
    tags=["travel"],
    metadata={"component": "planner"}
)

chain.invoke(
    input,
    config={
        "tags": ["eval"],
        "metadata": {"case_id": "C001"}
    }
)
```

最终配置不是简单覆盖，而是合并：

```text
tags: travel + eval
metadata: component + case_id
callbacks: 合并或继承
configurable: 合并
```

工程建议：

```text
链路级 tags：标注模块，如 travel / planner / parser
请求级 metadata：标注业务请求，如 user_id / session_id / case_id
评估级 metadata：标注测试样本，如 dataset / case_id / expected_intent
```

---

## 11. 源码核心概念六：callbacks 如何进入执行链

### 11.1 callback 的本质

Callback 是 LangChain 的生命周期钩子。它让你能观察：

```text
chain 开始
chain 结束
chain 报错
LLM 开始
LLM 结束
tool 开始
tool 结束
retriever 开始
retriever 结束
```

Runnable 层通过 RunnableConfig 传递 callbacks。

```python
from langchain_core.tracers import ConsoleCallbackHandler

chain.invoke(
    {"destination": "东京", "days": 5},
    config={
        "callbacks": [ConsoleCallbackHandler()],
        "tags": ["debug", "travel"],
        "metadata": {"case_id": "debug_001"},
    }
)
```

### 11.2 callback 在 RunnableSequence 中的层级

执行一个 RunnableSequence 时，callback trace 大致是：

```text
on_chain_start: RunnableSequence
  on_chain_start: ChatPromptTemplate
  on_chain_end: ChatPromptTemplate

  on_chat_model_start: ChatModel
  on_llm_end: ChatModel

  on_parser_start: StrOutputParser
  on_parser_end: StrOutputParser
on_chain_end: RunnableSequence
```

不同组件的 callback 类型可能不同，但父子层级由 `run_manager.get_child(...)` 保持。

### 11.3 旅行助手中的建议

给每条 RunnableSequence 都配置明确名称：

```python
intent_chain = (intent_prompt | model | intent_parser).with_config(
    run_name="intent_chain",
    tags=["travel", "intent", "runnable"]
)

planner_chain = (planner_prompt | model | planner_parser).with_config(
    run_name="planner_chain",
    tags=["travel", "planner", "runnable"]
)
```

这样后续 LangSmith / 日志里才不会只看到一堆匿名 RunnableSequence。

---

## 12. 源码核心概念七：RunnableParallel 如何并行调用多个子 Runnable

### 12.1 表面用法

```python
from langchain_core.runnables import RunnableParallel

parallel = RunnableParallel({
    "food": food_chain,
    "attractions": attraction_chain,
    "weather": weather_chain,
})

result = parallel.invoke({
    "destination": "东京",
    "days": 5
})
```

结果：

```python
{
    "food": "东京美食推荐...",
    "attractions": "东京景点推荐...",
    "weather": "东京天气建议..."
}
```

### 12.2 dict 隐式转换

你也可以写：

```python
parallel = {
    "food": food_chain,
    "attractions": attraction_chain,
    "weather": weather_chain,
}
```

只要它出现在 `|` 组合里：

```python
chain = {
    "food": food_chain,
    "attractions": attraction_chain,
    "weather": weather_chain,
} | merge_prompt | model | parser
```

`coerce_to_runnable` 会把 dict 转为 `RunnableParallel`。

### 12.3 RunnableParallel 的语义

RunnableParallel 的语义是：

```text
给每个子 Runnable 同一个输入，
并行执行，
最后把每个子 Runnable 的输出按 key 合并成 dict。
```

简化伪源码：

```python
def invoke(self, input, config=None):
    steps = self.steps__
    results = {}

    with get_executor_for_config(config) as executor:
        futures = {
            key: executor.submit(step.invoke, input, child_config)
            for key, step in steps.items()
        }

        for key, future in futures.items():
            results[key] = future.result()

    return results
```

### 12.4 max_concurrency 如何影响并行

```python
parallel.invoke(
    input,
    config={"max_concurrency": 3}
)
```

`max_concurrency` 会影响内部 executor 的最大并发数。

对旅行助手来说：

```text
景点检索、餐厅检索、天气查询、交通建议
可以并行。

但创建订单、扣款、退款、写数据库
不能盲目并行，必须看副作用和事务顺序。
```

### 12.5 RunnableParallel 和 Agent 范式的关系

它不是 Multi-Agent，但可以承载“多路信息收集”：

```text
并行检索多个来源
并行调用多个轻量模型
并行生成多个候选方案
并行做多个维度评分
```

在旅行规划助手里，典型结构是：

```python
research_chain = {
    "attractions": attraction_retriever | format_docs,
    "food": food_retriever | format_docs,
    "weather": weather_tool,
    "transport": transport_tool,
} | synthesis_prompt | model | parser
```

范式映射：

```text
信息收集阶段：RunnableParallel
综合生成阶段：RunnableSequence
整体任务范式：Plan-and-Execute / Workflow 中的某个节点
```

---

## 13. 源码核心概念八：RunnablePassthrough / assign / pick

### 13.1 为什么需要 Passthrough

在链式执行中，一个常见问题是：

```text
经过某个步骤后，原始输入丢了。
```

例如：

```python
chain = retriever | prompt | model | parser
```

执行到 prompt 时，可能只剩下检索结果，没有原始 question。

这时需要 `RunnablePassthrough` 保留输入。

### 13.2 RAG 常见写法

```python
from langchain_core.runnables import RunnablePassthrough

rag_chain = (
    {
        "context": retriever | format_docs,
        "question": RunnablePassthrough(),
    }
    | prompt
    | model
    | StrOutputParser()
)
```

执行语义：

```text
输入 question
  ↓
RunnableParallel:
  context = retriever(question) | format_docs
  question = 原样透传 question
  ↓
prompt 接收 {context, question}
  ↓
model
  ↓
parser
```

### 13.3 assign 的语义

`assign` 用于在 dict 输出上追加字段：

```python
chain = base_chain.assign(
    total_chars=lambda x: len(x["answer"]),
    source_count=lambda x: len(x["sources"]),
)
```

语义：

```text
保留原 dict 字段；
并行计算新字段；
把新字段合并回原 dict。
```

### 13.4 pick 的语义

`pick` 用于从 dict 输出中抽取字段：

```python
answer_only = chain.pick("answer")
```

语义：

```text
输入：{"answer": "...", "sources": [...], "score": 0.9}
输出："..."
```

### 13.5 旅行助手应用

```python
travel_context_chain = (
    {
        "user_request": RunnablePassthrough(),
        "attractions": attraction_chain,
        "food": food_chain,
        "weather": weather_chain,
    }
    | RunnablePassthrough.assign(
        evidence_count=lambda x: len(x["attractions"]) + len(x["food"])
    )
)
```

这个链路的作用是：

```text
并行收集多类旅行信息；
保留原始用户请求；
追加 evidence_count；
把结构化上下文交给 planner prompt。
```

---

## 14. 源码核心概念九：RunnableBranch 如何实现轻量 Router

### 14.1 RunnableBranch 的定位

`RunnableBranch` 是 LangChain Core 里的条件分支 Runnable。它适合轻量路由：

```text
如果满足条件 A，执行 chain_a；
如果满足条件 B，执行 chain_b；
否则执行 default_chain。
```

表面代码：

```python
from langchain_core.runnables import RunnableBranch

branch = RunnableBranch(
    (lambda x: "预算" in x["user_request"], budget_chain),
    (lambda x: "景点" in x["user_request"], attraction_chain),
    general_chain,
)
```

### 14.2 与 LangGraph Router 的区别

| 对比项 | RunnableBranch | LangGraph conditional edge |
|---|---|---|
| 所在层级 | LangChain Core Runnable | LangGraph 图编排 |
| 状态模型 | 单次输入输出 | 共享 State |
| 路由粒度 | 链内部轻量分支 | 节点级流程控制 |
| 可观测性 | Runnable trace | Graph trace / checkpoint |
| 适合场景 | 简单分支 | 复杂业务流程 |

旅行助手中：

```text
简单：根据用户请求走预算 chain / 景点 chain → RunnableBranch
复杂：多轮状态、工具失败重试、人工确认 → LangGraph conditional edge
```

### 14.3 工程建议

不要把所有路由都塞进 RunnableBranch。

```text
如果只是链内部的轻量条件选择，用 RunnableBranch。
如果需要状态持久化、循环、回滚、HITL，用 LangGraph。
```

---

## 15. 源码阅读问题逐条解答

### 问题 1：Runnable 的核心抽象方法有哪些？

核心是：

```text
invoke / ainvoke
batch / abatch
stream / astream
transform / atransform
```

其中 `invoke` 是最基础的单输入单输出协议；`batch` 面向多输入；`stream` 面向流式输出；`transform` 是更底层的流式转换协议。

你可以把它们理解为：

| 方法 | 输入 | 输出 | 适用场景 |
|---|---|---|---|
| `invoke` | 单个输入 | 单个最终结果 | 普通调用 |
| `ainvoke` | 单个输入 | 单个最终结果 | 异步服务 |
| `batch` | 输入列表 | 输出列表 | 测试集评估 / 批量请求 |
| `abatch` | 输入列表 | 输出列表 | 异步批处理 |
| `stream` | 单个输入 | chunk 迭代器 | SSE / token 流式 |
| `astream` | 单个输入 | async chunk 迭代器 | 异步流式 |
| `transform` | 输入流 | 输出流 | 真正流式管道 |

### 问题 2：invoke、ainvoke、stream、batch 的默认实现关系是什么？

简化关系：

```text
ainvoke 默认通过 executor 调用 invoke
batch 默认通过线程池并发调用 invoke
abatch 默认通过 asyncio 并发调用 ainvoke
stream 默认依赖 transform；如果没有原生流式，可能退化为最终结果输出
```

所以：

```text
一个 Runnable 只实现 invoke，也能拥有完整执行外观；
但高质量组件会重写 batch / stream / ainvoke 来提升性能。
```

### 问题 3：`|` 运算符如何构造 RunnableSequence？

核心流程：

```text
左侧 Runnable 调用 __or__(右侧对象)
  ↓
coerce_to_runnable(右侧对象)
  ↓
把右侧对象转成 Runnable
  ↓
返回 RunnableSequence(左侧 Runnable, 右侧 Runnable)
```

如果左侧不是 Runnable，右侧是 Runnable，则触发 `__ror__`：

```text
右侧 Runnable 调用 __ror__(左侧对象)
  ↓
coerce_to_runnable(左侧对象)
  ↓
返回 RunnableSequence(左侧 Runnable, 右侧 Runnable)
```

### 问题 4：RunnableConfig 如何向下传递？

核心机制：

```text
1. 父 Runnable 接收 config；
2. ensure_config 补齐默认字段；
3. set_config_context 把 config 放入 ContextVar；
4. 子 Runnable 执行时通过 ensure_config 继承父配置；
5. RunnableSequence / Parallel 会通过 patch_config 创建 child callbacks；
6. tags / metadata / configurable 等字段继续向下传播。
```

### 问题 5：callbacks、tags、metadata 如何进入执行链？

入口：

```python
chain.invoke(input, config={
    "callbacks": [...],
    "tags": ["travel"],
    "metadata": {"case_id": "C001"},
})
```

运行时：

```text
get_callback_manager_for_config(config)
  ↓
CallbackManager.configure(
  inheritable_callbacks=config["callbacks"],
  inheritable_tags=config["tags"],
  inheritable_metadata=config["metadata"]
)
```

然后每个子步骤通过 child callback manager 记录为父运行的子调用。

### 问题 6：RunnableSequence 如何逐个调用子 Runnable？

核心是：

```python
for i, step in enumerate(steps):
    input = step.invoke(input, child_config)
return input
```

前一步输出覆盖 `input` 变量，成为下一步输入。

### 问题 7：RunnableParallel 如何并行调用多个子 Runnable？

核心是：

```text
给每个子 Runnable 同一个 input；
使用 executor / asyncio 并发执行；
按 key 收集结果；
返回 dict。
```

伪代码：

```python
outputs = {
    key: step.invoke(input, child_config)
    for key, step in parallel_steps.items()
}
```

只不过真实源码中这个过程会通过 executor 并行，并处理 callbacks / config / errors / stream。

---

## 16. 旅行规划助手中的实践任务

### 16.1 搜索目标

在旅行规划助手项目中查找所有类似代码：

```python
prompt | model
prompt | model | parser
retriever | formatter | prompt | model | parser
{
    "context": retriever,
    "question": RunnablePassthrough()
} | prompt | model
```

### 16.2 标注模板

给每一条链补充如下源码理解注释：

```python
travel_plan_chain = prompt | model | StrOutputParser()
"""
RunnableSequence 标注：
- 范式层：普通 LLM Chain / 行程生成节点
- 框架层：ChatPromptTemplate | ChatModel | StrOutputParser
- 源码层：Runnable.__or__ 构造 RunnableSequence
- 输入：dict(destination: str, days: int, preferences: list[str])
- Step1 输出：PromptValue / messages
- Step2 输出：AIMessage
- Step3 输出：str
- 支持 invoke：是
- 支持 batch：是，默认逐 step batch
- 支持 stream：取决于 model 和 parser 是否支持 transform
- 可加 with_retry：是，建议加在 model 或整个 chain 上
- 可加 with_config：是，建议添加 run_name / tags / metadata
"""
```

### 16.3 推荐整理表

| Chain 名称 | 代码形式 | Runnable 类型 | 输入 | 中间输出 | 最终输出 | 是否 stream | 是否 with_retry | 是否 with_config |
|---|---|---|---|---|---|---|---|---|
| `intent_chain` | `prompt | model | parser` | `RunnableSequence` | `user_request` | `AIMessage` | `IntentSchema` | 否 / 可选 | 是 | 是 |
| `planner_chain` | `prompt | model.with_structured_output(...)` | `RunnableSequence` | `TravelState` | `AIMessage` | `Plan` | 否 / 可选 | 是 | 是 |
| `final_chain` | `prompt | model | StrOutputParser()` | `RunnableSequence` | `full_state` | `AIMessage` | `str` | 是 | 是 | 是 |
| `research_chain` | `dict | prompt | model` | `RunnableParallel + RunnableSequence` | `destination` | `dict` | `AIMessage` | 部分支持 | 是 | 是 |

### 16.4 推荐项目目录补充

```text
docs/framework_source_notes/
  01_runnable_source_deep_dive.md
  runnable_chain_inventory.md

src/travel_agent/
  chains/
    intent_chain.py
    planner_chain.py
    research_chain.py
    final_chain.py
```

`runnable_chain_inventory.md` 专门记录项目中所有 Runnable 链路。

---

## 17. 常见误区

### 17.1 误区一：把 `|` 当成普通管道

错误理解：

```text
`|` 就是把函数一个接一个调用。
```

正确理解：

```text
`|` 是 Runnable 的组合运算符，会构造 RunnableSequence；
组合发生在构建阶段，执行发生在 invoke / stream / batch 阶段。
```

### 17.2 误区二：以为所有 stream 都是 token 级流式

错误理解：

```text
只要 chain.stream 就一定逐 token 输出。
```

正确理解：

```text
只有链路中组件支持 transform / 原生流式时，才能保持真正流式；
中间阻塞组件会延迟流式输出。
```

### 17.3 误区三：把 RunnableLambda 用成万能节点

错误理解：

```text
任何逻辑都用 RunnableLambda 包一下。
```

正确理解：

```text
RunnableLambda 适合轻量同步/异步函数；
复杂状态、重试、副作用、流式逻辑不建议全塞进去。
```

### 17.4 误区四：忽略 RunnableConfig

错误理解：

```text
config 只是可选参数，不重要。
```

正确理解：

```text
config 是生产级观测、追踪、并发控制、动态配置的入口。
```

### 17.5 误区五：把 RunnableParallel 当 Multi-Agent

错误理解：

```text
并行几个 chain 就是 Multi-Agent。
```

正确理解：

```text
RunnableParallel 是并行执行原语；
Multi-Agent 还需要角色边界、共享状态、协作协议、失败处理和评估。
```

---

## 18. 本篇源码心智模型

你最终应该形成这张图：

```text
Runnable
  是所有 LangChain 组件的统一执行协议
  ↓
Prompt / Model / Parser / Retriever / Tool / Function
  都可以被看作 Runnable
  ↓
Runnable.__or__
  把多个 Runnable 组合成 RunnableSequence
  ↓
RunnableSequence.invoke
  按 step 顺序执行，前一步输出作为后一步输入
  ↓
RunnableConfig
  把 callbacks / tags / metadata / concurrency 传给每个 step
  ↓
CallbackManager
  记录父子运行轨迹
  ↓
stream / batch / retry / config
  成为所有 Runnable 的通用能力
```

一句话总结：

> Runnable 是 LangChain Core 的“统一执行协议”；LCEL 的 `|` 不是语法糖那么简单，而是把 Prompt、Model、Parser、Retriever、Tool、普通函数统一注册成可执行、可追踪、可组合、可批处理、可流式的运行单元。

---

## 19. 下一篇衔接

下一篇建议进入：

```text
第 2 篇：Prompt / Message / ChatModel 源码解剖
```

核心问题：

```text
为什么 ChatPromptTemplate.invoke 返回的不是字符串？
PromptValue、BaseMessage、HumanMessage、SystemMessage、AIMessage 的关系是什么？
为什么 AIMessage 可以携带 tool_calls？
ChatModel.invoke 内部如何标准化输入并返回 AIMessage？
```

这会为后续 Tool Calling 和 ReAct Agent 源码解剖打基础。

---

## 20. 参考资料

1. LangChain Core Runnables Reference  
   `https://reference.langchain.com/python/langchain-core/runnables/`

2. Runnable API Reference  
   `https://reference.langchain.com/python/langchain-core/runnables/base/Runnable/`

3. RunnableSequence API Reference  
   `https://reference.langchain.com/python/langchain-core/runnables/base/RunnableSequence/`

4. RunnableParallel API Reference  
   `https://reference.langchain.com/python/langchain-core/runnables/base/RunnableParallel/`

5. RunnableConfig API Reference  
   `https://reference.langchain.com/python/langchain-core/runnables/config/RunnableConfig/`

6. LangChain GitHub Source: `base.py`  
   `https://github.com/langchain-ai/langchain/blob/master/libs/core/langchain_core/runnables/base.py`

7. LangChain GitHub Source: `config.py`  
   `https://github.com/langchain-ai/langchain/blob/master/libs/core/langchain_core/runnables/config.py`

8. LangChain Models Documentation  
   `https://docs.langchain.com/oss/python/langchain/models`

9. LangChain v1 Release Notes  
   `https://docs.langchain.com/oss/python/releases/langchain-v1`

