# 旅行规划助手 — AI 协作规则

## 项目背景
基于 LangChain + LangGraph 的旅行规划 Agent。用户输入自然语言旅行需求，系统解析需求 → 检查完整性 → 调用工具查天气/景点/美食 → 生成结构化计划 → 输出 Markdown 方案。

## 技术栈
- Python >= 3.11
- LangChain >= 1.1（Prompt、Chain、Tool、Structured Output）
- LangGraph >= 1.0（StateGraph、Node、Conditional Edge、Reflection Loop）
- FastAPI + Jinja2（Web 服务 + HTML 聊天界面）
- DeepSeek API（OpenAI 兼容协议）
- Pydantic >= 2.0（数据模型）
- pytest（测试）

## 项目结构
```
travel-planning-agent/
├── CLAUDE.md                      ← 本文件
├── app/
│   ├── server.py                  # FastAPI 服务 + API
│   ├── main.py                    # CLI 入口
│   ├── graph/                     # LangGraph 工作流
│   │   ├── state.py               # TravelState
│   │   ├── nodes.py               # 9 个节点
│   │   ├── routers.py             # 条件路由
│   │   └── workflow.py            # build_graph()
│   ├── chains/                    # LangChain Chains（PydanticOutputParser）
│   ├── prompts/                   # ChatPromptTemplate
│   ├── tools/                     # 6 个 Mock 工具 + base 适配器
│   ├── schemas/                   # Pydantic 数据模型
│   ├── config/settings.py         # 环境变量配置
│   ├── services/                  # PlannerService + SessionService
│   ├── templates/                 # HTML 聊天界面
│   └── static/                    # CSS
├── tests/                         # 36 个测试
└── docs/
    └── ai/                        # 上下文治理文件
```

## 架构原则
- **LangChain 负责节点内部**（LLM 调用、Prompt、Tool、Output Parser）
- **LangGraph 负责节点之间**（State 流转、条件分支、循环控制）
- **State 只存 dict**，不存 Pydantic 对象（model_dump() 后再写入）
- **能用代码判断就不调 LLM**（check_info、decide_tools、final_output 都是纯 Python）
- **工具失败不中断流程**（safe_tool_call 兜底）

## 开发规则
- 修改前先读相关文件，不要全项目扫描
- 不要主动重构无关模块
- 不引入未说明用途的新依赖
- Chain 中用 PydanticOutputParser（兼容所有 API），不用 with_structured_output
- parse_request 用 Python 关键词提取，不调 LLM（性能优化结果）
- 默认快速模式（max_revision_count=0），跳过 reflection

## 测试
```bash
# 全部测试
pytest tests/ -v

# 不需要 API Key 的测试（秒级）
pytest tests/test_parse.py tests/test_tools.py tests/test_reflection.py -v

# 需要 API Key 的测试（分钟级）
pytest tests/test_workflow.py tests/test_followup.py tests/test_tool_failure.py -v
```

## 启动
```bash
cd travel-planning-agent
cp .env.example .env   # 配置 API Key
python -m app.server    # Web 服务 → http://127.0.0.1:8000
```

## 上下文治理规则
- 当前任务边界写入 docs/ai/current-task.md
- 阶段进度写入 docs/ai/progress.md
- 架构决策写入 docs/ai/decisions.md
- 跨窗口交接写入 docs/ai/handoff-summary.md
- 大范围代码搜索用 subagent，只把摘要带回主上下文
- 切换无关任务时先 /clear
- 长任务继续时先更新 handoff-summary，再 /compact
