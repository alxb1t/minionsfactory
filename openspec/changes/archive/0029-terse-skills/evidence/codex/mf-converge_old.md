executor: codex-cli 0.163.0 · model: gpt-6.1-sol

1. Halt because the tree is not clean; **Step 1, precondition 1** requires `git status --porcelain` to be empty.

2. Halt because the derived range is empty; **Step 2, item 2** forbids proceeding when `base` equals `HEAD`.

3. Halt, naming the missing review findings path; **Step 5 — Read the verdicts** says a missing findings file is not clean.

4. No. **Step 5 — Read the verdicts** compares scope against the current round’s freeze, so one file over a one-file fix range is correct.

5. Only the review or security checker responsible for that card, running as a fresh verification worker, may mark it `verified`. **Step 6 — The fix station** forbids the fixer from touching frontmatter counters (`round`, `head`, `open_blocking`) or writing `verdict: clean`.

6. Halt, leave every findings file exactly as it stands, and write nothing to the backlog; **Step 7 — Verify, and the cap** also requires reporting the still-open blocking findings by id.

7. Run a catch-up round: check ancestry and the cap, run Step 1’s preconditions, freeze `<judged head>..HEAD`, and run Step 7 verification as round 3. Under **Catch-up round**, clean results proceed to Step 9 and Step 10, with no pickup.

8. No; halt and name the unavailable worker capability. **Executor and worker selection** and **Never** forbid reviewing in the conductor’s own context.