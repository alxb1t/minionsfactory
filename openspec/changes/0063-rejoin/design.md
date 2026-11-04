# Rejoin — design

A live run takes back a fixed version, and newly cut ones, through a request it polls; a person's fix voids a converge halt.
Verdict at the end: ready to build.

## Context

Read at `ced9bac` (v0.51.0). `conduct.py` is `skills/mf-ship/scripts/conduct.py`.

- **F1. The loop.** `ship()` starts one `threading.Thread(target=self.take, …)` per open version, then joins each in order; the
  main thread wakes only when a `join()` returns (`:2404-2470`). `open_versions` is read once (`:2406`); `read_plan` reads each
  models file once (`:2270-2284`); `advance` halts a version whose models file differs from the plan (`:2077-2165`).
- **F2. Halts are for good.** `halt` appends `(who, reason)`, `stopped` matches `who in ("run", change)`, nothing removes an entry
  (`:1983-1998`); `closing()` names them (`:2000`).
- **F3. The probe** runs once per executor before the threads, a failure halting the run (`probe`, `:2291-2326`; `ship`).
- **F4. The stale halt.** `stage_of` returns `converge-halted` from `_converge_halt` — the newest run's top line, no head compared
  (`:517-520`, `:681-744`); `_check_converge` reads it the same way (`:746-756`). Converge counts the cap from the findings files'
  `round:` (`skills/mf-converge/SKILL.md:168-171`, `:410`), so isekai `0095`'s Run 6 (2026-11-04 12:14) halted at once: "HEAD
  a851a06 is 3 commits past the judged head 7ee2179 … this run carries no grant=yes; nothing dispatched".
- **F5. `grant`** refuses unless the stage is `converge-halted` with "cap reached", then calls `preconditions`, which refuses a
  live run, then writes `.minions/grants/<id>` and starts a run (`:2555-2567`). A waiting grant reads `converge, granted`
  (`:722-723`), so a second `grant` is refused: "is at converge, not a cap halt".
- **F6. The base.** `catch_up` merges a cut-only version through `merge_in`, and halts a started one whose base the default
  branch passed changing `GATE_FILES` (`:2207-2249`). `merge_in` runs `git merge --no-ff --no-commit` through `_git`, which stops
  on any conflict, then the delta check (`:2185-2205`). `integrate.py` holds `changelog(tree)` and `decisions(tree)`, which settle
  `CHANGELOG.md` and `docs/decisions.md` mid-merge (`skills/mf-integrate/scripts/integrate.py:301-321`, `:463-487`); the conductor
  loads `delta` from it by `runpy` (`:1965`).
- **F7. The claim** — `.minions/runs/active`, live or stale (`_claim`); `preconditions` refuses a live one (`:1956`).
- **F8. The cards.** `0055·S2`: `_closed` reads `.done` with no `is_file()` (`:475-488`). `0051·R8`: `skills/mf-converge/SKILL.md`'s
  *Resuming a run* says nothing of a `· grant` run (`:123-127`).

## Goals / Non-Goals

**Goals:** a fixed halt rejoins the live run; a version cut mid-run joins it; a fix after a cap halt converges afresh with no
grant; `grant` never refuses without naming what to run; a sibling's release no longer halts a started version.

