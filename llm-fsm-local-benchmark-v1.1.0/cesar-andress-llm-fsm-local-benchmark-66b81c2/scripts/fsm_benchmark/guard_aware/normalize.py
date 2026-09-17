"""Guard normalisation (frozen)."""

from __future__ import annotations

import re
import unicodedata


_SPACE_RE = re.compile(r"\s+")
_IDENT_CHUNK_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)


def normalize_identifier(token: str) -> str:
    """Lower-case identifier with non-alnum collapsed to single underscores."""
    text = unicodedata.normalize("NFKC", token or "")
    parts = _IDENT_CHUNK_RE.findall(text.lower())
    return "_".join(parts)


def normalize_guard(text: str | None) -> str:
    """Frozen normalisation: case fold, quotes, whitespace, operator aliases."""
    if text is None:
        return ""
    raw = unicodedata.normalize("NFKC", str(text)).strip()
    if not raw:
        return ""

    s = raw.lower()
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        s = s[1:-1].strip()

    replacements = (
        ("&&", " and "),
        ("||", " or "),
        ("<>", " ≠ "),
        ("!=", " ≠ "),
        (">=", " ≥ "),
        ("<=", " ≤ "),
        ("==", " = "),
        ("⇒", " "),
        ("->", " "),
    )
    for old, new in replacements:
        s = s.replace(old, new)

    # Normalise remaining ASCII comparators surrounded by spaces later in parse;
    # keep single '=' / '<' / '>' characters.
    s = s.replace("≥", " ≥ ").replace("≤", " ≤ ").replace("≠", " ≠ ")
    s = _SPACE_RE.sub(" ", s).strip()
    return s


def is_empty_guard(text: str | None) -> bool:
    return normalize_guard(text) == ""
