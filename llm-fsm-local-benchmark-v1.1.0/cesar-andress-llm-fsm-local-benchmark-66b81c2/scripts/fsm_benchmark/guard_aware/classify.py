"""Pair / group / run classification under the frozen guard-aware criterion."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from .normalize import is_empty_guard, normalize_guard, normalize_identifier
from .parse import Atom, ParseResult, parse_guard


PairVerdict = Literal["EXCLUSIVE", "OVERLAP", "UNKNOWN"]
GroupVerdict = Literal["RESOLVED_DETERMINISTIC", "NON_DETERMINISTIC", "UNRESOLVED"]


@dataclass(frozen=True)
class Lexicon:
    polarity_pairs: list[tuple[str, str]]
    negation_markers: list[str]

    @classmethod
    def load(cls, path: Path | None = None) -> "Lexicon":
        lexicon_path = path or Path(__file__).with_name("lexicon.json")
        payload = json.loads(lexicon_path.read_text(encoding="utf-8"))
        pairs = [(normalize_identifier(a), normalize_identifier(b)) for a, b in payload["polarity_pairs"]]
        markers = [normalize_identifier(m) for m in payload.get("negation_markers", [])]
        return cls(polarity_pairs=pairs, negation_markers=markers)


@dataclass
class PairDecision:
    guard_a_raw: str
    guard_b_raw: str
    guard_a_norm: str
    guard_b_norm: str
    verdict: PairVerdict
    rule: str
    tag: str
    variables_a: list[str] = field(default_factory=list)
    variables_b: list[str] = field(default_factory=list)
    parse_ok_a: bool = False
    parse_ok_b: bool = False


def _bool_constraint(atom: Atom) -> tuple[str, bool]:
    """Return (variable, required_truth_value)."""
    truth = True if atom.value is True or atom.value is None else bool(atom.value)
    if atom.negated:
        truth = not truth
    return atom.variable, truth


def _interval_from_atom(atom: Atom) -> tuple[float, bool, float, bool] | None:
    """Map numeric comparison to (lo, lo_closed, hi, hi_closed); None if not numeric."""
    if atom.kind != "cmp" or atom.op is None:
        return None
    if not isinstance(atom.value, (int, float)) or isinstance(atom.value, bool):
        return None
    v = float(atom.value)
    op = atom.op
    neg = atom.negated
    # Apply negation by flipping operator
    if neg:
        flip = {"<": "≥", "≤": ">", ">": "≤", "≥": "<", "=": "≠", "≠": "="}
        op = flip[op]  # type: ignore[assignment]

    inf = float("inf")
    if op == ">":
        return (v, False, inf, False)
    if op == "≥":
        return (v, True, inf, False)
    if op == "<":
        return (-inf, False, v, False)
    if op == "≤":
        return (-inf, False, v, True)
    if op == "=":
        return (v, True, v, True)
    if op == "≠":
        return None  # handled separately
    return None


def _intervals_intersect(
    a: tuple[float, bool, float, bool],
    b: tuple[float, bool, float, bool],
) -> bool:
    a_lo, a_lc, a_hi, a_hc = a
    b_lo, b_lc, b_hi, b_hc = b
    lo = max(a_lo, b_lo)
    hi = min(a_hi, b_hi)
    if lo < hi:
        return True
    if lo > hi:
        return False
    # lo == hi: need both closed
    left_closed = a_lc if lo == a_lo else b_lc
    right_closed = a_hc if hi == a_hi else b_hc
    # When lo comes from both, need closed from each side contribution
    if lo == a_lo and lo == b_lo:
        left_closed = a_lc and b_lc
    if hi == a_hi and hi == b_hi:
        right_closed = a_hc and b_hc
    return left_closed and right_closed


def _same_var_verdict(atoms_a: list[Atom], atoms_b: list[Atom]) -> tuple[PairVerdict, str]:
    """Decide exclusivity for two conjunctive atom lists over the same variable set size 1."""
    # Collect per-variable constraints from both sides
    vars_a = {a.variable for a in atoms_a}
    vars_b = {a.variable for a in atoms_b}
    if vars_a != vars_b or len(vars_a) != 1:
        # Multi-var conjunctions on same set: try pairwise product conservatively
        if not vars_a.intersection(vars_b):
            return "UNKNOWN", "cross_var"
        # Shared variables exist — check each shared var; if any shared var exclusive → EXCLUSIVE
        shared = vars_a & vars_b
        any_exclusive = False
        any_overlap = False
        saw_unknown = False
        for var in shared:
            va = [a for a in atoms_a if a.variable == var]
            vb = [a for a in atoms_b if a.variable == var]
            verdict, tag = _same_var_atoms(va, vb)
            if verdict == "EXCLUSIVE":
                any_exclusive = True
            elif verdict == "OVERLAP":
                any_overlap = True
            else:
                saw_unknown = True
        # Conjunctions: exclusive if ANY conjunct pair on a shared var is exclusive
        # (g1 ∧ …) ∧ (h1 ∧ …) unsat if some gi∧hj unsat on same var — actually wrong.
        # Correct: (A∧B) and (C∧D) unsat if the combined conjunction is unsat.
        # Conservative: if any shared-var atom groups are exclusive, treat EXCLUSIVE;
        # if all shared are OVERLAP and no UNKNOWN, OVERLAP; else UNKNOWN.
        if any_exclusive:
            return "EXCLUSIVE", "interval"
        if any_overlap and not saw_unknown:
            return "OVERLAP", "same_var_satisfiable"
        return "UNKNOWN", "unparsed"

    return _same_var_atoms(atoms_a, atoms_b)


def _same_var_atoms(atoms_a: list[Atom], atoms_b: list[Atom]) -> tuple[PairVerdict, str]:
    bools_a = [a for a in atoms_a if a.kind == "bool"]
    bools_b = [a for a in atoms_b if a.kind == "bool"]
    cmps_a = [a for a in atoms_a if a.kind == "cmp"]
    cmps_b = [a for a in atoms_b if a.kind == "cmp"]

    # Boolean polarity on same variable
    if bools_a and bools_b and not cmps_a and not cmps_b:
        vals_a = {_bool_constraint(a)[1] for a in bools_a}
        vals_b = {_bool_constraint(a)[1] for a in bools_b}
        if len(vals_a) > 1 or len(vals_b) > 1:
            return "OVERLAP", "same_var_satisfiable"  # contradictory side → treat carefully
        if vals_a != vals_b:
            return "EXCLUSIVE", "bool"
        return "OVERLAP", "same_var_satisfiable"

    # Equality / enum style on string or number literals
    eqs_a = [a for a in cmps_a if a.op == "="]
    eqs_b = [a for a in cmps_b if a.op == "="]
    neqs_a = [a for a in cmps_a if a.op == "≠"]
    neqs_b = [a for a in cmps_b if a.op == "≠"]

    if eqs_a and eqs_b:
        for ea in eqs_a:
            for eb in eqs_b:
                if ea.value != eb.value:
                    return "EXCLUSIVE", "enum"
                return "OVERLAP", "same_var_satisfiable"

    if eqs_a and neqs_b:
        for ea in eqs_a:
            for nb in neqs_b:
                if ea.value == nb.value:
                    return "EXCLUSIVE", "enum"
    if eqs_b and neqs_a:
        for eb in eqs_b:
            for na in neqs_a:
                if eb.value == na.value:
                    return "EXCLUSIVE", "enum"

    # Numeric intervals
    intervals_a = [_interval_from_atom(a) for a in cmps_a]
    intervals_b = [_interval_from_atom(a) for a in cmps_b]
    if any(i is None for i in intervals_a + intervals_b) and (cmps_a or cmps_b):
        # ≠ or non-numeric remnants
        if all(a.op == "≠" for a in cmps_a + cmps_b) and cmps_a and cmps_b:
            return "OVERLAP", "same_var_satisfiable"
        # Mix of parseable intervals and ≠
        pass

    ia = [i for i in intervals_a if i is not None]
    ib = [i for i in intervals_b if i is not None]
    if ia and ib:
        # Intersect within each side first (conjunction)
        def intersect_all(items: list[tuple[float, bool, float, bool]]):
            acc = items[0]
            for it in items[1:]:
                if not _intervals_intersect(acc, it):
                    return None
                lo = max(acc[0], it[0])
                hi = min(acc[2], it[2])
                lc = (acc[1] if lo == acc[0] else True) and (it[1] if lo == it[0] else True)
                hc = (acc[3] if hi == acc[2] else True) and (it[3] if hi == it[2] else True)
                if lo == acc[0] and lo == it[0]:
                    lc = acc[1] and it[1]
                if hi == acc[2] and hi == it[2]:
                    hc = acc[3] and it[3]
                acc = (lo, lc, hi, hc)
            return acc

        sa = intersect_all(ia)
        sb = intersect_all(ib)
        if sa is None or sb is None:
            # A side is internally unsat — still OVERLAP with other? Treat UNKNOWN
            return "UNKNOWN", "unparsed"
        if _intervals_intersect(sa, sb):
            return "OVERLAP", "same_var_satisfiable"
        return "EXCLUSIVE", "interval"

    return "UNKNOWN", "unparsed"


def _minimal_pair_exclusive(norm_a: str, norm_b: str, lexicon: Lexicon) -> bool:
    """True iff norms differ by exactly one polarity lexicon swap or negation marker."""
    if not norm_a or not norm_b or norm_a == norm_b:
        return False

    target_a = normalize_identifier(norm_a)
    target_b = normalize_identifier(norm_b)
    if not target_a or not target_b or target_a == target_b:
        return False

    swaps: list[tuple[str, str]] = []
    for a, b in lexicon.polarity_pairs:
        swaps.append((normalize_identifier(a), normalize_identifier(b)))
        swaps.append((normalize_identifier(b), normalize_identifier(a)))

    for src, dst in swaps:
        for base, target in ((target_a, target_b), (target_b, target_a)):
            parts = base.split("_")
            if parts.count(src) != 1:
                continue
            idx = parts.index(src)
            trial = parts[:]
            trial[idx] = dst
            if "_".join(trial) == target:
                return True

    for marker in lexicon.negation_markers:
        m = normalize_identifier(marker)
        if not m:
            continue
        for left, right in ((target_a, target_b), (target_b, target_a)):
            left_parts = left.split("_")
            right_parts = right.split("_")
            if len(left_parts) == len(right_parts) + 1 and left_parts[0] == m and left_parts[1:] == right_parts:
                return True

    return False

def classify_pair(
    guard_a: str | None,
    guard_b: str | None,
    lexicon: Lexicon | None = None,
) -> PairDecision:
    lex = lexicon or Lexicon.load()
    raw_a = "" if guard_a is None else str(guard_a)
    raw_b = "" if guard_b is None else str(guard_b)
    empty_a = is_empty_guard(raw_a)
    empty_b = is_empty_guard(raw_b)
    norm_a = normalize_guard(raw_a)
    norm_b = normalize_guard(raw_b)

    def decision(verdict: PairVerdict, rule: str, tag: str, pa: ParseResult | None = None, pb: ParseResult | None = None) -> PairDecision:
        return PairDecision(
            guard_a_raw=raw_a,
            guard_b_raw=raw_b,
            guard_a_norm=norm_a,
            guard_b_norm=norm_b,
            verdict=verdict,
            rule=rule,
            tag=tag,
            variables_a=list(pa.variables) if pa else [],
            variables_b=list(pb.variables) if pb else [],
            parse_ok_a=bool(pa and pa.ok),
            parse_ok_b=bool(pb and pb.ok),
        )

    # Rule 1
    if empty_a and empty_b:
        return decision("OVERLAP", "1", "empty_pair")
    # Rule 2
    if empty_a != empty_b:
        return decision("OVERLAP", "2", "default_else_candidate")
    # Rule 3
    if norm_a == norm_b:
        return decision("OVERLAP", "3", "identical")

    pa = parse_guard(raw_a)
    pb = parse_guard(raw_b)

    # Rule 4 / 5
    if pa.ok and pb.ok:
        set_a = set(pa.variables)
        set_b = set(pb.variables)
        if set_a and set_a == set_b:
            verdict, tag = _same_var_verdict(pa.atoms, pb.atoms)
            rule = "4a" if verdict == "EXCLUSIVE" else "4b"
            return decision(verdict, rule, tag, pa, pb)
        if set_a.isdisjoint(set_b):
            return decision("UNKNOWN", "5", "cross_var", pa, pb)
        # Partial overlap of variable sets
        verdict, tag = _same_var_verdict(pa.atoms, pb.atoms)
        if verdict == "EXCLUSIVE":
            return decision("EXCLUSIVE", "4a", tag, pa, pb)
        if verdict == "OVERLAP":
            return decision("OVERLAP", "4b", tag, pa, pb)
        return decision("UNKNOWN", "7", "unparsed", pa, pb)

    # Rule 6 — minimal-pair lexicon (also when parse fails)
    if _minimal_pair_exclusive(norm_a, norm_b, lex):
        return decision("EXCLUSIVE", "6", "nl_negation", pa, pb)

    # Rule 7
    return decision("UNKNOWN", "7", "unparsed", pa, pb)


def classify_group(guards: list[str | None], lexicon: Lexicon | None = None) -> dict[str, Any]:
    lex = lexicon or Lexicon.load()
    n = len(guards)
    pair_decisions: list[dict[str, Any]] = []
    has_overlap = False
    has_unknown = False
    all_exclusive = True

    for i in range(n):
        for j in range(i + 1, n):
            d = classify_pair(guards[i], guards[j], lex)
            pair_decisions.append(
                {
                    "i": i,
                    "j": j,
                    "verdict": d.verdict,
                    "rule": d.rule,
                    "tag": d.tag,
                    "guard_a_raw": d.guard_a_raw,
                    "guard_b_raw": d.guard_b_raw,
                    "guard_a_norm": d.guard_a_norm,
                    "guard_b_norm": d.guard_b_norm,
                    "variables_a": d.variables_a,
                    "variables_b": d.variables_b,
                    "parse_ok_a": d.parse_ok_a,
                    "parse_ok_b": d.parse_ok_b,
                }
            )
            if d.verdict == "OVERLAP":
                has_overlap = True
                all_exclusive = False
            elif d.verdict == "UNKNOWN":
                has_unknown = True
                all_exclusive = False
            # EXCLUSIVE keeps all_exclusive if no other failures

    if has_overlap:
        group_verdict: GroupVerdict = "NON_DETERMINISTIC"
    elif has_unknown:
        group_verdict = "UNRESOLVED"
    elif all_exclusive or n < 2:
        group_verdict = "RESOLVED_DETERMINISTIC"
    else:
        group_verdict = "UNRESOLVED"

    norms = [normalize_guard(g) for g in guards]
    nonempty = [g for g in norms if g]
    string_distinct = len(nonempty) == len(guards) and len(set(nonempty)) == len(nonempty)

    return {
        "group_size": n,
        "guards_raw": [("" if g is None else str(g)) for g in guards],
        "guards_norm": norms,
        "pair_decisions": pair_decisions,
        "group_verdict": group_verdict,
        "string_distinct": string_distinct,
        "m1_pass": group_verdict == "RESOLVED_DETERMINISTIC",
        "m2_pass": group_verdict != "NON_DETERMINISTIC",
    }
