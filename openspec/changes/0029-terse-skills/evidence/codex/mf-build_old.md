executor: codex-cli 0.163.0 · model: gpt-6.1-sol

1. Halt and list the active changes; do not choose one. **Parameter — the change id**, item 1, requires this when several candidates exist.

2. Read the existing work against the phase’s acceptance, continue the interrupted phase rather than restarting, and say so in the report. **Step 1 — Lift the context** gives this rule for a dirty tree with tracked `tasks.md`.

3. Halt because the plan’s premise broke; never change code to make that check pass. **Step 2**, item 2, states the `HALT CHECK` rule.

4. Halt without committing or ticking the phase box; skipping a test outside the design’s `## Tests` table weakens the gate. **Step 2**, item 3, and **Stop-conditions**, item 5, require this.

5. State the justification and stop for approval without adding the package. **Stop-conditions**, item 4, permits packages only as listed in the cut commit’s `design.md` under `## Dependencies`.

6. Each phase gets one commit, with changed paths staged by name, never `git add -A`. **Step 2**, item 6, requires a Conventional-Commits subject and a final contiguous trailer block containing `Co-Authored-By: <session attribution>` followed by `Change: <change-id>`.

7. Do none of the HUMAN phase’s tasks; halt with the person’s checklist and nothing else, including the failing verifications word for word and `Next: /mf-build`. **Step 2 — The per-phase ritual**, HUMAN-phase rule, specifies this exception to full halt reporting.

8. Run the selected simplify pass: native `/simplify` for Claude Code, or the bundled generic simplify instructions otherwise, then re-run the full gate. **Step 3 — Close with the simplify pass** requires a halt if the gate is red, without committing simplify’s edits or weakening the gate.