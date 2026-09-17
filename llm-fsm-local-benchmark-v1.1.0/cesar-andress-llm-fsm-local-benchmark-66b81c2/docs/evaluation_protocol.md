# Evaluation Protocol — FSM-Bench-20 Local LLM Experiment

**Project:** LLM-FSM Local Benchmark  
**Artifact:** FSM-Bench-20 (20 systems × 6–7 Ollama models)  
**Runtime:** Ollama (local, no paid APIs)  
**Hardware target:** NVIDIA RTX 4090

---

## 1. Research questions

| ID | Research question |
|----|-------------------|
| **RQ1** | How accurately do local open-source LLMs generate **deterministic FSMs** from natural-language requirements? |
| **RQ2** | Which model achieves the highest **requirement coverage** across diverse application domains? |
| **RQ3** | How often do LLMs produce **invalid JSON**, **non-deterministic** transitions, or **unsupported transitions**? |
| **RQ4** | Does **structured JSON output** (Ollama `format` schema) improve validity and coverage compared to unstructured generation? |
| **RQ5** | How structurally and behaviourally do LLM FSMs differ from **gold-standard** reference FSMs? |
| **RQ6** | Which application domains (e.g. access control vs booking flows) are hardest for local LLMs? |

---

## 2. Hypotheses

| ID | Hypothesis |
|----|------------|
| **H1** | Code-specialised models (e.g. Qwen2.5-Coder) outperform general chat models on requirement coverage and determinism. |
| **H2** | Larger models (14B vs 7B) produce fewer invalid JSON outputs and higher schema validity rates. |
| **H3** | Structured output mode significantly reduces `invalid_json_rate` (≥ 50% relative reduction). |
| **H4** | Systems with more invariant (“must not”) requirements yield lower coverage and more inferred transitions. |
| **H5** | LLM FSMs converge behaviourally to gold standards on simple transactional systems (vending, ticket) more than on concurrent systems (elevator, warehouse). |
| **H6** | Null hypothesis (H0): no statistically significant difference in gold-aligned coverage across models — to be rejected if Kruskal-Wallis / pairwise tests show p < 0.05. |

---

## 3. Independent variables

| Variable | Type | Levels / values |
|----------|------|-----------------|
| **LLM model** | Categorical | `qwen2.5-coder:7b`, `qwen2.5-coder:14b`, `llama3.1:8b`, `mistral-nemo:12b`, `gemma2:9b`, `phi3:14b`, optional `qwen2.5-coder:32b` |
| **Application domain** | Categorical | 20 domains (see `dataset/index.json`) |
| **System** | Categorical | 20 systems (nested within domain) |
| **Structured output** | Boolean | `true` (JSON schema via Ollama `format`) vs `false` (ablation) |
| **Requirement count** | Continuous | 12–13 requirements per system (covariate) |

### 3.1 Controlled variables

| Variable | Fixed value |
|----------|-------------|
| Temperature | 0.0 |
| Context length (`num_ctx`) | 8192 |
| Prompt templates | `docs/experimental_prompts.md` (local `prompts/` derived at runtime) |
| Inference backend | Ollama local API |
| FSM output schema | Pydantic `FSMOutput` JSON schema |

---

## 4. Dependent variables

| Variable | Description |
|----------|-------------|
| **Valid JSON** | Binary — output parses as JSON |
| **Schema valid** | Binary — passes Pydantic FSM schema |
| **Requirement coverage** | Continuous ∈ [0, 1] |
| **Determinism** | Binary — no duplicate `(source, event)` pairs |
| **Unsupported transitions** | Count per FSM |
| **Inferred transitions** | Count per FSM |
| **Structural size** | `num_states`, `num_events`, `num_transitions` |
| **Unreachable states** | Count |
| **Gold structural similarity** | Continuous ∈ [0, 1] (when gold available) |
| **Gold behavioural score** | Continuous ∈ [0, 1] (when gold available) |
| **Generation latency** | Seconds / tokens (from Ollama metadata) |

---

## 5. Evaluation metrics

### 5.1 Primary metrics (requirement-only, no gold)

| Metric | Definition | Source |
|--------|------------|--------|
| `invalid_json_rate` | Fraction of runs where JSON parse fails | `scripts/evaluate.py` |
| `schema_valid_rate` | Fraction passing Pydantic validation | `scripts/evaluate.py` |
| `requirement_coverage` | \|cited requirements\| / \|R1…Rn\| | `scripts/fsm_benchmark/metrics.py` |
| `determinism_rate` | Fraction of FSMs with zero nondeterministic pairs | same |
| `avg_unsupported_transitions` | Mean unsupported transitions per FSM | same |
| `avg_inferred_transitions` | Mean inferred transitions per FSM | same |

