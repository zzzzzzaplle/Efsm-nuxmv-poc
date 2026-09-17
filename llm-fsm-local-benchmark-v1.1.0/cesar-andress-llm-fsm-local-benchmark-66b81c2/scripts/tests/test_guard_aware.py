"""Unit tests for the frozen guard-aware determinism criterion."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fsm_benchmark.guard_aware import (  # noqa: E402
    analyze_transitions,
    classify_pair,
    normalize_guard,
    parse_guard,
)
from fsm_benchmark.metrics import compute_determinism  # noqa: E402


class TestNormalize:
    def test_idempotent(self):
        g = "  Failed_PIN_Count >= 3  "
        once = normalize_guard(g)
        assert normalize_guard(once) == once

    def test_operators(self):
        assert "≥" in normalize_guard("x >= 5") or ">=" not in normalize_guard("x >= 5")
        assert normalize_guard("a != b") == normalize_guard("a ≠ b") or "≠" in normalize_guard("a != b")


class TestCaseTable:
    """§2.6 required case handling."""

    def test_two_empty(self):
        d = classify_pair("", "")
        assert d.verdict == "OVERLAP"
        assert d.tag == "empty_pair"

    def test_one_empty(self):
        d = classify_pair("", "x < 5")
        assert d.verdict == "OVERLAP"
        assert d.tag == "default_else_candidate"

    def test_identical(self):
        d = classify_pair("balance > 0", "Balance > 0")
        assert d.verdict == "OVERLAP"
        assert d.tag == "identical"

    def test_complementary_comparisons(self):
        d = classify_pair("x < 5", "x >= 5")
        assert d.verdict == "EXCLUSIVE"
        assert d.tag in {"interval", "enum"}

    def test_enumerated_alternatives(self):
        d = classify_pair("status = approved", "status = rejected")
        assert d.verdict == "EXCLUSIVE"
        assert d.tag == "enum"

    def test_nl_negation_minimal_pair(self):
        d = classify_pair("PIN is valid", "PIN is invalid")
        assert d.verdict == "EXCLUSIVE"
        # Same-subject "is" parses as enum equality; lexicon path is alternate.
        assert d.tag in {"nl_negation", "enum"}

    def test_nl_unrelated_unknown(self):
        d = classify_pair("PIN is valid", "account is locked")
        assert d.verdict == "UNKNOWN"


class TestAdversarial:
    def test_overlapping_thresholds(self):
        d = classify_pair("x > 0", "x > 100")
        assert d.verdict == "OVERLAP"

    def test_exclusive_boundaries(self):
        d = classify_pair("x >= 5", "x < 5")
        assert d.verdict == "EXCLUSIVE"

    def test_cross_var_unknown(self):
        d = classify_pair("pin_valid = true", "account_locked = true")
        assert d.verdict == "UNKNOWN"
        assert d.tag == "cross_var"

    def test_three_way_enum_exclusive(self):
        from fsm_benchmark.guard_aware import classify_group

        g = classify_group(
            ["status = a", "status = b", "status = c"],
        )
        assert g["group_verdict"] == "RESOLVED_DETERMINISTIC"
        assert g["m1_pass"] is True

    def test_three_way_with_empty_overlap(self):
        from fsm_benchmark.guard_aware import classify_group

        g = classify_group(["", "x < 5", "x >= 5"])
        assert g["group_verdict"] == "NON_DETERMINISTIC"
        assert g["m2_pass"] is False


class TestSymmetry:
    @pytest.mark.parametrize(
        "a,b",
        [
            ("x < 5", "x >= 5"),
            ("", "g"),
            ("status = a", "status = b"),
            ("PIN is valid", "PIN is invalid"),
            ("x > 0", "x > 100"),
        ],
    )
    def test_symmetric(self, a, b):
        d1 = classify_pair(a, b)
        d2 = classify_pair(b, a)
        assert d1.verdict == d2.verdict


class TestRunMonotonicity:
    def test_no_conflicts(self):
        transitions = [
            {"source": "A", "event": "e1", "guard": "", "target": "B"},
            {"source": "B", "event": "e2", "guard": "x > 0", "target": "C"},
        ]
        r = analyze_transitions(transitions)
        assert r.m0_pass and r.m1_pass and r.m2_pass

    def test_m0_implies_m1_m2_on_conflicts_resolved(self):
        transitions = [
            {"source": "A", "event": "e", "guard": "x < 5", "target": "B"},
            {"source": "A", "event": "e", "guard": "x >= 5", "target": "C"},
        ]
        r = analyze_transitions(transitions)
        assert r.m0_pass is False
        assert r.m1_pass is True
        assert r.m2_pass is True

    def test_unknown_fails_m1_passes_m2(self):
        transitions = [
            {"source": "A", "event": "e", "guard": "foo_bar_baz", "target": "B"},
            {"source": "A", "event": "e", "guard": "qux_zot_waldo", "target": "C"},
        ]
        r = analyze_transitions(transitions)
        assert r.m0_pass is False
        assert r.m1_pass is False
        assert r.m2_pass is True
        assert r.unresolved_group_count == 1

    def test_empty_pair_fails_both(self):
        transitions = [
            {"source": "A", "event": "e", "guard": "", "target": "B"},
            {"source": "A", "event": "e", "guard": "", "target": "C"},
        ]
        r = analyze_transitions(transitions)
        assert r.m1_pass is False
        assert r.m2_pass is False


class TestStrictPreserved:
    def test_compute_determinism_unchanged(self):
        transitions = [
            {"source": "A", "event": "e", "guard": "x < 5", "target": "B"},
            {"source": "A", "event": "e", "guard": "x >= 5", "target": "C"},
        ]
        det, n = compute_determinism(transitions)
        assert det is False
        assert n == 1


class TestParse:
    def test_comparison(self):
        p = parse_guard("failed_PIN_count < 3")
        assert p.ok
        assert p.variables == ["failed_pin_count"]

    def test_bool_atom(self):
        p = parse_guard("correct_pin")
        assert p.ok
        assert p.atoms[0].kind == "bool"
