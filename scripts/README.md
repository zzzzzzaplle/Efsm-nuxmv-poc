代码执行的是这个闭环链路

自然语言需求
→ 调用LLM
→ Candidate EFSM JSON
→ Schema与语义校验
→ 转换为SMV
→ 加载冻结的Gold CTL
→ nuXmv验证
→ 提取失败性质与反例
→ 反馈给LLM修复Candidate EFSM
→ 最多迭代3轮
→ 输出最终EFSM
---

### 代码实现与流程对照表

| 步骤 | 流程节点 | [scripts/run_pilot_experiment.py](scripts/run_pilot_experiment.py) 中的对应实现 |
| :---: | :--- | :--- |
| 1 | **自然语言需求** | 读取 `vending_machine.json`（提取 R1~R13 自然语言条款）。 |
| 2 | **调用 LLM** | [build_initial_generation_prompt()](scripts/run_pilot_experiment.py#L159-L199) 组装提示词 ➔ [call_openai_chat_completion()](scripts/run_pilot_experiment.py#L117-L156) 发送请求。 |
| 3 | **Candidate EFSM JSON** | [extract_json_text_from_response()](scripts/run_pilot_experiment.py#L93-L114) 提取 JSON 并保存为 `candidate_round_0.json`。 |
| 4 | **Schema 与语义校验** | 调用转译器执行 `validate_structure()` 与 `validate_semantics()`，检查状态/事件闭包及输出合法性。 |
| 5 | **转换为 SMV** | 调用 [src/efsm_to_smv.py](src/efsm_to_smv.py) 将模型转译，自动生成 `emit_` 输出宏与转移逻辑。 |
| 6 | **加载冻结的 Gold CTL** | 自动挂载 `--properties gold_properties.json`（独立只读的 22 条性质）。 |
| 7 | **nuXmv 验证** | [run_single_verification()](scripts/run_pilot_experiment.py#L288-L332) 调用本地 `nuxmv` 求解器执行数学证明，日志存盘。 |
| 8 | **提取失败性质与反例** | [parse_nuxmv_output()](scripts/run_pilot_experiment.py#L244-L285) 精确抓取 `is false` 的公式和随后的状态迁移反例路径（Trace）。 |
| 9 | **反馈给 LLM 修复** | [build_repair_prompt()](scripts/run_pilot_experiment.py#L202-L241) 将原模型 + 反例 Trace 打包成调试诊断报告，请求模型重新生成。 |
| 10 | **最多迭代 3 轮** | `while current_round <= max_allowed_rounds:`（中途一旦 22 条全通过则**提前收敛退出**；若未通过则最多修复 3 轮）。 |
| 11 | **输出最终 EFSM** | 统一导出 [final_efsm.json](scripts/run_pilot_experiment.py#L492-L500) 和详细的 `summary.json`，直接作为下一阶段代码生成的输入源。 |

---

### 另外增加的一个灵活性：一维数组模式控制

代码不仅支持这个完整的 **Treatment（反例修复）** 主流程，还能通过 `--mode baseline` 或 `--pipeline generate` 将流水线缩减为纯生成，用于产出论文所需的对照实验数据。