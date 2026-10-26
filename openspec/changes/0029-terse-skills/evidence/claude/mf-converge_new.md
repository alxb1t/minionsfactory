executor: 2.1.308 (Claude Code) · model: claude-opus-5-5

1. **Halt.** Step 1, precondition 1 requires `git status --porcelain` to be empty, because uncommitted work falls outside the frozen range. Name what is missing and write `halt` with the reason to the status log.

2. **Halt.** Over an empty range every station returns clean, so the loop would converge on a change it never read. This is set by Step 2 item 2 and Step 1 precondition 3.

3. **Treat it as not clean and halt, naming the missing file.** Step 5's table says a missing file is not clean: the station never ran or crashed. The status log gets `halt`.

4. **No.** Under Step 5, "this round's freeze" means Step 6's re-freeze of the scoped fix range, not round 1's freeze. One file over a one-file fix range is converging.

5. **Only the same checker can promote `fixed` to `verified`, on its verify pass (Step 4's status flow, Step 7).** The fixer, per Step 6, may not:
   - touch any frontmatter counter (`round`, `head`, `open_blocking`) or write `verdict: clean`;
   - change any card field other than **Status**;
   - delete, move, rename or empty a findings file or the diff patch;
   - write the backlog.

6. **Halt at the cap (Step 7).** Leave every findings file exactly as it stands and write nothing to the backlog. Report the open blocking findings by id, naming the pickup round if one ran, and write `halt` to the status log.

7. **A catch-up round runs (`## Catch-up round`).** The ancestry check passes and round 2 is under the cap of three. It goes:
   - open the run marked `· catch-up` and log `catch-up`;
   - run Step 1's preconditions;
   - freeze `<judged head>..HEAD`;
   - run one Step 7 verify round, which counts as round 3;
   - if both files come back clean, go to Step 9 then Step 10, with no pickup.

8. **No. Halt, naming the missing capability.** This comes from *Executor and worker selection* and the first *Never* item: never review inline and never report a verdict you produced.
