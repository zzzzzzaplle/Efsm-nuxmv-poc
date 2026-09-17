# Language Audit Report

> **Note:** For repository hygiene (prompt tracking, operational artifacts), see `docs/repository_hygiene_audit.md`. Earlier versions of this report referenced paths since removed from Git tracking.

**Date:** 2026-06-02  
**Repository:** `~/papers/ist2026/llm-fsm-local-benchmark`  
**Auditor action:** Apply project language and commit policy  
**Commit target message:** `docs(repo): enforce English language and commit policy`

---

## 1. Scope

### 1.1 In-repository (version controlled)

All files under `llm-fsm-local-benchmark/` excluding `.git/` (79 files at audit time).

### 1.2 Workspace siblings (migration context)

Files under `~/papers/ist2026/` outside the Git repository:

| Path | Role | In Git |
|------|------|--------|
| `paper/outline.md` | Paper draft outline | No (correct separation) |
| `results/` | Smoke-test metrics (regeneratable) | No |
| `outputs/` | Smoke-test FSM outputs (regeneratable) | No |
| `figures/` | Smoke-test plots (regeneratable) | No |
| `.venv/` | Local Python environment | No (gitignored) |

These paths were inspected for Spanish user-facing content. None required translation for repository publication.

---

## 2. Inspection method

1. Unicode scan for Spanish diacritics and inverted punctuation marks across project text files.
2. Keyword scan for common Spanish function words in Markdown, Python, JSON, YAML, shell, and CFF files.
3. Manual review of prompts, requirement specifications, and documentation.
4. Scan for prohibited tool references in user-facing documentation.
5. Repository validation: `python3.12 scripts/validate_integrity.py`.

Exclusions: `.git/`, `.venv/` (third-party packages may contain non-English test strings).

---

## 3. Files inspected (by category)

### 3.1 Root metadata (8)

- `README.md`
- `CHANGELOG.md`
- `CITATION.cff`
- `LICENSE`
- `REPRODUCIBILITY.md`
- `requirements.txt`
- `run_all.sh`

### 3.2 Documentation (11)

- `docs/PROJECT_RULES.md`
- `docs/LANGUAGE_POLICY.md`
- `docs/RESEARCH_REPOSITORY_POLICY.md`
- `docs/evaluation_protocol.md`
- `docs/gold_standard_strategy.md`
- `docs/dataset.md`
- `docs/RELEASE_v0.1.0.md`
- `docs/migration_report.md`
- `docs/pre_migration_setup_summary.md`
- `docs/language_audit.md` *(this file)*

### 3.3 Dataset (22)

- `dataset/index.json`
- `dataset/README.md`
- `dataset/systems/*.json` (20 systems)

### 3.5 Benchmark (22)

- `benchmark/index.json`
- `benchmark/README.md`
- `benchmark/gold/*.json` (20 placeholders)

### 3.6 Prompts (2)

- `prompts/fsm_system_prompt.txt`
- `prompts/fsm_user_prompt.txt`

### 3.7 Scripts (12)

- `scripts/check_models.py`
- `scripts/run_experiment.py`
- `scripts/evaluate.py`
- `scripts/plot_results.py`
- `scripts/validate_integrity.py`
- `scripts/fsm_benchmark/__init__.py`
- `scripts/fsm_benchmark/config.py`
- `scripts/fsm_benchmark/dataset.py`
- `scripts/fsm_benchmark/metrics.py`
- `scripts/fsm_benchmark/ollama_client.py`
- `scripts/fsm_benchmark/prompts.py`
- `scripts/fsm_benchmark/schema.py`

### 3.8 CI / placeholders (4)

- `.github/workflows/validate.yml`
- `.gitignore`
- `figures/.gitkeep`
- `outputs/raw/.gitkeep`, `outputs/cleaned/.gitkeep`

### 3.9 Workspace siblings (inspected, not in Git)

- `paper/outline.md`
- `results/metrics.csv`, `results/manifest_*.json`, `results/summary_by_model.json`, `results/details/**/*.json`
- `outputs/raw/**/*.json`, `outputs/cleaned/**/*.json`
- `figures/*.png`, `figures/*.svg`

