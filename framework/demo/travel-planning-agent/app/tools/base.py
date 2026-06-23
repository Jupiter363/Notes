"""
工具基础设施模块 (Tool Infrastructure / Safety Layer)
======================================================

本模块为整个 Agent 的工具调用提供**安全兜底**与**统一适配**能力，不直接参与业务逻辑。

在 Agent 架构中的角色：
  Agent 大脑 (LLM) 决定调用哪个工具
       ↓
  safe_tool_call()  ← 本模块：拦截调用，统一处理异常
       ↓
  具体工具函数 (如 get_weather, search_attractions ...)
       ↓
  ToolResult (dict) ← 统一返回格式，便于 Agent 解析

涉及的核心概念（参考 Stage 2 笔记 §3 Tool Calling）：
  - Tool Adapter 模式：用一个统一的包装函数（safe_tool_call）适配不同签名的工具，
    让调用方不需要关心工具的具体实现细节。
  - Fallback（降级）：当工具调用失败时，不抛异常让 Agent 崩溃，而是返回一个
    标记了 error 字段的降级结果，Agent 仍可据此做出决策。
  - Safe Execution：用 try/except 包裹所有工具调用，确保单点故障不传播。

为什么需要 base.py？
  1. 分离关注点：安全逻辑（try/except）和业务逻辑（查询天气、搜索景点）分开。
  2. 复用：所有工具共用一个安全包装器，不需要每个工具自己写异常处理。
  3. 一致性：所有工具无论成功或失败，都返回相同结构的 dict。
"""

from datetime import date
from typing import Any


# =============================================================================
# ToolResult 数据结构说明
# =============================================================================
# 所有工具都返回一个 dict，包含以下字段，这是 Agent 与工具之间的"约定协议"：
#
#   data:       dict | list  — 工具返回的实际数据（天气、景点列表、预算明细等）
#   source:     str          — 数据来源标识（mock_weather / real_api 等），便于调试
#   updated_at: str          — 数据更新时间，使用 ISO 日期格式
#   confidence: str          — 置信度，常见值：
#                               "high"   = 真实 API 返回，可信
#                               "low"    = 降级/兜底数据，仅供参考
#                               "mock"   = 开发阶段模拟数据
#   error:      str | None   — 错误信息，None 表示无错误，有值表示调用异常
#
# 这种统一格式让 Agent（LLM）在处理工具返回时无需针对不同工具做特殊解析。
# =============================================================================


def fallback_tool_result(source: str, error: str) -> dict:
    """
    构造一个"降级结果"，用于工具调用失败时的兜底返回。

    为什么需要 fallback（降级）？
      在 Agent 系统中，工具调用可能因网络超时、API 限流、参数错误等原因失败。
      如果直接让异常向上传播，Agent 可能崩溃或给出"我无法回答"这种无用的回复。
      Fallback 机制让工具在失败时仍返回一个结构完整的 dict，Agent 可以：
        - 读取 error 字段，知道"某个工具暂时不可用"
        - 读取 confidence: "low"，降低对该数据的依赖
        - 继续执行后续步骤，而不是整体中断

    Args:
        source: 数据来源标识，例如 "weather_api" 或 "attraction_db"
        error:  错误描述字符串，会原样放入返回 dict 的 error 字段

    Returns:
        dict: 符合 ToolResult 协议的降级结果，data 为空、confidence 为 low
    """
    return {
        "data": {},          # 空数据 — 降级时不提供虚假数据，让 Agent 知道"没拿到"
        "source": source,    # 保留来源标识，方便日志追踪
        "updated_at": str(date.today()),  # 记录降级发生的时间
        "confidence": "low", # low = 告诉 Agent 此结果不可靠，不要作为关键决策依据
        "error": error,      # 错误原因，Agent 可以据此向用户解释
    }


