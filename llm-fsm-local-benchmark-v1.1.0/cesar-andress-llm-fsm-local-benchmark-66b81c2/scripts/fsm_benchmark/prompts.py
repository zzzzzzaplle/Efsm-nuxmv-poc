from __future__ import annotations

import json
from pathlib import Path

from .config import PROMPTS_DIR
from .dataset import SystemSpec
from .schema import fsm_json_schema


def load_text(name: str, prompts_dir: Path = PROMPTS_DIR) -> str:
    path = prompts_dir / name
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def build_messages(system: SystemSpec) -> list[dict[str, str]]:
    system_prompt = load_text("fsm_system_prompt.txt")
    user_template = load_text("fsm_user_prompt.txt")

    requirements_block = "\n".join(system.requirements)
    schema_json = json.dumps(fsm_json_schema(), indent=2)

    user_content = user_template.format(
        system_name=system.system_name,
        domain=system.domain,
        requirements=requirements_block,
        json_schema=schema_json,
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]
