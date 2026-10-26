executor: codex-cli 0.163.0 · model: gpt-6.1-sol

1. Treat converge as skipped, let preconditions 2, 3 and 7 pass, and state `converge: skipped — no findings files` (Step 1, precondition 4). Include that line in the release commit body (Step 4.4).

2. Halt: one findings file means converge ran, so both review and security files must exist (Step 1, precondition 4).

3. Halt and direct the person to run `/mf-converge` for a catch-up round over `<head>..HEAD` (Step 1, precondition 7).

4. Halt: `Unreleased` must contain real entries (Step 1, precondition 5).

5. Halt, report the failure, and weaken nothing; the fold and archive move remain staged, with the changelog cut and any version bump uncommitted, and no release commit or tag created (Step 4.3). Reverting those changes belongs to the human.

6. Proceed to Step 6 without merging or pushing, report the local release, and provide the prescribed next steps for merging and pushing (Steps 5 and 6).

7. Halt because the merge would ship a tree nobody checked; report the failed check and commands still to run (Step 5.1).

8. No: release never edits feature code or tests; halt and return the failure to the build or converge loop (the opening rule and **Never** section).