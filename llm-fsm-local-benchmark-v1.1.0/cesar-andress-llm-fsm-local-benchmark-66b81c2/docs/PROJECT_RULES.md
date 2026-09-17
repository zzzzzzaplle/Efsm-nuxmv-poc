# Project Rules — Language, Repository, and Commits

Authoritative policy for the **LLM-FSM Local Benchmark** research artifact repository.

Related documents:

- `docs/LANGUAGE_POLICY.md` — language scope (summary)
- `docs/RESEARCH_REPOSITORY_POLICY.md` — artifact placement (summary)
- `docs/REPOSITORY_HYGIENE_POLICY.md` — AI-only artifact exclusion
- `REPRODUCIBILITY.md` — replication procedure
- `docs/language_audit.md` — English compliance audit
- `docs/experimental_prompts.md` — formal prompt specification (version controlled)

---

## 1. Mandatory language policy

This is an academic research project intended for international publication.

**All repository content must be written in professional academic English.**

This includes:

- README files
- Documentation
- Prompts
- Benchmark descriptions
- Dataset descriptions
- Requirement specifications
- JSON metadata
- CSV headers
- Figure titles
- Plot labels
- Tables
- Source code comments
- Generated reports
- GitHub release notes
- Commit messages
- Issue templates
- Pull request templates
- LaTeX sources (if any are ever stored here — prefer `~/papers/ist2026/paper/`)
- Paper notes intended for repository storage

Do **not** write Spanish text in repository files unless explicitly requested for external communication **outside** the repository.

---

## 2. Translation requirement

Before adding, modifying, or committing any file in:

`~/papers/ist2026/llm-fsm-local-benchmark`

you must check whether the file contains Spanish text.

If Spanish text exists:

1. Translate it into professional academic English.
2. Preserve the scientific meaning.
3. Preserve file structure and machine-readable formats.
4. Do not remove technical information.
5. Report which files were translated.

This applies to all existing files and all future files.

---

## 3. Repository separation

### Research artifact repository

`~/papers/ist2026/llm-fsm-local-benchmark`

This repository may contain:

- Dataset
- Benchmark definitions
- Prompts
- Scripts
- Reproducibility documentation
- Evaluation protocol
- Gold standards
- Selected baseline results (release snapshots)
- Selected baseline figures (release snapshots)
- GitHub release documentation

### Paper source directory

`~/papers/ist2026/paper`

This directory may contain:

- LaTeX files
- Paper sections
- `references.bib`
- Publication figures
- Publication tables

**Do not** place paper-only LaTeX source files inside `llm-fsm-local-benchmark`.

**Do not** place raw experimental outputs inside `paper/`.

When uncertain about placement, write a proposal in `docs/` and wait for approval before moving files.

---

## 3.1 Repository hygiene (AI-only artifacts)

Do **not** commit operational or prompt-working directories. See `docs/REPOSITORY_HYGIENE_POLICY.md`.

- Local runtime copies: `prompts/` (gitignored)
- Version-controlled specification: `docs/experimental_prompts.md`
- Excluded: `.cursor/`, `AGENTS.md`, chat logs, scratch prompts

---

## 4. Commit policy

Whenever changes are made inside:

`~/papers/ist2026/llm-fsm-local-benchmark`

create a Git commit after the changes are validated.

Do **not** mention internal development tools or automated assistants in commit messages.

All commit messages must be written in **English**.

Use this exact Conventional Commits format:

```text
<type>(<scope>): <short summary>
```

### Allowed types

| Type | Use |
|------|-----|
| `feat` | New capability |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `data` | Dataset or benchmark data |
| `experiment` | Experiment configuration or runs |
| `eval` | Evaluation metrics or analysis |
| `refactor` | Code restructuring |
| `test` | Tests |
| `chore` | Maintenance |
| `release` | Release preparation |

### Allowed scopes

`dataset` · `benchmark` · `prompts` · `scripts` · `docs` · `results` · `figures` · `ci` · `repo` · `release`

### Examples

```text
data(dataset): add initial benchmark systems
docs(repo): add reproducibility instructions
feat(scripts): implement local Ollama execution pipeline
eval(results): add baseline metric summary
chore(repo): configure repository ignore rules
release(release): prepare initial dataset release
```

---

## 5. Commit workflow

Before every commit:

1. Run repository validation if available (`python3.12 scripts/validate_integrity.py`).
2. Check Git status.
3. Ensure no virtual environments, cache files, local logs, secrets, or temporary files are staged.
4. Ensure all user-facing content is in English.
5. Ensure the commit message follows the required format.

### Never commit

- `.venv/`
- `__pycache__/`
- `*.pyc`
- `.env`
- Secrets
- Temporary logs
- Editor backup files
- Large local model files

---

## 6. GitHub and Zenodo readiness

Before a GitHub release:

1. Run the **repository-wide language audit** (mandatory):
   ```bash
   ./scripts/audit_release_language.sh vX.Y.Z
   ```
   Commit `docs/release_language_audit_vX.Y.Z.md` when the audit passes.
2. Confirm `README.md` is in English.
3. Confirm `LICENSE` exists.
4. Confirm `CITATION.cff` exists.
5. Confirm `REPRODUCIBILITY.md` exists.
6. Confirm the dataset is valid (`scripts/validate_integrity.py`).
7. Confirm scripts can be executed locally.
8. Confirm release notes are written in English.
9. Do **not** mention internal development tools or automated assistants in release notes.

---

## 7. Reporting requirement

After each substantial repository operation, provide a short report containing:

- Files changed
- Files translated
- Validation performed
- Commit hash
- Next recommended action

---

## 8. Priority

These rules take precedence over convenience, localization defaults, or undocumented repository layout changes.
