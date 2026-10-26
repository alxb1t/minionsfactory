executor: 2.1.308 (Claude Code) · model: claude-opus-5-5

1. Under **Parameters**, echo every parameter first. Then **halt** and ask for `version`, because a missing required parameter is a halt. Never infer it from the id.
2. Under **Parameters**, a `brief` path that does not resolve is a **halt**. Never search for the brief.
3. Under **Step 1 — Preconditions**, **halt** and name the precondition that failed: on the default branch, `git status --porcelain` must print nothing.
4. Under **Step 3 — Re-check premises**, put the failed premise to the human with the evidence and **wait**. Never overturn a settled decision alone (see also `I10`).
5. Under **Step 8 — Self-check**, read every `Verify:` and run none of them:
   - Rewrite a check that cannot run as written, such as one with an unknown flag or bad syntax.
   - Flag to the human a check that already holds, unless it is marked `**HALT CHECK**`.
6. No. Under **Step 9**, a `## Dependencies` that is not `None.` is shown word for word and waits for the human's OK on each package before **Step 10** commits. The **Never** list says the same.
7. Under **Step 6**, write `skip_specs: true` in the change's `.openspec.yaml` and add `specs/.gitkeep` (see `I2` and `D10`). Put no spec file beside `skip_specs`, or validation fails.
8. Under **Step 11 — Report**, the report has these parts, in order:
   - At most three sentences: the branch, the commit id, and `git status --porcelain` printing nothing. They also give the gate's exit code and anything the human must act on.
   - The model suggestions, in chat only, per **Suggesting models**.
   - The last line: `Next: /mf-build <change-id>, in a fresh session.`
