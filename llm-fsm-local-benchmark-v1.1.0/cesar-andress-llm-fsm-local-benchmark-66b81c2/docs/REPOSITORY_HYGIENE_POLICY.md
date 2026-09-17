# Repository Hygiene Policy — AI-Only Artifacts

This repository is a **clean research artifact** for academic replication and journal publication.

Path: `~/papers/ist2026/llm-fsm-local-benchmark`

> **Authoritative rules:** see also `docs/PROJECT_RULES.md`.

---

## 1. Prompt and operational artifact policy

Do **not** track prompt-only folders or operational tooling artifacts in Git.

### Must not be committed

- `prompts/`
- `prompt_drafts/`
- `ai_prompts/`
- `cursor_rules/`
- `.cursor/`
- `chat_logs/`
- `assistant_logs/`
- `scratch_prompts/`
- `local_notes/`
- `temporary_prompt_tests/`
- `AGENTS.md`
- Files whose sole purpose is instructing a development tool
- Workflow conversation logs

Keep these locally or outside the repository. All patterns above are listed in `.gitignore`.

### Formalized experiment inputs

Publication-ready prompt **specifications** belong in:

- `docs/experimental_prompts.md`

Replicators create local `prompts/*.txt` from that document before running experiments.

---

## 2. Public repository principle

Include only artifacts defensible in an academic replication package:

| Include | Exclude |
|---------|---------|
| Dataset | Raw chat logs |
| Benchmark metadata | Tool-specific rule files |
| Gold-standard FSMs | Untracked prompt working copies |
| Source code | Scratch notes |
| Validation / evaluation scripts | Local assistant instructions |
| Selected baseline results (release snapshots) | |
| Reproducibility documentation | |
| Citation metadata, license | |
| CI workflows | |

---

## 3. Neutral language requirement

Documentation must not describe repository maintenance in terms of specific commercial or proprietary development tools. Use neutral academic language (e.g., “internal development tools” rather than product names).

---

## 4. Related documents

- `docs/repository_hygiene_audit.md` — latest compliance audit
- `docs/experimental_prompts.md` — formal prompt specification
- `docs/PROJECT_RULES.md` — language, commits, separation