### 5.2 Secondary metrics (structural)

| Metric | Definition |
|--------|------------|
| `avg_num_states` | Mean state count |
| `avg_num_events` | Mean event count |
| `avg_num_transitions` | Mean transition count |
| `unreachable_state_rate` | Fraction of FSMs with ≥1 unreachable state |

### 5.3 Gold-aligned metrics (when gold FSM approved)

See `docs/gold_standard_strategy.md` §5:

- `state_jaccard`, `event_jaccard`, `transition_overlap`
- `trace_equivalence_rate`, `negative_trace_violation_rate`
- **GSS**, **GBS**, **GAC** composite scores

### 5.4 Aggregations

| Level | Aggregation |
|-------|-------------|
| Per (model, system) | Single run (temperature 0 → deterministic sampling) |
| Per model | Mean / median over 20 systems |
| Per domain | Mean over systems in domain |
| Global | Mean over all model × system pairs |

Output artifacts:

- `results/metrics.csv`
- `results/summary_by_model.json`
- `results/gold_metrics.csv` (future)
- `figures/*.png`, `figures/*.svg`

---

## 6. Experimental procedure

1. **Environment setup** — Python 3.12 venv, Ollama models pulled, `scripts/check_models.py` passes.
2. **Generation** — `scripts/run_experiment.py` for each (model, system) pair.
3. **Validation** — automatic JSON + schema checks on every output.
4. **Metrics** — `scripts/evaluate.py` → CSV.
5. **Visualisation** — `scripts/plot_results.py` → figures.
6. **Gold comparison** — `scripts/compare_to_gold.py` (when gold FSMs approved).
7. **Statistical analysis** — R / Python (`scipy`, `pandas`) for RQ2, RQ6; effect sizes (Cohen's d / Cliff's delta).

### 6.1 Ablation (optional)

| Run | Configuration |
|-----|---------------|
| A1 | Structured output ON (default) |
| A2 | Structured output OFF (`--no-structured-output`) |

Compare A1 vs A2 on `invalid_json_rate` and `requirement_coverage` (RQ4).

---

## 7. Threats to validity

### 7.1 Internal validity

| Threat | Mitigation |
|--------|------------|
| Prompt sensitivity | Fixed templates in `docs/experimental_prompts.md`; document local prompt hash in manifest |
| Temperature stochasticity | Temperature = 0.0 |
| Ollama version drift | Record `ollama --version` and model digests in `results/manifest_*.json` |
| Single run per condition | Optional: k=3 runs for variance estimation on subset |

### 7.2 External validity

| Threat | Mitigation |
|--------|------------|
| Limited to 20 systems | Diverse SE domains; disclose selection criteria in paper |
| English-only requirements | Acknowledge language bias |
| Local Ollama quantisation | Report quant level from `ollama show <model>` |
| GPU-specific performance | Separate correctness metrics from latency |

### 7.3 Construct validity

| Threat | Mitigation |
|--------|------------|
| Requirement coverage ≠ correctness | Gold standard behavioural comparison (RQ5) |
| Structural diff sensitive to naming | Normalisation rules before graph comparison |
| Self-reported `requirement` fields | Cross-check against gold traceability |

### 7.4 Conclusion validity

| Threat | Mitigation |
|--------|------------|
| Multiple comparisons (many models) | Bonferroni or FDR correction |
| Small benchmark size (n=20 systems) | Non-parametric tests; report effect sizes |
| Researcher degrees of freedom | Pre-register protocol (this document) before full run |

---

## 8. Success criteria

| Criterion | Target |
|-----------|--------|
| Experiment completion | ≥ 120 successful runs (6 models × 20 systems) |
| Reproducibility | Independent rerun achieves ≥ 95% identical metrics at temperature 0 |
| Gold coverage | ≥ 5 pilot gold FSMs before paper submission |
| Open science | Artifact public: dataset, scripts, prompts, evaluation protocol |

---

## 9. Ethical and resource considerations

- **No human subjects** — synthetic requirements only.
- **No paid APIs** — local compute only; reproducible on consumer hardware.
- **Energy** — report approximate GPU hours for full benchmark run.

---

## 10. Document history

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-06-02 | Initial protocol (pre-migration) |
