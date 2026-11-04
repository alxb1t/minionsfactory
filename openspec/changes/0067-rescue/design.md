# Rescue — design

A halted version gets a rescue in its own thread: a fresh worker fixes a plan halt with one path-checked amend and the version goes
on, or diagnoses a halt that needs the person. Verdict at the end: ready to build.

## Context

Read at `51ea75e` (v0.54.0). `conduct.py` is `skills/mf-ship/scripts/conduct.py`.

- **F1. Where a version halts:** `Run.advance` (`:2199-2265`) returns after `halt` at a STUCK stage (`:2204-2206`), with no
  worktree (`:2213-2215`), when `spawn` returns `None` — a timeout or a non-zero exit, already halted (`:2242-2243`) — and when
  `judge` fails a check, `halt(who, "<stage> check fail — <reason>")` (`:2187-2197`, `:2251-2252`). `take` (`:2406-2423`).
- **F2. Spawning:** `PROMPTS` (`:127-132`), the build's "Run the mf-build skill for change {change}."; `STATIONS` (`:71`);
  `spawn(who, station, cwd, prompt, models, repo=None)` (`:2150-2185`), its log `runs/<stamp>/<who>_<station>.log` (`:2165`).
- **F3. Models:** `_table` returns a table or `{}` and cannot tell an absent one from an empty one (`:1614-1624`); `_models` maps
  `integrate` to `[release]` alone (`:1627-1644`); `read_plan` reads `STATIONS` (`:2425-2434`); the plan is compared in `advance`
  (`:2229`) and `take_back` (`:2493-2499`). Nothing reads `skip`.
- **F4. Rejoin's reuse:** `take_back` clears a version's halts and blocks under `self.guard` (`:2500-2502`).
- **F5. `EVENTS`** (`:62-65`) lacks `rescue`; `report` replays `halt` and `rejoin` events per version (`:3073-3143`).
- **F6. `0063·S5`:** `_requests` checks `is_symlink`, then lists and unlinks by path (`:2825-2847`); the grants folder is read the
  same way in `ship` (`:2681-2684`).
- **F7. `mf-build`** writes `.closing` (`skills/mf-build/SKILL.md:191-192`) and `.done` (`:228-238`), and reports a halt in its
  close-out alone (`:243`); its stop-conditions (`:250-266`). No `.halt`.
- **F8. Skills:** `AGENTS.md` lists them (`:36-39`); `make install-skills` links every `skills/mf-*` (`Makefile:48-59`); `_unlinked`
  stops a run when one is not linked (`:2026-2038`); `tests/test_skills.py`'s scans over every `SKILL.md` — no `## The card` outside
  converge (`:195`), every `references/` link resolving (`:402`).
- **F9. Tests:** the `fake` fixture (`tests/test_conduct.py:155-175`); `fake_worker.py` reads `Run the mf-(\w+) skill` (`:115`) and
  has `liar-<id>` (`:163`); `test_a_fixed_version_rejoins_a_live_run` (`:1248`) is the halt-then-fix template.
- **F10. Decisions:** D47's "needs the person" list (`docs/decisions.md:462-464`); D52 the highest id; *Out of scope* in
  `THREAT_MODEL.md:52-59`.

## Goals / Non-Goals

**Goals:** a simple plan halt fixed and the version released in the same run; every other rescuable halt diagnosed on disk; no
rescue that writes code or a decision.

