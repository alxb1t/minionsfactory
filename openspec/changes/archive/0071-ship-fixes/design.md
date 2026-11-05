# Ship fixes — design

Integrate commits the merge, then gates the worktree; the changelog renumber is a rule; a dependent comes back with its dependency;
the person's amend answers a catch-up or verify halt; the fixer leaves the plan alone; a verify halt is the run's to diagnose.
Verdict at the end: ready to build.

## Context

Read at `1df4e7a` (v0.59.0). `conduct.py` is `skills/mf-ship/scripts/conduct.py`; line numbers move as the phases land, so the build
re-reads them by symbol.

- **F1. The gate's cwd:** `gate_run.py` takes only `--fresh` (`skills/mf-converge/scripts/gate_run.py:139-150`); `settled_tree()`
  (`:59-65`), `_run` (`:38`) and `make gate` (`:123`) run in the process cwd; `records()` finds the run directory by
  `--git-common-dir` (`:53-56`). The integrator runs in the primary (`conduct.py:2634`) and may not `cd`.
- **F2. diff-cover on an open merge:** the gate's `diff-cover --compare-branch=$(DIFF_BASE)` (`Makefile:21`) diffs from the merge
  base of `main` and `HEAD`; during the merge `HEAD` is the branch's pre-merge tip, so `main`'s incoming lines count as the branch's
  (`0068`: 98%). After the merge commit the merge base is `main`'s tip.
- **F3. Integrate's order:** Step 4 gates, then commits (`skills/mf-integrate/SKILL.md:140-172`); the description `:3`, the flow `:22`,
  the Step 2 table `:76-83`, Never `:189` ("Never commit over a red gate"). `.red` is read only under `_merge_open` in `stage_of`
  (`conduct.py:774-777`) and `_check_integrate` (`:849-864`). D45 says the integrator "gates, and commits"
  (`docs/decisions.md:447`).
- **F4. The `0070` halt:** `decisions()` recites every changed path but `docs/decisions.md` (`skills/mf-integrate/scripts/integrate.py:492-494`);
  `_recite` (`:449-470`) compares a file with `merge3` of its sides, but `CHANGELOG.md` is the `changelog` rule's output (`:311-329`),
  so it halts as ambiguous. `_split_changelog` (`:302-308`) and `_renumber` (`:332-342`) exist.
- **F5. Blocks:** `block()` appends a name (`conduct.py:2371-2375`); only `take_back` clears it, for itself (`:2952`), then re-reads
  the plan unconditionally (`:2953`). A blocked stage reads `waiting`, not in `HALTS` (`:70`); `take_requests` (`:2903-2923`) takes
  only requested names; `join()` (`:3108`) polls it. A rescue's amend continues the same thread (`:2683`), so its dependents wait in
  `ready()`'s `join` (`:2731-2733`) and are never blocked on that path.
- **F6. Cut-only:** `catch_up` counts `rev-list --count <base>..<change>` (`:2813-2817`); `merge_in`'s own `--no-ff` commit
  (`:2765-2766`) makes it 2.
- **F7. Answered:** `_answered` (`:580-606`) needs the halt's head to be both findings files' `head:`; its docstring excludes a
  catch-up halt (`0063-rejoin` design D4). `AMENDED` (`:71`, `:808-809`); with every stage stuck the run halts at once
  (`:3164-3174`). Converge's prose agrees (`skills/mf-converge/SKILL.md:136-140`).
- **F8. The catch-up count:** merges only (`skills/mf-converge/SKILL.md:169`, `:181-186`), By rule (`:199-201`, `:230`), `:445`;
  `docs/principles.md:81`. `tests/fake_worker.py`'s by-rule mimic returns `None` unless the selection is merges (`:104-105`).
- **F9. The fixer and Step 7:** the fixer's list puts no limit on `tasks.md` or `design.md` (`skills/mf-converge/SKILL.md:403-418`);
  Step 7 runs only `gate_run` (`:433`); Step 1.6 halts `verify: halt` (`:247-254`), whose text `gate_check.py` prints (`:270`).
