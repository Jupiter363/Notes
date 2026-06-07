# Travel Planning Agent

基于 LangChain + LangGraph 的旅行规划助手，使用结构化输出、工具适配器模式和 Reflection 循环。

## 特性

- LangChain Structured Output 约束模型输出
- LangGraph 有状态、多分支、可循环的 Agent Workflow
- 真实 Reflection Loop（生成→反思→修正→再反思）
- Tool Adapter 模式，mock 与真实 API 可替换
- 信息不足时追问，支持用户补充后续跑
- 完整的测试套件

## 快速开始

```bash
# 安装依赖
pip install -e ".[dev]"

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 API Key

# 运行旅行规划
python -m app.main
```

## 项目结构

```
travel-planning-agent/
  app/
    main.py                  # CLI 入口
    graph/                   # LangGraph 工作流
      state.py, workflow.py, nodes.py, routers.py
    chains/                  # LangChain Chains
      parse_chain.py, plan_chain.py, reflection_chain.py, revise_chain.py
    prompts/                 # Prompt 模板
    tools/                   # 工具适配器（mock providers）
    schemas/                 # Pydantic 数据模型
    config/                  # 配置
    services/                # 服务层
  tests/                     # 测试套件
  docs/                      # 文档
```

## 技术栈

- Python >= 3.11
- LangChain >= 1.1
- LangGraph >= 1.0
- Pydantic >= 2.0
- pytest >= 8.0
