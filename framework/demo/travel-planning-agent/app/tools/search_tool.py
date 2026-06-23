"""
网络搜索工具 (Web Search Tool)
===============================

在旅行规划 Agent 的架构中，本工具负责**搜索实时的景点信息、营业时间、票价变动等**。

Agent 调用链中的位置：
  用户："大熊猫基地明天开门吗？需要预约吗？"
       ↓
  LLM → 调用 web_search(query="成都大熊猫繁育研究基地 营业时间 预约")
       ↓
  返回搜索结果（当前为 mock，实际部署时接入搜索 API）
       ↓
  LLM → 提取关键信息并回答用户

与其他工具的本质区别：
  - 天气/景点/美食/预算/交通 → **知识型工具**（查静态数据库）
  - web_search → **检索型工具**（查动态互联网信息）

为什么需要单独的搜索工具？
  Mock 数据库不可能涵盖所有实时信息（营业时间变更、临时闭馆、票价调整）。
  web_search 作为"万能兜底"，让 Agent 在遇到 mock 数据无法回答的问题时，
  有一个查询外部世界的出口。

相关概念（§3 Tool Calling）：
  - 工具的分层设计：领域工具（精准但有限）+ 搜索工具（广泛但需 LLM 提取）
  - confidence 字段的实际意义：mock 数据的 confidence 可以是 "low"，
    因为它是模拟的、不具备时效性
"""

from datetime import date
from langchain_core.tools import tool


@tool
def web_search(query: str) -> dict:
    """
    搜索最新的景点营业时间、票价、临时通知等实时信息。

    这是 Agent 工具集中最"通用"的工具 —— 当其他领域工具无法回答时，
    LLM 可以调用它来搜索互联网。

    当前为 mock 实现，返回固定的示例结果。实际部署时：
      - 替换为 SerpAPI / Google Custom Search / Bing Search API
      - 或使用本地搜索引擎（如 Elasticsearch）
      - 保持返回的 ToolResult 格式不变

    Args:
        query: 搜索关键词。LLM 应尽量构造精确的查询字符串，
               例如 "成都武侯祠 2026年6月票价" 而非模糊的 "武侯祠"

    Returns:
        dict: 符合 ToolResult 协议的搜索结果
              - data.results: 搜索结果列表
              - confidence: "low" = 当前为 mock 数据，置信度低
    """  # noqa: D401
    # -----------------------------------------------------------------
    # Mock 搜索结果
    # -----------------------------------------------------------------
    # 当前返回固定的示例结果，因为真实的网络搜索需要外部 API。
    #
    # 设计意图：
    #   1. 占位：让 Agent 流程能跑通（有工具可调用 + 有结果可解析）
    #   2. 接口定义：确立 ToolResult 格式中 search 类数据的结构
    #      - data.query: 回显查询词，方便调试
    #      - data.results: list[dict]，每个结果含 title/snippet/url
    #      - data.note: 额外说明（这里提醒用户数据非实时）
    #
    # 替换为真实搜索 API 时，只需修改这个 return 语句的内容，
    # 函数签名和返回格式完全不变。
    return {
        "data": {
            "query": query,  # 回显查询词，调试时可以看到 LLM 搜了什么
            "results": [
                {
                    "title": f"关于「{query}」的搜索结果",
                    # snippet 是搜索结果的摘要片段
                    # LLM 最常引用这个字段来回答用户
                    "snippet": "此为 mock 搜索结果。实际部署时接入搜索 API 获取最新信息。",
                    "url": "",  # mock 阶段无真实 URL
                },
            ],
            # note 是给 LLM 看的提示，LLM 可能会把它转述给用户
            "note": "mock 数据，建议出行前在官方渠道确认最新信息",
        },
        "source": "mock_search",
        "updated_at": str(date.today()),
        # -----------------------------------------------------------------
        # confidence = "low" 的含义
        # -----------------------------------------------------------------
        # 与其他工具的 "mock" 不同，这里用了 "low"。
        # 语义区别：
        #   "mock" = 开发阶段的模拟数据，功能正确但数据非真实
        #   "low"  = 数据不可靠，不应作为关键决策的唯一依据
        #
        # web_search 的 mock 结果（固定模板、空 URL）即便在开发阶段也
        # 几乎没有任何参考价值，所以标记为 "low"。
        # Agent 读取 confidence 字段后可以决定：
        #   - 是否额外提醒用户"此信息未经实时验证"
        #   - 是否降低此工具结果的权重
        "confidence": "low",
        "error": None,
    }


# =============================================================================
# 工具的 Confidence 设计
# =============================================================================
# 在 Agent 系统中，不是所有工具返回的数据都同等可信。confidence 字段
# 让 Agent（或更上层的编排逻辑）能够"区别对待"不同来源的数据：
#
#   confidence="high"   → 真实 API 返回，可直接用于决策
#   confidence="mock"   → 模拟数据，开发/演示用，信息正确但非真实
#   confidence="low"    → 降级/兜底数据，仅供参考，不应作为唯一依据
#
# 这种"置信度标记"是生产级 Agent 的重要设计模式：
#   假设天气 API 挂了，fallback 返回 confidence="low" 的默认天气。
#   Agent 看到 low 后可以决定：给用户推荐"室内备选方案"（而不是草率地说
#   "明天晴天适合户外"）。
# =============================================================================


# =============================================================================
# Mock → 真实 API 的迁移指南
# =============================================================================
# 当需要接入真实搜索 API 时（以 SerpAPI 为例）：
#
# 1. 安装依赖：pip install google-search-results
# 2. 替换函数体：
#
#    from serpapi import GoogleSearch
#
#    @tool
#    def web_search(query: str) -> dict:
#        params = {"q": query, "api_key": os.getenv("SERPAPI_KEY"), "hl": "zh-cn"}
#        search = GoogleSearch(params)
#        raw = search.get_dict()
#
#        results = []
#        for r in raw.get("organic_results", []):
#            results.append({
#                "title": r.get("title"),
#                "snippet": r.get("snippet"),
#                "url": r.get("link"),
#            })
#
#        return {
#            "data": {"query": query, "results": results},
#            "source": "serpapi",
#            "confidence": "high",  # 真实 API → 高置信度
#            ...
#        }
#
# 3. 添加异常处理（也可以由 base.safe_tool_call 统一处理）
# 4. 将 SERPAPI_KEY 加入 .env，不硬编码在代码中
# =============================================================================
