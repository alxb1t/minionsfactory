# Cut awake — design

The cut holds the Mac awake from its Step 1 to its close-out with a bundled `awake.py`, bounded to two hours, recorded by change
id. Verdict at the end: ready to build.

## Context

Read at `f349aa8` (v0.66.0), the brief's `At` sha: `git diff --name-only f349aa8..HEAD` prints nothing, so every fact on a path
stands; the facts on no path were probed again at the cut.

- **F1. The run's hold:** `_hold_awake(pid)` in `skills/mf-ship/scripts/conduct.py:2398-2413` runs `caffeinate -is -w <pid>` with
  `subprocess.Popen`, DEVNULL streams and `start_new_session=True`, and returns `awake: held` or
  `awake: not held — caffeinate not on PATH`. Its test, `test_a_run_holds_the_machine_awake` (`tests/test_conduct.py:3365`), puts a
  fake `caffeinate` first on `PATH` that writes its argv to a file, and polls for it.
- **F2. The cut:** `skills/mf-cut-change/SKILL.md` echoes its parameters (`:33`); Step 1 opens at `:39`; it halts in Steps 1, 2, 4
  and 8, and waits for the person in Steps 3 and 9; Step 11 closes out (`:208-216`). Its search script is `scripts/verify_check.py`,
  "resolved from this skill's package" (`:151`).
- **F3. The process tree**, probed at the cut: `uv run --script` starts the script as a child of `uv`, itself a child of the Bash
  tool's `zsh`, itself a child of the long-lived `claude` process — `python ← uv ← zsh ← claude`.
- **F4. `-t` bounds `-w`:** `caffeinate -i -t 2 -w 1` exits after 2.10 s.
- **F5. `ps` in a worker:** the sandbox refuses the real `ps`, so `tests/test_conduct.py`'s `ps` fixture puts a fake one first on
  `PATH`, answering from files the test writes (`:88-131`).
- **F6. The run directory:** each bundled script finds it from `git rev-parse --path-format=absolute --git-common-dir`, as
  `records()` does in `skills/mf-converge/scripts/gate_run.py:54-57`. D57 (`docs/decisions.md:580-594`) keeps `grants/`, `runs/`,
  `gate/`, `replay/`, `metrics/` and `debt.md` generic.
- **F7. Bundled scripts are named:** `_METRICS_SCRIPTS` in `tests/test_skills.py:465-478` lists each skill's script, and
  `test_the_metrics_script_scan_reports_a_missing_script` (`:506-544`) expects one `not named` line per entry.

## Goals / Non-Goals

**Goals:** no cut stopped by sleep; no hold that outlives its cut by more than two hours; parallel cuts that stop only their own.

