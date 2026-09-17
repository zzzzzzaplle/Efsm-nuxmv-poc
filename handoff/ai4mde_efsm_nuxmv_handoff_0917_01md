# ai4MDE：EFSM + nuXmv + FSM-Bench-20 交接文档

> 更新时间：2026-09-17  
> 当前技术进度：已跑通 `手写 EFSM JSON → SMV → nuXmv/CTL`  
> 当前研究优先级：为 FSM-Bench-20 的 `vending_machine` 建立独立的 Gold EFSM、冻结 CTL 与最终代码测试 Oracle

---

## 1. 研究方向与当前核心 RQ

研究暂定名称：**基于形式化验证的高可信代码生成方法**。

设想中的完整流程：

```text
自然语言需求
→ LLM生成EFSM设计模型
→ 结构与语义检查
→ 转换为nuXmv模型
→ 使用CTL验证关键性质
→ 验证失败时根据反例修复EFSM（暂定最多3轮）
→ 从EFSM生成代码
→ 使用隐藏功能测试评价最终代码
```

已经明确且不可偏离的核心研究问题：

> **在其他条件相同的情况下，加入“形式化验证＋反例驱动修复”，能否提高最终生成代码的功能正确性？**

因此，形式化验证只是中间干预；最终评价对象必须是生成代码的功能正确性，不能只报告模型是否通过nuXmv。

---

## 2. 当前已冻结的技术选择

- 设计模型：暂定 **EFSM**。
- 性质语言：暂定 **CTL**。
- 模型检查器：**nuXmv**。
- 中间表示：轻量 EFSM JSON。
- 最终目标语言：当前仍以 **Java** 为主要方向。
- 修复策略：验证失败后，最多进行3轮自动反例驱动修复。
- CTL在主实验运行前必须冻结，修复模型不能删除、修改或弱化CTL。
- 正式结论必须落在最终代码测试上。
- 当前先做可行性与单系统pilot，不批量改造全部20个系统。

注意：EFSM JSON不是nuXmv的强制输入格式。它只是本项目为了连接LLM、语义检查、nuXmv和代码生成而设计的可控中间表示。论文中应将它描述为实现选择，而不是形式化验证理论要求。

---

## 3. 仓库与 Benchmark 位置

GitHub仓库：

