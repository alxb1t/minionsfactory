executor: codex-cli 0.163.0 · model: gpt-6.1-sol

1. Halt and list both active changes; do not choose one (**Parameter — the change id**, item 1).

2. Continue the interrupted phase against its acceptance rather than restarting, and state that in the report (**Step 1 — Lift the context**, start-state table).

3. Halt without committing or ticking the box; never change code to make that check pass because the plan’s premise broke (**Step 2**, item 2; **Stop-conditions**).

4. Halt: skipping a test outside the design’s `## Tests` table weakens the gate and signals a plan problem (**Step 2**, item 3; **Stop-condition 5**).

5. State the justification and stop for human approval; the package is not approved by the cut commit’s dependency list (**Stop-condition 4**).

6. Each phase gets one commit, with changed paths staged by name, never `git add -A`. Use a Conventional-Commits subject and end with contiguous `Co-Authored-By:` and `Change: <change-id>` trailers (**Step 2**, item 6).

7. Do none of the HUMAN phase’s tasks; run its checks and halt with only the prescribed person’s checklist, including the failing `Verify:` lines word for word and `Next: /mf-build` (**Step 2 — The per-phase ritual**, HUMAN phase rule).

8. Run the selected simplify engine over the change’s diff, applying improvements in place, then re-run the full gate. If it is red, halt, commit nothing over it, and never weaken the gate (**Step 3 — Close with the simplify pass**, items 1–2).