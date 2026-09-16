efsm-nuxmv-poc/
├── schema/       JSON格式约束
├── models/       Dishwasher模型(洗碗机)
├── src/          Python转换程序
└── generated/    生成的SMV和Java


src/efsm_to_smv.py
 是一个模型转换脚本。它的核心作用是将基于 JSON 格式定义的 EFSM（扩展有限状态机，Extended Finite State Machine）模型，校验并自动转换成 nuXmv 形式化模型检测器所使用的 SMV 语言模型文件。