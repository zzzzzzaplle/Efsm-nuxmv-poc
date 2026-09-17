# Guard-Aware Determinism Criterion — Frozen Specification

**Status:** FROZEN for INFSOF-D-26-01059 revision  
**Source methodology:** `paper-first-submission/reviewers/claude-analysis/03-guard-aware-criterion-design.md`  
**Implementation package:** `scripts/fsm_benchmark/guard_aware/`  
**Freeze date:** 2026-07-28

This file records the pre-registered criterion. Do not enrich the grammar,
lexicon, or decision rules after measuring corpus outcomes without a new
versioned freeze.

## Model class

Guarded finite-state machines with **uninterpreted** free-text guards
(reading ii): predicates over an implicit shared context; no typed
variables; no updates (SA1–SA5 as in the methodology document).

## Measures

| ID | Definition |
|----|------------|
| M0 | Strict structural determinism: unique `(source, event)` pairs (existing G3 predicate `deterministic`) |
| M1 | Conservative guard-aware: every conflict group has all pairs EXCLUSIVE |
| M2 | Optimistic guard-aware: no conflict group contains OVERLAP (UNKNOWN treated as pass) |
| M3 | Unresolved mass: groups/runs with UNRESOLVED (no OVERLAP, ≥1 UNKNOWN) |

Invariant: `M0_pass ⇒ M1_pass ⇒ M2_pass`.

Criterion A (unique non-empty guard strings) is reported only as a labelled
diagnostic ceiling (`string_distinct_pass`), **not** as M1 or M2.

## Pair decision rules (first match wins)

1. Both empty/absent → OVERLAP `[empty_pair]`
2. Exactly one empty → OVERLAP `[default_else_candidate]`
3. Normalised strings identical → OVERLAP `[identical]`
4. Both parse; same variable:
   - unsatisfiable conjunction → EXCLUSIVE `[interval]` / `[enum]` / `[bool]`
   - else → OVERLAP `[same_var_satisfiable]`
5. Both parse; disjoint variables → UNKNOWN `[cross_var]`
6. Minimal-pair negation lexicon → EXCLUSIVE `[nl_negation]`
7. Else → UNKNOWN `[unparsed]`

## Normalisation (frozen)

- Strip; Unicode NFKC; case fold
- Remove surrounding quotes
- Collapse whitespace
- Map `&&`→`and`, `||`→`or`, `!=`/`<>`→`≠`, `>=`→`≥`, `<=`→`≤`, `==`→`=`
- Identifier token normalisation: non-alnum → `_`, collapse `_`, lower case

## Restricted grammar (frozen)

- Comparisons: `var ⋈ literal` with ⋈ ∈ {`=`,`≠`,`<`,`≤`,`>`,`≥`}
- Boolean atoms: identifier, optional `not` / `!`
- Conjunction: `and` / `&`
- Disjunction: `or` recognised for parse status only; exclusivity on
  disjunctive formulae defaults to UNKNOWN unless reduced to same-var atoms

## Negation lexicon

See `lexicon.json` (paired antonyms / polarity markers). Minimal-pair test:
normalised guards identical except for exactly one lexicon polarity swap.

## Deviations from Claude methodology (documented)

1. **Manual annotation (E)** is not executed in this automated pass.
   Diagnostic rows include empty `manual_annotation` for later validation.
2. **M2** follows §8.4 (UNKNOWN passes), not criterion A. Criterion A is
   exposed separately as `string_distinct_pass`.
3. Function-call guards (`foo()`) parse as boolean atoms on identifier `foo`.
