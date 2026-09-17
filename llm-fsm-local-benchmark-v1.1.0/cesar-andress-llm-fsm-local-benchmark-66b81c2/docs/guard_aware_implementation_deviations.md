# Implementation deviations from Claude criterion design (03)

Documented during INFSOF-D-26-01059 guard-aware implementation.

1. **Manual annotation (E) not executed in this pass.**
   Diagnostic rows include empty `manual_annotation` / `agreement_flag`
   fields for a later blind validation protocol. Automated M1/M2/M3 are
   reported without human labels.

2. **M2 follows §8.4 (UNKNOWN passes), not criterion A.**
   Criterion A (unique non-empty guard strings) is exposed as
   `string_distinct_pass` / `string_distinct_rate` only.

3. **"X is Y" NL guards parse as subject equality (`pin = valid`),**
   so polarity pairs often resolve via `[enum]` (rule 4) rather than
   `[nl_negation]` (rule 6). Verdicts match the case table; the firing
   tag may differ.

4. **Disjunctive guards are not used for exclusivity proofs.**
   Presence of `or` / `||` marks the guard unparsed for exclusivity
   (UNKNOWN path), even though the corpus contains a few such strings.

5. **Paper default paths** updated from non-existent `~/papers/ist2026/...`
   to `~/papers/llm-fsm-local-benchmark/{llm-fsm-local-benchmark,paper}`.

6. **Existing publication tables keep G3 = nested M0.**
   New side-by-side metrics live in `table_guard_aware_determinism.tex`.
   Manuscript prose was not modified in this implementation pass.
