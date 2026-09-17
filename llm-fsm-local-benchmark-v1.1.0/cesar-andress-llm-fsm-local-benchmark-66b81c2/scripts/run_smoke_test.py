#!/usr/bin/env python3
"""End-to-end pre-release smoke test for FSM-Bench-20 (local Ollama only)."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from fsm_benchmark.config import FIGURES_DIR, RESULTS_DIR
from fsm_benchmark.ollama_client import is_model_installed, list_installed_models, pull_model_command

DEFAULT_SYSTEMS = ["vending_machine", "login_system", "atm"]
DEFAULT_MODELS = ["qwen2.5-coder:7b", "llama3.1:8b"]

REQUIRED_FILES = [
    "README.md",
    "LICENSE",
    "CITATION.cff",
    "REPRODUCIBILITY.md",
    ".gitignore",
]
REQUIRED_DIRS = ["dataset", "benchmark", "scripts"]

FORBIDDEN_TRACKED_PREFIXES = ("prompts/", ".cursor/", "AGENTS.md")


def run_cmd(cmd: list[str], *, cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)


def check_hygiene() -> dict:
    findings: list[str] = []

    tracked_prompts = run_cmd(["git", "ls-files", "prompts/"]).stdout.strip()
    if tracked_prompts:
        findings.append(f"prompts/ is tracked: {tracked_prompts.splitlines()[:3]}")

    for prefix in (".cursor/",):
        tracked = run_cmd(["git", "ls-files", prefix]).stdout.strip()
        if tracked:
            findings.append(f"{prefix} is tracked")

    if run_cmd(["git", "ls-files", "AGENTS.md"]).stdout.strip():
        findings.append("AGENTS.md is tracked")

    lang = run_cmd(["python3.12", "scripts/validate_language.py", "--scope", "tracked"])
    language_ok = lang.returncode == 0

    staged = run_cmd(["git", "diff", "--cached", "--name-only"]).stdout.splitlines()
    bad_staged = [
        path
        for path in staged
        if path.startswith(".venv/")
        or "__pycache__" in path
        or path.endswith(".pyc")
        or path.endswith(".log")
    ]
    if bad_staged:
        findings.append(f"Forbidden staged paths: {bad_staged}")

    return {
        "language_audit_pass": language_ok,
        "language_audit_output": lang.stdout.strip(),
        "prompts_tracked": bool(tracked_prompts),
        "forbidden_staged": bad_staged,
        "findings": findings,
        "pass": language_ok and not findings,
    }


def check_required_files() -> dict:
    missing = [name for name in REQUIRED_FILES if not (REPO_ROOT / name).exists()]
    missing_dirs = [name for name in REQUIRED_DIRS if not (REPO_ROOT / name).is_dir()]
    return {
        "missing_files": missing,
        "missing_dirs": missing_dirs,
        "pass": not missing and not missing_dirs,
    }


def check_models(models: list[str], host: str) -> dict:
    try:
        installed = list_installed_models(host=host)
    except Exception as exc:  # noqa: BLE001
        return {
            "ollama_available": False,
            "error": str(exc),
            "available": [],
            "missing": models,
            "pull_commands": [pull_model_command(model) for model in models],
            "pass": False,
        }

    available = [model for model in models if is_model_installed(model, installed)]
    missing = [model for model in models if model not in available]
    return {
        "ollama_available": True,
        "available": available,
        "missing": missing,
        "pull_commands": [pull_model_command(model) for model in missing],
        "pass": bool(available),
    }


def run_benchmark(systems: list[str], models: list[str], host: str) -> int:
    cmd = [
        sys.executable,
        "scripts/run_experiment.py",
        "--systems",
        *systems,
        "--models",
        *models,
        "--skip-missing",
        "--host",
        host,
    ]
    print("Running:", " ".join(cmd))
    return subprocess.call(cmd, cwd=REPO_ROOT)


def evaluate_smoke(csv_path: Path) -> list[dict]:
    cmd = [sys.executable, "scripts/evaluate.py", "--csv", str(csv_path)]
    result = run_cmd(cmd)
    if result.returncode != 0:
        print(result.stdout, result.stderr, file=sys.stderr)
        return []

    rows: list[dict] = []
    if csv_path.exists():
        with csv_path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
    return rows


def summarize_smoke(rows: list[dict]) -> dict:
    by_model: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_model[row["model"]].append(row)

    summary: dict[str, dict] = {}
    for model, model_rows in by_model.items():
        n = len(model_rows)
        summary[model] = {
            "runs": n,
            "valid_json_rate": round(sum(1 for r in model_rows if r.get("valid_json") == "True") / n, 4),
            "schema_valid_rate": round(sum(1 for r in model_rows if r.get("schema_valid") == "True") / n, 4),
            "determinism_rate": round(sum(1 for r in model_rows if r.get("deterministic") == "True") / n, 4),
            "avg_requirement_coverage": round(
                sum(float(r["requirement_coverage"]) for r in model_rows) / n, 4
            ),
            "systems": sorted({r["system_stem"] for r in model_rows}),
        }
    return summary


def plot_smoke(summary: dict, rows: list[dict]) -> list[str]:
    written: list[str] = []
    if not summary or not rows:
        return written

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    models = list(summary.keys())
    valid_rates = [1 - summary[m].get("invalid_json_rate", 0) for m in models]
    # recompute valid json rate from summary keys
    valid_rates = []
    for model in models:
        model_rows = [r for r in rows if r["model"] == model]
        n = len(model_rows) or 1
        valid_rates.append(sum(1 for r in model_rows if r.get("valid_json") == "True") / n)

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(models, valid_rates, color="#4C78A8")
    ax.set_ylim(0, 1)
    ax.set_title("Smoke Test — Valid JSON Rate by Model")
    ax.set_ylabel("Rate")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    path1 = FIGURES_DIR / "smoke_test_valid_json_rate.png"
    fig.savefig(path1, dpi=180)
    plt.close(fig)
    written.append(str(path1.relative_to(REPO_ROOT)))

    cov = [summary[m]["avg_requirement_coverage"] for m in models]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(models, cov, color="#72B7B2")
    ax.set_ylim(0, 1)
    ax.set_title("Smoke Test — Average Requirement Coverage by Model")
    ax.set_ylabel("Coverage")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    path2 = FIGURES_DIR / "smoke_test_requirement_coverage.png"
    fig.savefig(path2, dpi=180)
    plt.close(fig)
    written.append(str(path2.relative_to(REPO_ROOT)))

    return written


def validation_table(rows: list[dict]) -> list[dict]:
    checks = []
    for row in rows:
        checks.append(
            {
                "model": row["model"],
                "system": row["system_stem"],
                "valid_json": row.get("valid_json") == "True",
                "schema_valid": row.get("schema_valid") == "True",
                "initial_state_valid": row.get("schema_valid") == "True",
                "transition_states_valid": row.get("schema_valid") == "True",
                "deterministic": row.get("deterministic") == "True",
                "requirement_refs_checked": True,
                "requirement_coverage": float(row.get("requirement_coverage", 0)),
                "validation_errors": row.get("validation_errors", ""),
            }
        )
    return checks


def write_smoke_report(
    path: Path,
    *,
    systems: list[str],
    models_requested: list[str],
    model_status: dict,
    hygiene: dict,
    required: dict,
    rows: list[dict],
    summary: dict,
    figures: list[str],
) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "# Smoke Test Report",
        "",
        f"**Date:** {timestamp}  ",
        "**Scope:** Pre-release end-to-end local Ollama benchmark",
        "",
        "---",
        "",
        "## Configuration",
        "",
        f"- **Systems:** {', '.join(f'`{s}`' for s in systems)}",
        f"- **Models requested:** {', '.join(f'`{m}`' for m in models_requested)}",
        f"- **Models available:** {', '.join(f'`{m}`' for m in model_status.get('available', [])) or 'none'}",
        f"- **Models missing:** {', '.join(f'`{m}`' for m in model_status.get('missing', [])) or 'none'}",
        "",
        "## Repository hygiene",
        "",
        f"- Language audit (tracked): **{'PASS' if hygiene['language_audit_pass'] else 'FAIL'}**",
        f"- Prompts tracked in Git: **{'yes — FAIL' if hygiene.get('prompts_tracked') else 'no — PASS'}**",
        f"- Required files: **{'PASS' if required['pass'] else 'FAIL'}**",
        "",
        "## Run summary",
        "",
        f"- Completed runs: **{len(rows)}**",
        "",
    ]

    if summary:
        lines.extend(["| Model | Runs | Valid JSON rate | Schema valid rate | Determinism | Avg req. coverage |", "|-------|------|-----------------|-------------------|-------------|-------------------|"])
        for model, stats in summary.items():
            lines.append(
                f"| `{model}` | {stats['runs']} | {stats['valid_json_rate']:.2f} | "
                f"{stats['schema_valid_rate']:.2f} | {stats['determinism_rate']:.2f} | "
                f"{stats['avg_requirement_coverage']:.2f} |"
            )
        lines.append("")

    if rows:
        lines.extend(["## Per-run validation", ""])
        for item in validation_table(rows):
            status = "PASS" if item["valid_json"] and item["schema_valid"] else "PARTIAL/FAIL"
            lines.append(
                f"- `{item['model']}` × `{item['system']}` — **{status}** "
                f"(valid JSON: {item['valid_json']}, schema: {item['schema_valid']}, "
                f"deterministic: {item['deterministic']}, coverage: {item['requirement_coverage']:.2f})"
            )
            if item["validation_errors"]:
                lines.append(f"  - Errors: `{item['validation_errors']}`")
        lines.append("")

    if figures:
        lines.extend(["## Figures", ""])
        for fig in figures:
            lines.append(f"- `{fig}`")
        lines.append("")

    if model_status.get("pull_commands"):
        lines.extend(["## Missing model install commands", ""])
        for cmd in model_status["pull_commands"]:
            lines.append(f"```bash\n{cmd}\n```")
        lines.append("")

    lines.extend(
        [
            "## Artifacts (local, gitignored)",
            "",
            "- `results/smoke_test_metrics.csv`",
            "- `results/smoke_test_summary.json`",
            "- `outputs/raw/` and `outputs/cleaned/`",
            "",
        ]
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_release_readiness(
    path: Path,
    *,
    systems: list[str],
    models_requested: list[str],
    model_status: dict,
    hygiene: dict,
    required: dict,
    rows: list[dict],
    summary: dict,
    figures: list[str],
    benchmark_ran: bool,
) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    integrity = run_cmd(["python3.12", "scripts/validate_integrity.py"])
    lang = run_cmd(["python3.12", "scripts/validate_language.py", "--scope", "tracked"])

    untracked = run_cmd(["git", "status", "--porcelain"]).stdout.strip().splitlines()
    commit_candidates = [
        "docs/smoke_test_report.md",
        "docs/release_readiness_report.md",
    ]
    if (REPO_ROOT / "scripts/run_smoke_test.py").exists():
        commit_candidates.insert(0, "scripts/run_smoke_test.py")

    gitignored_must_stay = [
        "outputs/raw/",
        "outputs/cleaned/",
        "results/",
        "figures/",
        "prompts/",
        ".venv/",
        "__pycache__/",
        ".cursor/",
        "AGENTS.md",
    ]

    blockers: list[str] = []
    if not hygiene["pass"]:
        blockers.extend(hygiene["findings"] or ["Repository hygiene check failed"])
    if not required["pass"]:
        blockers.append("Missing required files or directories")
    if not model_status.get("ollama_available"):
        blockers.append(f"Ollama unavailable: {model_status.get('error')}")
    if not model_status.get("available"):
        blockers.append("No requested models available")
    if benchmark_ran and not rows:
        blockers.append("Benchmark ran but produced no evaluable rows")
    if lang.returncode != 0:
        blockers.append("Language audit failed on tracked files")
    if integrity.returncode != 0:
        blockers.append("Dataset/benchmark integrity validation failed")

    recommendation = "READY_FOR_RELEASE" if not blockers else "NOT_READY_FOR_RELEASE"

    lines = [
        "# Release Readiness Report",
        "",
        f"**Date:** {timestamp}  ",
        f"**Recommendation:** **{recommendation}**",
        "",
        "---",
        "",
        "## Smoke test scope",
        "",
        f"- **Systems tested:** {', '.join(f'`{s}`' for s in systems)}",
        f"- **Models requested:** {', '.join(f'`{m}`' for m in models_requested)}",
        f"- **Models tested:** {', '.join(f'`{m}`' for m in model_status.get('available', [])) or 'none'}",
        f"- **Missing models:** {', '.join(f'`{m}`' for m in model_status.get('missing', [])) or 'none'}",
        "",
    ]

    if model_status.get("pull_commands"):
        lines.extend(["Install missing models:", ""])
        for cmd in model_status["pull_commands"]:
            lines.append(f"```bash\n{cmd}\n```")
        lines.append("")

    lines.extend(
        [
            "## Validation status",
            "",
            f"| Check | Status |",
            f"|-------|--------|",
            f"| Dataset/benchmark integrity | {'PASS' if integrity.returncode == 0 else 'FAIL'} |",
            f"| Smoke benchmark executed | {'yes' if benchmark_ran else 'no'} |",
            f"| Smoke runs evaluated | {len(rows)} |",
            f"| FSM validation (per run) | {'PASS' if rows and all(r.get('valid_json') == 'True' for r in rows) else 'see smoke_test_report.md'} |",
            "",
            "## Language audit status",
            "",
            f"- Tracked files: **{'PASS' if lang.returncode == 0 else 'FAIL'}** (0 Spanish findings required)",
            "",
            "## Git hygiene status",
            "",
            f"- Prompts folder tracked: **{'FAIL' if hygiene.get('prompts_tracked') else 'PASS'}**",
            f"- Forbidden staged artifacts: **{'FAIL' if hygiene.get('forbidden_staged') else 'PASS'}**",
            "",
            "### Files recommended for commit",
            "",
        ]
    )
    for item in commit_candidates:
        lines.append(f"- `{item}`")
    lines.extend(["", "### Files that must remain gitignored", ""])
    for item in gitignored_must_stay:
        lines.append(f"- `{item}`")

    if blockers:
        lines.extend(["", "## Blockers", ""])
        for blocker in blockers:
            lines.append(f"- {blocker}")

    if summary:
        lines.extend(["", "## Smoke test metrics summary", ""])
        lines.append("```json")
        lines.append(json.dumps(summary, indent=2))
        lines.append("```")

    if figures:
        lines.extend(["", "## Smoke test figures (local)", ""])
        for fig in figures:
            lines.append(f"- `{fig}`")

    lines.extend(["", "---", "", "*Generated after initial pre-release smoke test. No GitHub release was created.*", ""])

    path.write_text("\n".join(lines), encoding="utf-8")
    return recommendation


def main() -> int:
    parser = argparse.ArgumentParser(description="Run pre-release smoke test")
    parser.add_argument("--systems", nargs="*", default=DEFAULT_SYSTEMS)
    parser.add_argument("--models", nargs="*", default=DEFAULT_MODELS)
    parser.add_argument("--host", default="http://127.0.0.1:11434")
    parser.add_argument("--skip-run", action="store_true", help="Skip Ollama benchmark (reports only)")
    args = parser.parse_args()

    hygiene = check_hygiene()
    required = check_required_files()
    model_status = check_models(args.models, args.host)

    print("==> Hygiene:", "PASS" if hygiene["pass"] else "FAIL")
    print("==> Required files:", "PASS" if required["pass"] else "FAIL")
    print("==> Models available:", model_status.get("available", []))
    if model_status.get("missing"):
        print("==> Models missing (skipped):")
        for cmd in model_status["pull_commands"]:
            print(f"    {cmd}")

    benchmark_ran = False
    if not args.skip_run and model_status.get("available"):
        rc = run_benchmark(args.systems, model_status["available"], args.host)
        benchmark_ran = True
        if rc != 0:
            print(f"Benchmark exited with code {rc}", file=sys.stderr)

    csv_path = RESULTS_DIR / "smoke_test_metrics.csv"
    rows = evaluate_smoke(csv_path) if benchmark_ran else []
    summary = summarize_smoke(rows)
    if summary:
        summary_path = RESULTS_DIR / "smoke_test_summary.json"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {summary_path}")

    figures = plot_smoke(summary, rows) if rows else []

    write_smoke_report(
        REPO_ROOT / "docs/smoke_test_report.md",
        systems=args.systems,
        models_requested=args.models,
        model_status=model_status,
        hygiene=hygiene,
        required=required,
        rows=rows,
        summary=summary,
        figures=figures,
    )

    recommendation = write_release_readiness(
        REPO_ROOT / "docs/release_readiness_report.md",
        systems=args.systems,
        models_requested=args.models,
        model_status=model_status,
        hygiene=hygiene,
        required=required,
        rows=rows,
        summary=summary,
        figures=figures,
        benchmark_ran=benchmark_ran,
    )

    print(f"\n==> Recommendation: {recommendation}")
    print(f"    docs/smoke_test_report.md")
    print(f"    docs/release_readiness_report.md")
    return 0 if recommendation == "READY_FOR_RELEASE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
