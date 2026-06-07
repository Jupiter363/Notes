# 工作流说明

## 核心流程

```
START
  → parse_request_node（LLM 结构化解析用户输入）
  → check_info_node（检查信息完整性）
  → 条件分支：
      ├── 不完整 → ask_clarification_node（追问） → END
      └── 完整 → decide_tools_node（决定所需工具）
                  → collect_context_node（安全调用工具）
                  → generate_plan_node（生成初版计划）
                  → reflect_plan_node（结构化反思）
                  → 条件分支：
                      ├── 需要修正且未超次数 → revise_plan_node → reflect_plan_node（循环）
                      └── 否则 → final_output_node（渲染 Markdown） → END
```

## Reflection 循环

```
generate_plan → reflect_plan → revise_plan → reflect_plan → ... → final_output
```

退出条件：
1. Reflection 判断 `need_revision = false` 或 `accepted_as_final = true`
2. `revision_count >= max_revision_count`（默认 2）

## 条件路由

- `route_after_check`: 检查 `is_info_complete` 决定继续或追问
- `route_after_reflection`: 检查 `need_revision` 和 `revision_count` 决定修正或输出