- **F10. Rescue:** `rescue()` (`conduct.py:2470-2507`) spawns a worker for every stage in `RESCUED` (`:78`); a verify halt fits no
  row of `skills/mf-rescue/SKILL.md:53-62` and falls to a diagnosis (`:51`); the proposal template (`:104`); D53
  (`docs/decisions.md:512-536`); D47's and `skills/mf-ship/SKILL.md`'s rejoin rows (`docs/decisions.md:469`,
  `skills/mf-ship/SKILL.md:55`, `:85`).

## Goals / Non-Goals

**Goals:** the trips of `0068`, `0069`, `0070` and isekai `0095` pass under `mf-ship` with no person beyond the amend a decision
needs.

**Non-Goals:** a blank-line rule for `_resolve`; editing `0.59.0`'s released entry or the archived `0070` artifacts; a repeat card
keeping its grade under the change's own backlog heading.

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | `gate_run.py --tree <path>` gates and records a worktree from any cwd | Q2 | `cd`; `make -C` |
| [D2](#d2) | Integrate commits, then gates; a broken test fixed by amending the merge; any other red halts with `.red` naming the merge | Q2, Q3, `0061·R4` | `DIFF_BASE=MERGE_HEAD` |
| [D3](#d3) | `decisions` renumbers the `[Unreleased]` entries, never recites `CHANGELOG.md` | Q5, Q6, `0070·R8` | a blank-line rule |
| [D4](#d4) | A taken-back version brings its blocked dependents; a rejoin re-reads only an unplanned plan; `--no-merges` | Q4, `0063·S2`, `0057·R9` | rejoin requests per dependent |
| [D5](#d5) | The person's amends answer a catch-up or verify halt | Q7 | the catch-up halt standing (`0063-rejoin` D4) |
| [D6](#d6) | Merges and amends have their own count and pass by rule | Q11 | a re-converge from round 1 |
| [D7](#d7) | The fixer never edits `tasks.md` or `design.md`; Step 7 runs `gate_check` | Q8 | a halt one round later |
| [D8](#d8) | The run diagnoses a verify halt itself; every proposal names the command | Q9, Q12 | a rescue worker |
| [D9](#d9) | The record: D45, D47, D53, `docs/principles.md`, the changelog note | Q6, Q10, `0067·R8` | — |

### D1

`main` gains `parser.add_argument("--tree", type=Path, help="gate this worktree, not the current directory")`; when given,
`os.chdir(args.tree)` runs inside the `try` before `gate(args.fresh)`, and an `OSError` raises `Stop(2, f"gate: cannot run —
{args.tree}: {error.strerror}")`. The docstring's usage line reads `gate_run.py [--fresh] [--tree <path>]`, and its second line
"Run from the repository root, or name a worktree with `--tree`."

### D2

`skills/mf-integrate/SKILL.md` Step 4, renamed *Commit and gate*:

1. `make -n gate` on the worktree, as now.
2. The clean check, as now.
3. **Commit the merge**, the body as now.
4. `uv run --script ../mf-converge/scripts/gate_run.py --tree <worktree>`. Red on a merged test the union broke → fix it per Step 3
   item 3, once, amend the merge commit — `git -C <worktree> commit --amend`, its message gaining the `<path>: test fixed — …`
   line before the trailers, its parents kept — and gate again.
   Any other red → **halt** with the merge committed: write `.minions/integrate/<change-id>.red` holding `gate red`, the date and
   `head: <the full sha the gate judged>`, `git -C <worktree> rev-parse HEAD`; never weaken the gate to pass.
5. Delete `.md`, `.resolved`, and `.red` on green, as now.

The description `:3` and flow `:22` read "commit the merge, and gate", and so does `skills/mf-release/SKILL.md:139`'s account of
integrate. Step 2's table gains, before the `fails · nothing to merge` row, two rows: `| fails | `.red` names `HEAD` | **halt**,
copying `.red` |` and `| fails | `.red` names another commit, and `git merge-base --is-ancestor <default-branch> <branch>` exits 0 |
the person fixed or amended the committed merge: Step 4.4 |`, a `.red` naming another commit otherwise going to Step 3.1; the
`succeeds · .red` row goes. Never `:189` reads "**Never release over a red gate**, or weaken it to pass."

`conduct.py` gains `_red(primary, tree, change) -> str | None`: the `.red` file's `head:` sha resolved with `git rev-parse --verify
<sha>^{commit}`, its full sha, or the raw text when it resolves to none; `None` when there is no file or no such line. Since the
sha is the head the gate judged, a red gate over the person's fix names that fix, and the version reads halted again. `stage_of` reads it before its `_merge_open` block: the sha is `HEAD` → `("integrating", "red gate: …")`; any other
sha — an ancestor after the person's fix, or none reachable after the person's amend of the merge — → `("integrate", "")`, and the
integrator gates again. `_check_integrate` fails on the sha being `HEAD`, before the subject check, and reads the subject of
`HEAD`'s newest first-parent merge, `git rev-list --first-parent --merges -1 HEAD`, with only one-parent commits after it, so the
person's fix commit after the merge passes. A `.red` with no `head:` line keeps today's open-merge reading.

### D3

In `decisions()`, the loop reads `if path not in (DECISIONS, "CHANGELOG.md"):`. After it, when `CHANGELOG.md` is in the tree, read
through `_safe_path` as `_recite` does: `head, entries, rest = _split_changelog(text)`, and `_write` `head + _renumber(entries, ids) +
rest` when it differs. The released sections are `rest`, never renumbered.

### D4

`Run._unblock(threads) -> None`: each change in `self.blocked`, in change-id order, one of whose `_dependencies(self.primary, change)`
has a live thread, is taken back with `take_back` — once per dependency thread: `self.unblocked`, a set of `(change, thread
object)`, skips a pair tried before, so a refused take-back logs once; the set holds the `Thread` itself, whose identity
no later thread reuses. `take_requests` calls it after its requested names; `join()`'s
loop calls it with no request, so a chain comes back in one pass and a thread started by any path brings its dependents. In
`take_back`, `self.read_plan([version])` runs only `if change not in self.planned`: a planned version's models file is still read
and compared as it joins (`conduct.py:2943-2949`), which is the read *A halted version rejoins a live run* requires.
`catch_up` counts `rev-list --count --no-merges`.

### D5

`_answered(runs, tree, change, halt)` keeps its rule and gains a second, read in `_answered`: the halt is of a kind the person's
amend answers, and `_amended_only(tree, change, halted)` holds — the halt's head is an ancestor of `HEAD` and not `HEAD`, and every
commit in `halted..HEAD` has one parent, the subject `docs(<change>): amend the change directory`, and only paths under
`openspec/changes/<change>/` (the diff-tree listing `_amend` reads). The kinds: a halt in a catch-up run — the newest `## Run`
heading ends ` · catch-up`, as `_granted_run` reads a heading — with both findings files still `verdict: clean`; a halt line holding
`verify: halt`; and one holding `amend needed` ([D7](#d7)). The docstring names this change's D5 where it named `0063-rejoin` D4.
`skills/mf-converge/SKILL.md:136-140` states both rules; a void catch-up halt with both files clean runs the catch-up round
again, any other void halt opens `· amended` from round 1, as now.

### D6

**Merges and amends** — merges, and the person's `docs(<id>): amend the change directory` commits touching only
`openspec/changes/<id>/` — replace *merges only* at `skills/mf-converge/SKILL.md:169`, `:181-186`, `:445` and in
`docs/principles.md:81`. By rule (`:199-201`) runs `replay` for each merge and skips each amend, which Step 1's gate and `gate_check`
already judged; its `## By rule` section names each amend `- <sha>: the person's amend`. A selection of amends alone, with no
merge, passes by rule too. *Empty resolutions* (`:230`) stays merges only. `tests/fake_worker.py`'s mimic takes a non-empty
selection whose every commit is a merge or an amend, in place of `not merges` and `selected != merges`, and writes an amend's line
as `- <sha> — the person's amend`, so `_write_by_rule`'s ` — ` split holds and an amends-only selection's lines are not empty.

### D7

Step 6 gains, after `:406`: "**never edits the change's `tasks.md` or `design.md`**: a card whose fix needs one is `wontfix`,
naming the amend the person commits, and the round halts `amend needed — <card ids>`." Step 7's `:433` reads "Re-run the gate
yourself, through `gate_run.py`, then Step 1.6's `gate_check.py`, and write `verify` to the status log." Step 1.6's halt line is
one line: `verify: halt — <sub-task ids>`.

### D8

In `rescue()`, after its spent and stopped guards: a `converge-halted` stage whose halt holds `verify: halt` → write
`.minions/rescue/<change>.md` through `os.open(…, O_WRONLY | O_CREAT | O_TRUNC | O_NOFOLLOW)` — `halt:` the line, `sub-task:
none`, `cause: a Verify: changed since the cut`, `proposal: commit docs(<change>): amend the change directory, then conduct.py
rejoin <change>, or /mf-ship with no run live` — log `rescue — <change>: diagnosed · .minions/rescue/<change>.md`, halt `rescue
diagnosed — …`, and return `False` with no spawn; it counts no rescue against `RESCUES`. `[rescue] skip` skips it, as it skips a
worker. `skills/mf-rescue/SKILL.md`: a row `converge's verify: halt | diagnosed by the run | —`, and the template's `proposal:`
names "the command the run takes back: `conduct.py rejoin <change-id>` while a run is live, else `/mf-ship`."

### D9

D45: "…hands a semantic conflict to the person with the merge open, and commits the merge, its body naming every path it settled…",
then "It gates the committed merge in its worktree; a red gate halts with `.red` naming the merge." D47: a version taken back
brings each version it blocked; a clean catch-up, verify or `amend needed` halt followed only by the person's amends is answered;
the rejoin rows read
"nor one whose converge or integrate halt was answered while its rescue ran" (`0067·R8`), also in `skills/mf-ship/SKILL.md:55`,
`:85`, its diagnosed row (`:90`) names the run's own diagnosis of a verify halt, and its `integrating` line (`:114`) says a red gate
holds the committed merge, and the run integrates again after the person's fix. D53: a verify halt is the run's to diagnose,
with no worker; the fixer edits no plan. Phase 2's `CHANGELOG.md` entry carries one line: "`0.59.0`'s entry calls the cap policy
D54; it is D56."

## Tests

`git grep -c '^def test_' 1df4e7a -- tests/test_conduct.py tests/test_integrate.py tests/test_gate_run.py` counts the files at the cut.
Extended, under `T2`:

| test | gains |
|---|---|
| `test_records_go_under_the_primary_run_directory` (`tests/test_gate_run.py`) | a commit in the worktree, then `--tree <worktree>` from the primary prints `gate: green` with the worktree's tree and records it under the primary; a missing path exits 2 |
| `test_status_reads_each_stage_from_disk`, `test_each_check_passes_only_on_disk_evidence` | a `.red` whose `head:` is `HEAD`, in short or full form, reads `integrating` and fails the check; one naming an ancestor, or an unreachable sha, reads `integrate`; a one-parent commit after the integrate merge passes the check |
| `test_decisions_renumbers_a_colliding_decision_and_its_citations` (`tests/test_integrate.py`) | an `[Unreleased]` citation renumbered, a released one kept |
| `test_a_halted_dependency_blocks_a_chain` | a rejoin of the dependency alone brings back the chain |
| `test_the_plan_is_read_once` | a rejoin of a planned version does not re-read its plan |
| `test_after_waits_for_its_dependency` | a cut-only version with a `merge_in` commit is merged in again when the default branch changes `README.md`, outside `GATE_FILES` — red before the fix, which reads it as started |
| `test_a_fix_after_a_cap_halt_converges_afresh` | a clean catch-up halt, a verify halt and an `amend needed` halt answered by the person's amend read `converge`; the catch-up then passes by rule and releases; a non-amend commit still stands |

Added, the fake worker's `verify-halts` mode beside it: `test_a_verify_halt_is_diagnosed_without_a_worker` — `T2`: no test reaches a
verify halt. `slow` when over 5 s (`T1`). None deleted.

## Dependencies

None.

## Risks / Trade-offs

- **A red merge is committed:** the branch holds a red tree until the person's fix; the release and the catch-up's gate refuse it,
  and nothing pushes it.
- **An amend that ratifies text already there:** with D7 the fixer no longer edits the plan, so the case does not arise in a run.
- **A worker writes a `docs(…): amend` commit:** the answer rule reads the subject and paths only; D7 forbids the fixer the plan,
  and `0063·S3` keeps the worker-writable mailbox in the backlog.

## Verdict

Ready to build.
