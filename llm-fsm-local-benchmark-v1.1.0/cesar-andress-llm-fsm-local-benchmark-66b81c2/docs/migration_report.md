# Migration Report — `~/papers/ist2026`

**Date:** 2026-06-02  
**Status:** PLAN ONLY — no files have been moved, renamed, deleted, or overwritten.  
**Awaiting:** explicit approval before any migration step is executed.

---

## 1. Executive summary

The workspace `~/papers/ist2026` currently contains a **flat experiment layout** at the repository root plus an **empty Git repository** at `llm-fsm-local-benchmark/`. All substantive artifact files (dataset, scripts, outputs, results, figures) live at the root level. The journal paper exists only as `paper/outline.md`; no LaTeX source has been created yet.

**Target separation:**

| Root | Role |
|------|------|
| `~/papers/ist2026/llm-fsm-local-benchmark/` | Research artifact repository (dataset, scripts, experiment outputs) |
| `~/papers/ist2026/paper/` | Journal paper source (LaTeX, figures for publication, tables) |

**Key findings:**

- **20 duplicate system JSON files** (`benchmark/systems/` ≡ `dataset/systems/`, byte-identical)
- **No files > 50 MB** in project source (`.venv/` is 188 MB and must not be committed)
- **No notebooks, `.tex`, `.bib`, LICENSE, CITATION.cff, or `.gitignore`** present yet
- **Smoke-test artifacts** from partial experiment run (2 models × 1 system) are regeneratable
- **Git remote** already configured at `llm-fsm-local-benchmark/.git` → `git@github.com:cesar-andress/llm-fsm-local-benchmark.git`

---

## 2. Current inventory (scan results)

### 2.1 Directory tree (excluding `.venv/` and `.git/` internals)

```text
~/papers/ist2026/
├── benchmark/              # 22 files — dataset catalog + 20 systems
├── dataset/                # 22 files — exact duplicate of benchmark/
├── figures/                # 8 plots + .gitkeep
├── llm-fsm-local-benchmark/   # EMPTY (only .git/)
├── outputs/
│   ├── raw/                # 2 FSM raw responses
│   └── cleaned/            # 1 cleaned FSM
├── paper/
│   └── outline.md
├── prompts/                # 2 prompt templates
├── results/                # CSV, summaries, manifests, details
├── scripts/                # Python experiment pipeline
├── README.md
├── requirements.txt
├── run_all.sh
└── .venv/                  # Python 3.12 virtualenv (188 MB)
```

### 2.2 File classification

| Category | Count | Current location(s) |
|----------|------:|---------------------|
| Dataset / requirement specs | 20 JSON + index | `dataset/systems/`, `benchmark/systems/` (duplicate) |
| Benchmark metadata | 2 | `benchmark/index.json`, `benchmark/README.md` (+ copies in `dataset/`) |
| Prompts | 2 | `prompts/` |
| Scripts | 4 CLI + 7 lib modules | `scripts/` |
| Generated FSMs (raw) | 2 | `outputs/raw/` |
| Generated FSMs (cleaned) | 1 | `outputs/cleaned/` |
| CSV results | 1 | `results/metrics.csv` |
| JSON results | 5 | `results/` (manifests, summary, details) |
| Plots (experiment) | 8 | `figures/` (PNG + SVG) |
| Documentation | 3 | `README.md`, `benchmark/README.md`, `dataset/README.md`, `paper/outline.md` |
| Notebooks | 0 | — |
| LaTeX | 0 | — |
| Build / env | 1 venv + `__pycache__/` | `.venv/`, `scripts/**/__pycache__/` |

---

## 3. Target architecture mapping

```text
~/papers/ist2026/
│
├── llm-fsm-local-benchmark/          ← Git repo root (existing remote)
│   ├── dataset/                      ← canonical requirement specifications
│   ├── benchmark/                    ← benchmark definition docs (no duplicate data)
│   ├── prompts/
│   ├── scripts/
│   ├── outputs/raw/
│   ├── outputs/cleaned/
│   ├── results/
│   ├── figures/                      ← experiment diagnostic plots
│   ├── docs/                         ← extended documentation
│   ├── README.md
│   ├── LICENSE                       ← TO CREATE
│   ├── CITATION.cff                  ← TO CREATE
│   ├── REPRODUCIBILITY.md            ← TO CREATE (split from README)
│   └── .gitignore                    ← TO CREATE
│
└── paper/
    ├── main.tex                      ← TO CREATE
    ├── references.bib                ← TO CREATE
    ├── sections/                     ← migrate outline.md here
    ├── figures/                      ← publication figures (copy from experiment)
    └── tables/                       ← TO CREATE (e.g. metrics.tex)
```

