# Ship fixes 2 — design

A halt before round 1 gets an answer, the load-bound tests get slack, and every worker gets a scratch folder inside its sandbox.
Verdict at the end: ready to build.

## Context

Read at `95dcad0` (v0.67.0). The brief's facts were read at `f349aa8`; `git diff --name-only f349aa8..HEAD` names no file the
facts below cite but `docs/decisions.md`, so they stand, and D57's line was re-read. `C` is `skills/mf-ship/scripts/conduct.py`,
`T` is `tests/test_conduct.py`.

- **F1. A halt before round 1.** `skills/mf-converge/SKILL.md:237` (Step 1 item 5) halts on a red gate before `start` (`:249`):
  the newest `## Run` holds one `round 1 · halt — … · head <sha>` line. `_answered` (`C:741-770`) is false for it — `HEAD` is the
  halted head (`C:756`), or no findings file names it (`C:762-769`); `stage_of` (`C:994-1001`) returns `converge-halted`; the
  rescue only diagnoses; `take_back` logs `still converge-halted` (`C:3330-3332`). Converge's resume rules (`SKILL.md:136-157`)
  have no case for it. Seen in `0077-run-metrics`' Run 2.
- **F2. Halts with no `start` already.** Step 1 item 6's `verify: halt` (`SKILL.md:239-247`) is written before `start` too; its
  answer is the person's amend (`_amendable`, `C:699-713`) and its diagnosis the run's own (`Run.rescue`, `C:2769-2772`).
- **F3. The lock test.** `test_a_stale_lock_is_cleared_and_converge_resumes` (`T:2270`) ages its young lock `time.time() - 599`
  (`T:2311`) against `LOCK_STALE = 600` (`C:52`, `<=` at `C:684`): the run must reach `_clear_stale_lock` within 1 s.
- **F4. The timing tests.** `test_a_failing_metric_is_unavailable_with_its_reason` sets `TIMEOUT_SECONDS` to 0.5
  (`tests/test_metrics.py:146`), so each catalogue script must start Python in 0.5 s; its `slow` script sleeps 5 s. `_when_logged`
  sleeps 0.5 s for the halted version's thread to return (`T:207-208`). The run's version threads are unnamed (`C:3361`, `C:3674`).
- **F5. No scratch path.** `argv` sets `UV_CACHE_DIR=<primary>/.minions/uv-cache` (`C:2171`) and no `TMPDIR`, so `mktemp` (allowed,
  `C:126`) writes outside a worker's sandbox, which writes only `reach()` and the common directory (`C:2137-2142`, Codex's
  `writable_roots` `C:2205-2207`). `skills/mf-release/SKILL.md` Step 2 (`:154-173`) names no scratch path. D57
  (`docs/decisions.md:580-588`) lists the generic run-directory folders; `uv-cache` is not among them.

## Goals / Non-Goals

**Goals:** a flaky gate before round 1 costs a rejoin, not a person's commit; the tests named in F3 and F4 pass at any load; a
worker's `mktemp` lands inside its sandbox.

