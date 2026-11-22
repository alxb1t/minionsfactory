# Gate outside — design

The conductor runs the gate and the close's steps as scripts; a worker runs `make check`, and the close worker only simplifies. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

A phase worker ends on `make gate` through `gate_run.py`, which outlasts the 5-minute cache, so the worker's context is written again. The close worker asks for the gate before simplify, after each angle, after simplify, and again in `mf-build`'s close. It runs on `[build]`, though simplify writes none of the change's logic.

`conduct.py` runs no gate during a build, so a red gate after the last phase has no worker behind it, and a red gate after simplify is a halt that only a person answers. Converge already runs the gate itself, in `converge.py`, under the sandbox runner.

```
before:  phase N ─ worker: make gate ─▶ close worker: simplify, gate × 8, metrics, plan check, build.done
after:   phase N ─ worker: make check ─▶ conductor: gate ─▶ simplify worker: make check
                                                      ─▶ conductor: close (gate, metrics, plan check, build.done)
```

## Goals / Non-Goals

- **Goals:** no worker waits on the gate; the close's steps are one code path for a run and a hand build; a red gate after the last phase or after simplify has a route that needs no person; the gate's time is logged.
- **Non-Goals:** the run log's new fields; a time budget for the gate that fails; the release's gate runs; the Codex side.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | The close has its own models key: a `build-close` part, a `[build.close]` table, and a close spawn that runs on it, else `[build.moderate]`, else `[build]`, key by key | simplify judges code but writes none of the change's logic, and the close ran on the strongest model | a close on `[build]` always, as before |
| [D2](#d2) | The close's steps are one command, `conduct.py close <change-id>`, which the run and a hand build both run | separate paths for the close would drift, and the hand path is the one no run exercises | a close inside the build loop alone |
| [D3](#d3) | The conductor runs the full gate, as a script, after the last phase and in the close; a worker runs `make check` where the target stands, and the gate through `gate_run.py` where it does not | a worker waiting on a gate that outlasts the cache writes its context again; a script's gate costs no tokens | a gate in the worker; a gate only at the close |
| [D4](#d4) | A red gate after the last phase starts one `phase=repair` worker, on the last phase's models, handed `gate.red`; the gate runs again, and a second red halts | the rescue may not edit code or a test, so a red gate with no worker behind it would always need a person | a halt on the first red; a repair loop |
| [D5](#d5) | The close worker is simplify alone, `make check` after each angle; a gate red after it drops the simplify commit and runs the steps again | simplify holds no verdict ([D13](../../../docs/decisions.md)), and its commit is the only thing between a green tree and the red one | a halt on a red gate after simplify |
| [D6](#d6) | A close whose every commit past `build.simplified`'s head amends the change directory runs the steps with no worker | a close was done again after a short rescue, and the redo cost more than the rescues | a second simplify after every amend |
| [D7](#d7) | `build.done` is the conductor's file, written by `close`; the freeze runs no plan check when `build.done` names the frozen head, and shows the close's own result | a worker wrote `build.done` before, so the freeze reran the plan check; the close's run is now the conductor's, under the same sandbox | a freeze that always reruns the check |
| [D8](#d8) | The conductor logs a gate with the `check` event the log already has, and adds no event and no field | many call sites write a halt's text, tests pin the spawn and finish lines' ends, and readers parse them | new log fields here |
| [D9](#d9) | The fixer runs `make check`, converge runs the gate after it as today, and the gate's pytest gains `--durations=20` | a fix round asks for the gate more than once, once inside the fixer's session; nothing names where the gate's time goes | a gate budget that fails now |

### D1

The brief's models line gains `build-close <model> <effort>` after `build-moderate`, with no host. `modelsfile.TABLES` writes it as `[build.close]` with `model` and `effort` and no `executor`; a hand-written `executor` there halts the version, as it does for `[build.moderate]`.

The conductor plans the station `build.close` with the others, so the run reads it once. The close's spawn takes its `model` from `[build.close]`, else `[build.moderate]`, else `[build]`, and its `effort` the same; its executor is `[build]`'s. The suggested value in the skills is Sonnet 5.5 · high.

### D2

`conduct.py close <change-id>` runs in the version's worktree: the gate, the metrics where a catalogue stands, the plan check, then `build.done`. It exits 0 `close: done`, 1 `close: fail — <why>`, 2 cannot run. Each step is a function the build loop also calls, so a run and a hand build share the code.

```
gate ─ red ─▶ gate.red, build.halt (stop: gate)          ─▶ exit 1
 │green
metrics ─ halt ─▶ build.halt (stop: metrics)             ─▶ exit 1
 │ok, or no catalogue
plan check ─ exit 1 ─▶ build.halt (stop: plan check)     ─▶ exit 1
 │clean
build.done: head, simplify ─▶ build.closing removed      ─▶ exit 0
```

`build.halt` keeps the keys the rescue reads — `sub-task: close`, `stop:`, `head:` — and an `evidence:` line, so the rescue's key and the viewer read on as today. The run folder is `.minions/changes/<change-id>/`.

### D3

`close` runs the gate as `gate_run.py` under `sandboxed()` over the version's trees, so a green record on a settled tree is reused. A gate past `GATE_SECONDS` is a traceback today; `gate_run.py` now prints `gate: red — past its limit · <seconds>s` and exits 124.

The conductor prints `check — gate · pass · <n>s` or `check — gate · fail — <why>`; in a run, the same detail goes to the run log as a `check` event. A repository with no `check` target keeps its workers on the gate through `gate_run.py`, and the conductor's gate takes that record on the same tree.

Fix note (2026-11-22, S1): `gate_run.py` runs `make gate` in its own session and kills the group on the limit, so no child outlives the red.

### D4

After the last phase's check passes, the loop runs the gate. Red writes the output to `gate.red` and spawns `phase=repair` once a run: the worker fixes the failing code, runs `make check` and the failed tests, and commits. The gate runs again: green goes on to the close, red halts `gate red after the repair`, with `build.halt` (`sub-task: repair`) so the rescue's key reads on.

### D5

After the `phase=close` worker, the check is every box ticked and a clean tree; the conductor then writes `build.simplified` (`head:`) and runs `close`. When the close's gate is red and `HEAD` is a `refactor(<change-id>): simplify` commit, `close` resets the branch to the commit before it, prints `reset — simplify dropped`, and runs its steps once more. A second red, or a red with no simplify commit, fails as in [D2](#d2).

Fix note (2026-11-22, S2): a red whose output says `past its limit` or `sandboxed: denied` keeps the simplify commit, for the commit did not cause it.

### D6

`stage()` reads a built version with no `build.done` naming `HEAD` as `build`, closing steps left. When `build.simplified` names an ancestor of `HEAD` and each commit past it is `docs(<change-id>): amend the change directory` touching paths under the change directory alone, the loop runs `close` with no worker. Any other commit past it, or no `build.simplified`, spawns the simplify worker.

### D7

`close` writes `build.done` as `head: <sha>` and `simplify: <sha>` — the newest `refactor(<change-id>): simplify` commit of the range — or `simplify: none`. It keeps the plan check's printed lines in `plan-check.txt` beside it. `converge.py`'s `_evidence` reads that file instead of running `plan_check.py` when `build.done` names the frozen head; a timed-out line stays as the close printed it. At another head, or with no `plan-check.txt`, it runs the plan check as before.

Fix note (2026-11-22, S4): `plan-check.txt` opens with a `base: <sha>` line, and `_evidence` reads the lines only when that base is the freeze's own.

### D8

The gate lines are the only new log lines. `check — gate · …` fits the event list in `skills/mflib/runlog.py`, so `conduct.py log --verify` passes a run that wrote one.

### D9

`skills/mf-converge/references/fix.md` says `make check` where `make -n check` exits 0, and keeps the plan check and the gate through `gate_run.py` for a repository with no `check` target. `converge.py` keeps its gates. The `Makefile` pytest line gains `--durations=20`; the gate's output then names the twenty slowest tests, and nothing fails on them.

## Tests

The tests added are unit and integration tests, named in [tasks](tasks.md): `tests/test_brief_check.py`, `tests/test_modelsfile.py`, `tests/test_gate_run.py`, `tests/test_converge.py` and `tests/test_conduct.py`, the last on the fake worker of `tests/fake_worker.py`. No end-to-end test is added, so no engine and no browser run; none is expected to pass 5 s, so none carries `slow`.

| measure | command |
|---|---|
| tests the change adds in `tests/test_conduct.py` | `uv run pytest --collect-only -q tests/test_conduct.py -k "close or repair or simplif"` |
| end-to-end runs added | none: `git grep -n -e "new e2e" -- tests/test_conduct.py` prints nothing |

Tests that turn, none deleted: `test_a_build_runs_a_worker_per_phase`, `test_each_check_passes_only_on_disk_evidence`, `test_the_stations_run_the_bundled_metrics_script`, the `MODELS` assertions of `tests/test_brief_check.py`, and each test of `tests/test_conduct.py` that reads the close's `build.done` from the fake worker. `tests/fake_worker.py` stops writing `build.done` at `phase=close` and answers `phase=repair`.

| removed or merged test | carried by |
|---|---|
| none | none |

## Dependencies

None.

## Risks / Trade-offs

- A hand build now ends on a command, not on the worker's own steps: a hand build run before this version resumes through `stage()` as before, since `build.done` keeps its keys.
- The conductor's gate runs under the sandbox runner, so a gate that needs the network fails red there, as converge's does ([D51](../../../docs/decisions.md)).
- The simplify commit dropped on a red gate is lost work by design: simplify holds no verdict.
- `--durations=20` changes the gate's dry run once, so the next gate runs in full; the cut quotes the line for `gate_check.py`.

## Verdict

Ready to build, in the phases of [tasks](tasks.md): the key first, then the command it serves, then the loop that calls it, then the text that names them, then the records.
