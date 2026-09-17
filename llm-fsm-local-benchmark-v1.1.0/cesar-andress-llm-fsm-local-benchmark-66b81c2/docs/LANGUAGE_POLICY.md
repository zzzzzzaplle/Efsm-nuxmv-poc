# Language Policy

> **Authoritative rules:** see `docs/PROJECT_RULES.md` (Sections 1–2).

This repository is an academic research project intended for international publication.

**All project artifacts MUST be written in English.**

## Scope

This policy applies to:

- Source code comments
- User-facing variable names and identifiers
- README files
- Documentation (`docs/`)
- Prompt specifications (`docs/experimental_prompts.md`; local `prompts/` is gitignored)
- Benchmark and dataset descriptions
- Requirement specifications (`dataset/systems/`)
- JSON metadata
- CSV column headers
- Figure titles, axis labels, and legends
- Tables and LaTeX sources
- GitHub releases, commit messages, issue templates, and pull request templates
- Evaluation protocols and reproducibility documentation
- Research notes stored in the repository

## Prohibited

Do **not** add Spanish (or other non-English) text to repository artifacts unless explicitly requested for a separate, external communication outside the repository.

## If non-English text is detected

1. Report the file and location.
2. Propose an English replacement.
3. Convert to academic English upon request or as part of repository maintenance.

## Commit enforcement

Commits **must be rejected** when Spanish text remains in **tracked** files.

Enforcement layers:

1. **Pre-commit hook** — run once after clone:
   ```bash
   ./scripts/install_git_hooks.sh
   ```
   The hook executes `scripts/validate_language.py --scope tracked` and exits non-zero on findings.
2. **CI** — GitHub Actions runs the same check on every push and pull request.

Manual audit (includes workspace siblings outside Git):

```bash
python3.12 scripts/validate_language.py --scope workspace
```

## Release audit (mandatory)

Before **every** GitHub or Zenodo release, run a **repository-wide** language audit:

```bash
./scripts/audit_release_language.sh vX.Y.Z
```

This command:

1. Scans the Git repository and workspace siblings (`paper/`, local prompts, smoke-test outputs, etc.).
2. Writes `docs/release_language_audit_vX.Y.Z.md`.
3. Runs `scripts/validate_integrity.py`.

**Do not tag or publish a release if the audit exits non-zero.** Commit the generated audit report with the release preparation changes.

CI re-runs the same audit on every `v*` tag push (`.github/workflows/release-audit.yml`). In CI, only the checked-out repository is available; run the full workspace audit locally before tagging.

## Writing style

Use professional academic English with standard terminology from:

- Software Engineering
- Model-Based Testing (MBT)
- Requirements Engineering
- Reproducible Research

GitHub-facing content must be publication-ready.

## Priority

This policy takes precedence over convenience, localization, or non-English default preferences.

## Related documents

- `REPRODUCIBILITY.md`
- `docs/RESEARCH_REPOSITORY_POLICY.md`
- `docs/evaluation_protocol.md`
- `docs/gold_standard_strategy.md`
