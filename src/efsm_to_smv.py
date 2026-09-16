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


def validate_semantics(model: dict[str, Any]) -> None:
    """检查Schema无法表达的EFSM语义关系。"""
    states = set(model["states"])
    events = set(model["events"])

    variable_names = {
        variable["name"]
        for variable in model["variables"]
    }

    problems: list[str] = []

    if model["initialState"] not in states:
        problems.append(
            f"initialState {model['initialState']!r} "
            "is not declared in states"
        )

    transition_ids: set[str] = set()

    for transition in model["transitions"]:
        transition_id = transition["id"]

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

        for variable_name in transition.get("actions", {}):
            if variable_name not in variable_names:
                problems.append(
                    f"{transition_id}: action updates unknown "
                    f"variable {variable_name!r}"
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
        conditions.append(f"({guard})")

    return " & ".join(conditions)


def smv_initial_value(value: bool | int) -> str:
    """把JSON初始值转换成SMV表示。"""
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"

    return str(value)


def generate_smv(model: dict[str, Any]) -> str:
    """将完整EFSM模型转换成SMV文本。"""
    lines = [
        f"-- Generated from EFSM: {model['name']}",
        "MODULE main",
        "",
        "IVAR",
        f"  event : {{NONE, {', '.join(model['events'])}}};",
        "",
        "VAR",
        f"  state : {{{', '.join(model['states'])}}};",
    ]

    for variable in model["variables"]:
        if variable["type"] == "boolean":
            smv_type = "boolean"
        else:
            minimum = variable.get("minimum", -1000)
            maximum = variable.get("maximum", 1000)
            smv_type = f"{minimum}..{maximum}"

        lines.append(
            f"  {variable['name']} : {smv_type};"
        )

    lines.extend([
        "",
        "ASSIGN",
        f"  init(state) := {model['initialState']};",
        "  next(state) :=",
        "    case",
    ])

    for transition in model["transitions"]:
        condition = transition_condition(transition)

        lines.append(
            f"      {condition} : "
            f"{transition['target']}; "
            f"-- {transition['id']}"
        )

    lines.extend([
        "      TRUE : state;",
        "    esac;",
    ])

    for variable in model["variables"]:
        variable_name = variable["name"]

        lines.extend([
            "",
            f"  init({variable_name}) := "
            f"{smv_initial_value(variable['initial'])};",
            f"  next({variable_name}) :=",
            "    case",
        ])

        for transition in model["transitions"]:
            actions = transition.get("actions", {})

            if variable_name not in actions:
                continue

            condition = transition_condition(transition)

            lines.append(
                f"      {condition} : "
                f"{actions[variable_name]}; "
                f"-- {transition['id']}"
            )

        lines.extend([
            f"      TRUE : {variable_name};",
            "    esac;",
        ])

    lines.append("")

    for formal_property in model["properties"]:
        description = formal_property.get(
            "description",
            "",
        )

        lines.append(
            f"-- {formal_property['id']}: {description}"
        )
        lines.append(
            f"CTLSPEC {formal_property['formula']}"
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

    args = parser.parse_args()

    model = load_json(args.model)
    schema = load_json(args.schema)

    validate_structure(model, schema)
    validate_semantics(model)

    smv_text = generate_smv(model)

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    args.output.write_text(
        smv_text,
        encoding="utf-8",
    )

    print(f"OK: validated {args.model}")
    print(f"OK: generated {args.output}")


if __name__ == "__main__":
    main()