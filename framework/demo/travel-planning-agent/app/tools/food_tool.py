"""
美食搜索工具 (Food Search Tool)
================================

在旅行规划 Agent 的架构中，本工具负责**根据目的地搜索当地美食与餐饮推荐**。

Agent 调用链中的位置：
  用户："成都有什么好吃的？"
       ↓
  LLM → 调用 search_foods(city="成都")
       ↓
  返回美食列表（含类别、人均消费、推荐备注）
       ↓
  LLM 将美食信息整合到行程中（如"午餐推荐担担面，人均15元"）

与景点工具的设计对比：
  - 相同点：都用 dict 做 mock 数据库，都有 default 兜底，都有偏好过滤
  - 不同点：偏好的过滤逻辑更精细 —— 只在用户明确偏好"美食/food"时保留完整列表，
    否则只返回前 3 条（精简推荐）

相关概念（§3 Tool Calling, Tool Adapter 模式）：
  - 多个工具如何协同工作（景点 + 美食 + 预算 → 完整行程）
  - 工具返回数据的"信息量控制"（全量 vs 精简）
"""

from datetime import date
from langchain_core.tools import tool


@tool
def search_foods(city: str, preferences: list | None = None) -> dict:
    """
    根据城市和偏好搜索当地美食。

    当 LLM 需要为行程安排餐饮推荐时调用此工具。
    preferences 参数允许 LLM 传入用户的饮食偏好（如"素食""辣"等），
    但目前 mock 实现仅识别"美食""food"两个标签。

    Args:
        city:        城市名称
        preferences: 偏好列表，可选。仅当包含"美食"或"food"时返回全量数据

    Returns:
        dict: 符合 ToolResult 协议的美食数据
              - data: list[dict]，每个元素 = {name, category, avg_cost, note}
    """  # noqa: D401
    # -----------------------------------------------------------------
    # Mock 数据库：按城市组织的特色美食
    # -----------------------------------------------------------------
    # 每个美食条目包含：
    #   name     → 菜品名称（会被 LLM 直接引用给用户）
    #   category → 类别（正餐/小吃/甜品/饮品），帮助 LLM 按餐次推荐
    #   avg_cost → 人均消费（元），整数。与 budget_tool 配合计算总花费
    #   note     → 推荐备注，包含具体的店铺名或食用建议
    mock_data = {
        "成都": [
            {"name": "火锅", "category": "正餐", "avg_cost": 120, "note": "推荐蜀大侠、小龙坎，微辣即可体验地道风味"},
            {"name": "串串香", "category": "正餐", "avg_cost": 60, "note": "冷锅串串和热锅串串两种，人均实惠"},
            {"name": "担担面", "category": "小吃", "avg_cost": 15, "note": "成都名小吃，麻辣鲜香"},
            {"name": "龙抄手", "category": "小吃", "avg_cost": 20, "note": "皮薄馅大，红油或清汤均可"},
            {"name": "钟水饺", "category": "小吃", "avg_cost": 20, "note": "甜水面风格，红油加蒜泥"},
            {"name": "麻婆豆腐", "category": "正餐", "avg_cost": 30, "note": "陈麻婆豆腐总店最正宗"},
            {"name": "夫妻肺片", "category": "凉菜", "avg_cost": 35, "note": "牛肉牛杂加红油，经典凉菜"},
            {"name": "三大炮", "category": "甜品", "avg_cost": 10, "note": "糯米团加红糖，宽窄巷子随处可见"},
            {"name": "茶馆盖碗茶", "category": "饮品", "avg_cost": 30, "note": "人民公园鹤鸣茶社是经典去处"},
        ],
        "default": [
            {"name": f"{city}本地特色菜", "category": "正餐", "avg_cost": 80, "note": ""},
            {"name": f"{city}夜市小吃", "category": "小吃", "avg_cost": 40, "note": ""},
            {"name": f"{city}网红餐厅", "category": "正餐", "avg_cost": 100, "note": ""},
            {"name": f"{city}早餐", "category": "小吃", "avg_cost": 15, "note": ""},
        ],
    }

    # 获取对应城市的美食数据，找不到时用 default 兜底
    data = mock_data.get(city, mock_data["default"])

    # -----------------------------------------------------------------
    # 偏好过滤逻辑：有选择地控制返回数据量
    # -----------------------------------------------------------------
    # 与 attraction_tool 的过滤逻辑不同，这里采用了"精简模式"：
    #   - 用户明确表示喜欢美食（preferences 含"美食"或"food"）
    #     → 返回全量列表（让 LLM 有充足素材做详细推荐）
    #   - 用户没有明确偏好，或提到了其他偏好
    #     → 只返回前 3 条（精简推荐，避免信息过载）
    #
    # 这种"信息量控制"在 Agent 设计中很重要：
    #   如果每次都给 LLM 塞 9 条美食，上下文窗口很快被占满。
    #   只有在用户真的关心美食时，才值得给出完整列表。
    if preferences:
        # 检查偏好中是否包含"美食"或"food"
        # 用 list comprehension 构建匹配列表，然后检查是否为空
        food_prefs = [p for p in preferences if p in ("美食", "food")]

        # 如果没有匹配到美食相关偏好 → 精简模式：只返回前 3 条
        # 注意：不是返回空列表！空列表会让 LLM 以为"没有美食"，
        # 而精简模式是"有美食但我不展开讲"。
        if not food_prefs:
            data = data[:3]  # 切片操作，取前 3 个元素

    # 返回 ToolResult 格式
    return {
        "data": data,
        "source": "mock_foods",
        "updated_at": str(date.today()),
        "confidence": "mock",
        "error": None,
    }


# =============================================================================
# 工具间数据协作 (Tool Data Collaboration)
# =============================================================================
# 本工具的 avg_cost 字段与 budget_tool.py 形成数据协作：
#
#   search_foods  →  返回每道菜的人均价格
#   budget_tool   →  用这些价格估算餐饮总预算
#   LLM           →  交叉验证："火锅人均120，预算每天餐饮150，可能不够"
#
# 这就是 Agent 编排多个工具的价值 —— 单个工具只知道自己领域的数据，
# LLM 作为"大脑"将跨工具的信息整合成连贯的决策。
# =============================================================================