**Non-Goals:** rescuing a timeout, a usage limit or D47's person-only halts; settling a decision.

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | `mf-build` writes `.minions/build/<id>.halt` | Q4 | reading the worker's stream-json |
| [D2](#d2) | `skills/mf-rescue/SKILL.md`: the inputs, the kinds, the fix and the diagnosis | Q3, Q5, Q9 | a prompt in `conduct.py` |
| [D3](#d3) | The rescue in the version's thread, after the halt; the path check; the halt cleared, `advance` again | Q2, Q5 | a rejoin request |
| [D4](#d4) | `RESCUES = 3` a version, a sub-task once | Q6 | one rescue |
| [D5](#d5) | `[rescue]`, the build's table when absent; `skip = true` | Q7 | a station in `STATIONS` |
| [D6](#d6) | The record: `rescue` events, `report`, D47, D53, the threat model, `AGENTS.md` | Q8 | — |
| [D7](#d7) | The rejoin and grants folders read and emptied by directory descriptor | Q12 | `is_symlink` then a path |

### D1

On every halt — a stop-condition, a failing `**HALT CHECK**`, a gate check's exit — `mf-build` writes `.minions/build/<id>.halt`:
`sub-task: <N.M>`, `stop: <the condition, by its number or name>`, `evidence: <one line>`, `head: <sha>`, before its close-out.
`conduct.py`'s build check failure reads it into the halt line: `build check fail — phase N unticked · <N.M>: <stop>`.

### D2

`skills/mf-rescue/SKILL.md`, read-only but for its one commit or its one file. Inputs: the `.halt` file, the run log's halt line,
`runs/<stamp>/<id>_build.log`'s last lines, the change directory, and the code at `HEAD`. **Fix** — a `Verify:` that cannot pass, a
reader a deletion missed, a task two readings would build differently, a `Verify:` that is not one plain command — a `$(…)`, a shell variable, a loop or a
`cd`: edit `tasks.md` (and `design.md`'s prose,
never its decisions table), commit `docs(<id>): amend the change directory` with a body naming each fix and a `Rescue: <sub-task>`
trailer. **Diagnose** — a design premise the code rules out, a converge cap, integrate's red gate or note: write
`.minions/rescue/<id>.md` — the halt, the cause with `path:line`, a proposal — and commit nothing. It closes in three sentences, then
`Next:`.

### D3

`Run.rescue(version, why)`, called in `advance` where a version halts on its build check (`:2251`), at `converge-halted` and
`integrating` (`:2204`) — never after a `spawn` that returned `None`, nor at `human` or `released`. It spawns
`PROMPTS["rescue"]` — "Run the mf-rescue skill for change {change}." — in the version's worktree. After it: a new commit whose
subject is `docs(<id>): amend the change directory` with a `Rescue:` trailer, every path in it under
`openspec/changes/<id>/` and named `tasks.md` or `design.md` → log `rescue — <id>: fixed · <sub-task> · <short sha>`, remove the
version's halts (F4), and `advance` again; any other path → keep the halt, adding `rescue touched <path>`; no commit and
`.minions/rescue/<id>.md` → log `rescue — <id>: diagnosed · .minions/rescue/<id>.md`, the halt naming the file.

### D4

`self.rescues: dict[str, list[str]]` — the sub-tasks rescued per version. A fourth halt, or a halt on a sub-task in the list, gets no
rescue; the halt adds `rescued <sub-tasks>`.

### D5

`_models(…, "rescue")` reads `[rescue]` when the file holds it, else `[build]`; `_table` tells an absent table from an empty one.
`[rescue] skip = true` → no rescue for that version. `read_plan` reads the rescue's models once with the others, and `advance`'s
plan comparison covers it.

### D6

`EVENTS` gains `rescue`; `report` prints `<id> · rescued <sub-task> · <sha>` and `<id> · diagnosed <file>` lines after a version's
halts. D47's list: a version halt's first step is its rescue. D53, *A rescue amends the plan, never the code or a decision* — the
paths, the trailer, the limits, the person-only halts. `THREAT_MODEL.md`: a worker writing the plan it is judged by, in the accepted
class, bounded by the path check and converge's review. `AGENTS.md`'s skills list and `skills/mf-ship/SKILL.md`'s halt table name
`mf-rescue`.

### D7

`_requests` and the grants read open the folder with `os.open(folder, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)`, list it with
`os.listdir(fd)`, and delete with `os.unlink(name, dir_fd=fd)`; a link at the folder or swapped in after the listing deletes
nothing. Pays `0063·S5`.

## Tests

`git grep -c '^def test_' main -- tests/` totals 131. Added, integration on the fake worker, each `slow` when it runs over 5 s (`T1`):
`test_a_rescue_fixes_a_plan_halt_in_its_run`, `test_a_rescue_diagnoses_a_decision_halt`, `test_a_rescue_outside_the_plan_halts`,
`test_a_sub_task_is_rescued_once` (the fourth halt beside it), `test_rescue_skip_runs_none` — `T2`: none reaches a rescue today —
with `rescue-fix`, `rescue-diagnose`, `rescue-wild` and `halt-<id>` modes in `tests/fake_worker.py`; `test_a_linked_rejoin_folder_deletes_nothing`
(unit). Extended: `tests/test_skills.py`'s scans read `mf-rescue` with the rest. None deleted or merged.

## Dependencies

None.

## Risks / Trade-offs

- **A wrong amend** passes the path check and is read by converge, which judges the whole change.
- **A rescue's spend:** at most three a version a run.
- **The pin:** the re-pin after this release links `mf-rescue`, or `_unlinked` stops every run.

## Verdict

Ready to build.