---

## 4. Migration plan (phased)

### Phase 0 — Pre-migration (no file moves)

1. Review and approve this report.
2. Decide canonical dataset location (`dataset/` recommended; `benchmark/systems/` to be removed).
3. Confirm Git root = `llm-fsm-local-benchmark/`.

### Phase 1 — Scaffold target directories

Create missing directories and placeholder files inside `llm-fsm-local-benchmark/`:

- `docs/`
- `.gitignore`, `LICENSE`, `CITATION.cff`, `REPRODUCIBILITY.md`

Create missing paper directories:

- `paper/sections/`, `paper/figures/`, `paper/tables/`

### Phase 2 — Move research artifacts into `llm-fsm-local-benchmark/`

Move (not copy) all experiment files from root into the Git repo subdirectory.

### Phase 3 — Consolidate duplicates

- Keep **one** copy of `systems/*.json` under `dataset/systems/`.
- Repurpose `benchmark/` for catalog documentation only (`README.md`, future gold FSMs, evaluation protocol).

### Phase 4 — Update path references

- Verify `scripts/fsm_benchmark/config.py` → `PROJECT_ROOT = parents[2]` resolves to `llm-fsm-local-benchmark/` after move (same relative depth; **no change expected**).
- Update root references in `README.md`, `run_all.sh` if any hard-coded paths exist.

### Phase 5 — Paper separation

- Move `paper/outline.md` → `paper/sections/00_outline.md`.
- After full experiment: copy selected plots to `paper/figures/` (do not symlink experiment `figures/`).

### Phase 6 — Git hygiene

- Initialize/commit from `llm-fsm-local-benchmark/`.
- Ensure `.venv/`, `outputs/`, `results/`, `__pycache__/` are gitignored.
- Remove empty duplicate directories at `~/papers/ist2026/` root.

---

## 5. File-by-file migration table

### 5.1 Dataset and benchmark

| Current location | Proposed location | Action | Justification |
|------------------|-------------------|--------|---------------|
| `dataset/systems/*.json` (20 files) | `llm-fsm-local-benchmark/dataset/systems/*.json` | **MOVE** | Canonical requirement specifications used by `scripts/run_experiment.py` |
| `dataset/index.json` | `llm-fsm-local-benchmark/dataset/index.json` | **MOVE** | Dataset catalog |
| `dataset/README.md` | `llm-fsm-local-benchmark/docs/dataset.md` | **MOVE** | Extended docs belong under `docs/`; avoid duplicate READMEs |
| `benchmark/systems/*.json` (20 files) | — | **DELETE** (after approval) | Byte-identical duplicate of `dataset/systems/` (MD5 verified) |
| `benchmark/index.json` | `llm-fsm-local-benchmark/benchmark/index.json` | **MOVE** | Benchmark catalog metadata |
| `benchmark/README.md` | `llm-fsm-local-benchmark/benchmark/README.md` | **MOVE** | Benchmark definition and authoring guidelines |

### 5.2 Prompts and scripts

| Current location | Proposed location | Action | Justification |
|------------------|-------------------|--------|---------------|
| `prompts/fsm_system_prompt.txt` | `llm-fsm-local-benchmark/prompts/fsm_system_prompt.txt` | **MOVE** | Experiment input artifacts |
| `prompts/fsm_user_prompt.txt` | `llm-fsm-local-benchmark/prompts/fsm_user_prompt.txt` | **MOVE** | Experiment input artifacts |
| `scripts/check_models.py` | `llm-fsm-local-benchmark/scripts/check_models.py` | **MOVE** | Experiment pipeline |
| `scripts/run_experiment.py` | `llm-fsm-local-benchmark/scripts/run_experiment.py` | **MOVE** | Experiment pipeline |
| `scripts/evaluate.py` | `llm-fsm-local-benchmark/scripts/evaluate.py` | **MOVE** | Metrics aggregation |
| `scripts/plot_results.py` | `llm-fsm-local-benchmark/scripts/plot_results.py` | **MOVE** | Figure generation |
| `scripts/fsm_benchmark/**` | `llm-fsm-local-benchmark/scripts/fsm_benchmark/**` | **MOVE** | Internal library |
| `scripts/**/__pycache__/**` | — | **DELETE** | Regenerated automatically; never commit |

