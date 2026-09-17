# FSM-Bench-20 — Local LLM FSM Benchmark

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20517969.svg)](https://doi.org/10.5281/zenodo.20517969)

Reproducible benchmark for evaluating **open-source large language models** on **deterministic finite state machine (FSM)** generation from natural-language requirements using local [Ollama](https://ollama.com) inference.

No paid cloud APIs are required.

---

## Project overview

**FSM-Bench-20** packages twenty software-domain requirement sets, a fixed FSM JSON schema, frozen prompt specifications, automated validators, and an experiment driver for local model comparison.

The repository is the implementation companion to the IST journal submission *FSM-Bench-20: A Reproducible Benchmark for Deterministic Finite State Machine Generation from Natural-Language Requirements Using Local Open-Source LLMs*.

| Item | Value |
|------|-------|
| Benchmark systems | 20 |
| Requirements per system | 12–13 numbered, testable statements |
| Models (campaign) | 6 mandatory + 1 optional (Ollama) |
| Inference | Local only; temperature 0.0; structured JSON output |
| Public revision artefact | GitHub tag [`v1.1.0`](https://github.com/cesar-andress/llm-fsm-local-benchmark/releases/tag/v1.1.0) |
| Zenodo published deposit | [10.5281/zenodo.20517969](https://doi.org/10.5281/zenodo.20517969) = GitHub **`v1.0.0`** (140-run freeze; concept [10.5281/zenodo.20516295](https://doi.org/10.5281/zenodo.20516295)) |

---

## FSM-Bench-20 benchmark

Each system specifies behaviour in English using identifiers `R1`, `R2`, … Models must emit a single JSON object conforming to the FSM schema (states, events, transitions with guards, actions, and requirement references).

Evaluation uses nested quality gates and a conservative guard-aware determinism instrument:

| Gate / measure | Criterion |
|------|-----------|
| **G1** | Valid JSON |
| **G2** | Schema-valid FSM with referential closure |
| **M0** (nested G3) | Strict structural determinism: unique `(source, event)` pairs among G2 passers |
| **M1** | Conservative guard-aware determinism (UNKNOWN fails) |
| **M2** | Optimistic upper bound (UNKNOWN passes; OVERLAP fails) |
| **M3** | Unresolved conflict-group / run mass |

Additional metrics include requirement citation coverage, unsupported/inferred transitions, reachability, and structural size.

See `docs/evaluation_protocol.md`, `docs/guard_aware_criterion_freeze.md`, and `docs/dataset.md` for full definitions.

---

## Final benchmark campaign

The **publication freeze** completed **140/140** planned runs (seven models × twenty systems):

| Field | Value |
|-------|-------|
| Manifest run ID | `20260602T195520Z` |
| Finalized (UTC) | `2026-06-02T21:02:56` |
| Structured output | Enabled for all runs |
| Campaign total | 140 runs |

**Frozen headline metrics** (descriptive; do not modify without a new campaign):

| Metric | Rate | Count |
|--------|------|-------|
| G1 — Valid JSON | 98.6% | 138/140 |
| G2 — Schema-valid FSM | 78.6% | 110/140 |
| Nested M0 (strict determinism) | 31.4% | 44/140 |
| Nested M1 (conservative guard-aware) | 33.6% | 47/140 |
| Nested M2 (optimistic upper bound) | 57.9% | 81/140 |
| Mean requirement coverage | 69.2% | — |

Mandatory six-model grid ($n=120$): nested M0/M1/M2 = 28.3%/29.2%/53.3%.

The public replication package under tag `v1.1.0` tracks compact campaign artefacts under `results/`: `summary_by_model.json`, `guard_aware_summary.json`, `guard_aware_groups.json` (106 conflict groups), `numeric_registry.json`, and the frozen campaign manifests.
Full per-pair CSV records (`metrics.csv`, `guard_aware_pairs.csv`) and raw/cleaned model outputs under `outputs/` remain with the frozen local campaign and are size-excluded from the Git tree.

---

## Reproducibility

1. Clone this repository and install Python 3.12+ and Ollama.
2. Pull the model tags listed in `scripts/fsm_benchmark/config.py`.
3. Create local prompt files from `docs/experimental_prompts.md` (prompts are gitignored by policy).
4. Run `./run_all.sh` or the step-by-step commands in `REPRODUCIBILITY.md`.
5. Compare regenerated `results/metrics.csv` against the frozen statistics above.

Full instructions: [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md)

Pre-flight checks:

```bash
python3.12 scripts/validate_integrity.py
python3.12 scripts/check_models.py
```

---

## Repository structure

```text
.
├── dataset/                 # FSM-Bench-20 requirement sets (versioned)
├── benchmark/               # Catalog and gold FSM placeholders
├── docs/                    # Protocol, prompts spec, policies
├── scripts/
│   ├── run_experiment.py    # Generation driver
│   ├── evaluate.py          # Metrics aggregation
│   ├── plot_results.py      # Diagnostic plots (gitignored output)
│   └── fsm_benchmark/       # Core library
├── outputs/                 # Raw/cleaned model outputs (gitignored)
├── results/                 # metrics.csv, manifest, details (gitignored)
├── figures/                 # Diagnostic plots (gitignored)
├── run_all.sh               # End-to-end pipeline
├── REPRODUCIBILITY.md
├── RELEASE_NOTES.md
├── CITATION.cff
└── LICENSE
```

---

## Quick start

```bash
git clone https://github.com/cesar-andress/llm-fsm-local-benchmark.git
cd llm-fsm-local-benchmark

python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

ollama serve   # separate terminal
python3.12 scripts/check_models.py

mkdir -p prompts
# Copy prompt templates per REPRODUCIBILITY.md §5

./run_all.sh
```

Pilot run:

```bash
python3.12 scripts/run_experiment.py \
  --models llama3.1:8b \
  --systems vending_machine atm
```

---

## Citation

If you use this benchmark, cite the accompanying paper and the public software release you actually used:

- **Revision package (this repository):** GitHub tag [`v1.1.0`](https://github.com/cesar-andress/llm-fsm-local-benchmark/releases/tag/v1.1.0)
- **Zenodo deposit (GitHub `v1.0.0` freeze):** [10.5281/zenodo.20517969](https://doi.org/10.5281/zenodo.20517969)
- **Metadata:** [`CITATION.cff`](CITATION.cff)

```bibtex
@software{fsm_bench_20_2026,
  author    = {Andr{\'e}s, C{\'e}sar},
  title     = {{FSM-Bench-20}: Local {LLM} Benchmark for Deterministic {FSM} Generation},
  version   = {1.0.0},
  year      = {2026},
  doi       = {10.5281/zenodo.20517969},
  url       = {https://doi.org/10.5281/zenodo.20517969},
  note      = {Zenodo record for GitHub release v1.0.0; IST revision contents under GitHub v1.1.0}
}
```

---

## Release history

| Version | Date | Notes |
|---------|------|-------|
| **v1.1.0** | 2026-07-28 | IST revision artefact — guard-aware M0–M3, diagnostics, author identity |
| **v1.0.0** | 2026-06-02 | First publication release — 140-run campaign freeze (`20260602T195520Z`) |
| v0.3.0 | 2026-06-02 | Repository hygiene and validation safeguards |
| v0.2.0 | 2026-06-02 | Expanded documentation and policies |
| v0.1.0 | 2026-06-02 | Initial public dataset and experiment framework |

See [`RELEASE_NOTES.md`](RELEASE_NOTES.md) for release scope and artefacts.

---

## Release v1.0.0

**FSM-Bench-20 publication release** used in the *Information and Software Technology* submission.

This tag marks the first archival-quality release of the benchmark **implementation** and documentation:

| Component | Location |
|-----------|----------|
| Benchmark dataset (20 systems) | `dataset/` |
| Prompt specification | `docs/experimental_prompts.md` |
| FSM JSON schema | `scripts/fsm_benchmark/schema.py` |
| Evaluation scripts | `scripts/evaluate.py`, `scripts/fsm_benchmark/` |
| Experiment driver | `scripts/run_experiment.py`, `run_all.sh` |
| Reproducibility guide | `REPRODUCIBILITY.md` |
| Evaluation protocol | `docs/evaluation_protocol.md` |

**Not included in the public Git tree** (size-excluded / regeneratable; see `.gitignore`):

- `results/metrics.csv`, `results/guard_aware_pairs.csv`, and `results/details/` — full per-pair and per-run records
- `outputs/raw/`, `outputs/cleaned/` — raw and cleaned model JSON
- `figures/` — intermediate diagnostic plots (publication figures ship with the manuscript artefact)

The frozen headline rates in this README match manifest `20260602T195520Z`.
Readers should use GitHub tag `v1.1.0` for the IST revision contents (guard-aware instrument and diagnostics).
Zenodo DOI `10.5281/zenodo.20517969` is the published deposit of GitHub release **`v1.0.0`** and does not contain the guard-aware revision files.

---

## Documentation index

| Document | Description |
|----------|-------------|
| `REPRODUCIBILITY.md` | Full reproduction guide |
| `RELEASE_NOTES.md` | v1.0.0 release notes |
| `docs/evaluation_protocol.md` | Research questions and metrics |
| `docs/experimental_prompts.md` | Formal prompt specification |
| `docs/dataset.md` | Dataset schema and catalog |
| `docs/PROJECT_RULES.md` | Repository conventions |
| `docs/RESEARCH_REPOSITORY_POLICY.md` | Artifact placement policy |

---

## License

MIT — see [`LICENSE`](LICENSE). Verify individual model licenses on Ollama before redistributing model weights or derived outputs.
