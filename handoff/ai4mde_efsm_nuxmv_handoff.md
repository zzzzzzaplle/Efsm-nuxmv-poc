# ai4MDE：EFSM + nuXmv 形式化验证 PoC 交接文档

> 更新时间：2026-09-16  18:06 北京时间
> 当前阶段：已跑通 `EFSM JSON → SMV → nuXmv`；下一步实现 `EFSM JSON → Java 骨架 → javac`

## 1. 项目目标

研究暂定方向：**基于形式化验证的代码生成方法**。

当前希望验证的主链路：

```text
自然语言需求
→ LLM生成EFSM设计模型
→ JSON Schema与语义检查
→ EFSM-to-SMV
→ nuXmv执行CTL验证
→ 验证失败时将反例反馈给LLM（最多3轮）
→ 从验证通过的EFSM生成Java受保护行为骨架
→ LLM只填充业务代码
→ 编译与隐藏JUnit/后续MBT测试
```

当前优先目标不是完整论文实验，而是确认这条工程主链路确实可行。正式实验组、统计分析、3–5个pilot任务和model-based testing细节后置。

## 2. 已做好的研究决定

- 模型类型：暂定 **EFSM**。
- 性质语言：暂定 **CTL**。
- EFSM表示：自建轻量 JSON，而不是第一阶段直接引入复杂SysML工具链。
- 模型检查器：**nuXmv**。
- 目标语言：**Java**。
- CTL性质：正式运行前由人工审核并冻结；LLM不能通过删除或弱化性质来“修复”模型。
- 自动修复：验证失败最多3轮，运行期间不逐样本人工介入。
- 生成策略：状态、事件、迁移、guard等行为逻辑由规则生成并保护；LLM只填充业务实现。
- 核心研究问题：模型级形式化验证能否提升最终生成代码的功能正确性。
- 测试：当前先用人工依据需求编写的隐藏JUnit；model-based testing保留为后续方向。

## 3. 用户工作环境与协作偏好

- 主设备：Windows 11。
- 开发环境：WSL2 Ubuntu + VS Code WSL。
- Conda环境：`ai4mde`，Python 3.12。
- 用户可以阅读简单Java，Python相对薄弱，希望“边做边学、边学边做”。
- 后续应继续使用小步实施方式：每一步给出命令、成功标志、必要原理，不要一次讲过多理论。
- 用户还有一台Mac，需要通过GitHub同步继续开发。

进入环境：

```bash
conda activate ai4mde
cd ~/projects/efsm-nuxmv-poc
```

确认Python：

```bash
which python
```

预期类似：

```text
/home/zeqing/miniconda3/envs/ai4mde/bin/python
```

## 4. GitHub仓库