### 5.3 Generated outputs and results

| Current location | Proposed location | Action | Justification |
|------------------|-------------------|--------|---------------|
| `outputs/raw/**` | `llm-fsm-local-benchmark/outputs/raw/**` | **MOVE** (optional) | Raw LLM responses; **regeneratable** via `run_experiment.py` |
| `outputs/cleaned/**` | `llm-fsm-local-benchmark/outputs/cleaned/**` | **MOVE** (optional) | Parsed FSM JSON; **regeneratable** |
| `outputs/**/.gitkeep` | `llm-fsm-local-benchmark/outputs/**/.gitkeep` | **MOVE** | Preserve empty-dir structure in Git |
| `results/metrics.csv` | `llm-fsm-local-benchmark/results/metrics.csv` | **MOVE** (optional) | **Regeneratable** via `evaluate.py` |
| `results/summary_by_model.json` | `llm-fsm-local-benchmark/results/summary_by_model.json` | **MOVE** (optional) | **Regeneratable** |
| `results/manifest_latest.json` | `llm-fsm-local-benchmark/results/manifest_latest.json` | **MOVE** (optional) | **Regeneratable**; keep for audit trail if desired |
| `results/manifest_20260602T192831Z.json` | — | **DELETE** (after approval) | Superseded by later manifest; regeneratable |
| `results/manifest_20260602T192849Z.json` | `llm-fsm-local-benchmark/results/manifest_20260602T192849Z.json` | **MOVE** (optional) | Historical run record |
| `results/details/**` | `llm-fsm-local-benchmark/results/details/**` | **MOVE** (optional) | **Regeneratable** via `evaluate.py` |

### 5.4 Experiment figures

| Current location | Proposed location | Action | Justification |
|------------------|-------------------|--------|---------------|
| `figures/*.png`, `figures/*.svg` | `llm-fsm-local-benchmark/figures/` | **MOVE** (optional) | Experiment plots; **regeneratable** via `plot_results.py` |
| `figures/.gitkeep` | `llm-fsm-local-benchmark/figures/.gitkeep` | **MOVE** | Directory placeholder |

### 5.5 Root-level project files

| Current location | Proposed location | Action | Justification |
|------------------|-------------------|--------|---------------|
| `README.md` | `llm-fsm-local-benchmark/README.md` | **MOVE** | Repository front page |
| `requirements.txt` | `llm-fsm-local-benchmark/requirements.txt` | **MOVE** | Python dependencies |
| `run_all.sh` | `llm-fsm-local-benchmark/run_all.sh` | **MOVE** | Reproducibility entry point |
| `README.md` content (repro section) | `llm-fsm-local-benchmark/REPRODUCIBILITY.md` | **COPY + EDIT** | Separate reproducibility instructions per target layout |
| — | `llm-fsm-local-benchmark/LICENSE` | **CREATE** | Required artifact file (missing) |
| — | `llm-fsm-local-benchmark/CITATION.cff` | **CREATE** | Required artifact file (missing) |
| — | `llm-fsm-local-benchmark/.gitignore` | **CREATE** | Required artifact file (missing) |

### 5.6 Paper source

| Current location | Proposed location | Action | Justification |
|------------------|-------------------|--------|---------------|
| `paper/outline.md` | `paper/sections/00_outline.md` | **MOVE** | Paper content belongs under `sections/` |
| — | `paper/main.tex` | **CREATE** | Missing LaTeX entry point |
| — | `paper/references.bib` | **CREATE** | Missing bibliography |
| — | `paper/figures/` | **CREATE** | Publication figures (separate from experiment plots) |
| — | `paper/tables/` | **CREATE** | LaTeX table sources (e.g. `metrics.tex` from CSV) |
| `figures/*.png` (selected) | `paper/figures/` | **COPY** (post-experiment) | Paper uses subset of experiment plots |

### 5.7 Environment and Git