def safe_tool_call(tool, args: dict, fallback_source: str) -> tuple[dict, dict | None]:
    """
    安全地调用一个工具，捕获所有异常并返回统一格式的结果。

    这是 **Tool Adapter 模式** 的核心实现（§3 Tool Calling）：
      不同工具有不同的函数签名和调用方式 —— 有的用 .invoke()（LangChain），
      有的直接可调用。safe_tool_call 统一适配这些差异，对外暴露一致的接口。

    返回值类型 tuple[dict, dict | None] 的含义：
      - 第一个元素 (dict)：始终是 ToolResult 格式的结果
        - 成功时：工具正常返回的数据
        - 失败时：fallback_tool_result() 构造的降级结果
      - 第二个元素 (dict | None)：错误详情
        - None 表示调用成功，无错误
        - dict 表示调用失败，包含 tool/args/error 三个字段，用于日志和调试

    为什么用 tuple 而不是抛出异常？
      tuple 多返回值是 Python 中一种轻量的错误处理模式（类似 Go 的 (result, error)）。
      调用方可以显式检查 error 是否为 None 来决定后续行为，比 try/except 更可控。

    Args:
        tool:            工具对象 — 可以是 LangChain @tool 装饰的函数，也可以是普通 callable
        args: dict       传给工具的参数，key 需匹配工具函数的参数名
        fallback_source: str  失败时写入降级结果的 source 字段

    Returns:
        tuple[dict, dict | None]: (结果, 错误详情)
    """
    try:
        # ---------------------------------------------------------------
        # 适配两种工具调用方式（Tool Adapter 模式的关键判断）：
        #
        # 1. hasattr(tool, "invoke") → LangChain 工具对象
        #    LangChain 的 @tool 装饰器会在函数上挂载一个 StructuredTool 对象，
        #    该对象以 .invoke() 方法接收 dict 参数。这种方式更"Agent 原生"。
        #
        # 2. tool(args) → 普通 Python 函数
        #    直接调用，适用于未被 LangChain 包装的工具或测试中的 mock 函数。
        #
        # 这种"先检查接口再调用"的写法是鸭子类型（Duck Typing）的典型应用：
        #   "如果它走起来像鸭子（有 invoke 方法），就把它当 LangChain 工具调用"
        # ---------------------------------------------------------------
        if hasattr(tool, "invoke"):
            # LangChain 工具路径：通过 invoke 方法传入 dict 参数
            result = tool.invoke(args)
        else:
            # 普通函数路径：直接调用，args 以 **kwargs 展开
            result = tool(**args)

        # 成功：返回结果 + None（表示无错误）
        return result, None

    except Exception as e:
        # ---------------------------------------------------------------
        # 异常处理策略：捕获所有 Exception（包括网络错误、类型错误、KeyError 等）
        #
        # 为什么用 broad Exception 而不是具体异常类型？
        #   在 Agent 系统中，工具的失败原因千变万化（API 挂了、参数不对、超时……），
        #   逐一捕获会让代码冗长且容易遗漏。broad except 确保"任何失败都不会
        #   让整个 Agent 崩溃"，这是 Agent 系统健壮性的基本要求。
        #
        # 为什么不用 bare except（不带 Exception）？
        #   裸 except 会捕获 KeyboardInterrupt 和 SystemExit，这些是进程级信号，
        #   不应该被业务代码吞掉。用 except Exception 是最佳实践。
        # ---------------------------------------------------------------

        # 构造错误详情，供日志系统记录
        error = {
            "tool": getattr(tool, "name", str(tool)),
            # 尝试获取工具名称，LangChain 工具对象有 .name 属性
            # 普通函数没有，退化为 str(tool) 显示函数 repr
            "args": args,    # 保留调用参数，方便复现问题
            "error": str(e), # 异常信息的字符串表示
        }

        # 返回降级结果 + 错误详情
        # 注意：即使失败了，仍然返回一个结构完整的 dict（而不是 None 或抛异常）
        # 这是 Agent 系统"优雅降级"的核心思想
        return fallback_tool_result(fallback_source, str(e)), error
