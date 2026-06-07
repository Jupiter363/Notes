# LangChain + LangGraph 旅行规划助手 —— 框架初学者详解

> 适用读者：有 Python 基础，了解"大模型能干嘛"但对 LangChain/LangGraph 框架不熟悉的开发者。
> 目标：通过一个完整项目，逐层理解 LangChain 和 LangGraph 各自负责什么、分别怎么用、两者如何配合。

---

## 目录

1. [先解决核心困惑：LangChain 和 LangGraph 分别负责什么？](#1-先解决核心困惑langchain-和-langgraph-分别负责什么)
2. [项目总览：旅行规划助手做了什么](#2-项目总览旅行规划助手做了什么)
3. [第一层：数据模型 —— Pydantic Schema](#3-第一层数据模型--pydantic-schema)
4. [第二层：能做什么和做到哪了 —— State](#4-第二层能做什么和做到哪了--state)
5. [第三层：大脑怎么说话 —— Prompt](#5-第三层大脑怎么说话--prompt)
6. [第四层：一次 LLM 调用怎么封装 —— Chain](#6-第四层一次-llm-调用怎么封装--chain)
7. [第五层：LLM 的手和眼 —— Tool](#7-第五层llm-的手和眼--tool)
8. [第六层：每一步做什么 —— Node](#8-第六层每一步做什么--node)
9. [第七层：路口怎么走 —— Router](#9-第七层路口怎么走--router)
10. [第八层：串起珍珠的线 —— Workflow](#10-第八层串起珍珠的线--workflow)
11. [第九层：对外接口 —— Service 和 CLI](#11-第九层对外接口--service-和-cli)
12. [完整数据流追踪](#12-完整数据流追踪)
13. [运行和测试](#13-运行和测试)
14. [关键设计模式总结](#14-关键设计模式总结)

---

## 1. 先解决核心困惑：LangChain 和 LangGraph 分别负责什么？

**一句话：LangChain 负责"单个节点里做什么"，LangGraph 负责"节点之间怎么走"。**

比喻理解：

```
LangChain = 工厂里的每台机器（每台机器只负责一道工序）
LangGraph = 流水线传送带（决定工作从哪台机器流到哪台机器）
```

| 问题 | 答案 |
|------|------|
| 调用 LLM 用谁？ | LangChain |
| 管理 Prompt 模板用谁？ | LangChain |
| 让 LLM 输出结构化 JSON 用谁？ | LangChain |
| 封装工具用谁？ | LangChain |
| 决定先解析需求还是先生成计划？ | LangGraph |
| 信息不足时要不要追问？ | LangGraph |
| 反思后要不要修正计划？ | LangGraph |
| 循环修正几次后必须停止？ | LangGraph |

**为什么不能只用 LangChain？**

如果你只用 LangChain，你可以写出：

```python
result = chain.invoke({"user_input": "我想去成都玩"})
```

这是一次性调用。输入进去，结果出来。但旅行规划不是一次调用能搞定的：

- 用户可能没说清楚目的地——你要追问，不是瞎猜
- 你需要先查天气、查景点——这些是额外步骤
- 你生成了计划，需要回头检查一遍——可能还要修改
- 修改完可能还要再检查——这是一个循环

**这些"步骤之间的流转、分支、循环"，就是 LangGraph 的活。**

---

## 2. 项目总览：旅行规划助手做了什么

```
你输入: "我想6月底去成都玩3天，预算3000，喜欢美食和轻松路线"
       │
       ▼
  ┌─────────────────────────────────────────────┐
  │           LangGraph 工作流                   │
  │                                             │
  │  ① 解析需求 ──→ ② 检查信息完整性            │
  │       │              │                      │
  │       │         ┌────┴────┐                 │
  │       │      不完整      完整                 │
  │       │         │         │                  │
  │       │      ③ 追问    ④ 选择工具            │
  │       │      (结束)       │                  │
  │       │                ⑤ 调用工具            │
  │       │                   │                  │
  │       │                ⑥ 生成计划            │
  │       │                   │                  │
  │       │                ⑦ 反思检查  ←────────┐ │
  │       │                   │                │ │
  │       │              ┌────┴────┐           │ │
  │       │           需修正     不需修正       │ │
  │       │              │         │           │ │
  │       │           ⑧ 修正 ─────┘           │ │
  │       │            (回到⑦)                 │ │
  │       │                                   │ │
  │       │                ⑨ 渲染输出          │ │
  └─────────────────────────────────────────────┘
       │
       ▼
  输出: 一份完整的 Markdown 旅行方案
```

**9 个节点（Node）+ 2 个路口（Router）+ 1 个循环 = 完整的 Agent 工作流**

---

## 3. 第一层：数据模型 —— Pydantic Schema

**文件位置：** `app/schemas/`

### 3.1 为什么需要 Schema？

LLM 返回的是自然语言文本，但代码需要结构化数据来判断"信息够不够"、"预算超没超"、"要不要修正"。Schema 就是 LLM 和代码之间的**格式契约**。

### 3.2 TravelRequest —— 用户想要什么

```python
# app/schemas/travel_request.py
from pydantic import BaseModel, Field
from typing import List, Optional

class TravelRequest(BaseModel):
    destination: Optional[str] = Field(default=None, description="目的地城市或地区")
    start_date: Optional[str] = Field(default=None, description="出发日期，例如 6 月底")
    days: Optional[int] = Field(default=None, ge=1, le=30, description="旅行天数")
    budget: Optional[float] = Field(default=None, ge=0, description="总预算，单位元")
    preferences: List[str] = Field(default_factory=list, description="旅行偏好")
    companions: Optional[str] = Field(default=None, description="同行人")
    departure_city: Optional[str] = Field(default=None, description="出发城市")
    pace: Optional[str] = Field(default=None, description="旅行节奏")
```

**关键理解：** 所有字段都是 `Optional`。因为用户可能一次没说全——比如只说"我想出去玩"，这时候 destination/days/budget 都是 None。后续框架会检测缺失并追问。

`Field(ge=1, le=30)` 是 Pydantic 的**校验**：如果有人输入 days=0 或 days=100，直接报错，不需要等到后面才发现。

### 3.3 TravelPlan —— 生成出来的计划长什么样

```python
# app/schemas/travel_plan.py
class Activity(BaseModel):
    time_slot: str              # morning / afternoon / evening
    title: str                  # 活动名称
    location: Optional[str] = None
    reason: str                 # 为什么这样安排（AI 的思考）
    estimated_cost: float = 0
    duration_hours: Optional[float] = None
    transport_note: Optional[str] = None   # 怎么去
    risk_note: Optional[str] = None        # 有什么风险

class DayPlan(BaseModel):
    day: int                    # 第几天
    theme: str                  # 当日主题
    activities: List[Activity]  # 当天的活动列表
    daily_estimated_cost: float # 当天预计花费
    pace_level: str             # relaxed / normal / tight
    notes: List[str] = []

class TravelPlan(BaseModel):
    destination: str
    total_days: int
    total_budget: float
    days: List[DayPlan]                     # 每天的安排
    total_estimated_cost: float             # 总预计花费
    budget_status: str                      # 预算是否超支
    preference_match_notes: List[str] = []  # 偏好匹配说明
    risk_notes: List[str] = []              # 风险提醒
    data_limitations: List[str] = []        # 数据局限性说明
```

**嵌套结构：** TravelPlan → DayPlan → Activity。这和真实的旅行计划一模一样——一个计划包含多天，每天包含多个活动。LLM 输出这个结构后，代码可以逐层检查：总预算超没超？某天是不是太赶了？某个活动的花费合理吗？

### 3.4 ReflectionResult —— 自我检查的结果

```python
# app/schemas/reflection.py
class ReflectionResult(BaseModel):
    need_revision: bool           # 要不要继续修正
    score: int = Field(ge=1, le=10)  # 质量评分 1-10
    issues: List[str] = []           # 一般问题
    suggestions: List[str] = []      # 修正建议
    blocking_issues: List[str] = []  # 阻断性问题（严重到必须修）
    accepted_as_final: bool = False  # 是否可以直接采纳
```

**为什么需要 blocking_issues 和 issues 分开？** 比如"某个餐厅价格略有偏差"是一般问题，"三个雨天全部安排了户外活动"是阻断性问题。LLM 修正时优先解决 blocking_issues。

### 3.5 ToolResult —— 所有工具的通用输出格式

```python
# app/schemas/tool_result.py
class ToolResult(BaseModel):
    data: dict | list
    source: str              # 数据来源（mock_weather / real_api）
    updated_at: Optional[str] = None
    confidence: str          # mock / high / medium / low
    error: Optional[str] = None
```

**这是工具适配器模式的核心。** 不管后面接的是 mock 数据还是真实的天气 API，返回的结构都一样。对上游代码来说，它不关心数据从哪来——它只认这个格式。

---

## 4. 第二层：能做什么和做到哪了 —— State

**文件位置：** `app/graph/state.py`

### 4.1 State 是什么？

State 是流经所有节点的**共享上下文**。每个节点从 State 读取数据，处理完后再往 State 里写入新数据。

把它想象成一个**文件夹在流水线上传**：工序 A 往文件夹里放入"解析结果"，工序 B 翻开文件夹看到已有解析结果，检查后放入"完整性检查结果"，工序 C 继续往里加东西……

### 4.2 我们的 State 设计

```python
# app/graph/state.py
from typing_extensions import TypedDict
from typing import Any, Dict, List

class TravelState(TypedDict, total=False):
    # ── 用户输入区 ──
    user_input: str                 # 当前用户输入
    user_inputs: List[str]          # 历史输入（多轮对话）

    # ── 需求区 ──
    request: Dict[str, Any]         # TravelRequest.model_dump() 的 dict

    # ── 信息检查区 ──
    missing_fields: List[str]       # 缺失的必要字段
    clarification_questions: List[str]  # 追问的问题
    is_info_complete: bool          # 信息是否完整

    # ── 工具区 ──
    required_tools: List[str]       # 需要调用哪些工具
    context: Dict[str, Any]         # 工具返回的数据合集

    # ── 计划区 ──
    draft_plan: Dict[str, Any]      # TravelPlan.model_dump() 的 dict

    # ── 反思区 ──
    reflection: Dict[str, Any]      # ReflectionResult.model_dump() 的 dict

    # ── 输出区 ──
    final_plan: str                 # 最终 Markdown 文本

    # ── 流程控制区 ──
    need_revision: bool             # 是否需要修正
    revision_count: int             # 当前修正次数
    max_revision_count: int         # 最大修正次数
    stop_reason: str                # 停止原因

    # ── 错误与追踪区 ──
    tool_errors: List[Dict[str, Any]]
    system_errors: List[Dict[str, Any]]
    trace: List[Dict[str, Any]]     # 轻量执行轨迹，方便调试
```

### 4.3 关键约定：State 里只存 dict，不存 Pydantic 对象

```python
# ✓ 正确做法
result: TravelRequest = parse_chain.invoke({"user_input": user_input})
return {"request": result.model_dump()}  # 转成 dict 存入 State

# 后续节点取值
state["request"]["destination"]  # dict 取值
```

为什么这样做？因为 LangGraph 底层用 JSON 序列化 State 来做 checkpoint（断点续跑），dict 可以直接序列化，Pydantic 对象需要转换。统一存 dict 避免混淆。

---

## 5. 第三层：大脑怎么说话 —— Prompt

**文件位置：** `app/prompts/`

### 5.1 Prompt 模板的设计思路

每个 Prompt 都是一个 `ChatPromptTemplate`，包含 `system` 消息（角色和规则）和 `human` 消息（具体输入）。

以解析 Prompt 为例：

```python
# app/prompts/parse_prompt.py
from langchain_core.prompts import ChatPromptTemplate

parse_prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一个旅行需求解析器。请从用户输入中抽取结构化旅行需求。
如果某个字段没有明确出现，请返回 null 或空列表，不要编造。

{format_instructions}"""),
    ("human", "用户输入：{user_input}")
])
```

**关键注意点：**

1. **`{format_instructions}`** 占位符：PydanticOutputParser 会自动注入 JSON 格式说明，告诉 LLM "你必须输出这个格式的 JSON"。调用时用 `prompt.partial(format_instructions=parser.get_format_instructions())` 填充。

2. **`不要编造`** 是约束 LLM 的关键指令。没有这句话，LLM 可能会把"我想出去玩"脑补成"想去三亚玩 5 天"——看起来很聪明，实际上是在替用户做决定。

### 5.2 四套 Prompt 的职责

| Prompt | 系统角色 | 输入 | 输出要求 |
|--------|---------|------|---------|
| parse_prompt | 需求解析器 | 用户自然语言 | TravelRequest JSON |
| plan_prompt | 旅行规划师 | 需求 + 工具上下文 | TravelPlan JSON |
| reflection_prompt | 计划审查员 | 需求 + 工具上下文 + 当前计划 | ReflectionResult JSON |
| revise_prompt | 计划修正器 | 需求 + 工具上下文 + 原计划 + 反思结果 | 修正后的 TravelPlan JSON |

---

## 6. 第四层：一次 LLM 调用怎么封装 —— Chain

**文件位置：** `app/chains/`

### 6.1 什么是 Chain？

Chain 是 LangChain 的核心概念：**把多个步骤串成一个可调用的管道**。

### 6.2 我们的 Chain 结构

```python
# app/chains/parse_chain.py
from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import PydanticOutputParser
from app.schemas.travel_request import TravelRequest
from app.prompts.parse_prompt import parse_prompt
from app.config.settings import settings

# 第1步：创建模型连接
model = init_chat_model(
    settings.MODEL_NAME,              # "deepseek-v4-flash" 或 "gpt-4o-mini"
    model_provider="openai",          # 使用 OpenAI 兼容协议
    openai_api_key=settings.OPENAI_API_KEY,
    openai_api_base=settings.OPENAI_BASE_URL,
    temperature=settings.TEMPERATURE, # 0 = 不要创造性，严格按指令输出
)

# 第2步：创建解析器（告诉模型输出什么格式的 JSON）
parser = PydanticOutputParser(pydantic_object=TravelRequest)

# 第3步：把格式说明注入 Prompt
prompt_with_format = parse_prompt.partial(
    format_instructions=parser.get_format_instructions()
)

# 第4步：串联成管道 ── Prompt → 模型 → JSON解析
parse_chain = prompt_with_format | model | parser
```

### 6.3 管道运算符 `|` 的含义

```python
parse_chain = prompt_with_format | model | parser
```

等价于：

```python
# 输入 → 填入 Prompt 模板 → 发给 LLM → 拿到文本 → 解析成 Pydantic 对象
def parse_chain(user_input):
    prompt_text = prompt_with_format.format(user_input=user_input)
    llm_response = model.invoke(prompt_text)
    travel_request = parser.parse(llm_response.content)
    return travel_request
```

`|` (pipe) 是 LangChain 的 LCEL（LangChain Expression Language），让你像搭积木一样组合组件。

### 6.4 为什么用 PydanticOutputParser 而不是 with_structured_output？

最初我们用了 `model.with_structured_output(TravelRequest)`，这在 OpenAI 上工作完美，但 DeepSeek V4 Flash 不支持。`PydanticOutputParser` 是更底层的方案：

```
with_structured_output:  LLM API 层面直接返回 JSON Schema 约束的输出（需要 API 支持）
PydanticOutputParser:    告诉 LLM "请输出 JSON"，然后代码解析（所有 API 都支持）
```

后者不需要 API 支持 `response_format` 或 `tool_choice`，兼容性更好。

---

## 7. 第五层：LLM 的手和眼 —— Tool

**文件位置：** `app/tools/`

### 7.1 什么是 Tool？

Tool 让 LLM 能够获取它不知道的信息。LLM 的知识有截止日期，也不知道实时天气、最新票价。Tool 就是给 LLM 装上的"手"（可以做事）和"眼"（可以看东西）。

### 7.2 一个具体的 Tool

```python
# app/tools/weather_tool.py
from langchain_core.tools import tool

@tool
def get_weather(city: str, date_range: str = "") -> dict:
    """查询城市的天气信息与出行风险。"""
    return {
        "data": {
            "city": city,
            "forecast": [
                {"date": "2026-06-25", "weather": "晴转多云", "temp_high": 29, "temp_low": 21},
                {"date": "2026-06-26", "weather": "多云", "temp_high": 30, "temp_low": 22},
                {"date": "2026-06-27", "weather": "阵雨", "temp_high": 28, "temp_low": 20},
            ],
        },
        "source": "mock_weather",
        "confidence": "mock",
        "error": None,
    }
```

`@tool` 装饰器把普通 Python 函数变成 LangChain Tool。LangChain 自动从函数签名和 docstring 生成 Tool 的 schema（输入参数、描述等）。

### 7.3 工具适配器模式

注意 `confidence: "mock"` 字段。当后续换成真实天气 API 时，这个字段变成 `"high"`。上游代码可以通过这个字段判断："这数据可信吗？要不要提醒用户自行确认？"

```python
# app/tools/base.py —— 安全调用机制

def safe_tool_call(tool, args: dict, fallback_source: str):
    try:
        if hasattr(tool, "invoke"):
            result = tool.invoke(args)   # LangChain Tool 的调用方式
        else:
            result = tool(args)           # 普通函数的调用方式
        return result, None
    except Exception as e:
        # 工具挂了不崩溃，返回兜底数据
        return fallback_tool_result(fallback_source, str(e)), error_info
```

**这是工程化 Agent 的一个关键设计：工具失败不应该让整个流程崩溃。** 天气 API 挂了？用兜底数据继续，然后在最终输出中提醒用户"天气数据获取失败，建议自行查询"。

### 7.4 六个 Mock 工具

| 工具 | 做什么 | 返回什么 |
|------|--------|---------|
| get_weather | 查询城市天气 | 3天预报 + 出行风险提示 |
| search_attractions | 搜索景点 | 景点列表（名称/评分/花费/时长/备注） |
| search_foods | 搜索美食 | 美食列表（名称/类别/人均/备注） |
| estimate_budget | 预算估算 | 每日花费明细 + 预算状态 |
| search_transport | 交通建议 | 地铁/公交/出租车/共享单车信息 |
| web_search | 搜索最新信息 | mock 搜索结果（提示用户自行确认） |

---

## 8. 第六层：每一步做什么 —— Node

**文件位置：** `app/graph/nodes.py`

### 8.1 什么是 Node？

Node 是 LangGraph 工作流中的**一个执行步骤**。每个 Node 是一个函数，签名为：

```python
def some_node(state: TravelState) -> dict:
    # 从 state 读取需要的字段
    # 做处理（调用 LLM、检查数据……）
    # 返回一个 dict，LangGraph 会自动合并回 state
    return {"some_field": new_value}
```

**关键：Node 不直接修改 state，它返回一个 dict，LangGraph 负责将这个 dict 的键值更新到 state 中。**

### 8.2 Node 1：parse_request_node —— 解析用户输入

```python
def parse_request_node(state: TravelState) -> dict:
    user_input = state["user_input"]

    # 调用 LangChain chain：Prompt → LLM → JSON Parser → TravelRequest 对象
    result: TravelRequest = parse_chain.invoke({"user_input": user_input})

    # 多轮对话时，合并新旧需求（新输入覆盖旧的非空字段）
    prev_request = state.get("request", {})
    new_request = result.model_dump()
    merged_request = {**prev_request}
    for key, value in new_request.items():
        if value not in [None, "", []]:
            merged_request[key] = value

    return {
        "request": merged_request,
        "trace": state.get("trace", []) + [{"node": "parse_request", "status": "ok"}],
    }
```

**trace 字段的作用：** 每次节点执行完都追加一条 trace 记录。出问题时你一看 trace 就知道"卡在哪个节点了"。

### 8.3 Node 2：check_info_node —— 检查信息完整性

```python
def check_info_node(state: TravelState) -> dict:
    request = state.get("request", {})
    missing = []

    for field in ["destination", "days", "budget", "preferences"]:
        value = request.get(field)
        if value in [None, "", []]:
            missing.append(field)

    return {
        "missing_fields": missing,
        "is_info_complete": len(missing) == 0,
    }
```

纯 Python 逻辑，不调 LLM。这是**一个好的 Agent 设计原则：能用代码判断的就不要浪费 LLM 调用**。

### 8.4 Node 3：ask_clarification_node —— 生成追问

```python
def ask_clarification_node(state: TravelState) -> dict:
    field_to_question = {
        "destination": "你想去哪个城市或地区旅行？",
        "days": "你计划玩几天？",
        "budget": "你的总预算大概是多少？",
        "preferences": "你更偏好美食、自然风光、历史文化、购物，还是轻松休闲路线？",
    }
    questions = [
        field_to_question[field]
        for field in state.get("missing_fields", [])
    ]
    return {
        "clarification_questions": questions,
        "stop_reason": "need_user_clarification",
        "final_plan": "为了更准确地规划行程，请先补充：\n" + "\n".join(f"- {q}" for q in questions),
    }
```

也是纯代码逻辑——缺失哪个字段就问对应的问题。

### 8.5 Node 4：decide_tools_node —— 动态选择工具

```python
def decide_tools_node(state: TravelState) -> dict:
    preferences = state["request"].get("preferences", [])
    required_tools = ["weather", "attractions", "budget", "transport"]  # 基础四件套

    if "美食" in preferences:
        required_tools.append("foods")     # 用户喜欢美食才查餐厅
    if state["request"].get("start_date"):
        required_tools.append("web_search") # 有具体日期才搜索最新信息

    return {"required_tools": required_tools}
```

**不是一股脑调所有工具**。用户没说要美食，就不查餐厅；没说具体日期，就不做实时搜索。省 API 调用，也避免无关信息干扰 LLM。

### 8.6 Node 5：collect_context_node —— 安全调用工具

```python
def collect_context_node(state: TravelState) -> dict:
    # 从 state 取出需要的参数
    city = state["request"]["destination"]
    required_tools = state.get("required_tools", [])

    context = {}
    errors = []

    if "weather" in required_tools:
        result, err = safe_tool_call(get_weather, {"city": city, "date_range": date_range}, "fallback_weather")
        context["weather"] = result
        if err:
            errors.append(err)  # 工具失败也不中断，记录错误继续

    # ... 对其他工具同样处理 ...

    return {"context": context, "tool_errors": errors}
```

**设计要点：每个工具独立调用，独立错误处理。** 天气 API 挂了不影响景点查询继续执行。

### 8.7 Node 6：generate_plan_node —— 生成初版计划

```python
def generate_plan_node(state: TravelState) -> dict:
    result: TravelPlan = plan_chain.invoke({
        "request": state["request"],
        "context": state.get("context", {}),   # 工具上下文
    })
    return {"draft_plan": result.model_dump()}
```

把用户需求和工具查到的信息一起喂给 LLM，让它生成结构化计划。

### 8.8 Node 7：reflect_plan_node —— 审查计划

```python
def reflect_plan_node(state: TravelState) -> dict:
    result: ReflectionResult = reflection_chain.invoke({
        "request": state["request"],
        "context": state.get("context", {}),
        "draft_plan": state["draft_plan"],
        "revision_count": state.get("revision_count", 0),
        "max_revision_count": state.get("max_revision_count", 2),
    })
    return {
        "reflection": result.model_dump(),
        "need_revision": result.need_revision,
    }
```

**LLM 自己检查自己的输出。** 这在 Agent 领域叫 Reflection 或 Self-Critique——让同一个（或另一个）模型审查计划质量。

### 8.9 Node 8：revise_plan_node —— 修正计划

```python
def revise_plan_node(state: TravelState) -> dict:
    result: TravelPlan = revise_chain.invoke({
        "request": state["request"],
        "context": state.get("context", {}),
        "draft_plan": state["draft_plan"],
        "reflection": state["reflection"],  # 上一轮的反思结果
    })
    revision_count = state.get("revision_count", 0) + 1
    return {
        "draft_plan": result.model_dump(),
        "revision_count": revision_count,
    }
```

把反思结果（问题 + 建议）告诉 LLM，让它有针对性地修正。修正后 `revision_count` + 1。

### 8.10 Node 9：final_output_node —— 渲染 Markdown

最后一个节点，纯 Python 代码。把结构化 `TravelPlan` 转成漂亮的 Markdown 文本。包括：
- 行程概览
- 每天的详细安排（活动、地点、花费、理由、交通、风险）
- 偏好匹配说明
- 风险提醒
- 方案自检结果
- 数据局限性说明

---

## 9. 第七层：路口怎么走 —— Router

**文件位置：** `app/graph/routers.py`

Router 是 LangGraph 的**条件分支**——根据 State 的当前状态决定下一步走到哪个 Node。

### 9.1 信息完整性路由

```python
def route_after_check(state: TravelState) -> Literal["ask_clarification", "decide_tools"]:
    if state.get("is_info_complete"):
        return "decide_tools"     # 信息全了，继续走工具选择
    return "ask_clarification"    # 信息不全，去追问
```

### 9.2 Reflection 循环路由

```python
def route_after_reflection(state: TravelState) -> Literal["revise_plan", "final_output"]:
    reflection = state.get("reflection", {})
    need_revision = reflection.get("need_revision", False)
    accepted_as_final = reflection.get("accepted_as_final", False)
    revision_count = state.get("revision_count", 0)
    max_revision_count = state.get("max_revision_count", 2)

    if accepted_as_final:
        return "final_output"      # LLM 判定质量够好，直接输出

    if need_revision and revision_count < max_revision_count:
        return "revise_plan"       # 需要修改且还有修改次数 → 去修正

    return "final_output"          # 不需要修改或次数用完 → 输出
```

**三个退出条件：**
1. `accepted_as_final = True` —— Reflection 认为计划可以接受
2. `need_revision = False` —— 不需要修正
3. `revision_count >= max_revision_count` —— 次数用完了，即使还有问题也强制输出（避免无限循环烧钱）

---

## 10. 第八层：串起珍珠的线 —— Workflow

**文件位置：** `app/graph/workflow.py`

### 10.1 build_graph() 逐行解读

```python
from langgraph.graph import StateGraph, START, END

def build_graph(checkpointer=None):
    # 第1步：创建状态图，指定 State 类型
    builder = StateGraph(TravelState)

    # 第2步：注册所有节点（只是注册，还没连接）
    builder.add_node("parse_request", parse_request_node)
    builder.add_node("check_info", check_info_node)
    builder.add_node("ask_clarification", ask_clarification_node)
    builder.add_node("decide_tools", decide_tools_node)
    builder.add_node("collect_context", collect_context_node)
    builder.add_node("generate_plan", generate_plan_node)
    builder.add_node("reflect_plan", reflect_plan_node)
    builder.add_node("revise_plan", revise_plan_node)
    builder.add_node("final_output", final_output_node)

    # 第3步：连接节点 —— 固定路线
    builder.add_edge(START, "parse_request")   # START → 解析需求
    builder.add_edge("parse_request", "check_info")  # 解析需求 → 检查信息

    # 第4步：第一个条件分支 —— 信息全不全？
    builder.add_conditional_edges(
        "check_info",
        route_after_check,      # 用这个函数判断
        {
            "ask_clarification": "ask_clarification",  # 返回这个 → 去追问
            "decide_tools": "decide_tools",            # 返回这个 → 去选工具
        },
    )

    builder.add_edge("ask_clarification", END)  # 追问后结束（等用户补充）

    # 第5步：固定流程 —— 选工具 → 调工具 → 生成计划
    builder.add_edge("decide_tools", "collect_context")
    builder.add_edge("collect_context", "generate_plan")
    builder.add_edge("generate_plan", "reflect_plan")

    # 第6步：第二个条件分支 —— 要不要修正？
    builder.add_conditional_edges(
        "reflect_plan",
        route_after_reflection,
        {
            "revise_plan": "revise_plan",    # 要修正 → 去修正
            "final_output": "final_output",   # 不修正 → 去输出
        },
    )

    # 第7步：循环！修正完回到反思，形成 generate → reflect → revise → reflect 循环
    builder.add_edge("revise_plan", "reflect_plan")

    builder.add_edge("final_output", END)

    # 第8步：编译成可执行的图
    return builder.compile(checkpointer=checkpointer)
```

### 10.2 图的可视化理解

```
                    ┌──────────────┐
                    │    START     │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │ parse_request│
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  check_info  │
                    └──────┬───────┘
                           │
              ┌────────────┴────────────┐
              │      条件：信息完整？     │
              └────────────┬────────────┘
                    不完整  │  完整
              ┌────────────▼──┐  ┌──────▼───────┐
              │ask_clarification│  │ decide_tools │
              └───────┬────────┘  └──────┬───────┘
                      │                  │
                     END          ┌──────▼───────┐
                                  │collect_context│
                                  └──────┬───────┘
                                         │
                                  ┌──────▼───────┐
                                  │generate_plan │
                                  └──────┬───────┘
                                         │
                                  ┌──────▼───────┐
                                  │ reflect_plan │◄──────────────┐
                                  └──────┬───────┘               │
                                         │                       │
                            ┌────────────┴────────────┐          │
                            │   条件：需要修正且       │          │
                            │   未超最大次数？         │          │
                            └────────────┬────────────┘          │
                                  是      │      否              │
                            ┌─────────────▼──┐  ┌──▼──────────┐  │
                            │  revise_plan   │  │final_output │  │
                            └────────┬───────┘  └──────┬──────┘  │
                                     │                  │         │
                                     └──────────────────┘         │
                                      (修正后回到 reflect) ───────┘
                                                         │
                                                        END
```

---

## 11. 第九层：对外接口 —— Service 和 CLI

**文件位置：** `app/services/` 和 `app/main.py`

### 11.1 PlannerService —— 对外的业务接口

```python
class PlannerService:
    def __init__(self):
        self.graph = build_graph()  # 初始化一次，复用

    def plan(self, user_input, session_id=None, max_revision_count=2):
        state = {"user_input": user_input, "max_revision_count": max_revision_count}
        result = self.graph.invoke(state)  # 运行整个工作流
        return self._format_response(result, session_id)

    def continue_plan(self, session_id, user_input):
        """
        用户补充信息后继续：
        1. 从 session 取出上一轮的 state
        2. 清理掉追问相关的临时字段
        3. 用新输入重新 invoke
        """
        prev_state = session_service.get_state(session_id)
        state = self._prepare_followup_state(prev_state, user_input)
        result = self.graph.invoke(state)
        return self._format_response(result, session_id)

    def _prepare_followup_state(self, prev_state, new_user_input):
        """关键：清理本轮临时字段，保留跨轮持久字段"""
        state = prev_state.copy()
        state["user_input"] = new_user_input
        # 清理上一轮产生的临时字段
        for key in ["clarification_questions", "final_plan", "missing_fields",
                     "is_info_complete", "required_tools", "context",
                     "draft_plan", "reflection", "need_revision", "stop_reason"]:
            state.pop(key, None)
        return state
```

### 11.2 CLI —— 命令行交互

```python
# python -m app.main "我想去成都玩3天，预算3000..."
# 或直接 python -m app.main 进入交互模式
```

### 11.3 后续扩展方向

如果后续接 FastAPI，`PlannerService` 的 `plan()` 和 `continue_plan()` 方法可以直接作为 API 的后端逻辑：

```python
# 伪代码，示意服务化方向
@app.post("/travel-plan")
def create_plan(request: PlanRequest):
    return planner_service.plan(request.user_input, session_id=create_session())
```

---

## 12. 完整数据流追踪

以一次完整调用为例，追踪数据在 State 中的流动：

```
用户输入: "我想6月底去成都玩3天，预算3000元，喜欢美食和轻松路线"

【Step 1: parse_request_node】
  输入: state["user_input"] = "我想6月底去成都..."
  调用: parse_chain.invoke({"user_input": ...})
  输出: TravelRequest(destination="成都", days=3, budget=3000, preferences=["美食","轻松"], start_date="6月底")
  写入 state:
    - request: {"destination": "成都", "days": 3, "budget": 3000, "preferences": ["美食","轻松"], ...}
    - trace: [{"node": "parse_request", "status": "ok"}]

【Step 2: check_info_node】
  输入: state["request"]
  检查: destination ✓ | days ✓ | budget ✓ | preferences ✓
  写入 state:
    - missing_fields: []
    - is_info_complete: True

【Step 3: 条件路由 route_after_check】
  读取: state["is_info_complete"] = True
  返回: "decide_tools"

【Step 4: decide_tools_node】
  输入: state["request"]["preferences"] = ["美食", "轻松"]
  判断: "美食" in preferences → 加 foods; 无 start_date → 不加 web_search
  写入 state:
    - required_tools: ["weather", "attractions", "budget", "transport", "foods"]

【Step 5: collect_context_node】
  遍历 required_tools，依次调用 5 个工具
  写入 state:
    - context: {
        "weather": {...成都天气...},
        "attractions": {...成都景点...},
        "budget_estimate": {...预算...},
        "transport": {...交通...},
        "foods": {...成都美食...}
      }

【Step 6: generate_plan_node】
  输入: state["request"] + state["context"]
  调用: plan_chain.invoke({"request": ..., "context": ...})
  输出: TravelPlan(3天的详细安排，每个活动有理由/花费/风险)
  写入 state:
    - draft_plan: TravelPlan.model_dump()

【Step 7: reflect_plan_node】
  输入: request + context + draft_plan + revision_count=0
  调用: reflection_chain.invoke({...})
  输出: ReflectionResult(need_revision=False, score=9, accepted_as_final=True)
  写入 state:
    - reflection: {need_revision: False, score: 9, accepted_as_final: True, ...}

【Step 8: 条件路由 route_after_reflection】
  读取: reflection["accepted_as_final"] = True
  返回: "final_output"

【Step 9: final_output_node】
  输入: state["draft_plan"] + state["reflection"]
  处理: 将结构化计划渲染为 Markdown
  写入 state:
    - final_plan: "# 成都3日旅行方案\n\n## 一、行程概览\n..."
    - stop_reason: "accepted_by_reflection"

【最终返回】
{
    "final_plan": "完整的 Markdown 旅行方案",
    "revision_count": 0,
    "trace": [
        {"node": "parse_request", "status": "ok"},
        {"node": "check_info", "missing": []},
        {"node": "generate_plan", "status": "ok"},
        {"node": "reflect_plan", "need_revision": False, "score": 9}
    ]
}
```

---

## 13. 运行和测试

### 13.1 环境配置

```bash
cd travel-planning-agent

# 1. 配置 API
cp .env.example .env
# 编辑 .env，填入你的 API Key 和模型名
# 支持 OpenAI、DeepSeek、Qwen、Moonshot 等所有 OpenAI 兼容 API

# 2. 安装依赖
pip install -e ".[dev]"
```

### 13.2 运行

```bash
# 命令行直接输入
python -m app.main "我想6月底去成都玩3天，预算3000，喜欢美食和轻松路线"

# 交互模式（信息不足时可以补充）
python -m app.main
```

### 13.3 测试

```bash
# 运行所有测试
pytest tests/ -v

# 只跑不需要 API 的测试（Schema、Tool、Reflection 逻辑）
pytest tests/test_parse.py tests/test_tools.py tests/test_reflection.py -v

# 跑端到端测试（需要 API Key）
pytest tests/test_workflow.py tests/test_followup.py tests/test_tool_failure.py -v
```

### 13.4 测试覆盖了什么

| 测试文件 | 测试内容 |
|---------|---------|
| test_parse.py | Schema 校验：days/budget 范围、空 request、model_dump |
| test_tools.py | 6 个工具的输出结构、safe_tool_call 容错、fallback 机制 |
| test_reflection.py | ReflectionResult 校验、路由逻辑（修正/不修正/超次数） |
| test_workflow.py | 完整输入 → 生成计划、信息缺失 → 追问 |
| test_followup.py | 用户补充后继续 → 成功输出、state 清理逻辑 |
| test_tool_failure.py | 单个工具挂 → 继续生成、全部工具挂 → 继续生成 |

---

## 14. 关键设计模式总结

### 14.1 LangChain 负责节点内部，LangGraph 负责节点之间

```
┌──────────────────────────────────────────────┐
│                  LangGraph                    │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐      │
│  │ Node A  │──│ Node B  │──│ Node C  │ ...  │
│  │         │  │         │  │         │      │
│  │ ┌─────┐ │  │ ┌─────┐ │  │ ┌─────┐ │      │
│  │ │Chain│ │  │ │纯逻辑│ │  │ │Chain│ │      │
│  │ └─────┘ │  │ └─────┘ │  │ └─────┘ │      │
│  └─────────┘  └─────────┘  └─────────┘      │
│       ↑ LangChain 负责每个方块里的内容        │
└──────────────────────────────────────────────┘
```

### 14.2 State 分层，不要把所有字段放顶层

State 按职责分区：`request` / `context` / `draft_plan` / `reflection` / `control` / `errors` / `trace`。这样每个 Node 只需要关心自己负责的那几个区。

### 14.3 State 里只存 dict，不存对象

所有 Pydantic 对象通过 `.model_dump()` 转为 dict 再写入 State。保持序列化一致性。

### 14.4 能用代码就不要调 LLM

`check_info_node`（检查缺失字段）、`decide_tools_node`（选择工具）、`ask_clarification_node`（生成追问）、`final_output_node`（渲染 Markdown）都是纯 Python 逻辑。LLM 调用是 Agent 最大的成本和延迟来源，**只在需要理解和生成的时候才调用**。

### 14.5 工具失败不中断流程

每个工具独立调用、独立错误处理。一个工具挂了，其他工具继续，兜底数据顶上，错误记录到 `tool_errors`，最终在输出中告知用户。

### 14.6 反思循环有硬边界

`max_revision_count`（默认 2）确保 LLM 不会无限自我修正。即使最后一次反思还有问题，也强制走 `final_output`，在输出中标注"已达最大修正次数，建议人工确认"。

### 14.7 适配器模式让工具可替换

所有工具输出统一的 `ToolResult` 结构（含 `confidence` 字段）。从 mock 切到真实 API，只需要换 provider，上游代码不用改。

---

## 附录：术语速查

| 术语 | 含义 | 在本项目中对应的文件 |
|------|------|-------------------|
| Schema | 数据结构定义 | `app/schemas/` |
| State | 工作流的共享上下文 | `app/graph/state.py` |
| Prompt | 发给 LLM 的指令模板 | `app/prompts/` |
| Chain | LangChain 的可执行管道 | `app/chains/` |
| Tool | LLM 可调用的外部函数 | `app/tools/` |
| Node | LangGraph 工作流中的一个步骤 | `app/graph/nodes.py` |
| Edge | 节点之间的连接 | `app/graph/workflow.py` |
| Conditional Edge | 根据条件决定走哪条路 | `app/graph/routers.py` + workflow |
| Router | 条件判断函数 | `app/graph/routers.py` |
| StateGraph | LangGraph 的有状态图 | `build_graph()` 函数 |
| Reflection | LLM 审查自己的输出 | `reflect_plan_node` |
| Revision | 根据反思修正输出 | `revise_plan_node` |
| PydanticOutputParser | 把 LLM 文本解析为 Pydantic 对象 | 各 chain 文件 |
| Adapter | 统一不同实现的接口 | `app/tools/base.py` |
