executor: 2.1.308 (Claude Code) · model: claude-opus-5-5

1. **Halt and list both changes.** With no id given, the station infers one only when exactly one active change exists (*Parameter — the change id*, item 1).
2. **Treat it as an interrupted pass.** The station reads what is there against the phase's acceptance, continues it instead of restarting, and says so in its report (Step 1, the dirty-tree paragraph after the evidence rule).
3. **Halt without committing or ticking the box.** A failing `**HALT CHECK**` means the plan's premise broke, so the station never changes code to make it pass (Step 2, item 2; `I15`; *Stop-conditions*).
4. **Halt.** Skipping a test that `design.md`'s `## Tests` table does not name weakens the gate, which makes it a plan problem (Step 2, item 3; `T5`; stop-condition 5).
5. **State why the package is needed and stop for approval.** Dependencies are human-gated, and only a package listed in `## Dependencies` at the cut commit may be added (stop-condition 4; `I11`).
6. **One commit per phase, files staged by name, never `git add -A`.** The subject follows Conventional Commits. The message ends with a `Co-Authored-By:` line followed directly by `Change: <change-id>`, with no blank line between them (Step 2, item 6).
7. **Do none of the phase's tasks.** The station halts and outputs only the person's checklist, in the given format: the `cd` to the repo root, each `N.M` with its commands, `Closes when:` with each failing `Verify:` word for word, and `Next: /mf-build` (Step 2, the HUMAN-phase paragraph).
8. **The simplify pass runs next and applies its edits in place.** Claude Code uses native `/simplify`; other executors use generic simplify. If the gate is red after it, the station halts: it does not commit those edits and does not weaken the gate to pass (Step 3, items 1–2).
