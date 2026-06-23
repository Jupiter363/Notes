"""
景点搜索工具 (Attraction Search Tool)
======================================

在旅行规划 Agent 的架构中，本工具负责**根据目的地和偏好搜索景点**。

Agent 调用链中的位置：
  用户："我想去成都玩，喜欢历史文化和自然风光"
       ↓
  LLM 提取意图 → 调用 search_attractions(city="成都", preferences=["历史文化","自然风光"])
       ↓
  本工具返回匹配的景点列表（含评分、花费、时长）
       ↓
  LLM 结合其他工具（预算、天气、交通）编排行程

核心设计模式：
  - **偏好过滤 (Preference Filtering)**：用 list comprehension 按游客偏好筛选景点
  - **默认兜底 (Default Fallback)**：城市不在 mock 数据库时，用通用景点模板代替
  - **ToolResult 协议**：返回统一格式的 dict

相关概念（§3 Tool Calling）：
  - @tool 装饰器与工具注册
  - Agent 如何根据参数 schema 选择工具
  - 多个工具的协作（景点 + 预算 + 天气 → 完整行程）
"""

from datetime import date
from langchain_core.tools import tool


@tool
def search_attractions(city: str, preferences: list | None = None) -> dict:
    """
    根据城市和偏好搜索景点。

    LLM 读取此 docstring 后知道：
      - 输入：城市名 + 可选偏好列表
      - 使用场景：需要根据目的地和兴趣推荐景点时调用
      - 注意：LLM 不需要知道内部如何实现过滤，它只关心"我传参数，得到结果"

    参数类型 list | None 的含义：
      list | None 是 Python 3.10+ 的联合类型（Union Type）写法，
      等价于 typing.Optional[list]。表示 preferences 可以是列表或 None。
      None 表示"没有特殊偏好"——工具会返回全部景点而不做过滤。

    Args:
        city:        城市名称
        preferences: 偏好类型列表，如 ["历史文化", "自然风光"]，可选

    Returns:
        dict: 符合 ToolResult 协议的景点列表
              - data:      list[dict]，每个元素是一个景点的详细信息
              - confidence: "mock" 表示模拟数据
    """  # noqa: D401
    # -----------------------------------------------------------------
    # Mock 数据库设计：字典嵌套结构
    # -----------------------------------------------------------------
    # 外层 key = 城市名，value = 该城市的景点列表
    # "default" key 是兜底：当查询的城市不在数据库中时使用
    #
    # 为什么用 dict 而不是数据库？
    #   开发阶段 mock 数据用 dict 最直观。后续替换为真实 API 时，
    #   只需修改函数体内部的获取逻辑，函数签名和返回格式都不需要变。
    #   这就是"接口不变，实现可替换"的设计原则。
    mock_data = {
        # 成都 — 已收录 8 个景点，覆盖历史文化/自然风光/购物/轻松四类
        "成都": [
            {
                "name": "宽窄巷子",
                "type": "历史文化",
                "rating": 4.5,           # 评分 0-5，float 类型
                "estimated_cost": 0,     # 预估花费（元），0=免费
                "duration_hours": 2.5,   # 建议游玩时长（小时），float 支持半小时
                "note": "免费，适合拍照和美食",
            },
            {
                "name": "锦里古街",
                "type": "历史文化",
                "rating": 4.4,
                "estimated_cost": 0,
                "duration_hours": 2,
                "note": "夜间更有氛围",
            },
            {
                "name": "大熊猫繁育研究基地",
                "type": "自然风光",
                "rating": 4.8,
                "estimated_cost": 55,
                "duration_hours": 3.5,
                "note": "建议早上去，熊猫更活跃",
            },
            {
                "name": "都江堰",
                "type": "自然风光",
                "rating": 4.6,
                "estimated_cost": 90,
                "duration_hours": 5,
                "note": "离市区约1小时车程",
            },
            {
                "name": "人民公园",
                "type": "轻松",
                "rating": 4.3,
                "estimated_cost": 0,
                "duration_hours": 1.5,
                "note": "喝盖碗茶，体验成都慢生活",
            },
            {
                "name": "春熙路/太古里",
                "type": "购物",
                "rating": 4.5,
                "estimated_cost": 0,
                "duration_hours": 2,
                "note": "成都核心商圈",
            },
            {
                "name": "武侯祠",
                "type": "历史文化",
                "rating": 4.4,
                "estimated_cost": 60,
                "duration_hours": 2,
                "note": "三国文化圣地",
            },
            {
                "name": "青羊宫",
                "type": "历史文化",
                "rating": 4.2,
                "estimated_cost": 10,
                "duration_hours": 1.5,
                "note": "道教名观",
            },
        ],
        # 默认兜底 — 任何未收录的城市都使用这套模板
        # 使用 f-string 动态插入城市名，生成"看起来合理"的通用景点
        "default": [
            {
                "name": f"{city}中心景区",
                "type": "自然风光",
                "rating": 4.0,
                "estimated_cost": 50,
                "duration_hours": 3,
                "note": "",
            },
            {
                "name": f"{city}博物馆",
                "type": "历史文化",
                "rating": 4.2,
                "estimated_cost": 30,
                "duration_hours": 2,
                "note": "",
            },
            {
                "name": f"{city}美食街",
                "type": "美食",
                "rating": 4.3,
                "estimated_cost": 0,
                "duration_hours": 2,
                "note": "",
            },
            {
                "name": f"{city}城市公园",
                "type": "轻松",
                "rating": 4.1,
                "estimated_cost": 0,
                "duration_hours": 1.5,
                "note": "",
            },
        ],
    }

    # -----------------------------------------------------------------
    # 数据获取：dict.get(key, default) 实现优雅的兜底
    # -----------------------------------------------------------------
    # mock_data.get(city, mock_data["default"]) 的含义：
    #   如果 city 在 mock_data 的 key 中 → 返回该城市的景点列表
    #   否则 → 返回 "default" 对应的通用模板
    # 这是一种内建的 fallback 模式 —— 宁可给出通用建议，也不返回空列表。
    data = mock_data.get(city, mock_data["default"])

    # -----------------------------------------------------------------
    # 偏好过滤：list comprehension 实现声明式筛选
    # -----------------------------------------------------------------
    # if preferences: 检查是否为 None 或空列表
    #   None → 不过滤，返回全部
    #   []   → 空列表也为 falsy，不过滤（用户没指定偏好 = 全都要）
    if preferences:
        # ---------------------------------------------------------------
        # 这一行 list comprehension 做了什么？
        #
        # [item for item in data if any(p in item.get("type", "") for p in preferences)]
        #
        # 逐层拆解：
        #   for item in data              → 遍历所有景点
        #   if any(...)                   → 只要满足任意一个偏好就保留
        #   for p in preferences          → 遍历用户的所有偏好
        #   p in item.get("type", "")     → 检查偏好词是否出现在景点类型中
        #
        # 例如：preferences=["历史文化", "自然风光"]
        #   "宽窄巷子".type = "历史文化"  → "历史文化" in "历史文化" → True  → 保留
        #   "春熙路".type = "购物"       → 都不匹配               → False → 过滤
        #
        # 为什么用 item.get("type", "") 而不是 item["type"]？
        #   .get() 在 key 不存在时返回默认值 ""（空字符串），避免 KeyError。
        #   这是一种防御性编程 —— 即使景点字典缺少 type 字段也不会崩溃。
        # ---------------------------------------------------------------
        data = [item for item in data if any(p in item.get("type", "") for p in preferences)]

    # -----------------------------------------------------------------
    # 返回 ToolResult 格式
    # -----------------------------------------------------------------
    return {
        "data": data,                     # 景点列表（可能已被偏好过滤）
        "source": "mock_attractions",     # 数据来源标识，方便调试
        "updated_at": str(date.today()),
        "confidence": "mock",             # mock = 开发阶段模拟数据
        "error": None,
    }


# =============================================================================
# 设计要点总结
# =============================================================================
# 1. **Default Fallback**：城市不在数据库时返回通用模板，避免 Agent 收到空列表
#    后陷入"不知道该推荐什么"的尴尬局面。
#
# 2. **偏好过滤**：用声明式的 list comprehension 代替命令式的 for + append，
#    代码更简洁，意图更明确（"我要这些类型"而非"循环检查类型然后加进去"）。
#
# 3. **defensive .get()**：用 .get("type", "") 代替直接索引，防止数据格式不完整
#    导致的 KeyError。在 mock 阶段这看起来多余，但在接入真实 API 时（API 返回
#    的字段可能不稳定），这种防御性写法就非常有用。
#
# 4. **ToolResult 协议**：与所有其他工具保持一致的数据格式，Agent 可以统一处理。
# =============================================================================
