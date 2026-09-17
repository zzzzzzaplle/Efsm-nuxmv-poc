## 核心文档
- `semantics.md`：是自动售货机（vending_machine）的形式化执行语义契约规范（Execution Semantics Specification）
该文档规定的 6 大核心语义内容：
1.**步进执行语义（Step Semantics，第 2 节）：**
        明确了系统配置（Configuration）= 控制状态 + 变量当前值；
        每一拍环境至多供给一个事件（无事件时为 NONE）；
        状态更新原则：迁移触发后，updates 在下一拍生效；未在 updates 中提及的变量严格保持原值；
        空转（Stuttering）语义：若当前状态遇到未匹配事件，保持当前状态与变量完全不变，不产生任何输出。

2.**状态与变量含义(State and Transaction Meaning，第 3 节)**
        明确定义了三个核心状态下的变量真值：
        Idle：creditStored = FALSE, selectedDrink = NONE；
        CreditAvailable：creditStored = TRUE, selectedDrink = NONE；
        Dispensing：creditStored = TRUE（保持直到出货完成），selectedDrink 必须是 COFFEE 或 TEA。
3.**输出效应语义（Output Semantics，第 4 节）：**
        将业务输出（如 DISPENSE_COFFEE、RETURN_COIN、REJECT_COIN）定义为瞬时可观测事件（Instantaneous Observable Effects），用于后续代码测试和断言。
4.**未指明事件的处理策略（Unspecified Events，第 5 节）：**
        坚决杜绝人工脑补无关迁移，非需求显式规定的输入统一走 Stuttering 默认规则。
5.**核心不变式（Required Invariants，第 6 节）：**
        为后续编写独立的 gold_properties.json（CTL 性质）提前拟定草案（如：洗涤/出货必须有信用、单次交易绝不同时出咖啡和茶等）。
6.**禁止行为解释（Forbidden Trace Interpretation，第 7 节）：**
解释了负向测试轨迹（forbidden_behaviours）的具体判定准则。


- `oracle/gold_efsm.json`：是根据 `semantics.md` 手写的黄金标准 Efsm 模型，完全兼容 Efsm-JsonSchema