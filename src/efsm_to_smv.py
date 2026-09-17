#!/usr/bin/env python3

import argparse
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


def load_json(path: Path) -> dict[str, Any]:
    """读取JSON文件并转换成Python字典。"""
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def validate_structure(
    model: dict[str, Any],
    schema: dict[str, Any],
) -> None:
    """使用JSON Schema检查模型的基本结构。"""
    validator = Draft202012Validator(schema)
    errors = sorted(
        validator.iter_errors(model),
        key=lambda error: list(error.path),
    )

    if not errors:
        return

    messages = []

    for error in errors:
        location = ".".join(str(part) for part in error.path)
        location = location or "<root>"
        messages.append(f"{location}: {error.message}")

    raise ValueError(
        "Schema validation failed:\n  - "
        + "\n  - ".join(messages)
    )


def validate_semantics(
    model: dict[str, Any],
    declared_outputs: set[str] | None = None,
) -> None:
    """检查Schema无法表达的EFSM语义关系。"""
    states = set(model["states"])
    events = set(model["events"])

    variables = model.get("variables", [])
    variable_names = {
        variable["name"]
        for variable in variables
    }

    problems: list[str] = []

    initial_state = model["initial_state"]
    if initial_state not in states:
        problems.append(
            f"initial_state {initial_state!r} "
            "is not declared in states"
        )

    transition_ids: set[str] = set()

    for idx, transition in enumerate(model["transitions"], start=1):
        transition_id = transition.get("id") or f"T{idx}"

        if transition.get("id"):
            if transition_id in transition_ids:
                problems.append(
                    f"duplicate transition id {transition_id!r}"
                )
            transition_ids.add(transition_id)

        if transition["source"] not in states:
            problems.append(
                f"{transition_id}: unknown source state "
                f"{transition['source']!r}"
            )

        if transition["target"] not in states:
            problems.append(
                f"{transition_id}: unknown target state "
                f"{transition['target']!r}"
            )

        if transition["event"] not in events:
            problems.append(
                f"{transition_id}: unknown event "
                f"{transition['event']!r}"
            )

        updates = transition.get("updates", {})
        for variable_name in updates:
            if variable_name not in variable_names:
                problems.append(
                    f"{transition_id}: update target unknown "
                    f"variable {variable_name!r}"
                )

        if declared_outputs is not None:
            for output_name in transition.get("outputs", []):
                if output_name not in declared_outputs:
                    problems.append(
                        f"{transition_id}: output {output_name!r} "
                        "is not declared in the system interface"
                    )

    if problems:
        raise ValueError(
            "Semantic validation failed:\n  - "
            + "\n  - ".join(problems)
        )


def transition_condition(
    transition: dict[str, Any],
) -> str:
    """把一条EFSM迁移转换成SMV条件表达式。"""
    conditions = [
        f"state = {transition['source']}",
        f"event = {transition['event']}",
    ]

    guard = transition.get("guard")

    if guard and guard != "TRUE":
        smv_guard = guard.replace("==", "=")
        conditions.append(f"({smv_guard})")

    return " & ".join(conditions)


def smv_initial_value(value: bool | int | str) -> str:
    """把JSON初始值转换成SMV表示。"""
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"

    return str(value)


def infer_output_events(model: dict[str, Any]) -> list[str]:
    """按名称稳定收集模型中出现的业务输出。"""
    return sorted({
        output_name
        for transition in model["transitions"]
        for output_name in transition.get("outputs", [])
    })


def output_expression(
    model: dict[str, Any],
    output_name: str,
) -> str:
    """生成一个瞬时输出对应的组合逻辑表达式。"""
    conditions = [
        transition_condition(transition)
        for transition in model["transitions"]
        if output_name in transition.get("outputs", [])
    ]

    if not conditions:
        return "FALSE"

    return " | ".join(
        f"({condition})"
        for condition in conditions
    )


