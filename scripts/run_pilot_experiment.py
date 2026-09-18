#!/usr/bin/env python3
"""
自动售货机主实验运行脚本 (Vending Machine Pilot Experiment Runner)

支持两类实验模式（由一维数组 pipeline_stages 控制）：
1. Treatment 模式: ["generate", "verify", "repair"]
   生成初版模型 -> nuXmv 形式化验证 -> 提取反例反馈 -> 最多3轮循环修复。
2. Baseline 模式: ["generate"]
   只执行初始生成，不进行形式化验证与反例反馈。

最终无论哪种模式，都会输出标准的 final_efsm.json，供下一阶段代码生成使用。
"""

import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
import requests

# 确保项目根目录在 sys.path 中，无论在哪个目录执行脚本均可正常导入 src
project_root_directory = Path(__file__).resolve().parent.parent
if str(project_root_directory) not in sys.path:
    sys.path.insert(0, str(project_root_directory))

# 引入项目自带的转译与语义校验模块
from src.efsm_to_smv import (
    generate_smv,
    load_json,
    validate_semantics,
    validate_structure,
)

# ==============================================================================
# 模型实验输出目录名称配置
# 可直接在此指定自定义简短别名 (如 "qwen3.7-flash", "deepseek-v4-flash")
# 若留空 ""，将自动读取下方 LLM_SETTINGS["model_name"] 并自动提取目录名
# ==============================================================================
MODEL_OUTPUTNAME = ""

# ==============================================================================
# 用户模型与 API 配置区域 (无需配置系统环境变量，可直接在此填写与维护)
# ==============================================================================
LLM_SETTINGS = {
    # 1. 你的 API Key (直接在此填入，例如 "sk-xxxxxxxx")
    "api_key": "",
    # 2. 接口地址 (常见服务商见下方注释，默认使用 DeepSeek)
    "base_url": "https://openrouter.ai/api/v1",
    # 3. 目标模型名称 (如 deepseek-chat, qwen-plus, gpt-4o 等)
    "model_name": "qwen/qwen3.7-flash",
    #qwen/qwen3.7-flash,z-ai/glm-5.3-flash,google/gemma-4-26b-a4b-it:free
}

# 常见厂商配置参考 (可直接将上方 base_url 和 model_name 替换为以下值):
# - openrouter:
#     base_url:   "https://openrouter.ai/api/v1"
#     model_name: ""
# - deepseek
    #  "api_key": 
    # "base_url": "https://api.deepseek.com/v1",
    # "model_name": "deepseek-v4-flash",

# ==============================================================================
# 待运行的 Benchmark 系统列表 (一维数组配置)
# 想要运行某个系统就保留，不想运行直接在行首添加 # 注释即可
# ==============================================================================
ACTIVE_BENCHMARK_SYSTEMS = [
    "vending_machine",  # 自动售货机（已配齐 22 条 Gold CTL 形式化规约与接口，首发试点）
    # "access_control",              # 门禁控制系统
    # "atm",                         # 自动取款机
    # "bike_rental",                 # 共享单车租赁
    # "car_rental",                  # 汽车租赁系统
    # "ecommerce_checkout",          # 电商结账流程
    # "elevator",                    # 电梯控制系统
    # "gym_membership",              # 健身房会员系统
    # "hotel_booking",               # 酒店预订系统
    # "library_loan",                # 图书借阅系统
    # "login_system",                # 用户登录鉴权
    # "medical_appointment_booking", # 医疗预约挂号
    # "online_examination",          # 在线考试系统
    # "package_locker",              # 快递快递柜
    # "parking_gate",                # 停车场道闸
    # "restaurant_reservation",      # 餐厅订座系统
    # "smart_thermostat",            # 智能恒温器
    # "ticket_machine",              # 自动售票机
    # "train_ticket_booking",        # 火车票预订系统
    # "warehouse_inventory",         # 仓库库存管理
]

# ==============================================================================
# nuXmv 求解器路径配置 (兼容 macOS 与 WSL)
# 自动探测优先级：
# 1. 命令行参数 --nuxmv-path
# 2. 环境变量 NUXMV_PATH (若外部环境已配置)
# 3. 系统 PATH (which nuxmv / nuXmv)
# 4. 与代码仓库平级的 tools 目录 (../tools/nuxmv/nuxmv)
# 5. 仓库内部的 tools 目录 (./tools/nuxmv/nuxmv)
# 6. 本地自定义路径 CUSTOM_NUXMV_PATH (若手动指定)
# ==============================================================================
CUSTOM_NUXMV_PATH = ""


