#!/usr/bin/env python3
"""Check which configured Ollama models are installed locally."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fsm_benchmark.config import MODELS, OPTIONAL_MODELS, OLLAMA_HOST
from fsm_benchmark.ollama_client import is_model_installed, list_installed_models, pull_model_command


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Ollama model availability")
    parser.add_argument("--include-optional", action="store_true", help="Also check optional models")
    parser.add_argument("--host", default=OLLAMA_HOST, help="Ollama API host")
    args = parser.parse_args()

    models = list(MODELS)
    if args.include_optional:
        models.extend(OPTIONAL_MODELS)

    try:
        installed = list_installed_models(host=args.host)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: Could not reach Ollama at {args.host}: {exc}")
        print("Start the daemon with: ollama serve")
        return 1

    missing: list[str] = []
    present: list[str] = []

    print(f"Ollama host: {args.host}\n")
    for model in models:
        if is_model_installed(model, installed):
            present.append(model)
            print(f"[OK]   {model}")
        else:
            missing.append(model)
            print(f"[MISS] {model}")
            print(f"       Install: {pull_model_command(model)}")

    print("\nSummary")
    print(f"  Installed: {len(present)}/{len(models)}")
    print(f"  Missing:   {len(missing)}/{len(models)}")

    if missing:
        print("\nInstall all missing models:")
        for model in missing:
            print(f"  {pull_model_command(model)}")
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
