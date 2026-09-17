#!/usr/bin/env python3
"""Validate repository JSON syntax, dataset integrity, and benchmark integrity."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = REPO_ROOT / "dataset"
BENCHMARK_DIR = REPO_ROOT / "benchmark"
GOLD_DIR = BENCHMARK_DIR / "gold"

# Pre-migration fallback: dataset may live one level above the Git repo root.
if not DATASET_DIR.is_dir() and (REPO_ROOT.parent / "dataset").is_dir():
    DATASET_DIR = REPO_ROOT.parent / "dataset"

SYSTEMS_DIR = DATASET_DIR / "systems"
INDEX_PATH = DATASET_DIR / "index.json"
BENCHMARK_INDEX_PATH = BENCHMARK_DIR / "index.json"


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    raise SystemExit(1)


def load_json(path: Path) -> dict | list:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"Invalid JSON in {path}: {exc}")
    except OSError as exc:
        fail(f"Cannot read {path}: {exc}")
    return {}


def validate_json_files(paths: list[Path]) -> None:
    for path in paths:
        load_json(path)
    print(f"  JSON syntax OK ({len(paths)} files)")


def validate_dataset() -> None:
    print("Validating dataset integrity...")
    if not SYSTEMS_DIR.is_dir():
        fail(f"Missing dataset systems directory: {SYSTEMS_DIR}")

    system_files = sorted(SYSTEMS_DIR.glob("*.json"))
    if not system_files:
        fail(f"No system files in {SYSTEMS_DIR}")

    validate_json_files(system_files)

    if not INDEX_PATH.exists():
        fail(f"Missing dataset index: {INDEX_PATH}")

    index = load_json(INDEX_PATH)
    if not isinstance(index, dict):
        fail("dataset/index.json must be a JSON object")

    catalog = index.get("systems", [])
    if not isinstance(catalog, list):
        fail("dataset/index.json: 'systems' must be an array")

    catalog_files = {entry.get("file") for entry in catalog if isinstance(entry, dict)}
    expected_files = {f"systems/{path.name}" for path in system_files}

    missing_in_index = expected_files - catalog_files
    extra_in_index = catalog_files - expected_files
    if missing_in_index:
        fail(f"dataset/index.json missing entries for: {sorted(missing_in_index)}")
    if extra_in_index:
        fail(f"dataset/index.json references missing files: {sorted(extra_in_index)}")

    for path in system_files:
        payload = load_json(path)
        if not isinstance(payload, dict):
            fail(f"{path} must be a JSON object")
        requirements = payload.get("requirements", [])
        if not isinstance(requirements, list) or not requirements:
            fail(f"{path}: 'requirements' must be a non-empty array")
        for i, req in enumerate(requirements, start=1):
            if not isinstance(req, str) or not req.startswith(f"R{i}:"):
                fail(f"{path}: requirement at index {i} must start with 'R{i}:'")

    print(f"  Dataset integrity OK ({len(system_files)} systems)")


def validate_benchmark() -> None:
    print("Validating benchmark integrity...")
    if not GOLD_DIR.is_dir():
        fail(f"Missing gold directory: {GOLD_DIR}")

    gold_files = sorted(GOLD_DIR.glob("*.json"))
    if not gold_files:
        fail(f"No gold placeholder files in {GOLD_DIR}")

    validate_json_files(gold_files)

    system_files = sorted(SYSTEMS_DIR.glob("*.json"))
    system_stems = {path.stem for path in system_files}
    gold_stems = {path.stem for path in gold_files}

    missing_gold = system_stems - gold_stems
    extra_gold = gold_stems - system_stems
    if missing_gold:
        fail(f"Missing gold files for systems: {sorted(missing_gold)}")
    if extra_gold:
        fail(f"Gold files without matching dataset system: {sorted(extra_gold)}")

    if BENCHMARK_INDEX_PATH.exists():
        load_json(BENCHMARK_INDEX_PATH)
        print(f"  benchmark/index.json OK")
    else:
        print("  WARN: benchmark/index.json not found (expected after migration)")

    print(f"  Benchmark integrity OK ({len(gold_files)} gold placeholders)")


def main() -> int:
    print(f"Repository root: {REPO_ROOT}")
    validate_dataset()
    validate_benchmark()
    print("All validation checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
