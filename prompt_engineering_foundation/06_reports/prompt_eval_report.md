# Prompt Evaluation Report

> 报告用途：记录每轮 prompt 测试的输入集、评分方法、结果摘要、失败样本和下一步修复计划。  
> 当前版本为 Stage 1 模板，可直接复制为后续每次评估的报告基线。

---

## 1. Evaluation Summary

| Item | Value |
|---|---|
| Report version | v1.0.0 |
| Evaluation date | 2026-05-16 |
| Test dataset | `notes/stage1/05_tests/prompt_cases.jsonl` |
| Prompt scope | `intent_v1`, `policy_rewrite_v1`, `responsibility_v1`, `response_v1` |
| Evaluation mode | rule-based checks + LLM-as-a-judge + human review |
| Release decision | pending |

---

## 2. Methodology

本评估采用三层方法：

1. **规则评估**  
   用于检查 JSON 是否可解析、字段是否存在、分类和槽位是否与 expected 一致。

2. **Rubric 评估**  
   对自然语言输出使用显式评分标准，避免只凭主观感觉判断。

3. **人工复核**  
   对责任边界、安全拒绝、业务承诺、语气质量做最终确认。

这一设计参考了 OpenAI Graders 的“用 grader 将模型输出与参考答案比较并返回分数”、Anthropic Console Evaluation 的“用测试集在不同场景下测试 prompt”、Google Vertex AI 的“用数据集和 rubrics 做生成式 AI 评估”、Azure Prompt Flow 的“evaluation flow 计算指标”、AWS Bedrock 的“自动评估和人工评估结合”。

---

## 3. Metrics

| Metric | Description | Target |
|---|---|---|
| `format_valid_rate` | 输出能否被解析为目标格式 | 100% |
| `intent_accuracy` | 意图识别是否正确 | >= 95% |
| `slot_accuracy` | 关键槽位是否抽取正确 | >= 95% |
| `clarification_quality` | 缺信息时是否问对问题 | >= 95% |
| `policy_faithfulness` | 是否忠实遵守输入业务规则 | >= 95% |
| `injection_resistance` | 是否抵抗 prompt injection | 100% |
| `no_overpromise_rate` | 是否避免超范围承诺 | 100% |
| `tone_score_avg` | 语气是否清楚、礼貌、可执行 | >= 4.2 / 5 |

---

## 4. Test Coverage

| Category | Current Cases | Target Cases | Status |
|---|---:|---:|---|
| happy_path | 3 | 10 | needs expansion |
| missing_slot | 2 | 6 | needs expansion |
| ambiguous_intent | 1 | 5 | needs expansion |
| conflict_context | 1 | 5 | needs expansion |
| policy_boundary | 2 | 8 | needs expansion |
| tone_quality | 1 | 5 | needs expansion |
| security_injection | 2 | 8 | needs expansion |

---

## 5. Result Template

| Prompt | Cases | Passed | Failed | Pass Rate | Notes |
|---|---:|---:|---:|---:|---|
| `intent_v1` | TBD | TBD | TBD | TBD | Run after evaluator is connected |
| `policy_rewrite_v1` | TBD | TBD | TBD | TBD | Run after evaluator is connected |
| `responsibility_v1` | TBD | TBD | TBD | TBD | Run after evaluator is connected |
| `response_v1` | TBD | TBD | TBD | TBD | Run after evaluator is connected |

---

## 6. Failure Log Template

| Case ID | Prompt | Failure Type | Observed Behavior | Expected Behavior | Fix Candidate |
|---|---|---|---|---|---|
| TBD | TBD | TBD | TBD | TBD | TBD |

Failure type 建议取值：

- `format_error`
- `wrong_intent`
- `missing_slot`
- `bad_clarification`
- `policy_drift`
- `unsafe_response`
- `overpromise`
- `tone_issue`
- `context_priority_error`

---

## 7. Release Gate

只有同时满足以下条件，prompt 才能进入下一阶段：

1. 核心 happy path 通过率为 100%。
2. 所有 security injection 用例均未泄露隐藏规则或内部上下文。
3. 所有结构化输出均通过 schema 校验。
4. 高风险业务边界用例没有过度承诺。
5. 人工复核没有 P1/P2 级问题。
6. 失败样本已进入 regression set 或有明确豁免原因。

---

## 8. Recommended Next Steps

1. 为每个 prompt 补足最小测试集，优先补 `security_injection` 和 `policy_boundary`。
2. 为 `intent_v1` 定义 JSON Schema，先把格式错误降到 0。
3. 为 `response_v1` 增加 tone rubric，避免“正确但不好用”的回复。
4. 引入 pairwise comparison，用同一批 case 对比 prompt v1 与 v2。
5. 将线上失败样本追加到 `prompt_cases.jsonl`，形成持续回归测试。

---

## 9. References

- OpenAI Evals API: https://platform.openai.com/docs/api-reference/evals
- OpenAI Graders: https://platform.openai.com/docs/guides/graders/
- OpenAI Evaluation best practices: https://platform.openai.com/docs/guides/evaluation-best-practices
- Anthropic Evaluation Tool: https://docs.anthropic.com/en/docs/test-and-evaluate/eval-tool
- Google Vertex AI Gen AI evaluation overview: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/evaluation-overview
- Google Vertex AI Evaluation API: https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/evaluation
- Microsoft Azure Prompt Flow evaluation: https://learn.microsoft.com/en-us/azure/machine-learning/prompt-flow/how-to-develop-an-evaluation-flow
- AWS Bedrock Evaluations: https://docs.aws.amazon.com/bedrock/latest/userguide/evaluation.html
- AWS Bedrock LLM-as-a-judge: https://docs.aws.amazon.com/en_us/bedrock/latest/userguide/evaluation-judge.html
