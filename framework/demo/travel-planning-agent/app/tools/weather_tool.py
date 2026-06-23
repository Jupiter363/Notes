"""
天气查询工具 (Weather Query Tool)
===================================

在旅行规划 Agent 的架构中，本工具负责**目的地天气查询与风险评估**。

Agent 调用链中的位置：
  用户输入"帮我规划成都6月25-27日的旅行"
       ↓
  LLM 分析意图 → 决定调用 get_weather(city="成都", date_range="6月25-27日")
       ↓
  本工具返回天气数据 + 风险提示
       ↓
  LLM 根据天气调整行程安排（如：第三天有阵雨 → 户外景点提前）

相关概念（§3 Tool Calling）：
  - @tool 装饰器：将普通 Python 函数标记为 LLM 可调用的工具
  - ToolResult 格式：统一的数据返回协议
  - Mock 数据：开发阶段替代真实 API 调用的模拟数据
"""

from datetime import date
from langchain_core.tools import tool


# =============================================================================
# @tool 装饰器详解
# =============================================================================
# @tool 是 LangChain 提供的装饰器，作用是将一个普通 Python 函数"注册"为
# Agent 可以调用的工具（Tool）。它做了以下事情：
#
# 1. **解析函数签名** → 提取参数名、类型注解、默认值，
#    生成 JSON Schema 作为工具的 input_schema。
#    LLM 通过这个 schema 知道调用工具时需要传什么参数。
#
# 2. **提取 docstring** → 将函数的文档字符串作为工具的 description。
#    LLM 阅读这个描述来决定"什么时候该调用这个工具"。
#    因此 docstring 必须：
#      - 说明工具的功能（做什么）
#      - 暗示使用场景（什么时候用）
#    **但不要描述返回格式**——LLM 不需要知道返回的 dict 结构，
#    它只需要知道"这个工具能给我天气信息"。
#
# 3. **包装为 StructuredTool 对象** → 赋予 .invoke(args) 方法，
#    使其可以被 safe_tool_call() 中的 hasattr(tool, "invoke") 检测到。
#    （参见 app/tools/base.py 中的 safe_tool_call 函数）
#
# 关键理解：@tool 本质上是一个**注册器（Registry）** +
#            **适配器（Adapter）**，它把普通函数"适配"成 LLM 能理解
#            和调用的标准接口。这就是 Tool Adapter 模式的具体实现。
# =============================================================================

@tool
def get_weather(city: str, date_range: str = "") -> dict:
    """
    查询城市的天气信息与出行风险。

    这个 docstring 会被 LangChain 提取为工具的 description。
    LLM 读取后知道：
      - 输入：城市名 + 可选日期范围
      - 用途：（推断）规划行程时评估天气风险
    注意：这里不需要写返回格式，LLM 用 function calling 的 response 字段
    来解析返回的 dict。

    为什么 date_range 默认值是空字符串 ""？
      空字符串作为 sentinel value（哨兵值），表示"未指定日期范围"。
      如果后续接入真实 API，可以判断 if date_range: 来决定是否
      请求特定日期的数据。用 "" 而非 None 是因为类型注解是 str，
      保持类型一致性。

    Args:
        city:       城市名称，如"成都"、"北京"
        date_range: 日期范围，如"2026-06-25到2026-06-27"，可选

    Returns:
        dict: 符合 ToolResult 协议的天气数据
              - data.forecast: 多日天气预报列表
              - data.risk:     出行风险提示（人类可读的文本建议）
              - source:        数据来源标识
              - confidence:    置信度（mock 表示模拟数据）
    """  # noqa: D401  # noqa: B950
    # -----------------------------------------------------------------
    # 返回的 dict 结构遵循 base.py 中定义的 ToolResult 协议：
    #   data       → 核心数据（forecast 列表 + risk 文本）
    #   source     → "mock_weather"，表明这是模拟数据
    #   updated_at → 当前日期，模拟"数据更新时间"
    #   confidence → "mock" = 开发/演示阶段的模拟数据，不可用于生产决策
    #   error      → None 表示本次调用无异常
    # -----------------------------------------------------------------
    return {
        "data": {
            "city": city,
            # forecast 是列表，每个元素是一个 dict，代表一天
            # 这种 list[dict] 结构便于 LLM 遍历和引用特定日期的数据
            "forecast": [
                {
                    "date": "2026-06-25",
                    "weather": "晴转多云",
                    "temp_high": 29,     # 最高温度（摄氏度）
                    "temp_low": 21,       # 最低温度（摄氏度）
                    "rain_prob": "10%",   # 降雨概率，字符串格式便于 LLM 直接引用
                },
                {
                    "date": "2026-06-26",
                    "weather": "多云",
                    "temp_high": 30,
                    "temp_low": 22,
                    "rain_prob": "20%",
                },
                {
                    "date": "2026-06-27",
                    "weather": "阵雨",
                    "temp_high": 28,
                    "temp_low": 20,
                    "rain_prob": "60%",
                },
            ],
            # risk 字段是"预处理"的人类可读建议
            # 为什么在这里做预处理而不是让 LLM 自己分析？
            #   当接入真实天气 API 后，API 本身可能就返回风险等级。
            #   在 mock 阶段预置 risk 文本，可以确保 Agent 即使没有强大的
            #   推理能力，也能给出合理的天气提示。
            "risk": "第三天可能有阵雨，建议带雨具，户外景点安排在上午",
        },
        "source": "mock_weather",
        "updated_at": str(date.today()),
        "confidence": "mock",
        "error": None,
    }


# =============================================================================
# Mock 数据设计思路
# =============================================================================
# 为什么用 mock 数据而不是直接接入天气 API（如 OpenWeatherMap）？
#
# 1. **快速原型开发**：不需要申请 API Key、处理认证、等待审核，直接写数据即可
#    验证"Agent 能否正确调用工具并根据结果做决策"这个核心流程。
#
# 2. **确定性测试**：真实 API 返回的数据每天都在变，无法编写可重复的测试用例。
#    Mock 数据让每次调用的结果完全可预测。
#
# 3. **离线开发**：不依赖网络连接，随时随地可以开发和演示。
#
# 4. **成本控制**：天气 API 通常有调用次数限制和费用，开发阶段没必要消耗配额。
#
# 替换为真实 API 的步骤：
#   1. 在 get_weather 函数内部添加 HTTP 请求（requests / httpx）
#   2. 解析 API 返回的 JSON，映射到现有 ToolResult 结构
#   3. 将 confidence 改为 "high"，source 改为 "openweather_api"
#   4. 保留 fallback 逻辑：API 失败时返回 confidence="low" 的降级数据
# =============================================================================
