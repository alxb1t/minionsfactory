executor: 2.1.308 (Claude Code) · model: claude-opus-5-5

1. Halt and name the problem. Step 1, precondition 1, requires `git status --porcelain` to be empty, because uncommitted work is not in the frozen range.
2. Halt. An empty range lets every station return clean over nothing (Step 1 precondition 3; Step 2 item 2).
3. A missing file is not clean, so halt and name the missing path (Step 5, first rule). Write `halt` with that reason to the status log before stopping (*The status log*).
4. No. Step 5 compares a station's counts with the freeze that this round judges, which here is Step 6's re-freeze of the fix range, not round 1's twelve files. One file over a one-file fix range means the loop is converging.
5. Only the checker that wrote the card can mark it `verified`, on its verify pass (Step 4; Step 7). The fixer must not touch `round`, `head`, `open_blocking` or the card's other fields, must never write `verdict: clean`, must not delete, move, rename or empty the findings files or diff patch, and must not write the backlog (Step 4; Step 6).
6. Halt and leave every findings file exactly as it stands. Write nothing to the backlog. Report the still-open blocking findings by id, and name the pickup round if one ran (Step 7, the cap).
7. A catch-up round runs, because the judged head is an ancestor of `HEAD` and round 2 is under the cap of three. It opens a run marked `· catch-up`, runs Step 1's preconditions, freezes `<judged head>..HEAD`, and runs one Step 7 verify round. If both files come back clean, it goes to Step 9 (backlog) and then Step 10 (report), with no Step 8 pickup (*Catch-up round*).
8. No. If the host cannot start a fresh worker, wait for it and read its output from shared disk, halt and name the missing capability. Do not review inline or report a verdict you produced (*Executor and worker selection*; *Never*, first item).
