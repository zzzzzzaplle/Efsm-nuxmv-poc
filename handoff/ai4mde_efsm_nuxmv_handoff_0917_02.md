# EFSM–nuXmv 研究项目交接文档

更新日期：2026-09-17  
代码仓库：<https://github.com/zzzzzzaplle/Efsm-nuxmv-poc>  
核对分支：`main`  
核对提交：`7c1633753e9f97c983ec4b8eef5a387bfdd01eff`  
当前主线：FSM-Bench-20 中 `vending_machine` 的单系统 Pilot

## 1. 研究目标

核心研究问题是：

> 在由自然语言需求生成软件的流程中，引入形式化验证与反例驱动的 EFSM 修复，能否提升最终生成代码的功能正确性？

计划中的完整链路为：

```text
自然语言需求
→ LLM 生成 Candidate EFSM JSON
→ Schema 与语义校验
→ EFSM 转换为 SMV
→ 使用冻结的 CTL 性质运行 nuXmv
→ 提取失败性质与反例
→ LLM 修复 Candidate EFSM（最多3轮）
→ 生成最终代码
→ 隐藏功能测试
```

研究的最终结论必须基于生成代码在隐藏功能测试中的表现，而不是仅依据 CTL 通过率。

## 2. 已冻结的实验原则

1. **Gold EFSM 只作为评测 Oracle。** 不得把 `gold_efsm.json` 提供给生成 Agent 或修复 Agent。
2. **CTL 性质独立存放并提前冻结。** 修复 Agent 可以看到失败性质和反例，但不能修改性质文件。
3. **Baseline 与 Treatment 必须共享同一个初始 Candidate。** 对每次实验先生成并保存 `Candidate_0`，然后分支：
   - Baseline：不进行形式化修复；
   - Treatment：最多进行3轮 nuXmv 反例驱动修复。
4. **需求编号只用于追踪和人工审查。** 不把需求编号当作 EFSM 的运行语义。
5. **正式效果评价使用隐藏测试。** nuXmv 结果是中间干预与诊断信号，不是最终正确性的替代指标。
6. 当前只完成并验证了 `vending_machine` Pilot，尚不能声称 FSM-Bench-20 的20个系统都已完成改造。

## 3. Benchmark 与 Schema 状态

已选择 FSM-Bench-20 作为研究基准，并以它原有的 Pydantic/FSM 输出结构为母版，扩展为可执行 EFSM IR。

当前 EFSM Schema 的核心字段包括：

- `states`
- `initial_state`
- `events`
- `variables`
- `transitions`
- transition 中的 `source`、`event`、`guard`、`updates`、`outputs`、`target`
- `forbidden_behaviours`

已经做出的关键决定：

- 放弃旧字段兼容，仅保留 `initial_state` 和 `updates`；
- `properties` 不嵌入 Candidate EFSM，使用独立性质文件；
- `action` 可用于人类阅读，但形式化执行以结构化的 `updates` 和 `outputs` 为准；
- 复杂的变量跨字段类型校验暂未作为 Pilot 的前置阻塞项，批量运行前应补强。

Schema 具备表达 FSM-Bench-20 各系统“有限状态抽象”所需的基础能力，但这不等同于已经忠实建模全部20个完整软件系统。

## 4. vending_machine Gold Oracle

Gold EFSM 和执行语义已经完成审查并进入 `main`。

关键文件：

- `benchmarks/fsm_bench_20_fv/vending_machine/oracle/gold_efsm.json`
- `benchmarks/fsm_bench_20_fv/vending_machine/oracle/gold_properties.json`
- `benchmarks/fsm_bench_20_fv/vending_machine/semantics.md`
- `benchmarks/fsm_bench_20_fv/vending_machine/system_interface.json`

Gold 模型的主要内容：

| 项目 | 内容 |
|---|---|
| 状态 | `Idle`、`CreditAvailable`、`Dispensing` |
| 输入事件 | 5种业务事件，另有环境静止选择 `NONE` |
| 变量 | `creditStored:boolean`、`selectedDrink:{NONE,COFFEE,TEA}` |
| 显式迁移 | 12条需求驱动迁移 |
| 输出 | `DISPENSE_COFFEE`、`DISPENSE_TEA`、`RETURN_COIN`、`REJECT_COIN` |
| 需求 | R1–R13 |

已冻结的执行语义：

