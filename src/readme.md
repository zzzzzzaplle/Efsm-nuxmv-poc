**efsm_to_smv.py**
 是一个模型转换脚本。它的核心作用是将基于 JSON 格式定义的 EFSM（扩展有限状态机，Extended Finite State Machine）模型，校验并自动转换成 nuXmv 形式化模型检测器所使用的 SMV 语言模型文件。

主要功能模块与流程
整个脚本的工作流程主要包含以下四个部分：

1.结构校验（Schema Validation）
validate_structure()：使用 jsonschema 按照 schema/efsm.schema.json
 对输入的 EFSM JSON 进行结构和格式规范性校验。

2.语义校验（Semantic Validation）
validate_semantics()：检查 Schema 无法约束的业务逻辑与状态机语义一致性：
initialState 是否在 states 集合内；
迁移的 id 是否存在重复；
迁移的 source、target 状态是否存在；
触发的 event 是否已声明；
迁移的 actions 修改的变量是否在 variables 中声明。

3.SMV 规则代码生成（Code Generation）
generate_smv() 与 transition_condition()：
变量映射：将事件集合映射为 SMV 输入变量 IVAR event : {NONE, ...};；将状态和数据变量映射为 VAR state 与范围变量（如 boolean 或 min..max）。
状态转移：基于当前 state、event 与 guard（守卫条件）构建 ASSIGN next(state) := case ... esac;。
数据变量更新：将迁移上的 actions 翻译为相应变量的 next(var) 赋值逻辑。
性质规格（Properties）：将模型中的待验证性质转换为 nuXmv 的 CTLSPEC 计算树逻辑公式。

4.CLI 命令行入口
main()：提供命令行接口，支持传入输入 JSON 路径、目标 SMV 输出路径以及 Schema 文件路径。


5.典型使用方式
在终端中执行如下命令将 EFSM 模型转换为 SMV 模型：
bash
python3 src/efsm_to_smv.py models/dishwasher.json generated/dishwasher.smv
