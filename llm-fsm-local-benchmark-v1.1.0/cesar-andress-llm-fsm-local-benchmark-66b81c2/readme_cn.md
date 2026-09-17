## 仓库目录
llm-fsm-local-benchmark/
├── dataset/                     # 包含 20 个软件系统的自然语言需求描述
│   ├── index.json               # 20 个系统的索引列表
│   └── systems/                 # 20 个 JSON 文件（vending_machine, atm, elevator 等）
├── benchmark/                   # 基准评估基准文件
│   └── gold/                    # 规划放置作者认可的标准 Ground Truth FSM（目前为 {} 占位符）
├── docs/                        # 详细的架构与评估策略文档
│   ├── gold_standard_strategy.md# 黄金标准（Gold Standard）建立规范与验证策略
│   └── evaluation_protocol.md   
└── README.md                    # Benchmark 官方说明文档

## 论文信息
### 标题
FSM-Bench-20: A Reproducible Benchmark for Deterministic Finite State Machine Generation from Natural-Language Requirements Using Local Open-Source LLMs

### 分类
CCF-B. IST（Information and Software Technology）

### 进度
v1.1.0（2026-07，即当前版本）：针对 IST 审稿人意见的 Major Revision（大修）复现包。重点补齐了 Guard-Aware Determinism（感知守卫条件的确定性判定工具）

### 核心RQ
核心研究问题（RQ）与假设（见 docs/evaluation_protocol.md）
论文设立了 6 个核心研究问题（RQ1 ~ RQ6），主要想探究：

RQ1（准确性）：开源 LLM 从纯文本需求生成“确定性状态机”的真实准确率有多高？
RQ2（覆盖率）：面对不同领域的系统需求，各模型的需求覆盖率如何？
RQ3（失误模式）：模型有多大概率会产生格式崩溃（非法 JSON）、非确定性冲突（同一输入不知道跳去哪）、或者凭空捏造转移（幻觉/Unsupported transitions）？
RQ4（结构化输出）：开启强制 JSON Schema 约束到底能带来多大收益？

RQ6（领域难度）：哪类系统最难？（论文假设：像并发复杂的电梯系统远比简单的售货机更难让模型搞对）。

### 实验设计(见config.py)
qwen2.5-coder:7b / qwen2.5-coder:14b / qwen2.5-coder:32b
llama3.1:8b
mistral-nemo:12b
gemma2:9b
phi3:14b
实验规模：7 款模型 × 20 套系统需求 = 140 次基准推理

### 实验结果(见README.md)

质检门禁（Gate）	衡量指标	140 次测试通过率	现象与结论
G1 门禁	JSON 语法正确	98.6% (138/140)	极高：说明主流 LLM 输出合规 JSON 的语法能力已经非常成熟。
G2 门禁	符合 Schema 规范 & 状态引用闭包	78.6% (110/140)	开始掉队：有 20% 的模型出现了状态/事件名字引用未声明等结构错误。
M0 门禁	严格结构确定性（无重复迁移）	31.4% (44/140)	断崖式暴跌：仅不到 1/3 的状态机能满足基本的确定性！
M1 门禁	守卫感知确定性（Guard 互斥）	33.6% (47/140)	即使大修时引入了语义分析，通过率依然不足 34%。
需求覆盖率	需求点（R1~Rn）覆盖均值	69.2%	大量关键需求被漏掉或没建立迁移。
论文的核心故事总结： “表面光鲜，内里漏洞百出” —— 开源大模型虽然能生成漂亮、合规的 JSON 结构（98.6%），但在软件工程最关键的确定性迁移（Determinism）和逻辑完备性上普遍不及格（仅约 30% 合格）。

### 结论
这篇论文通过实验证明单纯靠 LLM 一次性生成状态机是不可靠的

## 重要文档
### docs/ 目录下

## 需要改造 / 适配
1.原始benchmark相当于只提供了需求，然后运行脚本，大模型生成fsm，最后对fsm进行测试/验证
2.它中间的FSM json schema的结构详情位于llm-fsm-local-benchmark-v1.1.0/cesar-andress-llm-fsm-local-benchmark-66b81c2/docs/experimental_prompts.md
这个prompt里面规定按照scripts/fsm_benchmark/schema.py定义的结构生成结果
    '''
    {
    "title": "FSMOutput",
    "type": "object",
    "required": ["states", "initial_state", "events", "transitions"],
    "properties": {
        "states": { "type": "array", "items": { "type": "string" } },
        "initial_state": { "type": "string" },
        "events": { "type": "array", "items": { "type": "string" } },
        "transitions": {
        "type": "array",
        "items": {
            "type": "object",
            "required": ["source", "event", "target"],
            "properties": {
            "source": { "type": "string" },
            "event": { "type": "string" },
            "guard": { "type": "string", "default": "" },
            "action": { "type": "string", "default": "" },
            "target": { "type": "string" },
            "requirement": { "type": "string", "default": "" }
            }
        }
        },
        "forbidden_behaviours": {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
            "trace": { "type": "array", "items": { "type": "string" } },
            "reason": { "type": "string", "default": "" },
            "requirement": { "type": "string", "default": "" }
            }
        }
        }
    }
    }
    '''
3.此 Benchmark 只是一个**“自然语言描述型 FSM”**。比如它的动作是 action: "Store one credit"（一串英文句子），没有变量声明，nuXmv 根本不知道要把哪个变量从 0 变成 1，形式化验证直接瘫痪。
4.接下来做法: