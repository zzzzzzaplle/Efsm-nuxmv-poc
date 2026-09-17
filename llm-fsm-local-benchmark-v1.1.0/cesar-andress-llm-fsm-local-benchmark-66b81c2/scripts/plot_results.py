#!/usr/bin/env python3
"""Generate PNG and SVG plots from benchmark metrics."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fsm_benchmark.config import FIGURES_DIR, RESULTS_DIR


def load_rows(csv_path: Path) -> list[dict]:
    with csv_path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_summary(summary_path: Path) -> dict:
    if summary_path.exists():
        return json.loads(summary_path.read_text(encoding="utf-8"))
    return {}


def save_figure(fig: plt.Figure, stem: str) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / f"{stem}.png", dpi=180)
    fig.savefig(FIGURES_DIR / f"{stem}.svg")
    plt.close(fig)


def plot_model_bars(summary: dict) -> None:
    if not summary:
        return

    models = list(summary.keys())
    metrics = [
        ("invalid_json_rate", "Invalid JSON rate"),
        ("schema_valid_rate", "Schema valid rate"),
        ("determinism_rate", "Determinism rate"),
        ("avg_requirement_coverage", "Avg requirement coverage"),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    axes = axes.flatten()

    for ax, (key, title) in zip(axes, metrics):
        values = [summary[model][key] for model in models]
        ax.bar(models, values, color="#4C78A8")
        ax.set_title(title)
        ax.set_ylim(0, 1 if "rate" in key or "coverage" in key else max(values or [1]) * 1.2)
        ax.tick_params(axis="x", rotation=35)

    fig.suptitle("FSM Benchmark — Model Comparison")
    save_figure(fig, "model_comparison")


def plot_coverage_heatmap(rows: list[dict]) -> None:
    if not rows:
        return

    models = sorted({row["model"] for row in rows})
    systems = sorted({row["system_stem"] for row in rows})
    index = {(row["model"], row["system_stem"]): float(row["requirement_coverage"]) for row in rows}

    matrix = [[index.get((model, system), 0.0) for system in systems] for model in models]

    fig, ax = plt.subplots(figsize=(14, max(4, len(models) * 0.6)))
    image = ax.imshow(matrix, aspect="auto", cmap="YlGn", vmin=0, vmax=1)
    ax.set_xticks(range(len(systems)))
    ax.set_xticklabels(systems, rotation=60, ha="right")
    ax.set_yticks(range(len(models)))
    ax.set_yticklabels(models)
    ax.set_title("Requirement Coverage by Model and System")
    fig.colorbar(image, ax=ax, label="Coverage")
    save_figure(fig, "coverage_heatmap")


def plot_transition_counts(rows: list[dict]) -> None:
    if not rows:
        return

    models = sorted({row["model"] for row in rows})
    avg_transitions = []
    avg_unsupported = []
    avg_inferred = []

    for model in models:
        model_rows = [row for row in rows if row["model"] == model]
        n = len(model_rows)
        avg_transitions.append(sum(int(row["num_transitions"]) for row in model_rows) / n)
        avg_unsupported.append(sum(int(row["unsupported_transitions"]) for row in model_rows) / n)
        avg_inferred.append(sum(int(row["inferred_transitions"]) for row in model_rows) / n)

    x = range(len(models))
    width = 0.25
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar([i - width for i in x], avg_transitions, width=width, label="Transitions")
    ax.bar(x, avg_unsupported, width=width, label="Unsupported")
    ax.bar([i + width for i in x], avg_inferred, width=width, label="Inferred")
    ax.set_xticks(list(x))
    ax.set_xticklabels(models, rotation=30, ha="right")
    ax.set_title("Average Transition Counts by Model")
    ax.legend()
    save_figure(fig, "transition_counts")


def plot_domain_coverage(rows: list[dict]) -> None:
    if not rows:
        return

    domains = sorted({row["domain"] for row in rows})
    coverage_by_domain: dict[str, list[float]] = {domain: [] for domain in domains}
    for row in rows:
        coverage_by_domain[row["domain"]].append(float(row["requirement_coverage"]))

    averages = [sum(values) / len(values) for values in coverage_by_domain.values()]

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(domains, averages, color="#72B7B2")
    ax.set_ylim(0, 1)
    ax.set_title("Average Requirement Coverage by Domain")
    ax.tick_params(axis="x", rotation=35)
    save_figure(fig, "domain_coverage")


def main() -> int:
    parser = argparse.ArgumentParser(description="Plot benchmark results")
    parser.add_argument("--csv", default=str(RESULTS_DIR / "metrics.csv"))
    parser.add_argument("--summary", default=str(RESULTS_DIR / "summary_by_model.json"))
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"Missing metrics CSV: {csv_path}. Run scripts/evaluate.py first.")
        return 1

    rows = load_rows(csv_path)
    summary = load_summary(Path(args.summary))

    plot_model_bars(summary)
    plot_coverage_heatmap(rows)
    plot_transition_counts(rows)
    plot_domain_coverage(rows)

    print(f"Figures written to {FIGURES_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