- 仓库：[zzzzzzaplle/Efsm-nuxmv-poc](https://github.com/zzzzzzaplle/Efsm-nuxmv-poc)
- WSL本地目录：`~/projects/efsm-nuxmv-poc`
- 仓库应保持私有或按用户当前设置管理。
- 不要提交：API Key、`.env`、Conda/venv环境、nuXmv二进制、`.class`文件。
- `.gitignore` 已创建。

注意：本对话环境无法直接加载GitHub页面，因此未核对远程仓库的最后一次commit。下一个对话开始时应先让用户执行：

```bash
git status
git log --oneline -5
```

不要假设最后一次提交和push已经完成。

## 5. 当前目录结构

已知结构大致为：

```text
efsm-nuxmv-poc/
├── .gitignore
├── architecture.md
├── requirements.txt
├── schema/
│   └── efsm.schema.json
├── models/
│   ├── dishwasher.correct.json
│   └── dishwasher.faulty.json
├── src/
│   └── efsm_to_smv.py
└── generated/
    ├── Dishwasher.smv
    ├── DishwasherFaulty.smv
    └── DishwasherFaulty.verification.txt
```

是否所有生成文件均已提交，需要通过 `git status` 确认。

## 6. 已完成进度

### 6.1 nuXmv安装与官方示例

安装位置：

```text
~/tools/nuxmv/nuXmv-2.2.0-linux64/
```

版本：nuXmv 2.2.0。

官方示例已成功运行：

```bash
nuXmv \
  "$HOME/tools/nuxmv/nuXmv-2.2.0-linux64/usr/local/share/nuxmv/examples/invgen/QF_BV/up-nested.c.smv" \
  | tail -n 1
```

成功输出：

```text
-- invariant __expr35  is true
```

### 6.2 最小EFSM JSON Schema

文件：`schema/efsm.schema.json`

主要字段：

- `name`
- `initialState`
- `states`
- `events`
- `variables`
- `transitions`
- `properties`

transition主要字段：

- `id`
- `source`
- `event`
- `guard`（可选）
- `target`
- `actions`（可选）

property当前仅允许：

```json
{
  "id": "P1",
  "kind": "CTL",
  "formula": "AG (...)"
}
```

JSON Schema只检查结构；状态、事件、变量引用等跨字段关系由Python语义检查完成。

### 6.3 Dishwasher正确EFSM

文件：`models/dishwasher.correct.json`

状态：

```text
IDLE, READY, WASHING, DRYING, COMPLETE
```

事件：

```text
CLOSE_DOOR, OPEN_DOOR, START, WASH_DONE, DRY_DONE, RESET
```

扩展变量：

```text
doorClosed : boolean，初始值 false
```

关键迁移：

```text
T1  IDLE     + CLOSE_DOOR → READY      / doorClosed = TRUE
T2  READY    + OPEN_DOOR  → IDLE       / doorClosed = FALSE
T3  READY    + START [doorClosed=TRUE] → WASHING
T4  WASHING  + WASH_DONE  → DRYING
T5  DRYING   + DRY_DONE   → COMPLETE
T6  COMPLETE + OPEN_DOOR  → IDLE       / doorClosed = FALSE
T7  COMPLETE + RESET      → READY
```

冻结的三条CTL性质：

```text
P1: AG (state = WASHING -> doorClosed = TRUE)
P2: AG (state = DRYING -> doorClosed = TRUE)
P3: EF state = COMPLETE
```

含义：

- P1：所有路径的所有时刻，洗涤时门必须关闭。
- P2：所有路径的所有时刻，烘干时门必须关闭。
- P3：至少存在一条路径可以完成洗涤流程。

P3只是可达性，不是“每次启动后最终必然完成”。更强活性性质需要公平性假设，当前PoC暂不扩张。

### 6.4 EFSM-to-SMV转换器

文件：`src/efsm_to_smv.py`

职责分为三层：

1. `validate_structure()`：使用JSON Schema检查格式。
2. `validate_semantics()`：检查初始状态、source/target、event、action变量引用等关系。
3. `generate_smv()`：生成nuXmv SMV模型。

运行命令：

```bash
python src/efsm_to_smv.py \
  models/dishwasher.correct.json \
  generated/Dishwasher.smv
```

验证命令：

```bash
nuXmv generated/Dishwasher.smv \
  | grep -- "-- specification"
```

已得到：

```text
-- specification AG (state = WASHING -> doorClosed = TRUE)  is true
-- specification AG (state = DRYING -> doorClosed = TRUE)  is true
-- specification EF state = COMPLETE  is true
```

因此正确模型满足当前冻结的P1–P3。不能表述为“模型绝对正确”，只能表述为“满足被检查的性质”。

### 6.5 人为错误模型与错误传播

文件：`models/dishwasher.faulty.json`

人为加入：

```json
{
  "id": "T8",
  "source": "WASHING",
  "event": "OPEN_DOOR",
  "target": "WASHING",
  "actions": {
    "doorClosed": "FALSE"
  }
}
```

错误路径：

```text
IDLE，门开
→ CLOSE_DOOR
READY，门关
→ START
WASHING，门关
→ OPEN_DOOR（T8）
WASHING，门开       ← 违反P1
→ WASH_DONE
DRYING，门仍然开    ← 违反P2
```

验证结果：

- P1：false
- P2：false
- P3：true

P2失败原因：T4没有更新 `doorClosed`，因此SMV的默认分支 `TRUE : doorClosed` 保留了FALSE值，错误传播到DRYING。

关键研究认识：一个错误transition可能导致多条性质同时失败；不能把多个false简单当作多个独立错误。

### 6.6 根因修复与下游补救的区别

用户已经正确理解：若给T4增加 `doorClosed := TRUE`，P2会恢复为true。

但该修复只属于下游补救：

| 修复 | P1 | P2 | 判断 |
|---|---:|---:|---|
| T4强制关门 | false | true | 掩盖传播，根因仍在 |
| 删除/修正T8 | true | true | 根因修复 |

当前最小PoC的正确根因修复是删除T8，使WASHING状态下的OPEN_DOOR没有有效迁移。另一种设计是进入ERROR状态，但这属于新的需求决策，暂不引入。

正式LLM修复不能只追求“性质变true”，还需要：

- 不允许修改、删除或弱化冻结的CTL性质；
- 优先消除反例的根因transition；
- 检查是否引入新的行为偏差；
- 最多自动修复3轮。

## 7. 尚未完成的原始任务

最初8项任务状态：

| 序号 | 任务 | 状态 |
|---:|---|---|
| 1 | 安装并运行nuXmv官方示例 | 已完成 |
| 2 | 定义最小EFSM JSON Schema | 已完成 |
| 3 | 手工编写Dishwasher EFSM | 已完成 |
| 4 | 实现EFSM-to-SMV | 已完成 |
| 5 | 验证正确模型和人为错误模型 | 已完成 |
| 6 | 实现EFSM-to-Java骨架 | **未开始** |
| 7 | 确认Java骨架可编译 | **未开始** |
| 8 | 接入LLM生成、修复和业务代码填充 | **未开始，必须最后做** |

此外，nuXmv反例日志尚未实现结构化解析；当前只是保存原始日志并人工阅读。

## 8. 下一对话的直接起点

### 8.1 先核对仓库

让用户运行：

```bash
conda activate ai4mde
cd ~/projects/efsm-nuxmv-poc
git status
git log --oneline -5
find . -maxdepth 3 -type f | sort
```

若当前进度未提交：

```bash
git add .
git commit -m "feat: generate and verify dishwasher SMV models"
git push
```

提交前确认没有API Key、`.env`、nuXmv压缩包或二进制。

### 8.2 然后实现EFSM-to-Java

建议新文件：

```text
src/efsm_to_java.py
```

建议输出：

```text
generated/java/Dishwasher.java
```

第一版生成内容至少包括：

- `State` enum；
- `Event` enum；
- `state`字段和EFSM变量字段；
- 构造后的初始值；
- `handle(Event event)`或等价dispatcher；
- 按source/event/guard生成的迁移逻辑；
- action赋值；
- 状态和变量getter；
- 默认无迁移时保持状态；
- 可供LLM填充的受控业务hook。

建议保护策略：

- dispatcher由规则生成，声明为 `final`，LLM不得修改；
- 业务扩展通过 `protected` hook完成；
- 第一版hook可以默认no-op，使骨架无需业务实现即可编译；
- 后续可考虑“生成基类 + LLM业务子类”，进一步隔离规则行为和业务实现。

第一版不要为了通用性过度设计。先支持当前Schema中的boolean和有界integer、简单guard/action表达式即可。

### 8.3 编译验证

先确认：

```bash
javac -version
```

生成后执行：

```bash
mkdir -p generated/classes
javac -d generated/classes generated/java/Dishwasher.java
```

成功标准：命令无错误退出，并能在 `generated/classes` 下看到 `.class` 文件。

### 8.4 Java完成后再做的内容

1. 写最小Java smoke test，按事件序列检查状态变化。
2. 将nuXmv原始反例解析成结构化JSON，例如：失败性质、状态序列、输入事件、变量变化、疑似相关transition。
3. 冻结CTL性质，将结构化反例提供给LLM修复EFSM。
4. 限制最多3轮修复。
5. 验证通过后从EFSM重新生成Java骨架。
6. 最后才让LLM填充业务hook，并运行隐藏JUnit。

## 9. 当前实现的已知限制

- guard和action目前基本以字符串形式传入SMV，尚未建立严格表达式AST或安全DSL。
- JSON Schema不能检查transition引用的状态/事件是否真实存在，所以依赖Python语义检查。
- transition按JSON顺序生成到SMV `case`，存在隐含的“从上到下优先级”语义，后续应显式记录或限制冲突迁移。
- 当前P3只是 `EF COMPLETE`，不是强活性保证。
- 尚未自动解析nuXmv counterexample。
- 当前只验证了一个Dishwasher案例，不能据此声称方法具有普遍有效性。
- 正式实验还需要3–5个pilot任务、baseline、隐藏测试、统计分析等。

## 10. 给下一位助手的执行要求

1. 不要重新讨论或推翻已冻结的EFSM + CTL + nuXmv轻量方案，除非实际实现出现阻断。
2. 不要提前接入LLM；先完成Java生成与编译闭环。
3. 继续采用“边做边学”，但不要让教学拖慢实施。
4. 每一步给用户明确的命令、预期输出和失败排查方式。
5. 区分：Schema错误、EFSM语义错误、CTL性质失败、Java编译失败、业务测试失败。
6. 不要允许LLM通过修改冻结性质来获得验证通过。
7. 所有结论只说到证据支持的范围，例如“满足P1–P3”，不要说“系统完全正确”。

## 11. 可直接粘贴给下一对话的开场提示

```text
请读取这份交接文档并继续 ai4MDE 的 EFSM + nuXmv PoC。不要重做已完成的1–5步。先让我运行 git status、git log --oneline -5 和 find 命令核对仓库，然后从第6步“EFSM-to-Java受保护骨架生成”继续。请保持边做边学的方式：直接给可运行代码和命令，同时只解释当前最关键的概念。Java骨架编译通过后，再做反例结构化与LLM修复；LLM最多修复3轮，不能修改冻结的CTL性质。
```
