# Reproducibility Guide — FSM-Bench-20

This document describes how to fully reproduce the local LLM FSM generation experiment on your machine using **Ollama only** (no paid APIs).

---

## 1. Overview

| Item | Value |
|------|-------|
| Benchmark | FSM-Bench-20 (20 systems, 12–13 requirements each) |
| Public revision artefact | **v1.1.0** (git tag; IST guard-aware deposit) |
| Implementation freeze | **v1.0.0** (git tag; pre-guard-aware publication baseline) |
| Campaign manifest | `20260602T195520Z` (finalized 2026-06-02T21:02:56 UTC) |
| Campaign size | 140/140 runs (7 models × 20 systems) |
| Zenodo published deposit | [10.5281/zenodo.20517969](https://doi.org/10.5281/zenodo.20517969) = GitHub **`v1.0.0`** (concept [10.5281/zenodo.20516295](https://doi.org/10.5281/zenodo.20516295)); use GitHub `v1.1.0` for revision contents |
| Models | 6 mandatory + 1 optional via Ollama |
| Temperature | 0.0 |
| Structured output | Ollama JSON schema (`format`) enabled by default |
| Expected hardware | NVIDIA RTX 4090 or equivalent (24 GB VRAM) |

---

## 2. Prerequisites

### 2.1 System software

```bash
# Python 3.12+ (required)
python3.12 --version

# Ollama
ollama --version
ollama serve   # run in a separate terminal if needed
```

### 2.2 Ollama models

```bash
python3.12 scripts/check_models.py
# Install each missing model, e.g.:
ollama pull qwen2.5-coder:7b
ollama pull qwen2.5-coder:14b
ollama pull llama3.1:8b
ollama pull mistral-nemo:12b
ollama pull gemma2:9b
ollama pull phi3:14b
```

Optional:

```bash
ollama pull qwen2.5-coder:32b
python3.12 scripts/check_models.py --include-optional
```

---

## 3. Installation

```bash
git clone git@github.com:cesar-andress/llm-fsm-local-benchmark.git
cd llm-fsm-local-benchmark

python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 4. Repository validation (before experiment)

```bash
python3.12 scripts/validate_integrity.py
```

## 5. Local prompt setup (required)

Prompt working files are not version controlled. Create them from the formal specification:

```bash
mkdir -p prompts
# Copy templates from docs/experimental_prompts.md into:
#   prompts/fsm_system_prompt.txt
#   prompts/fsm_user_prompt.txt
```

See `docs/experimental_prompts.md` for exact template text.

---

## 6. Full experiment pipeline

### Option A — one command

```bash
chmod +x run_all.sh
./run_all.sh
```

With optional 32B model:

```bash
INCLUDE_OPTIONAL=1 ./run_all.sh
```

### Option B — step by step

```bash
source .venv/bin/activate

# 1. Verify models
python3.12 scripts/check_models.py

# 2. Generate FSMs (20 systems × N models)
python3.12 scripts/run_experiment.py

# 3. Compute metrics → CSV
python3.12 scripts/evaluate.py

# 4. Generate figures
python3.12 scripts/plot_results.py
```

### Pilot run (fast smoke test)

```bash
python3.12 scripts/run_experiment.py \
  --models qwen2.5-coder:14b \
  --systems vending_machine atm login_system
```

---

## 7. Expected outputs

| Path | Description | Regeneratable |
|------|-------------|---------------|
| `outputs/raw/<model>/<system>.json` | Raw LLM response + metadata | Yes |
| `outputs/cleaned/<model>/<system>.json` | Parsed FSM JSON | Yes |
| `results/metrics.csv` | Main results table | Yes |
| `results/summary_by_model.json` | Per-model aggregates | Yes |
| `results/details/<model>/<system>.json` | Detailed metrics | Yes |
| `figures/*.png`, `figures/*.svg` | Plots | Yes |
| `results/manifest_latest.json` | Run provenance | Yes |

---

## 8. Experiment configuration

Key parameters in `scripts/fsm_benchmark/config.py`:

```python
OLLAMA_TEMPERATURE = 0.0
OLLAMA_NUM_CTX = 8192
OLLAMA_TIMEOUT_SECONDS = 600
```

Prompt templates (formal specification):

- `docs/experimental_prompts.md` (version controlled)
- Local runtime: `prompts/fsm_system_prompt.txt`, `prompts/fsm_user_prompt.txt` (gitignored)

Disable structured output (ablation for RQ4):

```bash
python3.12 scripts/run_experiment.py --no-structured-output
```

---

## 9. Provenance to record

When publishing results, archive the following with your paper:

| Provenance item | How to capture |
|-----------------|----------------|
| Ollama version | `ollama --version` |
| Model digests | `ollama show <model> --modelfile` |
| Git commit | `git rev-parse HEAD` |
| Run manifest | `results/manifest_latest.json` |
| Python packages | `pip freeze > results/pip_freeze.txt` |
| GPU | `nvidia-smi --query-gpu=name,driver_version --format=csv` |

---

## 10. Gold standard comparison (future)

When gold FSMs in `benchmark/gold/` are approved (`metadata.status = "approved"`):

```bash
python3.12 scripts/compare_to_gold.py   # planned
```

See `docs/gold_standard_strategy.md` for methodology.

---

## 11. Continuous integration

GitHub Actions workflow `.github/workflows/validate.yml` runs on push/PR:

- JSON syntax validation
- Dataset integrity
- Benchmark / gold placeholder integrity

---

## 12. Troubleshooting

| Problem | Solution |
|---------|----------|
| `python3` is 3.6 | Use `python3.12` explicitly |
| Model not found | Run `ollama pull <model>`; exact tag must match config |
| Ollama connection refused | Start `ollama serve` |
| Out of VRAM | Run one model at a time; skip 32B |
| Invalid JSON from model | Retry; check structured output is enabled |

---

## 13. Related documents

- `README.md` — project overview
- `docs/evaluation_protocol.md` — research questions and metrics
- `docs/experimental_prompts.md` — formal prompt specification
- `docs/REPOSITORY_HYGIENE_POLICY.md` — artifact hygiene policy
- `docs/gold_standard_strategy.md` — gold FSM methodology
- `dataset/README.md` — dataset schema and domains

---

## 14. License and citation

- License: MIT (see `LICENSE`)
- Citation: see `CITATION.cff`
- Public revision artefact: GitHub tag [`v1.1.0`](https://github.com/cesar-andress/llm-fsm-local-benchmark/releases/tag/v1.1.0)
- Zenodo published deposit DOI: [10.5281/zenodo.20517969](https://doi.org/10.5281/zenodo.20517969) (= GitHub `v1.0.0`; concept [10.5281/zenodo.20516295](https://doi.org/10.5281/zenodo.20516295))

When reporting reproduced experiments, cite GitHub `v1.1.0` for the revision contents and the Zenodo DOI only when referring to the archived `v1.0.0` freeze.

```bash
# Generate BibTeX from CITATION.cff (optional)
# pip install cffconvert && cffconvert -i CITATION.cff -f bibtex
```
