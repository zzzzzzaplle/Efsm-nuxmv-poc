#!/usr/bin/env python3
"""Run the full FSM generation experiment against local Ollama models."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fsm_benchmark.config import (
    CLEANED_DIR,
    MODELS,
    OPTIONAL_MODELS,
    RAW_DIR,
    RESULTS_DIR,
)
from fsm_benchmark.dataset import load_all_systems
from fsm_benchmark.metrics import compute_metrics, validate_fsm_dict
from fsm_benchmark.ollama_client import (
    generate_fsm,
    is_model_installed,
    list_installed_models,
    pull_model_command,
)
from fsm_benchmark.prompts import build_messages


def sanitize_model_dir(model: str) -> str:
    return model.replace(":", "_").replace("/", "_")


def save_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> int:
    models = list(MODELS)
    if args.include_optional:
        models.extend(OPTIONAL_MODELS)
    if args.models:
        models = args.models

    systems = load_all_systems()
    if args.systems:
        wanted = set(args.systems)
        systems = [system for system in systems if system.file_stem in wanted]

    try:
        installed = list_installed_models(host=args.host)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: Ollama unavailable at {args.host}: {exc}")
        return 1

    missing = [model for model in models if not is_model_installed(model, installed)]
    if missing and not args.skip_missing:
        print("Missing models:")
        for model in missing:
            print(f"  {pull_model_command(model)}")
        print("Re-run with --skip-missing to continue with installed models only.")
        return 2

    models = [model for model in models if is_model_installed(model, installed)]
    if not models:
        print("No installed models to run.")
        return 3

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    manifest = {
        "run_id": run_id,
        "host": args.host,
        "models": models,
        "systems": [system.file_stem for system in systems],
        "structured_output": not args.no_structured_output,
        "started_at": run_id,
        "runs": [],
    }

    total = len(models) * len(systems)
    completed = 0

    for model in models:
        model_dir = sanitize_model_dir(model)
        for system in systems:
            completed += 1
            label = f"[{completed}/{total}] {model} × {system.file_stem}"
            print(label)

            messages = build_messages(system)
            started = time.time()

            try:
                result = generate_fsm(
                    model=model,
                    messages=messages,
                    host=args.host,
                    use_structured_output=not args.no_structured_output,
                )
            except Exception as exc:  # noqa: BLE001
                result_raw = {
                    "model": model,
                    "system": system.file_stem,
                    "error": str(exc),
                    "raw_text": "",
                    "parsed": None,
                    "valid": False,
                }
                raw_path = RAW_DIR / model_dir / f"{system.file_stem}.json"
                save_json(raw_path, result_raw)
                manifest["runs"].append(
                    {
                        "model": model,
                        "system": system.file_stem,
                        "status": "request_failed",
                        "error": str(exc),
                        "duration_sec": round(time.time() - started, 3),
                    }
                )
                continue

            result.system = system.file_stem
            elapsed = round(time.time() - started, 3)

            raw_record = {
                "model": model,
                "system": system.file_stem,
                "system_name": system.system_name,
                "domain": system.domain,
                "raw_text": result.raw_text,
                "parsed": result.parsed,
                "valid": result.valid,
                "error": result.error,
                "eval_count": result.eval_count,
                "eval_duration_ns": result.eval_duration_ns,
                "total_duration_ns": result.total_duration_ns,
                "duration_sec": elapsed,
            }
            save_json(RAW_DIR / model_dir / f"{system.file_stem}.json", raw_record)

            if result.parsed is not None:
                save_json(CLEANED_DIR / model_dir / f"{system.file_stem}.json", result.parsed)

            validation = validate_fsm_dict(result.parsed)
            metrics = compute_metrics(
                model=model,
                system_name=system.system_name,
                domain=system.domain,
                requirements=system.requirements,
                payload=result.parsed,
                validation=validation,
                eval_count=result.eval_count,
                eval_duration_ns=result.eval_duration_ns,
                total_duration_ns=result.total_duration_ns,
            )
            save_json(
                RESULTS_DIR / "details" / model_dir / f"{system.file_stem}.json",
                metrics.__dict__,
            )

            manifest["runs"].append(
                {
                    "model": model,
                    "system": system.file_stem,
                    "status": "ok" if result.valid else "invalid_json",
                    "valid_json": metrics.valid_json,
                    "schema_valid": metrics.schema_valid,
                    "duration_sec": elapsed,
                }
            )

            if args.sleep_seconds > 0:
                time.sleep(args.sleep_seconds)

    manifest["finished_at"] = datetime.now(timezone.utc).isoformat()
    save_json(RESULTS_DIR / f"manifest_{run_id}.json", manifest)
    save_json(RESULTS_DIR / "manifest_latest.json", manifest)

    print(f"\nDone. Manifest: {RESULTS_DIR / 'manifest_latest.json'}")
    print("Next: python scripts/evaluate.py && python scripts/plot_results.py")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local Ollama FSM benchmark")
    parser.add_argument("--models", nargs="*", help="Subset of models to run")
    parser.add_argument("--systems", nargs="*", help="Subset of system file stems")
    parser.add_argument("--include-optional", action="store_true", help="Include qwen2.5-coder:32b")
    parser.add_argument("--host", default="http://127.0.0.1:11434")
    parser.add_argument("--skip-missing", action="store_true")
    parser.add_argument("--no-structured-output", action="store_true")
    parser.add_argument("--sleep-seconds", type=float, default=0.0)
    args = parser.parse_args()
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
