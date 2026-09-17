"""FSM-level guard-aware determinism analysis (M0–M3)."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from ..metrics import compute_determinism
from .classify import Lexicon, classify_group
from .normalize import normalize_guard
from .parse import parse_guard


@dataclass
class GuardAwareRunResult:
    m0_pass: bool
    m1_pass: bool
    m2_pass: bool
    string_distinct_pass: bool
    conflict_group_count: int
    unresolved_group_count: int
    nondeterministic_group_count: int
    resolved_group_count: int
    nondeterministic_pairs_strict: int
    groups: list[dict[str, Any]] = field(default_factory=list)
    rule_histogram: dict[str, int] = field(default_factory=dict)
    parse_ok_guards: int = 0
    parse_total_nonempty_guards: int = 0

    @property
    def m3_unresolved_groups(self) -> int:
        return self.unresolved_group_count

    @property
    def run_unresolved(self) -> bool:
        return self.unresolved_group_count > 0 and self.nondeterministic_group_count == 0 and not self.m1_pass


def analyze_transitions(
    transitions: list[dict[str, Any]] | None,
    *,
    model: str = "",
    system: str = "",
    lexicon: Lexicon | None = None,
) -> GuardAwareRunResult:
    transitions = transitions or []
    lex = lexicon or Lexicon.load()

    m0_pass, nondet_pairs = compute_determinism(transitions)

    groups_map: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for transition in transitions:
        key = (str(transition.get("source", "")), str(transition.get("event", "")))
        groups_map[key].append(transition)

    conflict_items = {k: v for k, v in groups_map.items() if len(v) >= 2}

    # Parser coverage over all non-empty guards in the machine
    parse_ok = 0
    parse_total = 0
    for transition in transitions:
        raw = transition.get("guard", "")
        if normalize_guard(str(raw) if raw is not None else "") == "":
            continue
        parse_total += 1
        if parse_guard(raw).ok:
            parse_ok += 1

    group_records: list[dict[str, Any]] = []
    rule_hist: dict[str, int] = defaultdict(int)
    unresolved = 0
    nondet_groups = 0
    resolved = 0
    m1_ok = True
    m2_ok = True
    string_ok = True

    if not conflict_items:
        # No conflicts ⇒ all measures pass
        return GuardAwareRunResult(
            m0_pass=m0_pass,
            m1_pass=True,
            m2_pass=True,
            string_distinct_pass=True,
            conflict_group_count=0,
            unresolved_group_count=0,
            nondeterministic_group_count=0,
            resolved_group_count=0,
            nondeterministic_pairs_strict=nondet_pairs,
            groups=[],
            rule_histogram={},
            parse_ok_guards=parse_ok,
            parse_total_nonempty_guards=parse_total,
        )

    for (state, event), members in sorted(conflict_items.items(), key=lambda x: (x[0][0], x[0][1])):
        guards = [m.get("guard", "") for m in members]
        result = classify_group(guards, lex)
        for pair in result["pair_decisions"]:
            key = f"{pair['rule']}:{pair['tag']}"
            rule_hist[key] += 1

        if result["group_verdict"] == "RESOLVED_DETERMINISTIC":
            resolved += 1
        elif result["group_verdict"] == "NON_DETERMINISTIC":
            nondet_groups += 1
            m1_ok = False
            m2_ok = False
        else:
            unresolved += 1
            m1_ok = False
            # m2 still ok (UNKNOWN-as-pass)

        if not result["string_distinct"]:
            string_ok = False

        variables: list[str] = []
        for g in guards:
            pr = parse_guard(g)
            variables.extend(pr.variables)

        group_records.append(
            {
                "model": model,
                "system": system,
                "state": state,
                "event": event,
                "group_size": result["group_size"],
                "guards_raw": result["guards_raw"],
                "guards_norm": result["guards_norm"],
                "parsed_variables": sorted(set(variables)),
                "pair_decisions": result["pair_decisions"],
                "group_verdict": result["group_verdict"],
                "string_distinct": result["string_distinct"],
                "manual_annotation": "",
                "agreement_flag": "",
            }
        )

    # Monotonicity with M0: if strict-deterministic, there are no conflict groups.
    # If somehow m0_pass with conflicts, treat as bug — trust compute_determinism.
    if m0_pass:
        m1_ok = True
        m2_ok = True
        string_ok = True

    return GuardAwareRunResult(
        m0_pass=m0_pass,
        m1_pass=m1_ok,
        m2_pass=m2_ok,
        string_distinct_pass=string_ok,
        conflict_group_count=len(conflict_items),
        unresolved_group_count=unresolved,
        nondeterministic_group_count=nondet_groups,
        resolved_group_count=resolved,
        nondeterministic_pairs_strict=nondet_pairs,
        groups=group_records,
        rule_histogram=dict(rule_hist),
        parse_ok_guards=parse_ok,
        parse_total_nonempty_guards=parse_total,
    )


def run_result_to_metrics_fields(result: GuardAwareRunResult) -> dict[str, Any]:
    return {
        "m0_pass": result.m0_pass,
        "m1_pass": result.m1_pass,
        "m2_pass": result.m2_pass,
        "string_distinct_pass": result.string_distinct_pass,
        "conflict_group_count": result.conflict_group_count,
        "unresolved_group_count": result.unresolved_group_count,
        "nondeterministic_group_count": result.nondeterministic_group_count,
        "resolved_group_count": result.resolved_group_count,
        "run_unresolved": result.run_unresolved,
        "parse_ok_guards": result.parse_ok_guards,
        "parse_total_nonempty_guards": result.parse_total_nonempty_guards,
    }