**Total in-repo files inspected:** 79 (+ 2 created during this audit)  
**Total sibling files inspected:** 15+

---

## 4. Files translated

| File | Action | Notes |
|------|--------|-------|
| *(none this audit)* | — | Repository already in English after commit `9c77bda` |

### Prior translation (historical)

| File | Commit | Change |
|------|--------|--------|
| `README.md` | `9c77bda` | Full rewrite from Spanish to academic English |

No additional translations were required during this audit.

---

## 5. Files created or updated (historical — 2026-06-02)

| File | Action |
|------|--------|
| `docs/language_audit.md` | Created — this report |
| `docs/PROJECT_RULES.md` | Updated — neutral policy wording |

Operational IDE rule files were later removed from Git tracking; see `docs/repository_hygiene_audit.md`.

---

## 6. Remaining non-English text

### 6.1 Inside `llm-fsm-local-benchmark/`

**None detected** in user-facing repository artifacts.

Policy documents intentionally reference the word “Spanish” when describing the translation requirement (meta-policy language in English).

### 6.2 Outside repository (not version controlled)

| Location | Non-English content | Risk |
|----------|---------------------|------|
| `.venv/` | Third-party test fixtures (French, etc.) | **None** — gitignored, not published |
| Git CLI messages | Localized to Spanish (`git status` output) | **None** — not stored in repo |

### 6.3 Requirement specifications

All 20 `dataset/systems/*.json` files use **English** natural-language requirements (`R1:` … `Rn:`).

---

## 7. Prompts verification

Formal specification (version controlled): `docs/experimental_prompts.md` — English.

Local runtime copies (gitignored): `prompts/fsm_system_prompt.txt`, `prompts/fsm_user_prompt.txt` — English, verified on disk.

---

## 8. Documentation verification

All Markdown documentation under `docs/` and root `README.md`, `REPRODUCIBILITY.md`, `CHANGELOG.md` verified **English**.

---

## 9. Commit message policy

### 9.1 Format enforced going forward

```text
<type>(<scope>): <short summary>
```

Documented in: `docs/PROJECT_RULES.md`.

### 9.2 Historical commits (manual review)

| Hash | Message | Conventional format | English |
|------|---------|---------------------|---------|
| `a5da661` | `Release v0.1.0: initial dataset...` | Partial | ✓ |
| `9c77bda` | `Enforce English-only policy...` | No | ✓ |
| `98023c3` | `docs(repo): add project rules...` | ✓ | ✓ |

**Recommendation:** retain history; apply Conventional Commits for all future commits. Optional squash at next tagged release.

---

## 10. Risks and manual checks

| Item | Severity | Manual check |
|------|----------|--------------|
| LLM-generated FSM outputs in `outputs/` | Low | Content is JSON/English when experiment re-run |
| Future gold FSM authoring | Medium | Reviewers must author gold in English |
| Paper directory (`paper/`) | Low | `outline.md` already English; LaTeX not yet created |
| Orphan workspace `results/`, `figures/` | Low | Consolidate under repo locally or delete before Zenodo archive |
| Git push authentication | — | Requires `cesar-andress` credentials (2 commits ahead of origin) |
| Zenodo DOI | — | Not yet assigned; update `CITATION.cff` after deposit |

---

## 11. Validation performed

```text
python3.12 scripts/validate_integrity.py
→ PASS (20 dataset systems, 20 gold placeholders, index consistency)
```

Pre-commit staging review: no `.venv/`, `__pycache__/`, secrets, or generated experiment outputs staged.

---

## 12. Conclusion

The repository **meets the English-language policy** for publication-ready artifacts. Authoritative policies:

- `docs/PROJECT_RULES.md`
- `docs/REPOSITORY_HYGIENE_POLICY.md`

**Next recommended action:** push commits to GitHub and publish `v0.1.0` release when credentials are available.

---

*Generated as part of `docs(repo): enforce English language and commit policy`.*