- [zzzzzzaplle/Efsm-nuxmv-poc](https://github.com/zzzzzzaplle/Efsm-nuxmv-poc)

FSM-Bench-20已经被用户下载并推送到该仓库，目录为：

```text
llm-fsm-local-benchmark-v1.1.0/
└── cesar-andress-llm-fsm-local-benchmark-66b81c2/
```

其核心目录：

```text
dataset/
├── index.json
└── systems/                  # 20个系统的自然语言需求

benchmark/
└── gold/                     # 当前均为 {} 占位符

docs/
├── gold_standard_strategy.md
└── evaluation_protocol.md
```

当前试点系统：

```text
dataset/systems/vending_machine.json
```

---

## 4. 已完成的最小技术PoC

### 4.1 nuXmv

- 已安装并运行nuXmv 2.2.0官方示例。
- 已能通过命令行读取生成的SMV文件并验证CTL。

### 4.2 现有EFSM Schema

文件：

```text
schema/efsm.schema.json
```

主要字段：

- `name`
- `initialState`
- `states`
- `events`
- `variables`
- `transitions`
- `properties`

transition当前主要字段：

- `id`
- `source`
- `event`
- `guard`
- `target`
- `actions`

当前 `actions` 是变量赋值对象，而不是业务动作标签。

### 4.3 EFSM-to-SMV转换器

文件：

```text
src/efsm_to_smv.py
```

主要职责：

1. 使用JSON Schema检查结构；
2. 检查初始状态、source/target、事件、变量引用等语义关系；
3. 生成nuXmv SMV模型。

### 4.4 Dishwasher示例

已有：

```text
models/dishwasher.correct.json
models/dishwasher.faulty.json
```

正确模型已经通过：

```text
P1: AG (state = WASHING -> doorClosed = TRUE)
P2: AG (state = DRYING -> doorClosed = TRUE)
P3: EF state = COMPLETE
```

错误模型人为加入了WASHING状态下打开门的迁移，导致P1和P2同时失败。已经确认：同一个根因迁移可以导致多个性质失败，不能把多个false简单视为多个独立错误。

根因修复应删除或修正错误迁移，而不是只在下游迁移中把门重新关闭来掩盖错误传播。

### 4.5 尚未完成

- nuXmv反例结构化解析；
- LLM反例驱动修复；
- EFSM-to-Java；
- Java编译和隐藏JUnit；
- model-based testing；
- 完整Baseline/Treatment实验。

原计划下一步曾是EFSM-to-Java，但当前讨论后，优先级已经调整为：**先建立可用Benchmark Oracle，再继续代码生成闭环。**

---

## 5. Benchmark调研结论

### 5.1 LLM-FSM

LLM-FSM原本看起来最匹配，但没有找到可直接获得的公开Benchmark仓库或完整数据，因此暂时不能作为可复现实验基础。

### 5.2 AutoFSM与fsm2sv

用户找到：

- [mohamed/fsm2sv](https://github.com/mohamed/fsm2sv)

核对后应注意：该仓库不是AutoFSM完整开源实现，而是FSM YAML到SystemVerilog、Graphviz、测试平台和SVA的生成工具/相关后端。它适合硬件/SystemVerilog路线，不直接支撑当前Java软件FSM路线。

它可以作为未来确定性FSM-to-SystemVerilog后端的备选，但不应把由同一Candidate模型生成的testbench或SVA直接当作独立需求Oracle。

### 5.3 FSM-Bench-20

FSM-Bench-20目前是最适合立即适配的起点：

- 包含20个软件系统；
- 每个系统大约12–13条自然语言需求；
- 包含状态、事件、约束、禁止行为和时序关系；
- 更贴近软件FSM和Java代码生成方向；
- 原仓库明确规划了Gold FSM、需求追踪、禁止行为和MBT评估。

但需要准确表述其局限：

- 当前 `benchmark/gold/*.json` 仍是 `{}` 占位符；
- Benchmark没有现成、完成的Gold EFSM；
- 没有现成的Gold CTL；
- 没有能直接评价最终Java代码的完整隐藏测试；
- 任务规模较小，最终论文需要讨论外部有效性。

因此，本研究不是直接使用一个完整Benchmark，而是：

> **在保持FSM-Bench-20原始需求不变的前提下，构建一个可复现的形式化验证评测扩展。**

论文中可称为：

```text
an evaluation extension built on FSM-Bench-20
```

不能声称Gold EFSM和CTL是FSM-Bench-20作者已经正式发布的标准答案。

---

## 6. 当前对“改造Benchmark”的准确理解

不修改FSM-Bench-20的原始自然语言需求；原始Benchmark作为任务来源只读保存。

本项目另行增加：

| 产物 | 表达内容 | 是否提供给被测方法 |
|---|---|---:|
| `gold_efsm.json` | 完整的正确参考行为 | 否 |
| `gold_properties.json` | 冻结、人工审查的CTL性质 | Treatment使用 |
| `traceability.json` | 需求—迁移—性质—测试映射 | 否 |
| 隐藏测试 | 最终代码预期行为 | 否 |
| Candidate EFSM | LLM根据需求生成的待测设计模型 | 是 |

Gold EFSM是评测Oracle，不是生成阶段提供给LLM的答案。

Treatment可以使用冻结的CTL性质，但不能看到完整Gold EFSM，否则修复Agent可能直接复制标准模型，无法判断反例驱动修复本身的贡献。

---

## 7. 核心实验设计

主实验采用配对设计：

```text
同一份自然语言需求
→ 只生成一次初始Candidate EFSM
   ├─ Baseline：直接从该EFSM生成代码
   └─ Treatment：同一EFSM → nuXmv验证 → 反例驱动修复 → 生成代码
→ 两组运行完全相同的隐藏功能测试
```

必须控制：

- 两组使用完全相同的初始Candidate EFSM；
- 相同的代码生成器；
- 相同的模型和推理配置；
- 相同的代码生成提示模板；
- 相同的最终测试Oracle；
- 唯一主要差异是Treatment增加“形式化验证＋反例驱动修复”。

核心效果量可定义为：

```text
FV-Gain = CodePassRate(Treatment) - CodePassRate(Baseline)
```

不要分别为Baseline和Treatment重新生成初始EFSM，否则生成随机性会混淆形式化验证的因果作用。

nuXmv通过率、修复轮数和失败性质数量可以作为中间指标，但不能代替代码功能正确性。

---

## 8. Gold EFSM、Gold CTL与隐藏测试的区别

### 8.1 Gold EFSM

`gold_efsm.json` 表示系统完整的参考状态、事件、变量、迁移、guard、更新和可观察输出。

主要用于：

- 审查Candidate EFSM行为；
- 生成或辅助生成隐藏测试；
- 生成行为轨迹；
- 构造错误变异体；
- 验证Oracle能否识别典型错误。

### 8.2 Gold CTL property suite

主实验所说的“冻结的人工审查CTL”，可以理解为一套可信的Gold formal properties，但更严谨的说法是：

> **经过人工构建、独立审查并在实验前冻结的Gold CTL property suite。**

不要宣称它是绝对正确且完整的formal specification。CTL通常只覆盖选定的关键性质，多个不正确模型也可能同时满足这些性质。

例如：

```text
AG !(dispensingCoffee & dispensingTea)
```

只能保证不会同时分发两种饮料；一个“永远不分发任何饮料”的错误模型也可能满足它。

因此，验证通过只表示：

> Candidate EFSM在给定执行语义和环境假设下满足被检查的性质。

### 8.3 完整Gold Formalization

应显式包含：

```text
Gold Formalization
= Execution Semantics
+ Initial Conditions
+ Environment Assumptions
+ CTL Property Suite
```

必须提前规定：

- 动作在当前步还是下一步生效；
- 未处理事件是自循环、忽略还是非法；
- 输出是瞬时事件还是持久变量；
- guard和多个可用迁移如何选择；
- 是否要求确定性；
- 环境在哪些状态可以发送哪些事件；
- `Dispensing`通过什么事件结束。

### 8.4 隐藏测试

隐藏测试才是最终代码功能正确性的主要Oracle。

测试可以参考Gold EFSM生成，但不能只机械地从Gold EFSM生成。还应保留一部分由研究者直接依据自然语言需求编写的正向和负向测试，以减少Gold模型与测试共享同一种错误解释的风险。

---

## 9. 需求编号的当前决定

用户已经明确：实际实验运行时不需要R1、R2等需求编号。

结论：

- Candidate EFSM Schema不必强制包含需求编号；
- nuXmv、反例修复和代码生成都不依赖需求编号；
- 需求编号只建议保留在Gold Oracle的独立追踪文件中；
- 实验程序可以完全不读取 `traceability.json`。

建议形式：

```json
{
  "R3": {
    "transitions": ["T3"],
    "properties": ["P2"],
    "tests": ["pressCoffeeWithCredit"]
  }
}
```

保留它的原因是Oracle覆盖检查、人工审查、错误定位和论文可复现性，而不是方法运行需要。

---

## 10. FSM-Bench-20与现有Schema的主要差异

FSM-Bench-20原始输出Schema大致包含：

- `states`
- `initial_state`
- `events`
- `transitions`
- `forbidden_behaviours`

transition中的 `action` 是一个业务描述字符串。

现有项目Schema则有：

- `initialState`
- 显式变量；
- `actions`变量赋值对象；
- 内嵌 `properties`；
- 强制transition ID。

不能只做字段重命名。最关键的语义问题是区分：

```json
{
  "updates": {
    "credit": "FALSE"
  },
  "outputs": [
    "DISPENSE_COFFEE"
  ]
}
```

- `updates`：可翻译到nuXmv的状态变量赋值；
- `outputs`：代码测试能够观察的业务效果。

建议把CTL从Candidate EFSM中移出，存为独立 `gold_properties.json`，防止修复Agent通过修改性质获得“验证通过”。

`forbidden_behaviours` 更适合作为Oracle信息或有限反例轨迹，不应简单假定它和CTL一一等价。有限轨迹与CTL分支时序语义不是同一种东西。

---

## 11. 建议的Pilot目录

建议不要直接修改FSM-Bench-20原始目录，而是在项目中建立扩展目录，例如：

```text
benchmarks/
└── fsm_bench_20_fv/
    └── vending_machine/
        ├── requirements.json
        ├── semantics.md
        ├── oracle/
        │   ├── gold_efsm.json
        │   ├── gold_properties.json
        │   └── traceability.json
        ├── candidates/
        │   └── initial_efsm.json
        └── tests/
            └── hidden/
```

原始 `dataset/systems/vending_machine.json` 应保持不变。扩展目录中的 `requirements.json` 可以是固定副本或通过manifest引用原文件。

---

## 12. 下一对话的首要任务

当前不要批量处理20个系统，也不要立即接入LLM。

下一步应当围绕 `vending_machine` 完成：

### Step 1：核对仓库当前状态

```bash
git status
git log --oneline -5
find . -maxdepth 4 -type f | sort
```

确认FSM-Bench-20已经存在于当前分支，并读取：

```text
dataset/systems/vending_machine.json
docs/gold_standard_strategy.md
docs/evaluation_protocol.md
schema/efsm.schema.json
src/efsm_to_smv.py
```

### Step 2：先冻结执行语义

在编写Gold EFSM前，先确定：

1. 事件步进语义；
2. 输出表示方式；
3. 未处理事件语义；
4. guard冲突与迁移确定性；
5. 状态变量更新时机；
6. `DISPENSE_COMPLETE`等内部/外部事件如何触发。

结果记录在：

```text
benchmarks/fsm_bench_20_fv/vending_machine/semantics.md
```

### Step 3：确定EFSM Schema v2最小改动

重点不是追求通用大Schema，而是让vending machine能够同时支持：

- nuXmv验证；
- 以后确定性生成Java；
- 隐藏测试观察业务输出。

建议重点字段：

- `states`
- `initialState`
- `events`
- `variables`
- `transitions`
- `guard`
- `updates`
- `outputs`

需求编号不设为Candidate必填字段；properties从模型文件中解耦。

### Step 4：人工构建 `gold_efsm.json`

根据 `vending_machine.json` 的全部需求构建完整、确定、可执行的Gold EFSM。

Gold EFSM必须先通过：

- JSON Schema检查；
- Python语义检查；
- 确定性检查；
- 可达状态检查；
- 人工逐条需求审查。

### Step 5：构建并冻结 `gold_properties.json`

CTL性质独立存储，不能嵌入Candidate EFSM。每条性质至少包含：

```json
{
  "id": "P1",
  "kind": "CTL",
  "formula": "...",
  "description": "..."
}
```

需求编号可以放在 `traceability.json`，不必进入实验运行文件。

### Step 6：验证Gold自身一致性

将Gold EFSM转换为SMV，确认所有Gold CTL成立。但这只是基本一致性检查，不能证明Oracle绝对正确。

### Step 7：为Oracle做变异测试

对Gold EFSM制造典型错误：

- 删除迁移；
- 改错target；
- 反转guard；
- 删除update；
- 错误保留credit；
- 同时触发咖啡和茶输出；
- 在错误状态接受cancel或coin。

检查Gold CTL与隐藏测试能否发现这些错误，并报告mutation score或至少报告被检测比例。

完成单系统Pilot后，才能判断如何扩展到其余19个系统。

---

## 13. 需要避免的实验错误

1. 不要把Gold EFSM直接提供给Candidate生成或修复Agent。
2. 不要分别生成Baseline与Treatment的初始EFSM。
3. 不要允许Treatment修改或删除CTL。
4. 不要用Candidate EFSM自行生成的测试评价同一个Candidate。
5. 不要把“nuXmv全部true”表述为系统完全正确。
6. 不要把所有Gold测试都从同一个Gold EFSM机械生成。
7. 不要把FSM-Bench-20未完成的Gold占位符说成官方已发布Gold答案。
8. 不要在执行语义未冻结前批量转换20个系统。
9. 不要把需求编号变成被测方法不必要的强制输出。
10. 不要把有限 `forbidden_behaviours` 直接等同于CTL性质。

---

## 14. 当前研究结论边界

当前只证明：

- 轻量EFSM JSON可以转换为SMV；
- nuXmv能够检查预设CTL；
- 人为错误可以产生反例；
- 一个根因可能导致多个性质失败；
- FSM-Bench-20可以作为需求来源，并允许我们扩展Gold Oracle。

当前尚未证明：

- 反例驱动修复能够稳定修复LLM生成的EFSM；
- 修复后的EFSM会提升最终Java代码正确性；
- 人工Gold CTL覆盖全部自然语言需求；
- FSM-Bench-20上的收益能泛化到真实大型软件系统；
- 自动从需求生成CTL同样可靠。

---

## 15. 可直接粘贴给下一次对话的开场提示

```text
请读取这份交接文档，继续“基于形式化验证的高可信代码生成”研究。核心RQ已经固定为：在其他条件相同的情况下，加入“形式化验证＋反例驱动修复”，能否提高最终生成代码的功能正确性？

不要重新讨论是否使用EFSM、CTL和nuXmv，也不要批量处理全部FSM-Bench-20。当前首要任务是基于仓库中的 FSM-Bench-20 `vending_machine.json`，设计并实现第一个 `gold_efsm.json`。

开始前先读取仓库中的原始需求、gold_standard_strategy.md、evaluation_protocol.md、现有efsm.schema.json和efsm_to_smv.py。然后先和我确认执行语义，尤其是输出、变量更新、未处理事件和迁移确定性；之后再最小化升级Schema并构建Gold EFSM。

需求编号不是Candidate EFSM的必填输入，只在独立traceability.json中用于Oracle审查。Gold EFSM不能提供给生成或修复Agent。主实验使用冻结、人工审查的gold_properties.json进行nuXmv验证，Baseline和Treatment必须共享完全相同的初始Candidate EFSM，最终使用相同隐藏测试评价生成代码。
```

