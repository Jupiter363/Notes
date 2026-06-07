# 评估方案

## 评估层级

| 层级 | 指标 | 说明 |
|------|------|------|
| 需求解析 | Slot Accuracy | 目的地、天数、预算、偏好是否正确 |
| 信息检查 | Missing Field Recall | 缺失字段是否识别完整 |
| 工具调用 | Tool Success Rate | 工具是否成功返回统一结构 |
| 工具选择 | Tool Selection Accuracy | 是否调用了必要工具 |
| 计划生成 | Plan Validity | 天数正确、预算合理、结构完整 |
| Reflection | Issue Detection Rate | 是否发现明显问题 |
| 修正 | Revision Effectiveness | 修正后评分是否提升 |
| 端到端 | Task Success Rate | 是否生成可用最终方案 |

## 评估用例示例

```json
{
  "case_id": "travel_001",
  "user_input": "我想6月底去成都玩3天，预算3000，喜欢美食和轻松路线",
  "expected_slots": {
    "destination": "成都",
    "days": 3,
    "budget": 3000,
    "preferences": ["美食", "轻松"]
  },
  "expected_tools": ["weather", "attractions", "foods", "budget", "transport"],
  "must_have_in_plan": ["成都", "美食", "Day 1"]
}
```

建议构造 30-50 条评估集进行系统化评测。