def resolve_model_output_name(configured_name: str, model_name: str) -> str:
    """
    确定模型在实验输出目录中的文件夹名称。
    业务意图：优先使用用户配置的 MODEL_OUTPUTNAME；若为空，则自动取 model_name (去除斜杠前缀)。
    """
    # 卫语句 1：如果配置了 MODEL_OUTPUTNAME，优先使用
    if configured_name and configured_name.strip():
        return configured_name.strip()

    # 卫语句 2：若未配置，自动取 model_name
    # 业务意图：若包含斜杠 (如 'qwen/qwen3.7-flash')，提取最后一部分以避免产生多余层级的目录
    clean_model_name = model_name.split("/")[-1].strip()
    if clean_model_name:
        return clean_model_name

    return "default_model"


def determine_next_sample_directory(
    base_runs_directory: Path,
    model_output_name: str,
    system_name: str,
    explicit_sample_name: str | None = None,
) -> Path:
    """计算当前实验的 sample 归档目录，统一存放在 runs/<model_name>/<system_name>/sampleX。"""
    system_runs_directory = base_runs_directory / model_output_name / system_name
    system_runs_directory.mkdir(parents=True, exist_ok=True)

    # 业务意图：如果用户显式指定了 sample 目录名称，直接使用该名称
    if explicit_sample_name:
        return system_runs_directory / explicit_sample_name

    # 业务意图：扫描已有的 sampleX 文件夹，提取已有数字编号
    existing_sample_numbers: list[int] = []
    for item in system_runs_directory.iterdir():
        if not item.is_dir():
            continue
        if not item.name.startswith("sample"):
            continue

        sample_suffix = item.name.replace("sample", "").lstrip("_")
        if sample_suffix.isdigit():
            existing_sample_numbers.append(int(sample_suffix))

    # 业务意图：若还没有任何 sample 目录，从 1 开始编号 (sample1)
    if not existing_sample_numbers:
        return system_runs_directory / "sample1"

    # 业务意图：在已有最大编号基础上递增 1 (sample2, sample3...)
    next_sample_number = max(existing_sample_numbers) + 1
    return system_runs_directory / f"sample{next_sample_number}"


def append_experiment_log(log_file_path: Path, message: str) -> None:
    """
    向当前实验 sample 的 log.txt 实时追加一行核心生命周期日志。
    业务意图：同时在控制台输出并在文件系统中落盘，防止中途异常导致进度丢失。
    """
    print(message)
    with log_file_path.open(mode="a", encoding="utf-8") as file:
        file.write(message + "\n")


def get_system_paths(
    repository_root: Path,
    system_name: str,
) -> tuple[Path, Path, Path]:
    """根据系统名称获取需求文件、接口文件和 Gold CTL 规约文件路径。"""
    benchmark_system_directory = repository_root / "benchmarks" / "fsm_bench_20_fv" / system_name
    raw_dataset_file = (
        repository_root
        / "llm-fsm-local-benchmark-v1.1.0"
        / "cesar-andress-llm-fsm-local-benchmark-66b81c2"
        / "dataset"
        / "systems"
        / f"{system_name}.json"
    )

    # 业务意图：优先使用 benchmark 目录下的需求文件，若不存在则回退至原始数据集
    system_file = benchmark_system_directory / f"{system_name}.json"
    if not system_file.exists():
        system_file = raw_dataset_file

    # 接口文件和形式化规约固定在 benchmarks/fsm_bench_20_fv/<system_name> 之下
    interface_file = benchmark_system_directory / "system_interface.json"
    properties_file = benchmark_system_directory / "oracle" / "gold_properties.json"

    return system_file, interface_file, properties_file


