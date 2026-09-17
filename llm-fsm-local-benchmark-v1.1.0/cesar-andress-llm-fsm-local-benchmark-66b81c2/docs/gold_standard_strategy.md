# Gold Standard FSM Strategy

This document defines how reference (gold) finite state machines will be authored, validated, and used to evaluate LLM-generated FSMs in **FSM-Bench-20**.

Gold FSMs live in `benchmark/gold/<system>.json` — one file per system in `dataset/systems/`.

---

## 1. Purpose

Gold standards provide a **human-authored, requirement-complete, deterministic** reference model for each benchmark system. They enable:

- objective comparison beyond self-reported `requirement` fields in LLM outputs
- structural similarity metrics (states, events, transitions)
- behavioral equivalence checks via model-based testing (MBT)
- inter-rater reliability studies during gold authoring

LLM outputs in `outputs/cleaned/` are compared against gold; they are **not** used to derive gold.

---

## 2. How gold FSMs will be created

### 2.1 Authoring workflow

| Step | Activity | Output |
|------|----------|--------|
| G1 | Select system from `dataset/systems/<system>.json` | Requirement list R1…Rn |
| G2 | Author FSM manually (or with LLM assist **heavily reviewed** by expert) | Draft FSM JSON |
| G3 | Map every requirement to ≥1 state or transition (`requirement` field) | Traceability matrix |
| G4 | Map every transition to ≥1 requirement | No unsupported transitions |
| G5 | Add `forbidden_behaviours` for each “must not” requirement | Negative test seeds |
| G6 | Independent review by second author | Review log in PR |
| G7 | Resolve conflicts; mark file `"status": "approved"` | Gold FSM v1.0 |

### 2.2 Authoring rules

1. **Determinism** — at most one transition per `(source, event)` under defined guard semantics.
2. **Completeness** — every `(state, event)` pair not in the spec gets an explicit self-loop or documented omission in `metadata.completions`.
3. **Traceability** — every transition cites `R<n>` from the requirement file.
4. **Naming** — PascalCase states, snake_case events (consistent with prompts).
5. **Initial state** — must match R1 in the requirement specification.
6. **No implementation detail** — gold models behavioural FSMs, not code.

### 2.3 JSON schema (gold file)

Gold files extend the LLM output schema with metadata:

```json
{
  "metadata": {
    "status": "approved",
    "system_stem": "vending_machine",
    "version": "1.0.0",
    "authors": ["..."],
    "reviewers": ["..."],
    "created": "2026-06-02",
    "requirement_source": "dataset/systems/vending_machine.json"
  },
  "states": [],
  "initial_state": "",
  "events": [],
  "transitions": [],
  "forbidden_behaviours": []
}
```

Placeholder files currently contain `{}` until authoring begins.

### 2.4 Roles

| Role | Responsibility |
|------|----------------|
| **Primary author** | Draft FSM + traceability matrix |
| **Reviewer** | Independent consistency check vs requirements |
| **Adjudicator** | Resolves disagreements; approves merge |

Target: **20 approved gold FSMs** (one per system).

---

## 3. How gold FSMs will be validated

### 3.1 Automated checks (CI + scripts)

| Check | Description |
|-------|-------------|
| JSON syntax | Valid UTF-8 JSON |
| Schema validation | Pydantic `FSMOutput` + required `metadata` for non-placeholder files |
| Requirement coverage | Every `R<n>` in dataset appears in ≥1 transition or forbidden behaviour |
| Unsupported transitions | Every transition cites a valid requirement ID |
| Determinism | No duplicate `(source, event)` without disjoint guards |
| Reachability | All states reachable from `initial_state` |
| Initial state | Matches R1 declaration in requirements |
| Placeholder detection | `{}` files excluded from strict validation until authored |

Planned script: `scripts/validate_gold.py` (post-migration).

### 3.2 Manual review checklist

- [ ] Each requirement R1…Rn is testable from the FSM
- [ ] Each “must not” requirement has a `forbidden_behaviours` entry
- [ ] No contradictory cycles unless specified
- [ ] Guard conditions are boolean and unambiguous
- [ ] Second reviewer sign-off recorded in `metadata.reviewers`

### 3.3 Consistency check against requirements

For each system, compute a **requirements ↔ FSM consistency score** (0–100):

