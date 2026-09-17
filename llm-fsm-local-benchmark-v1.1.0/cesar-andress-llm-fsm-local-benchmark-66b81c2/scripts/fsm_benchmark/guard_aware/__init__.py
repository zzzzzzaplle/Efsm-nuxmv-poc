"""Guard-aware determinism (M0–M3) for FSM-Bench-20."""

from .analyze import GuardAwareRunResult, analyze_transitions, run_result_to_metrics_fields
from .classify import Lexicon, PairDecision, classify_group, classify_pair
from .normalize import is_empty_guard, normalize_guard, normalize_identifier
from .parse import ParseResult, parse_guard

__all__ = [
    "GuardAwareRunResult",
    "Lexicon",
    "PairDecision",
    "ParseResult",
    "analyze_transitions",
    "classify_group",
    "classify_pair",
    "is_empty_guard",
    "normalize_guard",
    "normalize_identifier",
    "parse_guard",
    "run_result_to_metrics_fields",
]