- 每一步环境选择一个事件；允许 `NONE`；
- guard 读取当前状态和当前变量；
- target 与 `updates` 在下一状态生效；
- `outputs` 是一次迁移产生的瞬时脉冲，不持久保存；
- 未匹配的状态—事件组合默认 stutter：状态和变量保持不变，不产生输出；
- 明确要求拒绝或忽略的事件使用显式自循环表达；
- 同一状态、事件和当前变量配置下最多启用一条迁移；
- 完成交易或取消时清除信用，并把所选饮料恢复为 `NONE`。

## 5. 形式化验证工具链现状

`EFSM JSON → SMV → nuXmv` 的 Pilot 工具链已经打通。

关键实现提交：

- commit：`e5d6e5381ff4538b66313f2cd2ef25e1d9e3a719`
- 链接：<https://github.com/zzzzzzaplle/Efsm-nuxmv-poc/commit/e5d6e5381ff4538b66313f2cd2ef25e1d9e3a719>

该提交涉及：

- `src/efsm_to_smv.py`
- `schema/system_interface.schema.json`
- `benchmarks/fsm_bench_20_fv/vending_machine/oracle/gold_properties.json`
- `benchmarks/fsm_bench_20_fv/vending_machine/system_interface.json`
- `generated/VendingMachine.smv`
- `generated/VendingMachine.verification.txt`
- `tests/test_output_encoding.py`
- 相关语义说明和使用文档

### 5.1 输出编码

转换器会把业务输出编码为组合式瞬时布尔信号：

```text
emit_DISPENSE_COFFEE
emit_DISPENSE_TEA
emit_RETURN_COIN
emit_REJECT_COIN
```

固定的 `system_interface.json` 声明合法输出全集。其作用包括：

- Candidate 完全遗漏某个输出时，相应信号仍被定义为 `FALSE`，CTL 会正常失败，而不是产生未定义符号；
- Candidate 使用拼写错误或未声明输出时，语义校验直接拒绝模型。

### 5.2 事件建模

nuXmv 不允许 CTL 公式直接引用输入变量，因此 `event` 没有使用 `IVAR`，而被编码为每一步非确定更新的状态变量：

```smv
init(event) := {NONE, ...};
next(event) := {NONE, ...};
```

它在执行语义上仍代表由环境每步选择的输入事件，但现在可在 CTL 中观察。

### 5.3 性质与验证结果

- 已建立22条独立 CTL 性质，覆盖 R1–R13、关键输出以及输出不应发生的范围；
- nuXmv 2.0.0 已成功执行生成的 `VendingMachine.smv`；
- 22/22 条性质全部为 true；
- 输出编码单元测试 4/4 通过；
- mutation test 把 `emit_RETURN_COIN` 强制改为 `FALSE` 后，性质 P10 失败并产生反例，证明输出错误确实能被工具链检测。

因此，早期“Gold 已记录 outputs，但转换器尚未编码 outputs”的边界已经解决，不再是当前待办项。

## 6. 最新 GitHub 状态

在输出感知形式化验证提交之后，`main` 增加了4个与实验编排相关的提交：

| Commit | 内容 |
|---|---|
| `95f213c` | 新增主实验 Python 脚本 |
| `816edfdd` | 增加可运行配置、样本目录和跨平台 nuXmv 探测等 |
| `4feb5157` | 修复转译器路径、显式传入3类 Schema、处理求解器失败，并把 guard 中 `==` 规范化为 SMV 的 `=` |
| `7c163375` | 完善静态接口契约、逻辑表达式清洗、多模型运行目录和日志，并提交成功的生成/验证/修复运行证据 |

新增的主要文件和目录：

- `scripts/run_pilot_experiment.py`
- `scripts/README.md`
- `requirements.txt`
- `runs/vending_machine/sample_1/`

脚本目前已经实现以下代码路径：

```text
自然语言需求
→ OpenAI-compatible Chat Completions API
→ 提取 Candidate EFSM JSON
→ 调用 efsm_to_smv.py
→ 加载冻结的 Gold CTL 和 system interface
→ 调用 nuXmv
→ 解析 true/false 与反例文本
→ 调用 LLM 修复
→ 最多3轮
→ final_efsm.json
```

它还支持：

- `treatment` 与 `baseline` 两种模式；
- 通过 `ACTIVE_BENCHMARK_SYSTEMS` 或 `--systems` 选择系统；
- 自动建立 `runs/<system>/sample_N`；
- 命令行、环境变量、PATH 和工具目录等多种 nuXmv 定位方式；
- 为候选、SMV、验证日志和 summary 建立运行产物。

