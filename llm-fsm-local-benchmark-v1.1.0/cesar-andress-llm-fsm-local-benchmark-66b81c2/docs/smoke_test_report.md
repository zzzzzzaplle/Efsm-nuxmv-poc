# Smoke Test Report

**Date:** 2026-06-02 19:48:11 UTC  
**Scope:** Pre-release end-to-end local Ollama benchmark

---

## Configuration

- **Systems:** `vending_machine`, `login_system`, `atm`
- **Models requested:** `qwen2.5-coder:7b`, `llama3.1:8b`
- **Models available:** `qwen2.5-coder:7b`, `llama3.1:8b`
- **Models missing:** none

## Repository hygiene

- Language audit (tracked): **PASS**
- Prompts tracked in Git: **no — PASS**
- Required files: **PASS**

## Run summary

- Completed runs: **6**

| Model | Runs | Valid JSON rate | Schema valid rate | Determinism | Avg req. coverage |
|-------|------|-----------------|-------------------|-------------|-------------------|
| `llama3.1:8b` | 3 | 1.00 | 1.00 | 0.00 | 0.77 |
| `qwen2.5-coder:7b` | 3 | 1.00 | 1.00 | 0.33 | 0.74 |

## Per-run validation

- `llama3.1:8b` × `atm` — **PASS** (valid JSON: True, schema: True, deterministic: False, coverage: 0.77)
- `llama3.1:8b` × `login_system` — **PASS** (valid JSON: True, schema: True, deterministic: False, coverage: 0.69)
- `llama3.1:8b` × `vending_machine` — **PASS** (valid JSON: True, schema: True, deterministic: False, coverage: 0.85)
- `qwen2.5-coder:7b` × `atm` — **PASS** (valid JSON: True, schema: True, deterministic: False, coverage: 0.85)
- `qwen2.5-coder:7b` × `login_system` — **PASS** (valid JSON: True, schema: True, deterministic: False, coverage: 0.69)
- `qwen2.5-coder:7b` × `vending_machine` — **PASS** (valid JSON: True, schema: True, deterministic: True, coverage: 0.69)

## Figures

- `figures/smoke_test_valid_json_rate.png`
- `figures/smoke_test_requirement_coverage.png`

## Artifacts (local, gitignored)

- `results/smoke_test_metrics.csv`
- `results/smoke_test_summary.json`
- `outputs/raw/` and `outputs/cleaned/`
