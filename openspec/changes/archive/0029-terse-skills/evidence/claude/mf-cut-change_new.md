executor: 2.1.308 (Claude Code) · model: claude-opus-5-5

1. Echo the parameters I was given, then **halt** and ask for `version`. I don't infer it from the change id (*Parameters* section).
2. **Halt**, and don't search for another brief (*Parameters* section, the paragraph on the source).
3. **Halt**, naming the precondition that failed: being on the default branch with `git status --porcelain` printing nothing (Step 1, Preconditions).
4. Show the human the mismatch with the evidence and **wait**. I never overturn a settled decision on my own (Step 3, Re-check premises).
5. Read each one but run none; the build runs them later (Step 8, Self-check).
   - If a check clearly won't run as written (an unknown flag, bad syntax), I rewrite it.
   - If a check already holds before the build, I flag it to the human, unless it is marked `**HALT CHECK**`.
6. No. If `## Dependencies` is anything other than `None.`, I show it word for word and wait for the human's OK on each package before committing (Step 9 table; *Never* list; D38).
7. Put `skip_specs: true` in `.openspec.yaml` and add `specs/.gitkeep`, both together. A spec file next to `skip_specs` fails validation (Step 6; I2; D10).
8. The report has at most three sentences: the branch, the commit id, and that `git status --porcelain` prints nothing. Model suggestions for build, converge and release follow, in chat only. The last line is `Next: /mf-build <change-id>, in a fresh session.` (Step 11, Report; *Suggesting models*).
