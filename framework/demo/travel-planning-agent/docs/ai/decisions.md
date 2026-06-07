# 架构决策记录

## ADR-001：使用 PydanticOutputParser 而非 with_structured_output

### 背景
LangChain 提供两种结构化输出方式：
1. `model.with_structured_output(Schema)` — 依赖 API 的 response_format json_schema 或 tool_choice
2. `PydanticOutputParser` — 在 prompt 中注入 JSON 格式说明，用普通 text completion

### 决策
使用 PydanticOutputParser。

### 原因
DeepSeek V4 Flash 的 thinking 模式不支持 tool_choice，也不支持 json_schema 格式的 response_format。PydanticOutputParser 只依赖 text completion，兼容所有 OpenAI 兼容 API。

### 影响
- 需要手动管理 `{format_instructions}` 占位符
- Prompt 会变长（包含 JSON schema 说明），但对模型理解和生成质量无负面影响

### 状态
已采纳，不可回退。

---

## ADR-002：parse_request 用 Python 关键词提取代替 LLM

### 背景
原始设计中 parse_request_node 调用 LLM 解析用户输入为 TravelRequest，耗时 ~16s。

### 决策
用 Python 正则表达式提取目的地、天数、预算、偏好等字段。

### 原因
- 中文旅行描述结构固定（"去X玩Y天预算Z"），正则准确率足够
- 省去一次 LLM 调用（~16s），大幅降低延迟
- 多轮对话时用户补充信息也可被正则提取

### 影响
- 对非标准输入可能提取失败，触发追问（可接受的用户体验）
- parse_request_node 不再依赖 LLM

### 状态
已采纳。

---

## ADR-003：model 延迟初始化 + LRU 缓存

### 背景
模型在 chain 模块 import 时创建，httpx client 与 uvicorn 事件循环冲突，导致 API 请求永久挂起。

### 决策
- Chain 用 RunnableLambda 包装，每次 invoke 时才构建
- init_chat_model() 用 @lru_cache(maxsize=1) 缓存，只创建一次

### 原因
- 模块 import 时 uvicorn 事件循环尚未就绪，httpx client 创建在错误的上下文
- 延迟到首次 invoke 时才创建（在正确的线程上下文中）
- LRU 缓存避免每次 invoke 都重建 model

### 影响
- 首次 API 调用时会多花几百 ms 初始化 model，后续调用复用缓存
- 修复了 uvicorn 服务启动后首个请求挂死的严重 bug

### 状态
已采纳，不可回退到 import 时创建 model。

---

## ADR-004：默认快速模式（跳过 Reflection）

### 背景
完整工作流包含 Reflection 循环（plan → reflect → [revise → reflect] → output），需要 2-3 次 LLM 调用。

### 决策
- 默认 max_revision_count=0，跳过 reflection，generate_plan 直接到 final_output
- 用户可手动设置 max_revision_count=2 开启完整模式

### 原因
- Reflection 增加 1-2 次 LLM 调用，每次 10-35s
- 快速模式下只需 1 次 LLM 调用，平均 24s
- 对大多数简单旅行规划，初次生成的计划质量已足够

### 影响
- workflow.py 增加 route_after_generate 条件分支
- 前端/API 默认值改为 0
- 用户可在需要时主动开启深度审查

### 状态
已采纳。

---

## ADR-005：State 只存 dict，不存 Pydantic 对象

### 背景
LangGraph State 在 checkpoint 时需要 JSON 序列化。Pydantic 对象无法直接序列化。

### 决策
所有 Pydantic 对象通过 model_dump() 转为 dict 后写入 State，读取时用 dict[key] 访问。

### 原因
- 保持序列化一致性
- 避免对象/dict 混用导致类型混乱
- LangGraph checkpoint 机制依赖 JSON 序列化

### 状态
已采纳。