| Current location | Proposed location | Action | Justification |
|------------------|-------------------|--------|---------------|
| `.venv/` | `llm-fsm-local-benchmark/.venv/` | **MOVE** or **RECREATE** | Local env; never commit; recreate via `python3.12 -m venv .venv` preferred |
| `llm-fsm-local-benchmark/.git/` | stays in place | **KEEP** | Existing remote: `cesar-andress/llm-fsm-local-benchmark` |
| Empty `llm-fsm-local-benchmark/` (except `.git`) | populated by moves above | — | Becomes Git repo root |

### 5.8 This report

| Current location | Proposed location | Action | Justification |
|------------------|-------------------|--------|---------------|
| `migration_report.md` | `llm-fsm-local-benchmark/docs/migration_report.md` | **MOVE** (after approval) | Architectural record belongs in artifact repo docs |

---

## 6. Duplicate detection

### 6.1 Confirmed byte-identical duplicates

| File A | File B | MD5 match |
|--------|--------|-----------|
| `benchmark/systems/*.json` (20 files) | `dataset/systems/*.json` (20 files) | ✅ All 20 pairs identical |
| `benchmark/index.json` | `dataset/index.json` | ✅ Identical |
| `benchmark/README.md` | `dataset/README.md` | ✅ Identical |

**Recommendation:** retain `dataset/systems/` as the single source of truth; delete `benchmark/systems/` after migration.

### 6.2 Logical duplicates (not byte-identical)

| Files | Relationship |
|-------|--------------|
| `results/manifest_20260602T192831Z.json` vs `manifest_20260602T192849Z.json` | Two smoke-test runs; latest supersedes |
| `results/manifest_latest.json` | Pointer/copy of most recent manifest |
| `README.md` vs `benchmark/README.md` vs `dataset/README.md` | Overlapping documentation; consolidate into `README.md` + `docs/` |

---

## 7. Obsolete files

| File / directory | Reason obsolete | Recommended action |
|------------------|-----------------|-------------------|
| `benchmark/systems/` | Duplicate of `dataset/systems/` | Delete after migration |
| `results/manifest_20260602T192831Z.json` | Failed `llama3.1:8b` run (model not installed) | Delete or exclude from release |
| `outputs/raw/llama3.1_8b/vending_machine.json` | Error artifact (`404` / model-not-found) | Delete or regenerate after model install |
| `results/details/llama3.1_8b/vending_machine.json` | Derived from failed run | Delete with raw file |
| `scripts/**/__pycache__/**` | Python bytecode cache | Delete; add to `.gitignore` |
| Root-level dirs after migration (`dataset/`, `scripts/`, etc.) | Emptied by move | Remove empty directories |
| `llm-fsm-local-benchmark/` empty workspace | Placeholder before migration | Filled by Phase 2 moves |

---

## 8. Files that must never be committed to Git

| Path pattern | Size | Reason |
|--------------|------|--------|
| `.venv/` | 188 MB | Recreate locally from `requirements.txt` |
| `**/__pycache__/` | ~164 KB | Auto-generated bytecode |
| `**/*.pyc` | small | Auto-generated |
| `outputs/raw/**` | 40 KB now; grows with experiment | Regeneratable; may use Git LFS or release archives instead |
| `outputs/cleaned/**` | regeneratable | Same as above |
| `results/**` | regeneratable | Same as above |
| `figures/**` (experiment) | 344 KB | Regeneratable via `plot_results.py` |
| `.env`, `*.secret`, API keys | — | None present; policy for future |
| OS / editor files | — | `.DS_Store`, `*~`, `.vscode/` (if local settings) |

**Suggested `.gitignore` entries:**

```gitignore
.venv/
__pycache__/
*.py[cod]
outputs/raw/
outputs/cleaned/
results/
figures/
*.egg-info/
.dist/
.pytest_cache/
```

**Optional tracked paths** (for reproducible paper snapshots):

- `results/metrics.csv` tagged per release
- `dataset/` and `benchmark/` (without duplicate systems)
- `prompts/`, `scripts/`

---

## 9. Files larger than 50 MB

| Path | Size | Commit? |
|------|------|---------|
| *(none in project source)* | — | — |
| `.venv/lib/...` (multiple packages) | 188 MB total | **NO** — excluded |