def is_valid_nuxmv_executable(candidate_path: str | Path | None) -> bool:
    """业务意图：验证 candidate_path 是否是真实存在且能成功运行的 nuXmv 可执行程序。"""
    if not candidate_path:
        return False

    resolved_path = str(candidate_path)
    # 卫语句：检查文件是否存在以及是否有可执行权限
    if not os.path.exists(resolved_path) or not os.access(resolved_path, os.X_OK):
        return False

    try:
        # 运行轻量级探测指令 (nuXmv -help)
        probe_result = subprocess.run(
            [resolved_path, "-help"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=3,
            text=True,
        )
        combined_output = probe_result.stdout + probe_result.stderr
        # 只要输出中包含官方标识 nuXmv，说明程序真实可用
        return "nuXmv" in combined_output
    except Exception:
        return False


def find_nuxmv_executable(custom_path: str | None = None) -> str:
    """跨平台寻找可用的 nuXmv 执行程序路径 (同时兼容 macOS 与 WSL/Linux)。"""
    # 业务意图 1：优先使用命令行参数显式指定的路径
    if is_valid_nuxmv_executable(custom_path):
        return str(custom_path)

    # 业务意图 2：检查环境变量 NUXMV_PATH
    env_path = os.environ.get("NUXMV_PATH")
    if is_valid_nuxmv_executable(env_path):
        return str(env_path)

    # 业务意图 3：优先探测官方大写命名 nuXmv (WSL 与 macOS 均天生支持)
    official_nuxmv = shutil.which("nuXmv")
    if is_valid_nuxmv_executable(official_nuxmv):
        return str(official_nuxmv)

    # 业务意图 4：兜底探测小写命名 nuxmv
    lowercase_nuxmv = shutil.which("nuxmv")
    if is_valid_nuxmv_executable(lowercase_nuxmv):
        return str(lowercase_nuxmv)

    # 业务意图 5：检查与项目代码仓库平级的 tools 目录 (../tools/nuxmv/nuXmv 或 nuxmv)
    repository_root = Path(__file__).resolve().parent.parent
    for name in ["nuXmv", "nuxmv"]:
        sibling_tools_path = repository_root.parent / "tools" / "nuxmv" / name
        if is_valid_nuxmv_executable(sibling_tools_path):
            return str(sibling_tools_path)

    # 业务意图 6：检查项目仓库内部的 tools 目录 (./tools/nuxmv/nuXmv 或 nuxmv)
    for name in ["nuXmv", "nuxmv"]:
        repo_tools_path = repository_root / "tools" / "nuxmv" / name
        if is_valid_nuxmv_executable(repo_tools_path):
            return str(repo_tools_path)

    # 业务意图 7：检查脚本顶部用户手动配置的 CUSTOM_NUXMV_PATH
    if is_valid_nuxmv_executable(CUSTOM_NUXMV_PATH):
        return str(CUSTOM_NUXMV_PATH)

    # 业务意图 8：所有跨平台探测均未命中，提供清晰的报错和配置指引
    raise FileNotFoundError(
        "\n[!] 未能自动定位到可用的 nuXmv 求解器！请通过以下任意一种方式配置 (兼容 macOS 与 WSL/Linux)：\n"
        "    1. 确保 nuXmv 所在目录在系统 PATH 中 (which nuXmv 能输出有效路径)\n"
        "    2. 设置环境变量: export NUXMV_PATH=/path/to/nuXmv\n"
        "    3. 放置在与项目平级的 tools 目录: ../tools/nuxmv/nuXmv\n"
        "    4. 运行脚本时传入命令行参数: --nuxmv-path /path/to/nuXmv\n"
        "    5. 在 scripts/run_pilot_experiment.py 顶部的 CUSTOM_NUXMV_PATH 中填写"
    )


def extract_json_text_from_response(raw_response_text: str) -> str:
    """从大模型的文本回复中提取纯净的 JSON 字符串。"""
    cleaned_text = raw_response_text.strip()
    if not cleaned_text:
        return ""

    # 业务意图：如果模型包裹了 markdown 代码块，提取代码块内部文本
    code_block_match = re.search(
        r"```(?:json)?\s*([\s\S]*?)\s*```",
        cleaned_text,
        re.IGNORECASE,
    )
    if code_block_match:
        return code_block_match.group(1).strip()

    # 业务意图：若没有代码块标签，寻找最外层的大括号边界
    first_brace_index = cleaned_text.find("{")
    last_brace_index = cleaned_text.rfind("}")
    if first_brace_index != -1 and last_brace_index != -1 and last_brace_index > first_brace_index:
        return cleaned_text[first_brace_index : last_brace_index + 1].strip()

    return cleaned_text


def call_openai_chat_completion(
    api_key: str,
    base_url: str,
    model_name: str,
    messages: list[dict[str, str]],
    temperature: float = 0.0,
) -> str:
    """调用兼容 OpenAI 格式的云端大模型接口。"""
    normalized_url = base_url.rstrip("/")
    request_endpoint = f"{normalized_url}/chat/completions"

    request_headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    request_payload = {
        "model": model_name,
        "messages": messages,
        "temperature": temperature,
    }

    response = requests.post(
        request_endpoint,
        headers=request_headers,
        json=request_payload,
        timeout=180,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"大模型 API 调用失败 [HTTP {response.status_code}]: {response.text}"
        )

    response_json = response.json()
    choices = response_json.get("choices", [])
    if not choices:
        raise RuntimeError("大模型返回结果为空 choices")

    return choices[0]["message"]["content"]


def build_initial_generation_prompt(
    system_data: dict[str, Any],
    schema_data: dict[str, Any],
    interface_data: dict[str, Any],
) -> list[dict[str, str]]:
    """构建初始生成候选 EFSM 的 Prompt。"""
    system_name = system_data.get("system_name", "Drink Vending Machine")
    domain = system_data.get("domain", "vending machine")
    requirements = system_data.get("requirements", [])
    requirements_text = "\n".join(requirements)

    allowed_outputs = interface_data.get("output_events", [])
    expected_states = interface_data.get("states", [])
    expected_initial_state = interface_data.get("initial_state", "")
    expected_events = interface_data.get("events", [])
    expected_variables = interface_data.get("variables", [])

    interface_contract_lines = [
        "System Interface Contract (You MUST strictly follow these signatures):",
    ]
    if expected_states:
        interface_contract_lines.append(f"- States: {json.dumps(expected_states)}")
    if expected_initial_state:
        interface_contract_lines.append(f"- Initial State: '{expected_initial_state}'")
    if expected_events:
        interface_contract_lines.append(f"- Input Events: {json.dumps(expected_events)}")
    if expected_variables:
        interface_contract_lines.append(f"- State Variables: {json.dumps(expected_variables, indent=2)}")
    if allowed_outputs:
        interface_contract_lines.append(f"- Observable Output Signals: {json.dumps(allowed_outputs)}")

    interface_contract_text = "\n".join(interface_contract_lines)

    system_prompt = (
        "You are an expert formal methods and state machine engineer.\n"
        "Your task is to convert natural-language software requirements into an Extended Finite State Machine (EFSM).\n"
        "Rules:\n"
        "1. Strictly conform to the provided JSON Schema.\n"
        "2. You MUST strictly follow the System Interface Contract below:\n"
        f"{interface_contract_text}\n"
        "3. In transitions, use 'updates' (key-value dictionary) to modify variables.\n"
        "4. In transitions, use 'outputs' (array of strings) to emit observable signals.\n"
        "5. Cite the requirement identifier (e.g. 'R2') in the 'requirement' field of each transition.\n"
        "6. Ensure deterministic transitions: guards for the same (source, event) must be mutually disjoint.\n"
        "7. Return ONLY valid JSON, without any commentary or markdown wrapper."
    )

    user_prompt = (
        f"System Name: {system_name}\n"
        f"Domain: {domain}\n\n"
        "Requirements:\n"
        f"{requirements_text}\n\n"
        f"{interface_contract_text}\n\n"
        "Target EFSM JSON Schema:\n"
        f"{json.dumps(schema_data, indent=2)}\n\n"
        "Please generate the complete EFSM model JSON for this system."
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def build_repair_prompt(
    previous_model: dict[str, Any],
    validation_error_message: str | None,
    counterexample_report: str | None,
    interface_data: dict[str, Any],
) -> list[dict[str, str]]:
    """构建反例驱动修复提示词。"""
    allowed_outputs = interface_data.get("output_events", [])
    expected_states = interface_data.get("states", [])
    expected_initial_state = interface_data.get("initial_state", "")
    expected_events = interface_data.get("events", [])
    expected_variables = interface_data.get("variables", [])

    interface_contract_lines = [
        "System Interface Contract (Do NOT deviate from these signatures):",
    ]
    if expected_states:
        interface_contract_lines.append(f"- States: {json.dumps(expected_states)}")
    if expected_initial_state:
        interface_contract_lines.append(f"- Initial State: '{expected_initial_state}'")
    if expected_events:
        interface_contract_lines.append(f"- Input Events: {json.dumps(expected_events)}")
    if expected_variables:
        interface_contract_lines.append(f"- State Variables: {json.dumps(expected_variables, indent=2)}")
    if allowed_outputs:
        interface_contract_lines.append(f"- Observable Output Signals: {json.dumps(allowed_outputs)}")

    interface_contract_text = "\n".join(interface_contract_lines)

    system_prompt = (
        "You are an expert formal methods debugging engineer.\n"
        "Your previously generated EFSM failed formal verification or semantic validation.\n"
        "Analyze the provided counterexample execution trace and validation errors.\n"
        "Fix the transitions, guards, updates, or outputs to satisfy all requirements.\n"
        f"{interface_contract_text}\n"
        "Return ONLY the complete, repaired EFSM JSON."
    )

    diagnostic_parts = []
    if validation_error_message:
        diagnostic_parts.append(
            f"[Schema / Semantic Validation Error]:\n{validation_error_message}"
        )
    if counterexample_report:
        diagnostic_parts.append(
            f"[nuXmv Formal Verification Counterexample Trace]:\n{counterexample_report}"
        )

    user_prompt = (
        "Here is your previous EFSM model:\n"
        f"{json.dumps(previous_model, indent=2)}\n\n"
        "Verification Failure Details:\n"
        f"{chr(10).join(diagnostic_parts)}\n\n"
        "Please carefully analyze the root cause of the violation and output the entire corrected EFSM JSON."
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def parse_nuxmv_output(raw_output: str) -> tuple[bool, int, int, str]:
    """
    解析 nuXmv 验证输出。
    返回: (是否全部通过, 通过数量, 失败数量, 失败与反例详情文本)
    """
    lines = raw_output.splitlines()
    total_true_count = 0
    total_false_count = 0

    failed_sections: list[str] = []
    current_failed_section: list[str] = []
    is_capturing_counterexample = False

    for line in lines:
        if "-- specification " in line and " is true" in line:
            total_true_count += 1
            if is_capturing_counterexample:
                failed_sections.append("\n".join(current_failed_section))
                current_failed_section = []
                is_capturing_counterexample = False
            continue

        if "-- specification " in line and " is false" in line:
            total_false_count += 1
            if is_capturing_counterexample:
                failed_sections.append("\n".join(current_failed_section))
                current_failed_section = []

            is_capturing_counterexample = True
            current_failed_section.append(line.strip())
            continue

        if is_capturing_counterexample:
            current_failed_section.append(line)

    if current_failed_section:
        failed_sections.append("\n".join(current_failed_section))

    all_passed = total_false_count == 0 and total_true_count > 0
    failure_details = "\n\n".join(failed_sections)

    return all_passed, total_true_count, total_false_count, failure_details


def run_single_verification(
    candidate_model_path: Path,
    output_smv_path: Path,
    properties_path: Path,
    interface_path: Path,
    nuxmv_path: str,
) -> tuple[bool, str, int, int, str]:
    """
    执行单次完整形式化校验流程：
    转译 SMV -> 调用 nuXmv -> 解析输出。
    """
    # 业务意图：首先调用项目已有的 efsm_to_smv 生成 SMV 文件
    translate_command = [
        sys.executable,
        str(project_root_directory / "src" / "efsm_to_smv.py"),
        str(candidate_model_path),
        str(output_smv_path),
        "--schema",
        str(project_root_directory / "schema" / "efsm.schema.json"),
        "--properties",
        str(properties_path),
        "--properties-schema",
        str(project_root_directory / "schema" / "formal_properties.schema.json"),
        "--interface",
        str(interface_path),
        "--interface-schema",
        str(project_root_directory / "schema" / "system_interface.schema.json"),
    ]

    translation_result = subprocess.run(
        translate_command,
        capture_output=True,
        text=True,
    )

    # 卫语句：转译脚本失败（如语法校验或语义错误未通过）
    if translation_result.returncode != 0:
        error_message = translation_result.stderr or translation_result.stdout
        return False, error_message, 0, 0, ""

    # 业务意图：调用 nuXmv 求解器
    nuxmv_command = [nuxmv_path, str(output_smv_path)]
    solver_result = subprocess.run(
        nuxmv_command,
        capture_output=True,
        text=True,
    )

    raw_verification_log = solver_result.stdout + solver_result.stderr
    if solver_result.returncode != 0:
        return False, raw_verification_log, 0, 0, ""

    all_passed, passed_count, failed_count, failure_trace = parse_nuxmv_output(
        raw_verification_log
    )

    return all_passed, raw_verification_log, passed_count, failed_count, failure_trace


def execute_experiment(
    pipeline_stages: list[str],
    system_file: Path,
    schema_file: Path,
    interface_file: Path,
    properties_file: Path,
    output_dir: Path,
    model_name: str,
    api_key: str,
    base_url: str,
    max_repair_rounds: int,
    nuxmv_executable: str,
) -> dict[str, Any]:
    """执行主实验流水线（由 pipeline_stages 数组精确控制）。"""
    output_dir.mkdir(parents=True, exist_ok=True)

    system_data = load_json(system_file)
    schema_data = load_json(schema_file)
    interface_data = load_json(interface_file)

    summary_records: dict[str, Any] = {
        "timestamp": datetime.datetime.now().isoformat(),
        "model": model_name,
        "pipeline_stages": pipeline_stages,
        "rounds": [],
        "success": False,
        "total_rounds": 0,
    }

    current_candidate_model: dict[str, Any] | None = None
    last_verification_trace: str | None = None
    last_validation_error: str | None = None

    # =======================================================
    # 环节 1：初始候选模型生成 (generate 阶段)
    # =======================================================
    if "generate" not in pipeline_stages:
        raise ValueError("流水线阶段必须包含 'generate'")

    print(f"[*] 启动初始模型生成 (模型: {model_name})...")
    initial_messages = build_initial_generation_prompt(
        system_data=system_data,
        schema_data=schema_data,
        interface_data=interface_data,
    )

    initial_response = call_openai_chat_completion(
        api_key=api_key,
        base_url=base_url,
        model_name=model_name,
        messages=initial_messages,
    )

    json_text = extract_json_text_from_response(initial_response)
    try:
        current_candidate_model = json.loads(json_text)
    except json.JSONDecodeError as decode_error:
        print(f"[!] 初始生成输出非合法 JSON: {decode_error}")
        summary_records["initial_error"] = str(decode_error)
        summary_records["raw_response"] = initial_response
        return summary_records

    round_0_file = output_dir / "candidate_round_0.json"
    round_0_file.write_text(json.dumps(current_candidate_model, indent=2), encoding="utf-8")
    print(f"[+] 初始模型已保存至: {round_0_file}")

    sample_log_file = output_dir / "log.txt"
    if sample_log_file.exists():
        sample_log_file.unlink()

    # =======================================================
    # 卫语句：若流水线不包含验证 (Baseline 模式)，生成完毕直接导出
    # =======================================================
    if "verify" not in pipeline_stages:
        append_experiment_log(sample_log_file, "[*] 流水线未启用 'verify'，作为 Baseline 导出最终模型。")
        final_efsm_file = output_dir / "final_efsm.json"
        final_efsm_file.write_text(json.dumps(current_candidate_model, indent=2), encoding="utf-8")
        summary_records["final_efsm_path"] = str(final_efsm_file)
        summary_records["log_path"] = str(sample_log_file)
        summary_records["success"] = True
        return summary_records

    # =======================================================
    # 环节 2 & 3：验证与反例驱动修复迭代 (verify & repair 阶段)
    # =======================================================
    current_round = 0
    max_allowed_rounds = max_repair_rounds if "repair" in pipeline_stages else 0
    validation_repair_count = 0
    max_allowed_validation_repairs = 1

    while current_round <= max_allowed_rounds:
        round_name = f"round_{current_round}"
        if current_round > 0:
            append_experiment_log(sample_log_file, "")
        append_experiment_log(sample_log_file, f"--- 执行形式化验证 [{round_name}] ---")

        candidate_file = output_dir / f"candidate_{round_name}.json"
        candidate_file.write_text(json.dumps(current_candidate_model, indent=2), encoding="utf-8")

        smv_output_file = output_dir / f"model_{round_name}.smv"
        verification_log_file = output_dir / f"verification_{round_name}.txt"

        # 运行验证
        all_passed, log_output, true_count, false_count, failure_trace = run_single_verification(
            candidate_model_path=candidate_file,
            output_smv_path=smv_output_file,
            properties_path=properties_file,
            interface_path=interface_file,
            nuxmv_path=nuxmv_executable,
        )

        verification_log_file.write_text(log_output, encoding="utf-8")

        round_record = {
            "round": current_round,
            "passed_properties": true_count,
            "failed_properties": false_count,
            "all_passed": all_passed,
        }
        summary_records["rounds"].append(round_record)

        append_experiment_log(sample_log_file, f"[{round_name}] 结果: 通过 {true_count} 条，违例 {false_count} 条")

        # 业务意图 1：全部性质通过，提前成功终止
        if all_passed:
            append_experiment_log(sample_log_file, f"[√] 模型在第 {current_round} 轮成功通过全部形式化性质！")
            summary_records["success"] = True
            summary_records["converged_at_round"] = current_round
            break

        # 卫语句 2：如果不包含 repair 环节，或者已达最大修复轮次，停止迭代
        if "repair" not in pipeline_stages or current_round == max_allowed_rounds:
            if true_count == 0 and false_count == 0:
                error_message = log_output.strip() or "结构或语义校验失败"
                append_experiment_log(sample_log_file, f"[!] 达到轮次上限仍未解决格式校验错误，停止迭代: {error_message}")
                summary_records["error"] = error_message
            else:
                append_experiment_log(sample_log_file, "[!] 达到修复上限或未配置 repair 环节，停止迭代。")
            break

        # 卫语句 3：格式校验失败修复最多允许 1 次，若已达上限则立即停止迭代
        is_validation_failure = (true_count == 0 and false_count == 0)
        if is_validation_failure and validation_repair_count >= max_allowed_validation_repairs:
            error_message = log_output.strip() or "结构或语义校验失败"
            append_experiment_log(
                sample_log_file,
                f"[!] 格式校验失败已达最大重试上限({max_allowed_validation_repairs}次)，停止迭代: {error_message}",
            )
            summary_records["error"] = error_message
            break

        # 业务意图 4：根据错误类型组装诊断提示词并递增校验修复计数
        if is_validation_failure:
            validation_repair_count += 1
            append_experiment_log(
                sample_log_file,
                f"[*] 结构或语义校验未通过(第{validation_repair_count}次)，正在组装错误信息请求大模型修复格式...",
            )
            validation_error_message = log_output
            counterexample_report = None
        else:
            append_experiment_log(sample_log_file, "[*] 捕捉到反例，正在组装修复提示词并请求大模型修复...")
            validation_error_message = None
            counterexample_report = failure_trace

        # 准备下一轮修复 Prompt
        repair_messages = build_repair_prompt(
            previous_model=current_candidate_model,
            validation_error_message=validation_error_message,
            counterexample_report=counterexample_report,
            interface_data=interface_data,
        )

        repair_response = call_openai_chat_completion(
            api_key=api_key,
            base_url=base_url,
            model_name=model_name,
            messages=repair_messages,
        )

        repaired_json_text = extract_json_text_from_response(repair_response)
        try:
            current_candidate_model = json.loads(repaired_json_text)
        except json.JSONDecodeError as decode_err:
            append_experiment_log(sample_log_file, f"[!] 修复轮次输出非法 JSON: {decode_err}")
            break

        current_round += 1

    summary_records["total_rounds"] = current_round

    # =======================================================
    # 环节 4：统一封装导出 final_efsm.json
    # =======================================================
    final_efsm_file = output_dir / "final_efsm.json"
    final_efsm_file.write_text(json.dumps(current_candidate_model, indent=2), encoding="utf-8")
    summary_records["final_efsm_path"] = str(final_efsm_file)
    summary_records["log_path"] = str(sample_log_file)

    summary_file = output_dir / "summary.json"
    summary_file.write_text(json.dumps(summary_records, indent=2), encoding="utf-8")

    print(f"\n[+] 实验完成！最终 EFSM 模型已导出至: {final_efsm_file}")
    print(f"[+] 实验汇总已保存至: {summary_file}")
    print(f"[+] 实验日志已保存至: {sample_log_file}")

    return summary_records


def main() -> None:
    parser = argparse.ArgumentParser(
        description="FSM-Bench-20 主实验脚本 (Treatment vs Baseline，支持多系统一维数组配置与 sample 自增归档)"
    )

    parser.add_argument(
        "--mode",
        choices=["treatment", "baseline"],
        default="treatment",
        help="实验模式: treatment (带验证修复) 或 baseline (仅初次生成)",
    )

    parser.add_argument(
        "--pipeline",
        type=str,
        default=None,
        help="一维数组控制环节，逗号分隔 (如 'generate,verify,repair')",
    )

    parser.add_argument(
        "--systems",
        type=str,
        default=None,
        help="指定待运行的系统名列表，逗号分隔 (可选，默认读取脚本顶部的 ACTIVE_BENCHMARK_SYSTEMS)",
    )

    parser.add_argument(
        "--sample-id",
        type=str,
        default=None,
        help="指定输出 sample 目录名称 (如 'sample_1'，默认自动扫描并递增编号)",
    )

    parser.add_argument(
        "--model",
        type=str,
        default=LLM_SETTINGS["model_name"],
        help=f"调用的大模型名称 (默认: {LLM_SETTINGS['model_name']})",
    )

    parser.add_argument(
        "--api-key",
        type=str,
        default=LLM_SETTINGS["api_key"],
        help="OpenAI 兼容接口 API Key (默认读取脚本顶部配置)",
    )

    parser.add_argument(
        "--base-url",
        type=str,
        default=LLM_SETTINGS["base_url"],
        help=f"OpenAI 兼容接口 Base URL (默认: {LLM_SETTINGS['base_url']})",
    )

    parser.add_argument(
        "--max-repair-rounds",
        type=int,
        default=3,
        help="最大反例修复轮次 (默认: 3)",
    )

    parser.add_argument(
        "--model-output-name",
        type=str,
        default=MODEL_OUTPUTNAME,
        help="模型在输出目录中的文件夹名称 (默认读取脚本顶部 MODEL_OUTPUTNAME，留空则自动从模型名提取)",
    )

    parser.add_argument(
        "--nuxmv-path",
        type=str,
        default=None,
        help="nuXmv 可执行文件路径",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="自定义产物输出根目录 (默认归档在项目根目录 runs/<model_output_name>/<system>/sampleX)",
    )

    args = parser.parse_args()

    # 卫语句 1：检查是否已在脚本顶部填入或传入有效的 API Key
    if not args.api_key or args.api_key == "YOUR_API_KEY_HERE":
        print("\n[!] 提示: 请在 scripts/run_pilot_experiment.py 顶部的 LLM_SETTINGS 中填入你的 api_key 后再次运行！")
        print("    例如: LLM_SETTINGS = {'api_key': 'sk-xxxxxx', ...}")
        sys.exit(1)

    # 业务意图：解析流水线阶段一维数组
    if args.pipeline:
        pipeline_stages = [stage.strip() for stage in args.pipeline.split(",")]
    else:
        if args.mode == "baseline":
            pipeline_stages = ["generate"]
        else:
            pipeline_stages = ["generate", "verify", "repair"]

    # 业务意图：如果包含形式化验证，预先寻找并验证 nuXmv 可执行路径
    nuxmv_path = ""
    if "verify" in pipeline_stages:
        nuxmv_path = find_nuxmv_executable(args.nuxmv_path)

    # 业务意图：确定当前批次要运行的系统列表
    if args.systems:
        systems_to_run = [item.strip() for item in args.systems.split(",") if item.strip()]
    else:
        systems_to_run = list(ACTIVE_BENCHMARK_SYSTEMS)

    # 卫语句 2：检查系统列表是否为空
    if not systems_to_run:
        print("\n[!] 提示: ACTIVE_BENCHMARK_SYSTEMS 列表为空，没有指定任何要运行的系统！")
        print("    请在 scripts/run_pilot_experiment.py 顶部取消注释至少一个系统 (例如 'vending_machine')。")
        sys.exit(1)

    # 业务意图：确定模型归档目录名 (若留空则自动从模型名称中解析)
    resolved_model_output_name = resolve_model_output_name(
        configured_name=args.model_output_name,
        model_name=args.model,
    )

    repository_root = Path(__file__).resolve().parent.parent
    schema_file = repository_root / "schema" / "efsm.schema.json"
    base_runs_root = args.output_dir if args.output_dir else (repository_root / "runs")

    print(f"\n[*] 准备执行 Benchmark 任务，总共配置了 {len(systems_to_run)} 个系统: {systems_to_run}")
    print(f"[*] 模型输出目录标识: {resolved_model_output_name}")

    for system_name in systems_to_run:
        print(f"\n{'=' * 65}")
        print(f"[*] 开始处理系统: {system_name}")
        print(f"{'=' * 65}")

        system_file, interface_file, properties_file = get_system_paths(
            repository_root=repository_root,
            system_name=system_name,
        )

        # 卫语句 3：检查系统需求文件是否存在
        if not system_file.exists():
            print(f"[跳过] 系统 '{system_name}' 的需求文件不存在: {system_file}，跳过此系统。")
            continue

        # 卫语句 4：如果流水线启用了形式化验证，检查规约文件是否存在
        if "verify" in pipeline_stages and not properties_file.exists():
            print(f"[跳过] 系统 '{system_name}' 尚未配置 Gold CTL 规约文件: {properties_file}")
            print(f"       (当前仅 vending_machine 已就绪，其他系统规约正在开发中)，自动跳过此系统。")
            continue

        # 卫语句 5：如果流水线启用了形式化验证，检查接口定义文件是否存在
        if "verify" in pipeline_stages and not interface_file.exists():
            print(f"[跳过] 系统 '{system_name}' 缺少接口定义文件: {interface_file}，跳过此系统。")
            continue

        # 业务意图：计算 sample 存放目录，统一归档在 runs/<model_output_name>/<system_name>/sampleX
        system_output_dir = determine_next_sample_directory(
            base_runs_directory=base_runs_root,
            model_output_name=resolved_model_output_name,
            system_name=system_name,
            explicit_sample_name=args.sample_id,
        )
        print(f"[*] 实验输出目录: {system_output_dir}")

        execute_experiment(
            pipeline_stages=pipeline_stages,
            system_file=system_file,
            schema_file=schema_file,
            interface_file=interface_file,
            properties_file=properties_file,
            output_dir=system_output_dir,
            model_name=args.model,
            api_key=args.api_key,
            base_url=args.base_url,
            max_repair_rounds=args.max_repair_rounds,
            nuxmv_executable=nuxmv_path,
        )


if __name__ == "__main__":
    main()
