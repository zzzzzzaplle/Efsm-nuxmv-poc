# Research Repository Policy

> **Authoritative rules:** see `docs/PROJECT_RULES.md` (Sections 3, 5–7).

This repository supports a **journal publication** on local LLM generation of deterministic FSMs from natural-language requirements.

All contributors and automation must follow this policy **before creating, moving, or committing files**.

---

## 1. Decision checklist

Before adding any artifact, answer:

| # | Question | If “no” |
|---|----------|---------|
| 1 | **Is this artifact reproducible?** | Do not commit; add to `.gitignore` or document regeneration steps |
| 2 | **Is this artifact useful to reviewers?** | Keep local only, or move to supplementary material at publication time |
| 3 | **Should this artifact be version controlled?** | Exclude from Git; regenerate in replication studies |
| 4 | **Should this belong in the paper repository instead?** | Place under `~/papers/ist2026/paper/`, not here |

When uncertain, **write a short organization or migration proposal** in `docs/` and wait for approval before moving files.

---

## 2. Repository separation (mandatory)

```text
~/papers/ist2026/
├── llm-fsm-local-benchmark/    ← Research artifact repository (this repo)
└── paper/                      ← Journal paper sources (separate tree)
```

### Research artifact repository (`llm-fsm-local-benchmark`)

**Belongs here:**

| Category | Path | Version control |
|----------|------|-----------------|
| Requirement dataset | `dataset/` | Yes |
| Benchmark catalog & gold FSMs | `benchmark/` | Yes (gold: yes once approved) |
| Prompt specification | `docs/experimental_prompts.md` | Yes |
| Local prompt runtime files | `prompts/` | No (gitignored; create locally) |
| Experiment scripts | `scripts/` | Yes |
| Evaluation & gold strategy docs | `docs/` | Yes |
| Reproducibility guide | `REPRODUCIBILITY.md` | Yes |
| CI validation | `.github/workflows/` | Yes |
| Citation & license | `CITATION.cff`, `LICENSE` | Yes |
| Raw LLM outputs | `outputs/raw/` | No (regeneratable) |
| Cleaned FSM JSON | `outputs/cleaned/` | No (regeneratable) |
| Metrics & aggregates | `results/` | Optional snapshot per release |
| Diagnostic plots | `figures/` | No (regeneratable; gitignored — use `paper/figures/` for publication) |

**Must NOT be placed here:**

- LaTeX sources (`.tex`, `.bib`, `.sty`)
- Paper sections, drafts, or reviewer response letters
- Camera-ready publication figures (belong in `paper/figures/`)
- Author notes unrelated to replication

### Paper repository (`~/papers/ist2026/paper/`)

**Belongs there:**

| Category | Path |
|----------|------|
| Main manuscript | `main.tex` |
| Bibliography | `references.bib` |
| Sections | `sections/` |
| Publication figures | `figures/` (whitelist; see `figures/FIGURES.md`) |
| LaTeX tables | `tables/` (e.g. `metrics.tex` generated from CSV) |

**Must NOT be placed there:**

- Raw LLM responses (`outputs/raw/`)
- Full experiment output trees
- Ollama model weights
- Python virtual environments
- Dataset source JSON (cite the benchmark repository instead)

---

## 3. Reproducibility over convenience

- Prefer **scripts + pinned dependencies** over committed generated data.
- Record run provenance in `results/manifest_*.json` when archiving a release snapshot.
- Paper figures must be **derivable** from `results/metrics.csv` or documented exports.
- Never symlink experimental output directories into `paper/`; **copy** selected assets with documented provenance.

---

## 4. Version control guidelines

### Always track

- `dataset/`, `scripts/`, `benchmark/` (except empty gold placeholders are tracked until replaced)
- `docs/experimental_prompts.md`
- `docs/evaluation_protocol.md`, `docs/gold_standard_strategy.md`
- `requirements.txt`, `run_all.sh`, `.github/workflows/validate.yml`

### Do not track (see `.gitignore`)

- `.venv/`, `__pycache__/`
- `outputs/raw/`, `outputs/cleaned/`
- `results/` (default; optional tagged release exception)
- `figures/` (default; optional release exception)

### Tag release snapshots

For Zenodo/GitHub releases, optionally attach:

- `results/metrics.csv` from a completed experiment run
- Selected `figures/*.png` referenced in the paper

Document the Git tag and manifest in `CHANGELOG.md`.

---

## 5. Workflow for new artifacts

```text
New file needed
      │
      ▼
Answer checklist (§1)
      │
      ├─ Paper-only content? ──► paper/
      │
      ├─ Regeneratable experiment output? ──► outputs/ or results/ (gitignored)
      │
      ├─ Replication-critical source? ──► dataset/ | prompts/ | scripts/ | docs/
      │
      └─ Uncertain? ──► docs/proposals/<name>.md → approval → move
```

---

## 6. Current compliance audit (2026-06-02)

### Compliant

| Item | Location |
|------|----------|
| Dataset & scripts | `llm-fsm-local-benchmark/` |
| Paper outline only | `paper/outline.md` |
| No LaTeX in benchmark repo | ✓ |
| English documentation policy | `docs/LANGUAGE_POLICY.md` |

### Open organization items (proposal only — not yet moved)

Legacy smoke-test outputs remain **outside** the Git repository at the workspace root:

| Orphan path | Type | Recommended action |
|-------------|------|-------------------|
| `~/papers/ist2026/results/` | Regeneratable metrics | Delete or move to `llm-fsm-local-benchmark/results/` locally (gitignored) |
| `~/papers/ist2026/figures/` | Regeneratable plots | Delete or regenerate via `plot_results.py` inside repo |
| `~/papers/ist2026/outputs/` | Raw/cleaned FSM (if present) | Same as above |

These do not violate the paper/benchmark split but should be consolidated under `llm-fsm-local-benchmark/` for local workflows.

### Documentation candidates for archival

| File | Reviewer value | Recommendation |
|------|----------------|----------------|
| `docs/migration_report.md` | Low (historical) | Keep for provenance; optional move to `docs/archive/` |
| `docs/pre_migration_setup_summary.md` | Low (historical) | Same |

---

## 7. Related policies

- `docs/LANGUAGE_POLICY.md` — English-only artifacts
- `REPRODUCIBILITY.md` — Replication procedure
- `docs/evaluation_protocol.md` — Research design

---

## 8. Priority

This policy takes precedence over ad-hoc directory layout or convenience when preparing publication artifacts.