**Non-Goals:** an amend during a rescue and a rescue's own amend at `amend needed` (D47, D53 stand); a build rule placing a timing
`Verify:`; `test_run_halts_on_a_timeout`'s `< 20` s check.

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | A halt before round 1 is answered by any commit past its head, or re-run once per run at it; converge opens a plain new run | Q3 | a rescue for it; a rule on the halt's reason text |
| [D2](#d2) | The `verify: halt` keeps its own answer and diagnosis | C1 | re-running it, which halts again and drops the run's diagnosis |
| [D3](#d3) | The lock test's young lock is `LOCK_STALE - 60` old | Q4 | a mocked clock |
| [D4](#d4) | `test_metrics`' limit is 5 s; the timed-out script moves to its own `slow` test | Q6 | marking the whole test `slow` |
| [D5](#d5) | `_when_logged` polls the halted version's thread, found by name | Q6 | a longer sleep |
| [D6](#d6) | `TMPDIR=<primary>/.minions/tmp` in every worker's environment, emptied at a run's start; mf-release Step 2 names `mktemp` | Q5 | a `scratch/` in the change folder, which edits D57 |

### D1

A **halt before round 1** is a converge halt, other than a `verify: halt` ([D2](#d2)), in a newest run with no `start` line, not
marked `· grant`. In
`C`:

- `_run_started(runs, change)` returns whether the newest run, from its `## Run` heading to the next, holds a line `_is_event`
  reads as `start`; `C`'s `_started(pid)` keeps its name. `_before_round(runs, change, halt)` is `not _run_started(…)`, not
  `_granted_run(…)`, and no `verify: halt` in `halt`.
- `_answered`, after its `halted == HEAD` return, returns `_ancestor(tree, halted, "HEAD")` for a halt before round 1: any commit
  past the head answers it, the findings files unread. `stage_of` gives it `AMENDED`, as today.
- `_rerun(runs, tree, change, halt)` is `_before_round(…)` and the halt's `· head` resolving to `HEAD`. `stage_of` checks it after
  the debt lock and before `_answered`, returning `("converge", RERUN)`, `RERUN = "re-run: halted before round 1 at this head"`.
- `_check_converge` is unchanged: right after the station, `HEAD` is the halt's head, `_answered` is false, and the check names
  the halt. `Run.held` reads `converge` on disk, not in `RESCUED`, so no rescue starts.
- `Run.reruns: set[str]`, beside `self.answered` (`C:2631`). `advance` adds the change when its stage is `("converge", RERUN)`.
  `take_back`, after its `answered` check, logs `rejoin — <id>: still halted — <RERAN>` and returns False when the stage is
  `("converge", RERUN)` and the change is in `reruns`; `RERAN = "halted before round 1 again at this head: a commit answers it"`.

```
  converge halts, no start, no grant, head H
      │
      ├── HEAD past H ─────────▶ converge · amended: HEAD past the halted head
      └── HEAD is H ── re-run in this run? ── no ──▶ converge · re-run   (advance adds it to reruns)
                                   │ yes
                                   ▼
                           halted; a rejoin logs: still halted — halted before round 1 again …
```

`skills/mf-converge/SKILL.md`'s *Resuming a run* gains a paragraph after the debt-lock one: the top line is a halt in a run with no
`start` line, and no `verify: halt` → open a plain new run, with no mark, as a fresh invocation does; no grant is needed. A catch-up
run halted before its `start` — in its catch-up check or Step 1 — falls under it too: the plain new run's own catch-up check, over
both findings files still clean, runs the catch-up round again, so the commits since are judged.

### D2

C1, decided by the cutter: Q3's "no `start`" also reads a `verify: halt` (F2). Re-run at its head, it halts again, and `stage_of`'s
`converge` would skip `Run.rescue`'s diagnosis (0071-ship-fixes D8). It stays as it is: answered by the person's amend alone.

### D3

`T:2311` reads `young = time.time() - (conduct["LOCK_STALE"] - 60)`. The test only.

### D4

`tests/test_metrics.py:146` sets `TIMEOUT_SECONDS` to 5, and the `slow` body and its expected value leave
`test_a_failing_metric_is_unavailable_with_its_reason`. The new `test_a_metric_past_the_limit_is_unavailable`, marked `slow`, sets
the same 5 s limit, runs one script that sleeps 30 s, and expects `{"status": "unavailable", "why": "timed out after 5 s"}`.

### D5

The run names each version's thread for its change: `name=change` at `C:3361`, `name=version.change` at `C:3674`. `_when_logged`'s
`wait` reads the changes from each `said` part holding ` · halt — `, the second ` · `-field, and polls every 0.05 s, to its 60 s
deadline, until no live thread in `threading.enumerate()` bears one of their names. `said` holding no halt part waits for none.

### D6

`argv` adds `TMPDIR=<primary>/.minions/tmp` after `UV_CACHE_DIR`, on both executors' `env` prefix, and makes the folder when it is
missing, so every caller — a run's worker, the probe's scratch repository, `conduct.py agent` — names one that exists. `_fresh_tmp(primary)` empties
it: a link or a file there is unlinked, a folder removed with `shutil.rmtree`, then `mkdir(parents=True, exist_ok=True)`.
A link at `.minions` halts the run, `.minions is a link: a person settles what it names`, and its target's `tmp` keeps its files:
the delete runs through a descriptor on `.minions` itself. `Run.ship` calls it after `self.unlock(DEBT_LOCK)` (`C:3638`), under the claim, before any probe or worker. The folder sits in
the primary, which every worker writes. Like `uv-cache`, it is no change's file and goes unlisted in D57.

`skills/mf-release/SKILL.md` Step 2 gains one line: a scratch file for the fold is made with `mktemp`, inside a run's worker's
sandbox: its environment names `.minions/tmp/`, and a Claude worker's sandboxed command may use Claude Code's own `TMPDIR` instead.

## Tests

`git grep -c '^def test_' -- tests/` totals 221 at the cut. Added: 2 — an integration test of the conductor with the fake
worker, and a unit test of the collector. No end-to-end test.

- `test_a_halt_before_round_1_runs_again_at_the_same_head` (`T`, new, marked `slow`: it holds live runs, per `T1`) — its
  `stage_of` `RERUN`, `check` and `AMENDED` steps sit in `test_a_fix_after_a_cap_halt_converges_afresh`: a run whose only line is
  `round 1 · halt — gate red before round 1 · head H` at `HEAD` H gives `stage_of` `("converge", RERUN)`, and `check`'s converge
  names the halt; a commit past H gives `AMENDED`, and so does one past a `· catch-up` run's halt with a `catch-up` line and no
  `start`. A live run with `tests/fake_worker.py`'s new `red-halts` mode and a
  held second version: the halt, then `rejoin` with no commit and the fake reset, and converge runs again and releases. A second
  run, the halt on disk at `HEAD`, `red-halts` on: converge re-runs, halts again, and a `rejoin` logs
  `still halted — halted before round 1 again at this head: a commit answers it`. `T2`: no run test reaches a halt before round 1.
- `test_a_metric_past_the_limit_is_unavailable` (`tests/test_metrics.py`, new, `slow`) — [D4](#d4).

Extended or edited:

- `test_a_fix_after_a_cap_halt_converges_afresh` (`T:5017`) — each `## Run` it writes with a headed halt, save the debt lock's,
  gains a `start` line below the halt, so it still reads a halt after `start`; beside the `verify: halt` the line changes nothing.
- `test_a_stale_lock_is_cleared_and_converge_resumes` (`T:2270`) — [D3](#d3); its first run starts over a `.minions/tmp/` holding a
  file, and a second over a `.minions/tmp` link to a folder outside the repository: after each, `.minions/tmp/` is an empty folder,
  and the link's target keeps its file. A third starts over `.minions` a link: the run halts naming it, and the link's target keeps
  its `tmp` file.
- `test_a_failing_metric_is_unavailable_with_its_reason` — [D4](#d4).
- `test_a_claude_worker_starts_in_the_sandbox` (`T:5552`) — each executor's `env` prints `TMPDIR=<root>/.minions/tmp`, and
  `<root>/.minions/tmp` is a folder after `argv`.
- `test_a_worker_carries_the_allowlist_and_a_denial_is_named` (`T:5714`) — the Claude and the Codex prefix each end `cache, tmp`,
  read `len(hooks_off) + 5` long (`T:5769-5770`, `T:5846-5847`).
- `_when_logged` (`T:188`) — [D5](#d5).

No test is deleted or merged.

## Dependencies

None.

## Risks / Trade-offs

- A gate red for a real reason re-runs once per run before it stays out: one gate's time, against a person's commit per flake.
- A plain new run after a halted `· amended` run drops that mark: Q3 settled a plain run.
- Claude Code's sandbox may set its own `TMPDIR` for a sandboxed Bash command; then a Claude worker's `mktemp` writes there,
  still inside its sandbox, and the prefix's value reaches the worker's own process and every Codex worker.
- Emptying `.minions/tmp/` at a run's start removes a hand-run station's scratch file left there; a hand run sets no `TMPDIR`.

## Verdict

Ready to build.
