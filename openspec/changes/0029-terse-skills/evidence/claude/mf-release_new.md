executor: 2.1.308 (Claude Code) · model: claude-opus-5-5

1. **Treat converge as skipped and carry on.** Preconditions 2, 3 and 7 pass. Put the line `converge: skipped — no findings files` in the report and in the release commit, as its own paragraph before the trailer block (Step 1 precondition 4; Step 4.4).
2. **Halt.** One findings file without the other means converge ran but is incomplete (Step 1 precondition 4).
3. **Halt and tell the person to run `/mf-converge`.** It runs a catch-up round over `<head>..HEAD`, because the later commit would otherwise ship unreviewed (Step 1 precondition 7).
4. **Halt.** The version line is not aligned: `## [Unreleased]` must hold real entries, not an empty heading (Step 1 precondition 5).
5. **Halt: report the red gate and stop, and never weaken anything to fix it** (Step 4.3).
   - Nothing is committed or tagged.
   - Left behind: the staged fold and archive move, plus the uncommitted changelog cut and version bump.
   - Reverting them is named as the human's job.
6. **Skip the merge and push; report and stop** (Step 5 → Step 6).
   - Anything but yes goes straight to the report.
   - The last line is `Next: merge and push — release <version>.0 is on branch <branch>:`, followed by the switch, merge and push commands.
7. **Halt and report the error and the commands still to run** (Step 5.1).
   - The gate judged this branch on its old base, so merging now would ship a tree nobody checked.
   - The release commit and tag stay local, and the rest is left to the human (*Never* list).
8. **No.** The station never edits feature code or tests (*Never* list). A red gate is a halt, and the build owns the fix (Step 1 precondition 1).