def generate_smv(
    model: dict[str, Any],
    properties: list[dict[str, Any]] | None = None,
    output_events: list[str] | None = None,
) -> str:
    """将完整EFSM模型转换成SMV文本。"""
    model_name = (
        model.get("name")
        or model.get("system_name")
        or "EFSM_Model"
    )
    initial_state = model["initial_state"]

    lines = [
        f"-- Generated from EFSM: {model_name}",
        "MODULE main",
        "",
        "VAR",
        f"  event : {{NONE, {', '.join(model['events'])}}};",
        f"  state : {{{', '.join(model['states'])}}};",
    ]

    variables = model.get("variables", [])
    for variable in variables:
        v_type = variable["type"]
        if v_type == "boolean":
            smv_type = "boolean"
        elif v_type == "enum":
            values = variable.get("values", [])
            smv_type = f"{{{', '.join(values)}}}"
        else:
            minimum = variable.get("minimum", -1000)
            maximum = variable.get("maximum", 1000)
            smv_type = f"{minimum}..{maximum}"

        lines.append(
            f"  {variable['name']} : {smv_type};"
        )

    if output_events is None:
        output_events = infer_output_events(model)

    if output_events:
        lines.extend([
            "",
            "DEFINE",
        ])

        for output_name in output_events:
            expression = output_expression(model, output_name)
            lines.append(
                f"  emit_{output_name} := {expression};"
            )

    lines.extend([
        "",
        "ASSIGN",
        "  init(event) := "
        f"{{NONE, {', '.join(model['events'])}}};",
        "  next(event) := "
        f"{{NONE, {', '.join(model['events'])}}};",
        "",
        f"  init(state) := {initial_state};",
        "  next(state) :=",
        "    case",
    ])

    for idx, transition in enumerate(model["transitions"], start=1):
        condition = transition_condition(transition)
        trans_id = transition.get("id") or f"T{idx}"

        lines.append(
            f"      {condition} : "
            f"{transition['target']}; "
            f"-- {trans_id}"
        )

    lines.extend([
        "      TRUE : state;",
        "    esac;",
    ])

    for variable in variables:
        variable_name = variable["name"]

        lines.extend([
            "",
            f"  init({variable_name}) := "
            f"{smv_initial_value(variable['initial'])};",
            f"  next({variable_name}) :=",
            "    case",
        ])

        for idx, transition in enumerate(model["transitions"], start=1):
            updates = transition.get("updates", {})

            if variable_name not in updates:
                continue

            condition = transition_condition(transition)
            trans_id = transition.get("id") or f"T{idx}"

            lines.append(
                f"      {condition} : "
                f"{updates[variable_name]}; "
                f"-- {trans_id}"
            )

        lines.extend([
            f"      TRUE : {variable_name};",
            "    esac;",
        ])

    if properties:
        lines.append("")
        for formal_property in properties:
            description = formal_property.get(
                "description",
                "",
            )
            spec_kind = formal_property.get("kind", "CTL")
            spec_prefix = (
                "LTLSPEC" if spec_kind == "LTL" else "CTLSPEC"
            )

            if description:
                lines.append(
                    f"-- {formal_property['id']}: {description}"
                )
            lines.append(
                f"{spec_prefix} {formal_property['formula']}"
            )
            lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Validate an EFSM JSON model "
            "and generate a nuXmv SMV model."
        )
    )

    parser.add_argument(
        "model",
        type=Path,
        help="Input EFSM JSON file",
    )

    parser.add_argument(
        "output",
        type=Path,
        help="Generated SMV file",
    )

    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("schema/efsm.schema.json"),
        help="EFSM JSON Schema file",
    )

    parser.add_argument(
        "--properties",
        type=Path,
        default=None,
        help="Decoupled formal properties JSON file",
    )

    parser.add_argument(
        "--properties-schema",
        type=Path,
        default=Path("schema/formal_properties.schema.json"),
        help="Formal properties JSON Schema file",
    )

    parser.add_argument(
        "--interface",
        type=Path,
        default=None,
        help=(
            "Optional system interface JSON. Its output_events "
            "declare stable observable output signals."
        ),
    )

    parser.add_argument(
        "--interface-schema",
        type=Path,
        default=Path("schema/system_interface.schema.json"),
        help="System interface JSON Schema file",
    )

    args = parser.parse_args()

    model = load_json(args.model)
    schema = load_json(args.schema)

    validate_structure(model, schema)

    output_events = None
    if args.interface:
        interface_data = load_json(args.interface)
        interface_schema = load_json(args.interface_schema)
        validate_structure(interface_data, interface_schema)
        output_events = interface_data["output_events"]

    declared_outputs = (
        set(output_events)
        if output_events is not None
        else None
    )
    validate_semantics(model, declared_outputs=declared_outputs)

    properties_list = None
    if args.properties:
        properties_data = load_json(args.properties)
        properties_schema = load_json(args.properties_schema)
        validate_structure(properties_data, properties_schema)
        properties_list = properties_data["properties"]

    smv_text = generate_smv(
        model,
        properties=properties_list,
        output_events=output_events,
    )

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    args.output.write_text(
        smv_text,
        encoding="utf-8",
    )

    print(f"OK: validated {args.model}")
    if args.properties:
        print(f"OK: validated properties {args.properties}")
    if args.interface:
        print(f"OK: validated interface {args.interface}")
    print(f"OK: generated {args.output}")


if __name__ == "__main__":
    main()
