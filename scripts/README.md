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
| 2 | **调用 LLM** | [build_initial_generation_prompt()](scripts/run_pilot_experiment.py#L311-L373) 组装提示词 ➔ [call_openai_chat_completion()](scripts/run_pilot_experiment.py#L269-L308) 发送请求。 |
| 3 | **Candidate EFSM JSON** | [extract_json_text_from_response()](scripts/run_pilot_experiment.py#L245-L266) 提取 JSON 并保存为 `candidate_round_0.json`。 |
| 4 | **Schema 与语义校验** | 调用转译器执行 `validate_structure()` 与 `validate_semantics()`，检查状态/事件闭包及输出合法性。 |
| 5 | **转换为 SMV** | 调用 [src/efsm_to_smv.py](src/efsm_to_smv.py) 将模型转译，自动生成 `emit_` 输出宏与转移逻辑。 |
| 6 | **加载冻结的 Gold CTL** | 自动挂载 `--properties gold_properties.json`（独立只读的 22 条性质）。 |
| 7 | **nuXmv 验证** | [run_single_verification()](scripts/run_pilot_experiment.py#L481-L535) 调用本地 `nuXmv` 求解器执行数学证明，日志存盘。 |
| 8 | **提取失败性质与反例** | [parse_nuxmv_output()](scripts/run_pilot_experiment.py#L437-L478) 精确抓取 `is false` 的公式和随后的状态迁移反例路径（Trace）。 |
| 9 | **反馈给 LLM 修复** | [build_repair_prompt()](scripts/run_pilot_experiment.py#L375-L434) 将原模型 + 反例 Trace 打包成调试诊断报告，请求模型重新生成。 |
| 10 | **最多迭代 3 轮** | `while current_round <= max_allowed_rounds:`（中途一旦 22 条全通过则**提前收敛退出**；若未通过则最多修复 3 轮）。 |
| 11 | **输出最终 EFSM** | 统一导出 [final_efsm.json](scripts/run_pilot_experiment.py#L701-L709) 和详细的 `summary.json`，直接作为下一阶段代码生成的输入源。 |

---

### Prompt 提示词组装

在自动化闭环中，提示词（Prompt）分为初始生成和反例修复两个阶段。以下展示发送给 LLM 的**英文原文模板**（其中动态嵌入的内容以 `<文件名>` 作为占位符）及对应的中文设计解析：

#### 1. 初始阶段生成EFSM提示词 ([build_initial_generation_prompt](scripts/run_pilot_experiment.py#L311-L372))

##### 英文原文

**System Prompt:**
```text
You are an expert formal methods and state machine engineer.
Your task is to convert natural-language software requirements into an Extended Finite State Machine (EFSM). //角色定义
Rules:
1. Strictly conform to the provided JSON Schema. //结构 Schema 约束
2. You MUST strictly follow the System Interface Contract below:
<system_interface.json> //将 `<system_interface.json>` 注入模型，强制固定状态集
3. In transitions, use 'updates' (key-value dictionary) to modify variables.
4. In transitions, use 'outputs' (array of strings) to emit observable signals.
5. Cite the requirement identifier (e.g. 'R2') in the 'requirement' field of each transition.
6. Ensure deterministic transitions: guards for the same (source, event) must be mutually disjoint.
7. Return ONLY valid JSON, without any commentary or markdown wrapper.
```

**User Prompt:**
```text
System Name: <system_name>
Domain: <domain>

Requirements:
<vending_machine.json 中的需求条款 (R1~R13)>

System Interface Contract (You MUST strictly follow these signatures):
<system_interface.json>

Target EFSM JSON Schema:
<efsm.schema.json>

Please generate the complete EFSM model JSON for this system.
```



---

#### 2. 反例驱动修复阶段提示词 ([build_repair_prompt](scripts/run_pilot_experiment.py#L376-L435))

##### 英文原文

**System Prompt:**
```text
You are an expert formal methods debugging engineer. //角色定义
Your previously generated EFSM failed formal verification or semantic validation. //任务目标
Analyze the provided counterexample execution trace and validation errors. //分析反例
Fix the transitions, guards, updates, or outputs to satisfy all requirements. //修复
System Interface Contract (Do NOT deviate from these signatures): //接口契约
<system_interface.json>
Return ONLY the complete, repaired EFSM JSON. //输出修复后的EFSM
```

**User Prompt:**
```text
Here is your previous EFSM model:
<candidate_round_X.json> // 上一轮的EFSM模型

Verification Failure Details:
[Schema / Semantic Validation Error]:
<转译与语义校验报错信息 (若有)> // 转译与语义校验报错信息

[nuXmv Formal Verification Counterexample Trace]:
<nuXmv 形式化验证失败性质与反例执行路径 Trace> // 将 nuXmv 求解器生成的具体违规路径（输入事件序列与变量跳变）完整呈现

Please carefully analyze the root cause of the violation and output the entire corrected EFSM JSON.
```


---

### 另外增加的一个灵活性：一维数组模式控制

代码不仅支持这个完整的 **Treatment（反例修复）** 主流程，还能通过 `--mode baseline` 或 `--pipeline generate` 将流水线缩减为纯生成，用于产出论文所需的对照实验数据。