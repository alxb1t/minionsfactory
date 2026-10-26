executor: 2.1.308 (Claude Code) · model: claude-opus-5-5

1. Halt and list the candidate changes (*Parameter — the change id*, item 1).
2. Treat it as an interrupted pass at this phase. Continue it against the phase's acceptance instead of restarting, and say so in the report (Step 1, the *at the start* table).
3. Halt, because the plan's premise broke. Never change code to make the check pass (Step 2, item 2; input contract `I15`).
4. Halt, because this is a plan problem. Skipping a test the design's `## Tests` table does not name weakens the gate. Stop cleanly, with no commit and no ticked box (Step 2, item 3; stop-condition 5; `T5`).
5. State why the package is needed and stop for approval, because dependencies are human-gated. Do not install it (stop-condition 4; input contract `I11`).
6. A phase gets exactly one commit, and phases are never batched (Step 2, item 6; *What you must NOT do*).
   - Stage each path by name, never with `git add -A`.
   - Use a Conventional-Commits subject.
   - End the message with this trailer block, with no blank line between the two lines:

     ```
     Co-Authored-By: <attribution>
     Change: <change-id>
     ```
7. Do none of the phase's tasks. Halt with only the person's checklist: the sub-tasks' exact commands, then `Closes when:` with each failing `Verify:` copied word for word, then `Next: /mf-build`. This is the one halt not reported in full (Step 2, *A HUMAN phase…*).
8. The simplify pass runs next: native `/simplify` in Claude Code, otherwise the generic simplify reference. It applies its fixes in place, the full gate is re-run, and its edits go in their own trailered commit. If the gate is red, halt: commit nothing and never weaken the gate to fix it (Step 3, items 1–3).
