executor: codex-cli 0.163.0 · model: gpt-6.1-sol

1. Echo the supplied parameters, then halt and ask for `version`; never infer it (**Parameters**).

2. Halt because the given `brief` path does not resolve; never search for another brief (**Parameters**).

3. Halt, naming the failed clean-tree precondition: `git status --porcelain` must print nothing on the default branch (**Step 1 — Preconditions**).

4. Show the human the failed premise with evidence and wait; never overturn a settled decision alone (**Step 3 — Re-check premises**).

5. Read every `Verify:` and run none; rewrite checks visibly unable to run, and flag checks already true before the build, except premise checks marked `**HALT CHECK**` (**Step 8 — Self-check**).

6. No: show `## Dependencies` word for word and get the human’s OK for each package before committing (**Step 9 — Show, then commit**).

7. Write `skip_specs: true` in the change’s `.openspec.yaml` and `specs/.gitkeep`, with no spec file beside `skip_specs` (**Step 6 — Write**).

8. Report what happened, the branch, commit id, gate exit code, clean `git status --porcelain`, and anything the human must act on, within three sentences; then suggest models in chat (**Step 11 — Report**, **Suggesting models**). The last line is `Next: /mf-build <change-id>, in a fresh session.`