from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .config import DATASET_DIR


@dataclass(frozen=True)
class SystemSpec:
    file_stem: str
    system_name: str
    domain: str
    requirements: list[str]


def load_catalog(dataset_dir: Path = DATASET_DIR) -> list[dict]:
    index_path = dataset_dir / "index.json"
    if index_path.exists():
        payload = json.loads(index_path.read_text(encoding="utf-8"))
        return payload.get("systems", [])
    systems_dir = dataset_dir / "systems"
    return [
        {"file": f"systems/{path.name}", "system_name": path.stem}
        for path in sorted(systems_dir.glob("*.json"))
    ]


def load_system(file_stem: str, dataset_dir: Path = DATASET_DIR) -> SystemSpec:
    path = dataset_dir / "systems" / f"{file_stem}.json"
    if not path.exists():
        raise FileNotFoundError(f"System not found: {path}")

    payload = json.loads(path.read_text(encoding="utf-8"))
    return SystemSpec(
        file_stem=file_stem,
        system_name=payload["system_name"],
        domain=payload.get("domain", "unknown"),
        requirements=payload["requirements"],
    )


def load_all_systems(dataset_dir: Path = DATASET_DIR) -> list[SystemSpec]:
    systems_dir = dataset_dir / "systems"
    return [load_system(path.stem, dataset_dir) for path in sorted(systems_dir.glob("*.json"))]


def requirement_ids(requirements: list[str]) -> set[str]:
    ids: set[str] = set()
    for req in requirements:
        if req.startswith("R") and ":" in req:
            ids.add(req.split(":", 1)[0].strip())
    return ids
