# Release Readiness Report

**Date:** 2026-06-02 19:48:11 UTC  
**Recommendation:** **READY_FOR_RELEASE**

---

## Zenodo status

| Item | Status |
|------|--------|
| DOI assigned | **yes** — [10.5281/zenodo.20516296](https://doi.org/10.5281/zenodo.20516296) |
| `CITATION.cff` updated | yes |
| README badge | yes |
| `REPRODUCIBILITY.md` updated | yes |

---

## Smoke test scope

- **Systems tested:** `vending_machine`, `login_system`, `atm`
- **Models requested:** `qwen2.5-coder:7b`, `llama3.1:8b`
- **Models tested:** `qwen2.5-coder:7b`, `llama3.1:8b`
- **Missing models:** none

## Validation status

| Check | Status |
|-------|--------|
| Dataset/benchmark integrity | PASS |
| Smoke benchmark executed | yes |
| Smoke runs evaluated | 6 |
| FSM validation (per run) | PASS |

## Language audit status

- Tracked files: **PASS** (0 Spanish findings required)

## Git hygiene status

- Prompts folder tracked: **PASS**
- Forbidden staged artifacts: **PASS**

### Files recommended for commit

- `scripts/run_smoke_test.py`
- `docs/smoke_test_report.md`
- `docs/release_readiness_report.md`

### Files that must remain gitignored

- `outputs/raw/`
- `outputs/cleaned/`
- `results/`
- `figures/`
- `prompts/`
- `.venv/`
- `__pycache__/`
- `.cursor/`
- `AGENTS.md`

## Smoke test metrics summary

```json
{
  "llama3.1:8b": {
    "runs": 3,
    "valid_json_rate": 1.0,
    "schema_valid_rate": 1.0,
    "determinism_rate": 0.0,
    "avg_requirement_coverage": 0.7692,
    "systems": [
      "atm",
      "login_system",
      "vending_machine"
    ]
  },
  "qwen2.5-coder:7b": {
    "runs": 3,
    "valid_json_rate": 1.0,
    "schema_valid_rate": 1.0,
    "determinism_rate": 0.3333,
    "avg_requirement_coverage": 0.7436,
    "systems": [
      "atm",
      "login_system",
      "vending_machine"
    ]
  }
}
```

## Smoke test figures (local)

- `figures/smoke_test_valid_json_rate.png`
- `figures/smoke_test_requirement_coverage.png`

---

*Generated after initial pre-release smoke test. Zenodo DOI 10.5281/zenodo.20516296 added to citation metadata.*
