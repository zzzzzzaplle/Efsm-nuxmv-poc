#!/usr/bin/env python3
"""Aggregate metrics from raw/cleaned outputs into CSV summaries.

Preserves strict structural determinism (M0 / ``deterministic``) and adds
guard-aware measures M1–M3 plus conflict-group diagnostics.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fsm_benchmark.config import CLEANED_DIR, RAW_DIR, RESULTS_DIR
from fsm_benchmark.dataset import load_all_systems
from fsm_benchmark.guard_aware import analyze_transitions
from fsm_benchmark.metrics import compute_metrics, validate_fsm_dict


def model_dir_to_name(model_dir: str) -> str:
    if "_latest" in model_dir:
        return model_dir.replace("_latest", ":latest")
    parts = model_dir.rsplit("_", 1)
    if len(parts) == 2:
        return f"{parts[0]}:{parts[1]}"
    return model_dir


def load_raw_record(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def build_guard_aware_campaign_summary(rows: list[dict], groups: list[dict]) -> dict:
    n = len(rows)
    g2 = [r for r in rows if _bool(r.get("schema_valid"))]

    def rate(pred, population: list[dict]) -> float | None:
        if not population:
            return None
        return sum(1 for r in population if pred(r)) / len(population)

    m0 = rate(lambda r: _bool(r.get("m0_pass")), rows)
    m1 = rate(lambda r: _bool(r.get("m1_pass")), rows)
    m2 = rate(lambda r: _bool(r.get("m2_pass")), rows)
    nested_m0 = rate(lambda r: _bool(r.get("m0_pass")), g2)
    nested_m1 = rate(lambda r: _bool(r.get("m1_pass")), g2)
    nested_m2 = rate(lambda r: _bool(r.get("m2_pass")), g2)

    unresolved_runs = sum(1 for r in rows if _bool(r.get("run_unresolved")))
    runs_with_conflicts = sum(1 for r in rows if int(r.get("conflict_group_count") or 0) > 0)

    group_verdicts = Counter(g.get("group_verdict") for g in groups)
    rule_hist: Counter[str] = Counter()
    for g in groups:
        for pair in g.get("pair_decisions") or []:
            rule_hist[f"{pair.get('rule')}:{pair.get('tag')}"] += 1

    parse_ok = sum(int(r.get("parse_ok_guards") or 0) for r in rows)
    parse_total = sum(int(r.get("parse_total_nonempty_guards") or 0) for r in rows)

    # Migration M0 × M1
    migration = Counter()
    for r in rows:
        migration[( _bool(r.get("m0_pass")), _bool(r.get("m1_pass")) )] += 1

    # Monotonicity check
    mono_violations = [
        {"model": r["model"], "system_stem": r.get("system_stem"), "m0": r.get("m0_pass"), "m1": r.get("m1_pass"), "m2": r.get("m2_pass")}
        for r in rows
        if (_bool(r.get("m0_pass")) and not _bool(r.get("m1_pass")))
        or (_bool(r.get("m1_pass")) and not _bool(r.get("m2_pass")))
    ]

    def by_key(key: str) -> dict:
        buckets: dict[str, list[dict]] = defaultdict(list)
        for r in rows:
            buckets[str(r.get(key))].append(r)
        out = {}
        for name, pop in sorted(buckets.items()):
            g2_pop = [r for r in pop if _bool(r.get("schema_valid"))]
            out[name] = {
                "runs": len(pop),
                "m0_rate": rate(lambda r: _bool(r.get("m0_pass")), pop),
                "m1_rate": rate(lambda r: _bool(r.get("m1_pass")), pop),
                "m2_rate": rate(lambda r: _bool(r.get("m2_pass")), pop),
                "nested_m0_rate": rate(lambda r: _bool(r.get("m0_pass")), g2_pop),
                "nested_m1_rate": rate(lambda r: _bool(r.get("m1_pass")), g2_pop),
                "nested_m2_rate": rate(lambda r: _bool(r.get("m2_pass")), g2_pop),
                "unresolved_runs": sum(1 for r in pop if _bool(r.get("run_unresolved"))),
                "conflict_groups": sum(int(r.get("conflict_group_count") or 0) for r in pop),
                "unresolved_groups": sum(int(r.get("unresolved_group_count") or 0) for r in pop),
            }
        return out

    return {
        "campaign": {
            "runs": n,
            "g2_runs": len(g2),
            "m0_rate": m0,
            "m1_rate": m1,
            "m2_rate": m2,
            "nested_m0_rate": nested_m0,
            "nested_m1_rate": nested_m1,
            "nested_m2_rate": nested_m2,
            "string_distinct_rate": rate(lambda r: _bool(r.get("string_distinct_pass")), rows),
            "unresolved_runs": unresolved_runs,
            "unresolved_run_rate": unresolved_runs / n if n else None,
            "runs_with_conflict_groups": runs_with_conflicts,
            "conflict_groups_total": len(groups),
            "group_verdict_counts": dict(group_verdicts),
            "m3_unresolved_groups": group_verdicts.get("UNRESOLVED", 0),
            "m3_unresolved_group_rate": (
                group_verdicts.get("UNRESOLVED", 0) / len(groups) if groups else None
            ),
            "parser_coverage_nonempty_guards": {
                "ok": parse_ok,
                "total": parse_total,
                "rate": (parse_ok / parse_total) if parse_total else None,
            },
            "rule_histogram": dict(rule_hist),
            "migration_m0_m1": {
                "m0_pass_m1_pass": migration[(True, True)],
                "m0_pass_m1_fail": migration[(True, False)],
                "m0_fail_m1_pass": migration[(False, True)],
                "m0_fail_m1_fail": migration[(False, False)],
            },
            "monotonicity_violations": mono_violations,
        },
        "by_model": by_key("model"),
        "by_system_stem": by_key("system_stem"),
    }


def evaluate_all(output_csv: Path) -> list[dict]:
    systems = {system.file_stem: system for system in load_all_systems()}
    rows: list[dict] = []
    all_groups: list[dict] = []

    for raw_path in sorted(RAW_DIR.glob("*/*.json")):
        record = load_raw_record(raw_path)
        model = record.get("model") or model_dir_to_name(raw_path.parent.name)
        system_stem = record.get("system") or raw_path.stem
        system = systems.get(system_stem)
        if system is None:
            continue

        parsed = record.get("parsed")
        cleaned_path = CLEANED_DIR / raw_path.parent.name / raw_path.name
        if cleaned_path.exists():
            parsed = json.loads(cleaned_path.read_text(encoding="utf-8"))

        validation = validate_fsm_dict(parsed)
        metrics = compute_metrics(
            model=model,
            system_name=system.system_name,
            domain=system.domain,
            requirements=system.requirements,
            payload=parsed,
            validation=validation,
            eval_count=record.get("eval_count"),
            eval_duration_ns=record.get("eval_duration_ns"),
            total_duration_ns=record.get("total_duration_ns"),
        )

        # Diagnostics from the same analysis path
        transitions = (parsed or {}).get("transitions") if isinstance(parsed, dict) else None
        ga = analyze_transitions(transitions, model=model, system=system_stem)
        for group in ga.groups:
            group = dict(group)
            group["system_stem"] = system_stem
            group["domain"] = system.domain
            group["schema_valid"] = metrics.schema_valid
            all_groups.append(group)

        row = metrics.__dict__.copy()
        row["system_stem"] = system_stem
        row["invalid_json"] = not metrics.valid_json
        row["missing_requirements"] = ",".join(metrics.missing_requirements)
        row["unreachable_states"] = ",".join(metrics.unreachable_states)
        row["validation_errors"] = "|".join(metrics.validation_errors)
        row["validation_warnings"] = "|".join(metrics.validation_warnings)
        rows.append(row)

        details_path = RESULTS_DIR / "details" / raw_path.parent.name / raw_path.name
        details_path.parent.mkdir(parents=True, exist_ok=True)
        details_path.write_text(json.dumps(row, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if not rows:
        return rows

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    summary = summarize(rows)
    summary_path = RESULTS_DIR / "summary_by_model.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Guard-aware diagnostics inside existing results/
    groups_path = RESULTS_DIR / "guard_aware_groups.json"
    groups_path.write_text(json.dumps(all_groups, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Flatten pair-level CSV for auditing
    pair_rows: list[dict] = []
    for g in all_groups:
        for pair in g.get("pair_decisions") or []:
            pair_rows.append(
                {
                    "model": g.get("model"),
                    "system_stem": g.get("system_stem"),
                    "state": g.get("state"),
                    "event": g.get("event"),
                    "group_size": g.get("group_size"),
                    "group_verdict": g.get("group_verdict"),
                    "guards_raw": " || ".join(g.get("guards_raw") or []),
                    "guards_norm": " || ".join(g.get("guards_norm") or []),
                    "parsed_variables": ",".join(g.get("parsed_variables") or []),
                    "pair_i": pair.get("i"),
                    "pair_j": pair.get("j"),
                    "verdict": pair.get("verdict"),
                    "rule": pair.get("rule"),
                    "tag": pair.get("tag"),
                    "guard_a_raw": pair.get("guard_a_raw"),
                    "guard_b_raw": pair.get("guard_b_raw"),
                    "guard_a_norm": pair.get("guard_a_norm"),
                    "guard_b_norm": pair.get("guard_b_norm"),
                }
            )
    pairs_csv = RESULTS_DIR / "guard_aware_pairs.csv"
    if pair_rows:
        with pairs_csv.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(pair_rows[0].keys()))
            writer.writeheader()
            writer.writerows(pair_rows)

    ga_summary = build_guard_aware_campaign_summary(rows, all_groups)
    ga_summary_path = RESULTS_DIR / "guard_aware_summary.json"
    ga_summary_path.write_text(json.dumps(ga_summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return rows


def summarize(rows: list[dict]) -> dict:
    by_model: dict[str, list[dict]] = {}
    for row in rows:
        by_model.setdefault(row["model"], []).append(row)

    summary: dict[str, dict] = {}
    for model, model_rows in by_model.items():
        n = len(model_rows)
        summary[model] = {
            "runs": n,
            "invalid_json_rate": round(sum(1 for r in model_rows if r["invalid_json"]) / n, 4),
            "avg_requirement_coverage": round(sum(r["requirement_coverage"] for r in model_rows) / n, 4),
            "avg_num_states": round(sum(r["num_states"] for r in model_rows) / n, 2),
            "avg_num_events": round(sum(r["num_events"] for r in model_rows) / n, 2),
            "avg_num_transitions": round(sum(r["num_transitions"] for r in model_rows) / n, 2),
            "determinism_rate": round(sum(1 for r in model_rows if r["deterministic"]) / n, 4),
            "m0_rate": round(sum(1 for r in model_rows if r.get("m0_pass")) / n, 4),
            "m1_rate": round(sum(1 for r in model_rows if r.get("m1_pass")) / n, 4),
            "m2_rate": round(sum(1 for r in model_rows if r.get("m2_pass")) / n, 4),
            "unresolved_run_rate": round(sum(1 for r in model_rows if r.get("run_unresolved")) / n, 4),
            "avg_unsupported_transitions": round(
                sum(r["unsupported_transitions"] for r in model_rows) / n, 2
            ),
            "avg_inferred_transitions": round(sum(r["inferred_transitions"] for r in model_rows) / n, 2),
            "schema_valid_rate": round(sum(1 for r in model_rows if r["schema_valid"]) / n, 4),
        }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate FSM benchmark outputs")
    parser.add_argument(
        "--csv",
        default=str(RESULTS_DIR / "metrics.csv"),
        help="Path to output CSV",
    )
    args = parser.parse_args()

    rows = evaluate_all(Path(args.csv))
    if not rows:
        print("No raw outputs found. Run scripts/run_experiment.py first.")
        return 1

    print(f"Wrote {len(rows)} rows to {args.csv}")
    print(f"Summary: {RESULTS_DIR / 'summary_by_model.json'}")
    print(f"Guard-aware groups: {RESULTS_DIR / 'guard_aware_groups.json'}")
    print(f"Guard-aware summary: {RESULTS_DIR / 'guard_aware_summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