**Non-Goals:** a hold for the plan, the build, converge or the release run by hand (Q1); Linux (Q4); the unattended background
cut; the cutter's own hand practice until this ships (A3), which is no requirement.

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | `awake.py start <change-id>` holds `caffeinate -is -t 7200 -w <host pid>`, the host the nearest ancestor that is neither a shell nor `uv`, and records the hold's pid in `.minions/awake/<change-id>` | Q2, Q3, Q4, A1 | holding on the script's own pid; the claude pid alone, with no bound |
| [D2](#d2) | `awake.py stop <change-id>` kills the recorded pid only while `ps` names it `caffeinate`, and removes the record | Q3, A1 | killing the pid unchecked |
| [D3](#d3) | The cut starts the hold at the head of Step 1 and stops it at every halt from there and at Step 11; it names the lid | Q5, A2 | a stop at Step 11 alone |
| [D4](#d4) | D57 and the run directory's requirement name `awake/` generic; `_METRICS_SCRIPTS` names `awake.py` | A1, Q6 | a record under `.minions/changes/<change-id>/` |

### D1

`skills/mf-cut-change/scripts/awake.py`, a `uv` script with standard-library imports alone, run from the repository root:
`awake.py start <change-id>` and `awake.py stop <change-id>`, by `argparse`. Constants: `CAFFEINATE = "caffeinate"`,
`HOLD_SECONDS = 7200`, `LAUNCHERS = {"sh", "bash", "zsh", "dash", "ksh", "fish", "csh", "tcsh", "uv"}`, and
`CHANGE_ID = re.compile(r"\d+-[a-z0-9]+(?:-[a-z0-9]+)*")`.

- **The id:** a `change-id` that `CHANGE_ID` does not fully match prints `awake: cannot run — not a change id: <id>` and exits 2,
  so no id names a path outside `.minions/awake/`.
- **The record:** `.minions/awake/<change-id>` in the run directory, found as F6 says; a failed `git rev-parse` prints
  `awake: cannot run — not in a git repository` and exits 2. It holds the hold's pid, one line.
- **The host:** from `os.getppid()`, read `ps -o comm= -p <pid>`; its last path part, a leading `-` dropped, in `LAUNCHERS` → read
  `ps -o ppid= -p <pid>` and go up. The first other name is the host. A pid at or below 1, or a `ps` that answers nothing, is no host.
  Why `uv` too: F3 — "the nearest ancestor that is no shell" would be `uv`, which exits at once.
- **`start`:** first releases a hold recorded for the same id, as D2 does, silently. Then `shutil.which(CAFFEINATE)` is `None` →
  print `awake: not held — caffeinate not on PATH`; no host → print `awake: not held — no host process`; each starts nothing,
  records nothing and exits 0. Else `subprocess.Popen([found, "-is", "-t", "7200", "-w", str(host)], stdin=DEVNULL,
  stdout=DEVNULL, stderr=DEVNULL, start_new_session=True)`, as `_hold_awake` does (F1); create `.minions/awake/` with its parents,
  write the pid, print `awake: held (2 h at most)` and exit 0.

### D2

`stop`: no record → print `awake: none held`. Else read the pid; when `ps -o comm= -p <pid>`'s last path part is `caffeinate`,
`os.kill(pid, signal.SIGTERM)` and print `awake: released`; when it is not — the hold ended at its bound, or its pid was reused —
print `awake: none held` and kill nothing. Remove the record either way, and exit 0. A record that holds no integer is no hold. A
hold for another id is never read.

### D3

`skills/mf-cut-change/SKILL.md`, Step 1 gains a first paragraph, before the default branch's:

> **Hold the Mac awake.** First run `uv run --script scripts/awake.py start <change-id>`, `scripts/` resolved from this skill's
> package, and print its line, `awake: held (2 h at most)` or `awake: not held — <why>`; the cut goes on whatever it prints. Every halt from
> here on runs `uv run --script scripts/awake.py stop <change-id>` before its report; a wait for the person keeps the hold, which
> ends in two hours at most. A closed lid sleeps the Mac whatever the cut holds, unless it is in clamshell mode.

Step 11 gains, before its close-out: "Run `uv run --script scripts/awake.py stop <change-id>`."

### D4

`docs/decisions.md` D57: `` `grants/`, `runs/`, `gate/`, `replay/`, `metrics/` and `debt.md` stay generic `` →
`` `grants/`, `runs/`, `gate/`, `replay/`, `metrics/`, `awake/` and `debt.md` stay generic ``. A hold belongs to a session's cut,
not to the change's record, as a grant does; the brief's A1 settles the path. The delta's MODIFIED *Every worktree shares the
primary's run directory* makes the same edit to its list. `tests/test_skills.py`: `_METRICS_SCRIPTS` gains
`("mf-cut-change", "scripts/awake.py")`, appended after `("mf-cut-change", "scripts/verify_check.py")`, and each expected list of `test_the_metrics_script_scan_reports_a_missing_script` gains
`"skills/mf-cut-change/SKILL.md: scripts/awake.py: not named"`, after its `verify_check.py` line.

## Tests

`git grep -c '^def test_' f349aa8 -- tests/` totals 218 at the cut. Added, unit, in `tests/test_awake.py`. Each test runs in a
scratch repository — `git init` under `tmp_path`, then `monkeypatch.chdir` there — so no record reaches the real run directory, and
calls `main([...])` in-process. Its fixtures:

- **A fake `ps`** first on `PATH`, its own, not `tests/test_conduct.py`'s: it answers `-o comm= -p <pid>` and `-o ppid= -p <pid>`
  from files the test writes, `<pid>.comm` and `<pid>.ppid`, with no liveness check, and nothing for an unregistered pid. The
  test sets `os.getppid` through `monkeypatch` to a registered pid.
- **A fake `caffeinate`** first on `PATH`: `trap 'echo TERM >> <term file>; kill $!; exit 0' TERM; echo "$@" >> <argv file>; sleep 60 &
  wait`. The test polls the argv file for the start, and the term file for the kill; the pid `start` records is registered with
  `comm` `caffeinate`. CI runs on `ubuntu-latest`, with no real `caffeinate`, so every step that holds puts the fake first on `PATH`
  with `CAFFEINATE` at its default.

The tests:

- `test_a_cut_holds_the_machine_awake_by_change_id` — `start 0001-a` past a fake `-zsh`, then `/bin/zsh`, then `uv`, to a fake
  `claude` host records the fake's pid in `.minions/awake/0001-a`, its argv `-is -t 7200 -w <host pid>`, and prints
  `awake: held (2 h at most)`; `start 0002-b` holds apart; `stop 0001-a` kills its fake — `TERM` in its term file — removes its
  record and prints `awake: released`, and `0002-b`'s record stands; a second `start 0002-b` kills the first `0002-b` hold.
- `test_no_hold_starts_without_caffeinate_or_a_host` — `CAFFEINATE` set through `main.__globals__` to a name nothing provides
  prints `awake: not held — caffeinate not on PATH`, records nothing and exits 0; with `CAFFEINATE` restored and the fake first on
  `PATH`, ancestors all in `LAUNCHERS` up to pid 1 print `awake: not held — no host process`, and a `ps` that answers nothing does
  the same.
- `test_stop_kills_only_a_recorded_caffeinate` — a recorded pid `ps` names `sleep` gets no signal and its record goes; a record
  holding `x` prints `awake: none held` and goes; no record prints `awake: none held`; an id `../x` exits 2; `stop` in a `tmp_path`
  folder outside any repository, `GIT_CEILING_DIRECTORIES` set to its parent, prints `awake: cannot run — not in a git repository`
  and exits 2; the script run as a command, `[sys.executable, <script>, "stop", "0001-a"]` with `cwd` the scratch repository,
  prints `awake: none held`, covering its `__main__` line.

Extended: `test_the_metrics_script_scan_reports_a_missing_script`, per [D4](#d4). No end-to-end test (`T1`); none deleted.

## Dependencies

None.

## Risks / Trade-offs

- **A cut left halted, or waiting, holds up to two hours** → `-t 7200` ends it (F4); a person may run `awake.py stop` sooner.
- **A killed host** → `-w` ends the hold with it.
- **A worker writes `.minions/awake/<id>`** → `stop` kills only a `caffeinate`, so a forged pid ends at most another hold. The
  reader is a hand-run cut, not the conductor; the harm is a hold ended early, which the 2 h bound already allows.
- **A cut in a sandboxed session** — a host's OS sandbox that refuses `ps`, or `caffeinate` → `start` prints
  `awake: not held — no host process`, or `awake: held` over a `caffeinate` that could not hold, its stderr gone to DEVNULL; the
  cut goes on unheld, as with no `caffeinate`. The person's sessions probed at the cut run `ps` and `caffeinate` (F3, F4).
- **A closed lid** → sleeps the Mac whatever is held; the skill says so.

## Verdict

Ready to build.