**Non-Goals:** fixing a halt without the person; a request to an ended run; a run-level halt rejoined.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | A request file, `.minions/runs/rejoin/<id>` or `…/all`, polled by the main loop every `REJOIN_POLL` seconds | a signal still needs the loop to wake | a signal; a second run |
| [D2](#d2) | The run takes every requested open version whose stage is no halt; clears its halts and blocks; reads its models; starts `take` | the stage is read from disk, as D47 has it | keeping state for a version |
| [D3](#d3) | A new executor is probed in the live run, once; a failure halts only its versions | the running versions never touch it | waiting for the next run |
| [D4](#d4) | A converge halt names its head; it is void when that head is the findings `head:` and `HEAD` descends past it; converge opens a `· amended` run from round 1 | a commit past the judged head at a halt is never converge's own; converge counts from `round:` | voiding in the conductor alone (F4); voiding on `head:` not `HEAD` alone, which reads converge's own fix and catch-up halts, and a rewritten history, as answered |
| [D5](#d5) | `grant` names `/mf-ship` when it refuses; during a live run it writes the grant and a request | isekai #15 and 15:40 | — |
| [D6](#d6) | `merge_in` settles `CHANGELOG.md` and `docs/decisions.md` conflicts with `integrate.py`'s rules; `catch_up` merges a started version behind a gate change | a sibling release that touched `AGENTS.md` halted each started version | merging by an agent |
| [D7](#d7) | The record: `rejoin` and `grant` events, the `start` line's grants, `report` | the person sees what rejoined and what a grant bought | — |

### D1

`REJOIN_POLL = 10`, patched short in tests. `rejoin(cwd, change)` — a subcommand: no live claim → `Stop(2, "rejoin: no run is
live — run /mf-ship")`; a `change` no open version holds → `Stop(2, …)`; else it writes `.minions/runs/rejoin/<change>`, or
`all` with no id, and prints `rejoin: requested <change|every halted version>`. `ship()` deletes the folder's files before its
first worker. Its join loop becomes: start the threads; then `while True`: `self.take_requests(threads)`; join each live thread
with `timeout=REJOIN_POLL`; with none alive, `take_requests` once more, and break when it started none.

### D2

`take_requests(threads)` reads and deletes the request files, then for each open version (`open_versions` read again) a request
names, whose thread is not alive: `stage_of` in `HALTS` → log `rejoin — <id>: still <stage> — <why>`, and skip; else remove its
entries from `self.halts` and `self.blocked`, read its models into `self.plan` (`read_plan([version])`), probe its executors
not yet probed (D3), log `rejoin — <id>: <stage>`, and start `take`. A `run` halt in `self.halts` stops it all, as before.
The poll runs beside live threads, so it raises nothing: an entry `unlink` refuses is no request, a failed `open_versions`
logs `rejoin — skipped — <why>`, and a failure taking one version halts that version.

### D3

`self.probed: set[str]`, filled by the start's probes. `probe(executor, who)` halts `who`: `"run"` at the start, as before;
in `take_requests`, each taken version on that executor, the station `probe-<executor>`.

### D4

Every converge `halt` line ends `· head <sha>`, `git rev-parse HEAD` at the halt (`HALT_HEAD`). `_answered(runs, tree, change,
halt)` — the halt names a head that resolves, both findings files' `head:` resolve to it, and it is an ancestor of `HEAD` and not
`HEAD`. A halt after converge's own fix commit, or in a catch-up run, names a head the files did not judge; a halt naming no
head stands. `stage_of`: a halt naming `.minions/backlog.lock` first, as in the skill; then a halt with `_answered` true →
`("converge", "amended: HEAD past the halted head")`, before the grant case; `advance` then deletes a waiting grant unspent, and
sends no `grant=yes`. `_check_converge` skips an answered halt the same way. `skills/mf-converge/SKILL.md`'s *Resuming a run*
gains, after its lock case: the top line a `halt` whose head is both findings files' `head:`, and `HEAD` past it → open a run
marked `· amended`, and start at Step 1 over the whole change, writing `round: 1`; and, for `0051·R8`, a run marked `· grant`
that resumes stays a granted round: Step 9, never Step 8.

### D5

`grant`: stage `converge` with reason `granted` → `Stop(2, "grant: cannot run — <id> has a grant waiting: run /mf-ship")`; any
other stage → `Stop(2, "grant: cannot run — <id> is at <stage>: run /mf-ship; grant once converge caps")`. A live claim → write
the grant file and `.minions/runs/rejoin/<id>`, print `grant: recorded — the live run takes <id> back`, exit 0; else as before.

### D6

`merge_in(tree, change, default)`: the merge through `_maybe`; on a conflict, run `changelog(tree)` when `CHANGELOG.md` is
unmerged and `decisions(tree)` when `docs/decisions.md` is, staging each; any path still unmerged, or a rule that stops →
`git merge --abort` and `Stop(1, …)` naming the paths and `git -C <tree> merge <default>`. Then the delta check and the commit,
as before. `catch_up`'s gate-change case calls `merge_in` instead of halting. Both rules are loaded with `delta`, by `runpy`.

### D7

- **`rejoin — <id>: <stage>`**, and `rejoin — <id>: still <stage> — <why>`.
- **`grant — <id>: one more round past the cap`**, logged by `advance` when it sends `grant=yes`.
- **The `start` line** gains `· grant <ids>` for the grant files standing at the start.
- **`report`** prints a `rejoined` line per version that rejoined, after its halts.
- **`EVENTS`** gains `rejoin` and `grant`, so `verify_log` reads them.

## Tests

`grep -c '^def test_' tests/test_conduct.py` prints `41`; `uv run pytest -q --collect-only tests/` collects `112`. This change
adds four integration tests on the fake worker, no end-to-end run (`T1`); none is deleted or merged.

| test | why new (`T2`) |
|---|---|
| `test_a_fix_after_a_cap_halt_converges_afresh` | no test commits after a converge halt |
| `test_a_fixed_version_rejoins_a_live_run` | `test_a_later_version_ships_past_a_halted_one` ends with the run; a rejoin needs one held open |
| `test_a_version_cut_during_a_run_joins` | the same, with a version cut mid-run |
| `test_a_new_executor_is_probed_mid_run` | the probe tests run at the start only |

Extended: `test_a_grant_buys_one_round` (the refusals, a grant during a live run), `test_after_waits_for_its_dependency` (the
started version merged in), `test_a_build_dead_in_simplify_resumes_at_it` (a FIFO at `.done`, `0055·S2`).

## Dependencies

None.

## Risks / Trade-offs

- **A worker can write a request**: it makes the run read a stage from disk again, which D47 already trusts — the class
  `THREAT_MODEL.md`'s *Out of scope* accepts.
- **A rejoining version's stations read today's skills**, not those its run started with — the same as any station today.
- **An amended run restarts the count**, so a person's fix buys three rounds, not one; re-plan at the cap is its limit.

## Verdict

Ready to build.