## 7. 当前运行证据与准确结论

旧目录 `runs/vending_machine/sample_1` 中确实保留过路径错误记录，但它已经被后续成功运行取代，不能再代表当前工具链状态。

### 7.1 真实反例修复样本

目录：

```text
runs/vending_machine/sample_2_qwen3.7-flash/
```

运行模型为 `qwen/qwen3.7-flash`，结果为：

| 轮次 | CTL通过 | CTL失败 | 结果 |
|---|---:|---:|---|
| round 0 | 18 | 4 | 发现信用取消后未清除 `creditStored` 等问题 |
| round 1 | 22 | 0 | LLM 根据反例修复并收敛 |

初始 Candidate 的 `CreditAvailable + cancel → Idle` 迁移只输出 `RETURN_COIN`，却没有把 `creditStored` 更新为 `false`。nuXmv 因此为4条性质产生反例。修复后的 Candidate 在该迁移中加入：

```json
"updates": {
  "creditStored": "false",
  "selectedDrink": "NONE"
}
```

随后22条性质全部通过。这是一份真实的：

```text
自然语言需求 → LLM Candidate → nuXmv反例 → LLM修复 → 再验证通过
```

端到端证据。

### 7.2 另外3个首轮通过样本

目录：

```text
runs/qwen3.7-flash/vending_machine/sample1
runs/qwen3.7-flash/vending_machine/sample2
runs/qwen3.7-flash/vending_machine/sample3
```

这3个 Candidate 均在 round 0 直接通过22/22条 CTL，因此没有进入修复轮。

因此目前可以准确地说：

> Benchmark、Gold Oracle、输出敏感 EFSM→SMV→nuXmv 工具链已经完成；LLM 生成—验证—反例修复编排已在 `vending_machine` 上真实跑通，并至少有一例从18/22修复到22/22。

目前不能说：

- Baseline 与 Treatment 已满足配对实验要求；
- 已完成最终代码生成和隐藏测试；
- CTL 22/22 已证明 Candidate 与自然语言需求完全等价；
- 单次修复成功已证明方法在统计上有效；
- 已完成 FSM-Bench-20 全部20个系统。

## 8. 已解决的接口词汇问题

`7c163375` 已把 `system_interface.json` 从仅声明输出扩展为公共静态建模契约，现包含：

- 状态：`Idle`、`CreditAvailable`、`Dispensing`；
- 初态：`Idle`；
- 事件：`insert_coin`、`press_coffee`、`press_tea`、`cancel`、`dispense_complete`；
- 变量：`creditStored:boolean`；
- 变量：`selectedDrink:{NONE,COFFEE,TEA}`；
- 4种业务输出。

初始生成 prompt 和 repair prompt 都注入这份接口契约，要求 LLM 不得偏离这些签名。因此，之前 `credit` vs `creditStored`、`press_cancel` vs `cancel` 导致 CTL 无法引用的问题已解决。

这项设计需要在论文中准确描述：系统接口向 Candidate 暴露了状态、事件和变量词汇，但没有暴露正确迁移、guard、update 或 output 组合。它降低了“从零发明模型词汇”的难度，评测对象更准确地说是：

> 在给定系统建模接口和自然语言需求的条件下，生成正确的 EFSM 行为逻辑。

Baseline 与 Treatment 都必须获得完全相同的接口契约。

## 9. 现有编排脚本仍需补强的实验问题

### 9.1 Baseline 与 Treatment 尚未真正共享 Candidate_0

当前分别运行 `--mode baseline` 和 `--mode treatment` 时，两者都会各自调用一次 LLM。因此即使 prompt 和 temperature 相同，也不能保证获得完全相同的初始 Candidate。

正确做法应是一次生成并冻结 `candidate_0.json`，再由一个 run manifest 同时分出：

- Baseline：复制该 Candidate，不修复；
- Treatment：从同一个文件开始验证和修复。

### 9.2 Schema/语义错误目前不会进入修复循环

转译失败时 `run_single_verification()` 返回0条 true、0条 false；主循环随后把它判定为工具流程失败并停止。因此代码虽然在 repair prompt 中预留了 validation error 字段，实际流程并不会让 LLM 修复 Schema/语义无效的初始模型。

应区分三类结果：

