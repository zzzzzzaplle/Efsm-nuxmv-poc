# Experimental Prompt Specification

Publication-ready benchmark inputs for FSM generation experiments. These templates define the controlled prompt conditions documented in `docs/evaluation_protocol.md`.

For local execution, replicate the templates below as:

- `prompts/fsm_system_prompt.txt`
- `prompts/fsm_user_prompt.txt`

The `prompts/` directory is **not version controlled** (see `docs/REPOSITORY_HYGIENE_POLICY.md`). Replicators must create these files locally from this specification.

---

## System prompt template

```text
You are an expert in formal methods and model-based testing.

Your task is to transform natural-language software requirements into a deterministic finite state machine (FSM).

Rules:
1. Every requirement must be reflected in at least one state or transition.
2. Every transition must cite the supporting requirement identifier(s) in the requirement field.
3. The FSM must be deterministic: for each (source state, event) pair, at most one transition may apply under any guard evaluation.
4. Include self-loops when the specification requires the system to remain in the same state.
5. Use explicit PascalCase state names and snake_case event names.
6. Return only JSON that conforms to the provided schema. Do not include markdown or commentary.
```

---

## User prompt template

Placeholders: `{system_name}`, `{domain}`, `{requirements}`, `{json_schema}` (filled at runtime by `scripts/fsm_benchmark/prompts.py`).

```text
Transform the following software requirements into a deterministic finite state machine.

System: {system_name}
Domain: {domain}

Requirements:
{requirements}

Return a single JSON object with this schema:
{json_schema}

Mandatory fields on every transition: source, event, guard, action, target, requirement.
Use empty string for guard or action when not applicable.
List forbidden_behaviours for negative test cases implied by "must not" requirements.
```

---

## Runtime parameters

| Parameter | Value | Config location |
|-----------|-------|-----------------|
| Temperature | 0.0 | `scripts/fsm_benchmark/config.py` |
| Context length | 8192 | `scripts/fsm_benchmark/config.py` |
| Structured output | Ollama JSON schema (`FSMOutput`) | `scripts/fsm_benchmark/schema.py` |

---

## Provenance

Document the SHA-256 hash of local prompt files in `results/manifest_*.json` when archiving experiment runs.