| Dimension | Weight |
|-----------|--------|
| Requirement coverage | 30% |
| Transition support (no unsupported) | 25% |
| Determinism | 15% |
| Reachability / structural validity | 15% |
| Forbidden behaviour coverage | 15% |

Gold FSMs must score **100** before `metadata.status = "approved"`.

---

## 4. How gold FSMs will evaluate LLM outputs

### 4.1 Comparison pipeline

```text
dataset/systems/<system>.json
        │
        ▼
   LLM (Ollama) ──► outputs/cleaned/<model>/<system>.json
        │
        ▼
benchmark/gold/<system>.json
        │
        ▼
scripts/compare_to_gold.py  (planned)
        │
        ▼
results/gold_comparison/<model>/<system>.json
```

### 4.2 Comparison levels

| Level | What is compared |
|-------|------------------|
| **L1 — Syntactic** | Valid JSON, schema compliance |
| **L2 — Structural** | State/event/transition set overlap with gold |
| **L3 — Traceability** | Requirement coverage vs gold coverage |
| **L4 — Behavioural** | MBT traces: gold vs LLM FSM simulation on shared event sequences |
| **L5 — Equivalence** | Bisimulation or trace equivalence (where computationally feasible) |

LLM FSMs are **not** expected to be identical to gold structurally (different state naming is allowed). L3–L5 focus on requirement satisfaction and behaviour.

### 4.3 Normalisation before comparison

Before structural diff:

1. Rename states via best-efficiency graph alignment (optional)
2. Normalise event synonyms (`press_coffee` vs `press_coffee_button`)
3. Collapse self-loops with `action: none`

Document normalisation rules in `docs/gold_normalisation.md` (future).

---

## 5. Metrics computable against gold standard

### 5.1 Structural metrics

| Metric | Formula / description |
|--------|----------------------|
| `state_jaccard` | \|S_llm ∩ S_gold\| / \|S_llm ∪ S_gold\| (after normalisation) |
| `event_jaccard` | Same for events |
| `transition_overlap` | Fraction of gold `(source, event, target)` present in LLM FSM |
| `extra_states` | \|S_llm \ S_gold\| |
| `missing_states` | \|S_gold \ S_llm\| |
| `extra_transitions` | Transitions in LLM not in gold |
| `missing_transitions` | Transitions in gold not in LLM |

### 5.2 Traceability metrics

| Metric | Description |
|--------|-------------|
| `requirement_coverage_gap` | `coverage_gold(R) - coverage_llm(R)` per requirement |
| `unsupported_vs_gold` | LLM transitions not justified by gold requirement set |
| `forbidden_behaviour_coverage` | Fraction of gold forbidden traces also listed by LLM |

### 5.3 Behavioural metrics

| Metric | Description |
|--------|-------------|
| `trace_equivalence_rate` | Fraction of gold positive traces accepted by LLM FSM |
| `negative_trace_violation_rate` | Fraction of forbidden traces incorrectly allowed by LLM FSM |
| `determinism_gap` | LLM non-deterministic pairs minus gold non-deterministic pairs |

### 5.4 Aggregate benchmark scores

| Score | Description |
|-------|-------------|
| **Gold Structural Similarity (GSS)** | Weighted mean of Jaccard overlaps |
| **Gold Behavioural Score (GBS)** | Mean trace equivalence over test suite derived from gold |
| **Gold-Aligned Coverage (GAC)** | Harmonic mean of requirement coverage vs gold reference |

### 5.5 Reporting

Per-model aggregates exported to:

- `results/gold_metrics.csv`
- `paper/tables/gold_comparison.tex` (selected columns)

---

## 6. Placeholder policy

Files containing only `{}` are **placeholders**. CI must:

- verify file exists for each system in `dataset/systems/`
- verify JSON syntax
- **skip** strict gold validation until `metadata.status == "approved"`

---

## 7. Timeline (recommended)

| Phase | Deliverable |
|-------|-------------|
| Phase A | 5 pilot gold FSMs (vending, ATM, login, elevator, access control) |
| Phase B | Remaining 15 gold FSMs |
| Phase C | `compare_to_gold.py` + gold metrics in experiment pipeline |
| Phase D | Paper results section with gold-aligned scores |

---

## 8. References

- `docs/evaluation_protocol.md` — research questions and metrics
- `benchmark/README.md` — benchmark definition
- `docs/experimental_prompts.md` — formal LLM generation rules (gold should satisfy same constraints)
