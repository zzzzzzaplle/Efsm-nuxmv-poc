
通过 “EFSM JSON 描述 -> SMV 生成 -> nuXmv 自动化证明 -> 捕获反例 Trace”，形成了一套完整的状态机形式化规范与自动化检错闭环。



### generated(由转译器生成的SMV模型)
    -Dishwasher.smv
    由dishwasher.correct.json自动转换生成。完整定义了洗碗机状态（IDLE, READY, WASHING, DRYING, COMPLETE）、门状态变量（doorClosed）以及合法迁移
    末尾定义了 3 个待检验的 CTL 时序逻辑规范 
    P1：AG (state = WASHING -> doorClosed = TRUE)（洗涤过程中门必须始终关着）
    P2：AG (state = DRYING -> doorClosed = TRUE)（烘干过程中门必须始终关着）
    P3：EF state = COMPLETE（可达性：系统存在能够完成清洗的执行路径）

    -Dishwasher.smv
    由dishwasher.fault.json自动转换生成，该文件在READY状态下定义了一个不合法的迁移（允许 OPEN_DOOR事件转移到WASHING状态），
    该迁移不包含显式的 guard 条件，导致状态机不安全。
    执行检查后，nuXmv 报告存在以下违例（VIOLATION）：
    state = READY & event = OPEN_DOOR（不安全转换）

    -DishwasherFault.verfi
## models(具体的系统模型实例)
    -dishwasher.correct.json
    该模型是一个结构良好且语义正确的洗碗机EFSM(扩展状态机)。它定义了完整的操作流程和状态转换，并包含安全约束。检查生成的 SMV 模型时，
    应该验证其状态机行为符合预期，并且所有安全属性都被正确编码。

    -dishwasher.fault.json
    该模型引入了一个明显的安全缺陷：在READY状态下，允许 OPEN_DOOR 事件转移到 WASHING 状态，且没有显式的 guard 条件来阻止这种不安全转换。
    这违反了现实世界洗碗机的安全逻辑（通常门必须在运行前关闭）。检查生成的 SMV 模型时，应该能够通过模型检测器识别出这个不安全的转换
## schema(状态机语法规范)
    -efsm.schema.json
    “状态机语法规范与契约”：定义了合法状态机的书写格式（如状态命名规则大写驼峰/下划线、事件数组、变量类型定义、迁移三元组及 CTL 逻辑规范等）。    
        