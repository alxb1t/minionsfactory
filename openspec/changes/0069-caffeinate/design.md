# Caffeinate — design

The conductor holds the machine awake for its own life with `caffeinate -is -w <pid>`, and says so in the `start` line. Verdict at the
end: ready to build.

## Context

Read at `a3814cb` (v0.55.0); `after: 0068-pinned-release`, whose design adds `· mf <tag>` and `· pending <tag>` to the same `start`
line. `conduct.py` is `skills/mf-ship/scripts/conduct.py`.

- **F1.** `ship()` (`:2665`) builds the `start` line — `executor … · permissions: sandbox[ · worker MF_SHIP_AGENT] · versions …` —
  at `:2683-2688`. A run is one `conduct.py run` process, detached by `mf-ship` Step 3; `run()` holds the claim with its pid.
- **F2.** A missing tool is already found with `shutil.which` (`:1924`, `:2064`); fake workers set `MF_SHIP_AGENT` (`:1924`).
- **F3.** Tests put fakes first on `PATH` (a fake `ps`, `tests/test_conduct.py:117-122`) and load the conductor with `runpy`, whose returned dict is a
  copy: a test sets a module global through a function's `__globals__`, as `conduct["main"].__globals__[...]` does
  (`tests/test_conduct.py:755-756`).
- **F4.** `skills/mf-ship/SKILL.md` Step 3's say-once paragraph (`:99`).
- **F5.** `caffeinate -i -w <pid>` holds off idle sleep until that process exits; `-s` holds off system sleep on AC power; `-d` keeps the
  display on. A closed lid sleeps a MacBook unless it is in clamshell mode.

## Goals / Non-Goals

**Goals:** no live run stopped by sleep; nothing left to clean up; the record says whether the machine was held.

**Non-Goals:** the lid; the display; a hold for a station run by hand.

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | `_hold_awake(pid)` starts `caffeinate -is -w <pid>` from `ship()`'s start; none under `MF_SHIP_AGENT` | Q3, Q4, Q5 | `mf-ship`'s detach wrapping the run; `-d` |
| [D2](#d2) | The `start` line ends `· awake: held` or `· awake: not held — caffeinate not on PATH` | Q7 | — |
| [D3](#d3) | Step 3 names the lid | Q6 | — |

### D1

`CAFFEINATE = "caffeinate"`; `_hold_awake(pid) -> str`: `shutil.which(CAFFEINATE)` is `None` → return
`awake: not held — caffeinate not on PATH`; else `subprocess.Popen([found, "-is", "-w", str(pid)], stdin=DEVNULL, stdout=DEVNULL,
stderr=DEVNULL, start_new_session=True)` and return `awake: held`. `ship()` calls it in one line before the `start` line —
`awake = "" if os.environ.get("MF_SHIP_AGENT") else f" · {_hold_awake(os.getpid())}"` — so the line is covered under the fake
workers, which leave the field out; diff-cover counts lines, not branches.

### D2

The `start` line gains `awake` last, after `versions …` and every field before it, `0068`'s `· mf <tag>` among them; the integrator
orders the f-string if both land on it.

### D3

Step 3's say-once paragraph adds: "a closed lid sleeps the Mac whatever the run holds, unless it is in clamshell mode".

## Tests

`git grep -c '^def test_' main -- tests/` totals the suite at the cut. Added, unit: `test_a_run_holds_the_machine_awake` — a fake
`caffeinate` first on `PATH` writes its argv to a file: `_hold_awake` starts it once — the test polls for the argv file, since `Popen` does not wait — with `-is -w <pid>` and no `-d`, and returns
`awake: held`; with `conduct["_hold_awake"].__globals__["CAFFEINATE"]` set to a name nothing provides, it starts nothing and returns `awake: not held — caffeinate not on
PATH`. No end-to-end test (`T1`); none deleted.

## Dependencies

None.

## Risks / Trade-offs

- **A hold on battery:** `-i` holds idle sleep on battery too; the battery's own low-power sleep still wins.
- **A killed `caffeinate`:** the run goes on unheld, unnoticed — out of scope.

## Verdict

Ready to build.
