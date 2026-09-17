from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .dataset import requirement_ids
from .schema import FSMOutput


REQUIREMENT_REF = re.compile(r"R\d+")


@dataclass
class ValidationReport:
    valid_json: bool
    schema_valid: bool
    errors: list[str]
    warnings: list[str]


def validate_fsm_dict(payload: dict[str, Any] | None) -> ValidationReport:
    errors: list[str] = []
    warnings: list[str] = []

    if payload is None:
        return ValidationReport(False, False, ["Payload is null"], warnings)

    try:
        fsm = FSMOutput.model_validate(payload)
    except Exception as exc:  # noqa: BLE001
        return ValidationReport(True, False, [f"Schema validation failed: {exc}"], warnings)

    if not fsm.states:
        errors.append("states must not be empty")
    if fsm.initial_state not in fsm.states:
        errors.append(f"initial_state '{fsm.initial_state}' is not in states")
    if not fsm.events:
        warnings.append("events list is empty")

    state_set = set(fsm.states)
    event_set = set(fsm.events)

    for idx, transition in enumerate(fsm.transitions):
        prefix = f"transitions[{idx}]"
        if transition.source not in state_set:
            errors.append(f"{prefix}.source '{transition.source}' is not a declared state")
        if transition.target not in state_set:
            errors.append(f"{prefix}.target '{transition.target}' is not a declared state")
        if transition.event and transition.event not in event_set:
            warnings.append(f"{prefix}.event '{transition.event}' is not listed in events")
        if not transition.requirement.strip():
            warnings.append(f"{prefix} has empty requirement traceability")

    return ValidationReport(
        valid_json=True,
        schema_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


@dataclass
class Metrics:
    model: str
    system: str
    domain: str
    valid_json: bool
    schema_valid: bool
    num_states: int
    num_events: int
    num_transitions: int
    deterministic: bool
    nondeterministic_pairs: int
    requirement_coverage: float
    covered_requirements: int
    total_requirements: int
    unsupported_transitions: int
    inferred_transitions: int
    missing_requirements: list[str]
    unreachable_states: list[str]
    validation_errors: list[str]
    validation_warnings: list[str]
    eval_count: int | None = None
    eval_duration_ns: int | None = None
    total_duration_ns: int | None = None
    # Guard-aware extension (M0 == deterministic; M1/M2/M3 alongside)
    m0_pass: bool = False
    m1_pass: bool = False
    m2_pass: bool = False
    string_distinct_pass: bool = False
    conflict_group_count: int = 0
    unresolved_group_count: int = 0
    nondeterministic_group_count: int = 0
    resolved_group_count: int = 0
    run_unresolved: bool = False
    parse_ok_guards: int = 0
    parse_total_nonempty_guards: int = 0


def extract_requirement_refs(text: str) -> set[str]:
    return set(REQUIREMENT_REF.findall(text or ""))


def compute_determinism(transitions: list[dict[str, Any]]) -> tuple[bool, int]:
    """Strict structural determinism (M0): unique (source, event) pairs; guards ignored."""
    pairs: dict[tuple[str, str], int] = {}
    for transition in transitions:
        key = (transition.get("source", ""), transition.get("event", ""))
        pairs[key] = pairs.get(key, 0) + 1
    nondeterministic = sum(1 for count in pairs.values() if count > 1)
    return nondeterministic == 0, nondeterministic


def compute_unreachable_states(states: list[str], initial_state: str, transitions: list[dict[str, Any]]) -> list[str]:
    if not states or initial_state not in states:
        return list(states)

    graph: dict[str, set[str]] = {state: set() for state in states}
    for transition in transitions:
        source = transition.get("source", "")
        target = transition.get("target", "")
        if source in graph and target in graph:
            graph[source].add(target)

    reachable = {initial_state}
    queue = [initial_state]
    while queue:
        current = queue.pop(0)
        for nxt in graph[current]:
            if nxt not in reachable:
                reachable.add(nxt)
                queue.append(nxt)

    return [state for state in states if state not in reachable]


def is_inferred_transition(requirement_field: str) -> bool:
    text = (requirement_field or "").lower()
    if not text.strip():
        return True
    markers = ("extension", "implicit", "inferred", "assumption", "unspecified")
    return any(marker in text for marker in markers)


def compute_metrics(
    model: str,
    system_name: str,
    domain: str,
    requirements: list[str],
    payload: dict[str, Any] | None,
    validation: ValidationReport,
    eval_count: int | None = None,
    eval_duration_ns: int | None = None,
    total_duration_ns: int | None = None,
) -> Metrics:
    from .guard_aware import analyze_transitions, run_result_to_metrics_fields

    spec_ids = requirement_ids(requirements)
    covered: set[str] = set()

    if payload is None:
        return Metrics(
            model=model,
            system=system_name,
            domain=domain,
            valid_json=False,
            schema_valid=False,
            num_states=0,
            num_events=0,
            num_transitions=0,
            deterministic=False,
            nondeterministic_pairs=0,
            requirement_coverage=0.0,
            covered_requirements=0,
            total_requirements=len(spec_ids),
            unsupported_transitions=0,
            inferred_transitions=0,
            missing_requirements=sorted(spec_ids),
            unreachable_states=[],
            validation_errors=validation.errors,
            validation_warnings=validation.warnings,
            eval_count=eval_count,
            eval_duration_ns=eval_duration_ns,
            total_duration_ns=total_duration_ns,
            m0_pass=False,
            m1_pass=False,
            m2_pass=False,
        )

    states = payload.get("states", [])
    events = payload.get("events", [])
    transitions = payload.get("transitions", [])
    initial_state = payload.get("initial_state", "")

    deterministic, nondeterministic_pairs = compute_determinism(transitions)
    unreachable = compute_unreachable_states(states, initial_state, transitions)
    guard_aware = analyze_transitions(
        transitions,
        model=model,
        system=system_name,
    )
    ga_fields = run_result_to_metrics_fields(guard_aware)

    unsupported = 0
    inferred = 0
    for transition in transitions:
        refs = extract_requirement_refs(str(transition.get("requirement", "")))
        covered.update(refs)
        if not refs or refs.isdisjoint(spec_ids):
            unsupported += 1
        if is_inferred_transition(str(transition.get("requirement", ""))):
            inferred += 1

    missing = sorted(spec_ids - covered)
    coverage = (len(spec_ids & covered) / len(spec_ids)) if spec_ids else 0.0

    return Metrics(
        model=model,
        system=system_name,
        domain=domain,
        valid_json=validation.valid_json,
        schema_valid=validation.schema_valid,
        num_states=len(states),
        num_events=len(events),
        num_transitions=len(transitions),
        deterministic=deterministic,
        nondeterministic_pairs=nondeterministic_pairs,
        requirement_coverage=coverage,
        covered_requirements=len(spec_ids & covered),
        total_requirements=len(spec_ids),
        unsupported_transitions=unsupported,
        inferred_transitions=inferred,
        missing_requirements=missing,
        unreachable_states=unreachable,
        validation_errors=validation.errors,
        validation_warnings=validation.warnings,
        eval_count=eval_count,
        eval_duration_ns=eval_duration_ns,
        total_duration_ns=total_duration_ns,
        **ga_fields,
    )
