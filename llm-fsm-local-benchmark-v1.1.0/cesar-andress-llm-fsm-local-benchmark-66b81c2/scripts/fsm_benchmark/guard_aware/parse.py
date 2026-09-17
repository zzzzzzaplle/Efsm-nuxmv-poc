"""Restricted guard parser (frozen grammar)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from .normalize import normalize_guard, normalize_identifier


Op = Literal["=", "≠", "<", "≤", ">", "≥"]


@dataclass(frozen=True)
class Atom:
    """Boolean or comparison atom over one normalised variable."""

    variable: str
    kind: Literal["bool", "cmp"]
    op: Op | None = None
    value: str | float | bool | None = None
    negated: bool = False


@dataclass
class ParseResult:
    raw: str
    normalised: str
    ok: bool
    atoms: list[Atom] = field(default_factory=list)
    variables: list[str] = field(default_factory=list)
    has_disjunction: bool = False
    error: str | None = None


_CMP_OPS = ("≥", "≤", "≠", ">=", "<=", "!=", "==", "=", "<", ">")
_CMP_NORM = {
    ">=": "≥",
    "<=": "≤",
    "!=": "≠",
    "<>": "≠",
    "==": "=",
    ">": ">",
    "<": "<",
    "=": "=",
    "≥": "≥",
    "≤": "≤",
    "≠": "≠",
}

_CMP_RE = re.compile(
    r"^(?P<left>.+?)\s*(?P<op>≥|≤|≠|>=|<=|!=|==|=|<|>)\s*(?P<right>.+)$"
)
_BOOL_RE = re.compile(
    r"^(?:(?P<neg>not|no|!)\s+)?(?P<body>[a-zA-Z_][\w\s\(\)\.\-]*?)$"
)
_CALL_RE = re.compile(r"^(?P<name>[a-zA-Z_][\w]*)\s*\(\s*\)$")
_NUM_RE = re.compile(r"^[+-]?\d+(?:\.\d+)?$")


def _split_conjuncts(text: str) -> tuple[list[str], bool]:
    """Split on and/& ; detect or/|| without splitting (disjunction flag)."""
    has_or = bool(re.search(r"\bor\b|\|\|", text))
    # Split on ' and ' / ' & ' only at top level (no nesting in this grammar).
    parts = re.split(r"\s+and\s+|\s&\s", text)
    parts = [p.strip() for p in parts if p.strip()]
    return parts, has_or


def _parse_literal(token: str) -> str | float | bool:
    t = token.strip().strip("\"'")
    low = t.lower()
    if low in {"true", "yes"}:
        return True
    if low in {"false", "no"}:
        return False
    if _NUM_RE.match(t):
        return float(t) if "." in t else float(int(t))
    # Underscore numbers like 24_hours → keep as identifier string, not number
    if re.fullmatch(r"\d+[a-z_]+", low):
        return normalize_identifier(t)
    return normalize_identifier(t) if re.search(r"[a-zA-Z]", t) else t


def _parse_atom(fragment: str) -> Atom | None:
    frag = fragment.strip()
    if not frag:
        return None

    # Strip trailing/leading parentheses once
    if frag.startswith("(") and frag.endswith(")"):
        frag = frag[1:-1].strip()

    cmp_match = _CMP_RE.match(frag)
    if cmp_match:
        left = cmp_match.group("left").strip()
        right = cmp_match.group("right").strip()
        op = _CMP_NORM[cmp_match.group("op")]
        # Prefer variable on the left; if left is literal and right is ident, flip
        left_lit = _NUM_RE.match(left.strip().strip("\"'")) or left.lower() in {
            "true",
            "false",
        }
        right_ident = bool(re.search(r"[a-zA-Z_]", right)) and not _NUM_RE.match(
            right.strip().strip("\"'")
        )
        if left_lit and right_ident:
            # flip comparison
            flip = {"<": ">", ">": "<", "≤": "≥", "≥": "≤", "=": "=", "≠": "≠"}
            return Atom(
                variable=normalize_identifier(right),
                kind="cmp",
                op=flip[op],  # type: ignore[arg-type]
                value=_parse_literal(left),
            )
        # Function call on left: foo() >= 5
        call = _CALL_RE.match(left)
        var = normalize_identifier(call.group("name") if call else left)
        return Atom(variable=var, kind="cmp", op=op, value=_parse_literal(right))  # type: ignore[arg-type]

    # NL-ish "X is Y" / "X is not Y" → equality on subject (enables polarity via enum)
    is_match = re.match(
        r"^(?P<sub>.+?)\s+is\s+(?P<neg>not\s+)?(?P<pred>.+)$",
        frag,
        flags=re.IGNORECASE,
    )
    if is_match:
        subj = normalize_identifier(is_match.group("sub"))
        pred = normalize_identifier(is_match.group("pred"))
        negated = bool(is_match.group("neg"))
        if not subj or not pred:
            return None
        if pred in {"true", "false"}:
            val = pred == "true"
            if negated:
                val = not val
            return Atom(variable=subj, kind="bool", value=val, negated=False)
        if negated:
            return Atom(variable=subj, kind="cmp", op="≠", value=pred)
        return Atom(variable=subj, kind="cmp", op="=", value=pred)

    bool_match = _BOOL_RE.match(frag)
    if bool_match:
        body = bool_match.group("body").strip()
        negated = bool(bool_match.group("neg"))
        call = _CALL_RE.match(body)
        if call:
            var = normalize_identifier(call.group("name"))
        else:
            var = normalize_identifier(body)
        if not var:
            return None
        return Atom(variable=var, kind="bool", value=True, negated=negated)

    return None


def parse_guard(text: str | None) -> ParseResult:
    normalised = normalize_guard(text)
    if not normalised:
        return ParseResult(raw=str(text or ""), normalised="", ok=False, error="empty")

    conjuncts, has_or = _split_conjuncts(normalised)
    if has_or:
        # Disjunction: attempt atom parse of whole only if single fragment without and
        # Otherwise mark unparsed for exclusivity (UNKNOWN path).
        return ParseResult(
            raw=str(text or ""),
            normalised=normalised,
            ok=False,
            has_disjunction=True,
            error="disjunction_not_supported_for_exclusivity",
        )

    atoms: list[Atom] = []
    for part in conjuncts:
        atom = _parse_atom(part)
        if atom is None:
            return ParseResult(
                raw=str(text or ""),
                normalised=normalised,
                ok=False,
                has_disjunction=False,
                error=f"unparsed_fragment:{part}",
            )
        atoms.append(atom)

    variables = sorted({a.variable for a in atoms})
    return ParseResult(
        raw=str(text or ""),
        normalised=normalised,
        ok=True,
        atoms=atoms,
        variables=variables,
        has_disjunction=False,
    )
