# Pre-Migration Setup Summary

**Date:** 2026-06-02  
**Status:** Scaffolding complete — **no files moved**, **no Git commit** performed.  
**Awaiting:** approval to execute migration per `migration_report.md`.

---

## 1. What was requested

Pre-migration tasks from the approved migration plan:

1. Create `benchmark/gold/` with placeholders for all 20 systems
2. Author `docs/gold_standard_strategy.md`
3. Author `docs/evaluation_protocol.md`
4. Create `.github/workflows/validate.yml`
5. Create `LICENSE`, `CITATION.cff`, `.gitignore`, `REPRODUCIBILITY.md` (uncommitted)
6. Do **not** move existing files yet

---

## 2. Where new files were created

All new artifacts were placed in the **future Git repository root**:

```text
~/papers/ist2026/llm-fsm-local-benchmark/
```

Existing experiment files remain at `~/papers/ist2026/` root (unchanged).

---

## 3. Files and directories created

### 3.1 Gold standard placeholders (20 files)

| Path | Description |
|------|-------------|
| `llm-fsm-local-benchmark/benchmark/gold/access_control.json` | `{}` placeholder |
| `llm-fsm-local-benchmark/benchmark/gold/atm.json` | `{}` placeholder |
| `llm-fsm-local-benchmark/benchmark/gold/bike_rental.json` | `{}` placeholder |
| `llm-fsm-local-benchmark/benchmark/gold/car_rental.json` | `{}` placeholder |
| `llm-fsm-local-benchmark/benchmark/gold/ecommerce_checkout.json` | `{}` placeholder |
| `llm-fsm-local-benchmark/benchmark/gold/elevator.json` | `{}` placeholder |
| `llm-fsm-local-benchmark/benchmark/gold/gym_membership.json` | `{}` placeholder |
| `llm-fsm-local-benchmark/benchmark/gold/hotel_booking.json` | `{}` placeholder |
| `llm-fsm-local-benchmark/benchmark/gold/library_loan.json` | `{}` placeholder |
| `llm-fsm-local-benchmark/benchmark/gold/login_system.json` | `{}` placeholder |
| `llm-fsm-local-benchmark/benchmark/gold/medical_appointment_booking.json` | `{}` placeholder |
| `llm-fsm-local-benchmark/benchmark/gold/online_examination.json` | `{}` placeholder |
| `llm-fsm-local-benchmark/benchmark/gold/package_locker.json` | `{}` placeholder |
| `llm-fsm-local-benchmark/benchmark/gold/parking_gate.json` | `{}` placeholder |
| `llm-fsm-local-benchmark/benchmark/gold/restaurant_reservation.json` | `{}` placeholder |
| `llm-fsm-local-benchmark/benchmark/gold/smart_thermostat.json` | `{}` placeholder |
| `llm-fsm-local-benchmark/benchmark/gold/ticket_machine.json` | `{}` placeholder |
| `llm-fsm-local-benchmark/benchmark/gold/train_ticket_booking.json` | `{}` placeholder |
| `llm-fsm-local-benchmark/benchmark/gold/vending_machine.json` | `{}` placeholder |
| `llm-fsm-local-benchmark/benchmark/gold/warehouse_inventory.json` | `{}` placeholder |

One placeholder per file in `dataset/systems/` (MD5-matched stems).

### 3.2 Documentation

| File | Purpose |
|------|---------|
| `llm-fsm-local-benchmark/docs/gold_standard_strategy.md` | Gold FSM authoring, validation, comparison methodology |
| `llm-fsm-local-benchmark/docs/evaluation_protocol.md` | RQs, hypotheses, variables, metrics, threats to validity |
| `llm-fsm-local-benchmark/docs/pre_migration_setup_summary.md` | This report |

### 3.3 CI / validation

| File | Purpose |
|------|---------|
| `llm-fsm-local-benchmark/.github/workflows/validate.yml` | GitHub Actions: JSON, dataset, benchmark checks |
| `llm-fsm-local-benchmark/scripts/validate_integrity.py` | Local validation script used by CI |

### 3.4 Repository metadata (not committed)

| File | Purpose |
|------|---------|
| `llm-fsm-local-benchmark/LICENSE` | MIT License |
| `llm-fsm-local-benchmark/CITATION.cff` | Citation metadata (CFF 1.2.0) |
| `llm-fsm-local-benchmark/.gitignore` | Excludes `.venv/`, outputs, results, figures |
| `llm-fsm-local-benchmark/REPRODUCIBILITY.md` | Step-by-step reproduction guide |

---

## 4. Validation script behaviour

`scripts/validate_integrity.py`:

- Validates JSON syntax of all `dataset/systems/*.json`
- Checks `dataset/index.json` catalog matches system files
- Checks requirement numbering R1…Rn
- Validates every system has a matching `benchmark/gold/<system>.json`
- **Pre-migration fallback:** if `dataset/` is not inside the repo, reads `../dataset/` (sibling at `~/papers/ist2026/dataset/`)

### Local test result

Run from `llm-fsm-local-benchmark/`:

```bash
python3.12 scripts/validate_integrity.py
```

Expected: **pass** using sibling `../dataset/` until migration moves dataset into the repo.

---

## 5. What was NOT changed

| Item | Status |
|------|--------|
| `~/papers/ist2026/dataset/` | Unchanged |
| `~/papers/ist2026/benchmark/` (root) | Unchanged (no `gold/` at root) |
| `~/papers/ist2026/scripts/` | Unchanged |
| `~/papers/ist2026/outputs/`, `results/`, `figures/` | Unchanged |
| `~/papers/ist2026/paper/` | Unchanged |
| Git commits | **None** |

---

## 6. Duplicates and migration notes

| Issue | Resolution at migration |
|-------|-------------------------|
| Root `benchmark/systems/` duplicates `dataset/systems/` | Delete root `benchmark/systems/`; keep `dataset/systems/` as canonical |
| Root `benchmark/` vs `llm-fsm-local-benchmark/benchmark/` | Merge: move root `benchmark/index.json`, `README.md`; keep new `gold/` |
| `docs/` split | Root docs move to `llm-fsm-local-benchmark/docs/` |
| CI prompt check | Requires `prompts/` inside repo — will pass after migration |

---

## 7. Obsolete / git-excluded (unchanged policy)

See `.gitignore`:

- `.venv/` (188 MB)
- `outputs/`, `results/`, `figures/` (regeneratable)
- `__pycache__/`

Gold placeholders `{}` are **tracked** (intentionally) until real gold FSMs replace them.

---

## 8. Next steps (require approval)

1. Execute migration per `migration_report.md`
2. Merge root `benchmark/` into `llm-fsm-local-benchmark/benchmark/`
3. Move `dataset/`, `scripts/`, `prompts/`, etc. into repo root
4. Run `python3.12 scripts/validate_integrity.py` post-migration
5. Initial Git commit: LICENSE, CITATION.cff, .gitignore, dataset, docs, gold placeholders, scripts
6. Author pilot gold FSMs (see `docs/gold_standard_strategy.md` Phase A)

---

**End of pre-migration setup summary.**