No individual project artifact exceeds 50 MB. Full experiment outputs are unlikely to exceed 50 MB unless raw LLM traces are retained for all 20 systems × 6+ models.

---

## 10. Regeneratable artifacts

These can be **omitted from Git** and reproduced with the pipeline:

| Artifact | Regeneration command | Inputs required |
|----------|---------------------|-----------------|
| `outputs/raw/**` | `python3.12 scripts/run_experiment.py` | Ollama models, `dataset/`, `prompts/` |
| `outputs/cleaned/**` | same | same |
| `results/metrics.csv` | `python3.12 scripts/evaluate.py` | `outputs/` |
| `results/summary_by_model.json` | same | same |
| `results/details/**` | same | same |
| `results/manifest_*.json` | same | same |
| `figures/*.png`, `figures/*.svg` | `python3.12 scripts/plot_results.py` | `results/metrics.csv` |
| `.venv/` | `python3.12 -m venv .venv && pip install -r requirements.txt` | `requirements.txt` |
| `__pycache__/` | automatic on script run | — |
| `paper/tables/metrics.tex` | future script from CSV | `results/metrics.csv` |

**Minimum committed artifact set for full reproduction:**

1. `dataset/systems/*.json`, `dataset/index.json`
2. `prompts/`
3. `scripts/`
4. `requirements.txt`, `run_all.sh`, `REPRODUCIBILITY.md`

---

## 11. Missing components (to create post-migration)

| Component | Target path | Priority |
|-----------|-------------|----------|
| `.gitignore` | `llm-fsm-local-benchmark/.gitignore` | High |
| `LICENSE` | `llm-fsm-local-benchmark/LICENSE` | High |
| `CITATION.cff` | `llm-fsm-local-benchmark/CITATION.cff` | High |
| `REPRODUCIBILITY.md` | `llm-fsm-local-benchmark/REPRODUCIBILITY.md` | High |
| `main.tex` | `paper/main.tex` | High |
| `references.bib` | `paper/references.bib` | High |
| Gold-standard FSMs | `llm-fsm-local-benchmark/benchmark/gold/` | Medium (future) |
| CI workflow | `.github/workflows/reproduce.yml` | Low |

---

## 12. Risk register

| Risk | Mitigation |
|------|------------|
| `PROJECT_ROOT` breaks after move | Verify with smoke test: `scripts/check_models.py` |
| Duplicate Git history | Single repo root at `llm-fsm-local-benchmark/`; do not nest repos |
| Loss of smoke-test data | Archive `outputs/` and `results/` before delete if needed |
| Paper/experiment figure confusion | Separate `llm-fsm-local-benchmark/figures/` (experiment) from `paper/figures/` (publication) |
| `benchmark/` vs `dataset/` confusion | Document roles in `benchmark/README.md`; remove duplicate `systems/` |

---

## 13. Approval checklist

Before executing migration, confirm:

- [ ] Approve Phase 2 moves into `llm-fsm-local-benchmark/`
- [ ] Approve deletion of `benchmark/systems/` duplicate (20 files)
- [ ] Approve deletion of failed smoke-test artifacts (`llama3.1_8b/*`)
- [ ] Decide: track `results/metrics.csv` in Git or regenerate only
- [ ] Decide: move or recreate `.venv/`
- [ ] Approve creation of `LICENSE`, `CITATION.cff`, `.gitignore`, `REPRODUCIBILITY.md`
- [ ] Approve `paper/sections/00_outline.md` relocation

---

## 14. Estimated outcome after migration

```text
~/papers/ist2026/
├── llm-fsm-local-benchmark/     # Git repo — all experiment artifacts
│   ├── dataset/systems/         # 20 JSON (single copy)
│   ├── benchmark/               # README + index (no systems/)
│   ├── prompts/, scripts/, outputs/, results/, figures/
│   ├── docs/migration_report.md
│   ├── README.md, LICENSE, CITATION.cff, REPRODUCIBILITY.md, .gitignore
│   └── run_all.sh, requirements.txt
│
├── paper/
│   ├── sections/00_outline.md
│   ├── main.tex                 (to create)
│   ├── references.bib           (to create)
│   ├── figures/                 (to create)
│   └── tables/                  (to create)
│
└── (no loose experiment files at ist2026 root)
```

---

**End of report. No migration actions have been performed.**
