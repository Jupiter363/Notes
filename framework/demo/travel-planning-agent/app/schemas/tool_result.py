"""
工具返回结果数据模型 —— 定义"所有工具统一输出什么格式"。

这是 Tool Adapter 模式的核心：不管工具用的是 mock 数据还是真实 API，
返回的格式都一样。对上游代码来说，它不关心数据从哪来，
它只认这个格式。

统一格式的好处：
- 今天用 mock，明天换真实 API，只改工具内部，不改任何上游代码
- confidence 字段让 LLM 知道"这数据可信吗"，从而决定要不要提醒用户
- error 字段让系统可以优雅降级，而不是崩溃

Stage 2 对应概念：§3 Tool Calling（工具输出规范）
"""

from pydantic import BaseModel, Field
from typing import Optional


class ToolResult(BaseModel):
    """
    所有工具的通用输出格式。

    每个工具（天气、景点、美食、预算、交通、搜索）都返回这个结构。
    Pydantic 会自动校验格式，如果工具返回了错误结构会直接报错。
    """

    # 核心数据 —— dict（如 {"city": "成都", "forecast": [...]}）
    # 或 list（如 [{"name": "宽窄巷子", "rating": 4.5}, ...]）
    data: dict | list

    # 数据来源 —— 标识是哪个工具提供的
    # 如 "mock_weather"、"real_weather_api"、"fallback_weather"
    source: str

    # 更新时间 —— 标注数据的新鲜度
    updated_at: Optional[str] = None

    # 置信度 —— 告诉 LLM 这数据有多可信
    # "mock": 虚拟数据，仅供演示
    # "high": 真实 API 返回，高可信
    # "medium": 缓存数据或间接推算
    # "low": 兜底数据或降级数据
    confidence: str = Field(description="mock/high/medium/low")

    # 错误信息 —— 工具正常时是 None，失败时是错误描述
    # 这个字段让系统可以优雅降级：工具挂了不崩溃，记录错误继续运行
    error: Optional[str] = None