1. `INVALID_CANDIDATE`：JSON、Schema、语义或 SMV 生成失败，可提供诊断并请求格式/语义修复；
2. `VERIFICATION_FAILED`：nuXmv 正常运行且性质为 false，可提供性质与反例修复；
3. `TOOL_ERROR`：路径、求解器崩溃或超时，不应消耗修复轮次。

### 9.3 修复 prompt 已有接口契约，但仍缺原始需求

当前修复 prompt 已包含上一版 Candidate、失败详情和完整 `system_interface.json`，但没有重新提供原始自然语言需求、完整 Schema 和执行语义。修复 Agent 仍可能只针对反例局部打补丁，而不是同时维护全部需求。

### 9.4 运行记录仍不够完整

当前主要保存 Candidate、SMV、文本日志和简要 summary；还应保存：

- 初始及每轮 repair prompt；
- LLM 原始响应；
- 每条性质的结构化结果；
- 明确的错误分类；
- API 模型、temperature、seed（若支持）、token 和延迟；
- 仓库 commit、Schema/CTL/interface 文件哈希、nuXmv 版本；
- Candidate_0 的哈希以及 Baseline/Treatment 对同一文件的引用。

### 9.5 密钥配置方式

脚本允许把 API key 直接写进源码。即使当前仓库中的值为空，也不应把真实密钥提交到 Git。正式实验应优先使用环境变量或本机未跟踪配置文件。

### 9.6 缺少编排层自动测试

现有测试只覆盖 output encoding。还需要测试：

- LLM 返回非法 JSON；
- Schema/语义错误与工具错误分类；
- nuXmv true/false 解析；
- 反例只包含对应失败性质；
- 达到3轮后停止；
- 全部通过时提前停止；
- Baseline 与 Treatment 的 Candidate_0 哈希完全相同；
- 生成/修复路径从不读取 `gold_efsm.json`。

## 10. 下一位助手的优先任务

如果用户要求继续实现，建议严格按以下顺序：

1. 先从 GitHub `main@7c163375` 或更新提交开始，检查用户是否又有新提交；
2. 改成“一次生成 Candidate_0，再分叉 Baseline/Treatment”，首先保证配对实验有效；
3. 把运行结果改成 `INVALID_CANDIDATE / VERIFICATION_FAILED / TOOL_ERROR / PASSED` 等结构化状态；
4. 让 Schema/语义错误可以被修复，但工具错误不能进入 LLM 修复；
5. 在修复 prompt 中补回原始需求和必要执行语义；
6. 保存 prompt、原始响应、结构化性质结果、哈希与运行元数据；
7. 统一旧运行目录与新目录命名，修复 summary 内仍指向重命名前绝对路径的问题；
8. 增加编排层单元测试和故意缺陷 Candidate 的稳定集成测试；
9. 完成上述实验工程加固后，再进入 EFSM→Java 与隐藏测试阶段。

当前不应优先做：

- 扩展全部20个系统；
- 重新设计已冻结的 vending machine Gold；
- 重新解决 outputs 编码；
- 把22/22 CTL直接等同于完整功能正确；
- 在配对实验公平性未解决前批量采样。

## 11. 推荐的最终运行产物结构

```text
runs/<run_id>/
  manifest.json
  requirements.json
  generation/
    prompt.json
    raw_response.json
    candidate_0.json
  baseline/
    candidate_0.json
    final_efsm.json
  treatment/
    round_0/
      candidate.json
      model.smv
      nuxmv_raw.txt
      verification_result.json
    round_1/
      repair_prompt.json
      raw_response.json
      candidate.json
      model.smv
      nuxmv_raw.txt
      verification_result.json
    ...
    final_efsm.json
  codegen/
  hidden_tests/
```

`manifest.json` 至少记录仓库 commit、Candidate_0 SHA-256、Schema/CTL/interface SHA-256、prompt 版本、LLM 配置、nuXmv 版本和各阶段状态。

## 12. 用户偏好与协作方式

- 用户希望研究设计保持严谨，但优先完成可运行的单系统 Pilot；
- 用户已经允许后续修改直接进入 `main`，不要求每次创建 PR；
- 在直接修改 `main` 前仍应检查最新提交和工作区状态，避免覆盖用户并行修改；
- 对进度描述应保持精确，清楚区分“基础能力具备”“Pilot 已完成”和“全 Benchmark 已完成”；
- 如果解释 Python 实现，应使用清晰的项目语境说明模块职责和实验公平性，不假设用户熟悉复杂 Python 工程模式。
