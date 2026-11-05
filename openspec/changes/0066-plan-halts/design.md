# Plan halts — design

The cut catches a plan the code cannot satisfy: it runs each search's pattern, holds a `Verify:`'s shape, greps what a change
deletes, reads the target's rules, and has a fresh worker review the plan; the build refuses a check edited since the cut.
Verdict at the end: ready to build.

## Context

Read at `51ea75e` (v0.54.0).

- **F1. The cut** reads `AGENTS.md`, its mandatory context, the decisions and the threat model — not `CODING_STANDARDS.md` or
  `CONTRIBUTING.md` (`skills/mf-cut-change/SKILL.md:18-21`). Step 3 checks only what the source names (`:71-75`). Step 8: the
  plan check (`:118-120`), "Read every `Verify:`; run none" (`:122-125`), P9/P12/P13/A2 (`:126`), "`make gate` is green" (`:127`),
  the self-check exception (`:129-130`). Step 9's wait table (`:138-141`); the close-out names "the gate's exit code" (`:157`).
  The contract `I1`–`I18` (`:165-188`), `I3` at `:173`; `T1` carries the `slow` rule (`:227`).
- **F2. The build:** its contract `:42-67`, `I3` at `:52`, `I8` at `:57`; it reads the standards named or not (`:13`); each phase
  runs its `Verify:` lines at Step 2 item 2 (`skills/mf-build/SKILL.md:149-152`); `gate_check.py --change … --base … --head <the
  tree>` once, after them (`:160-168`); stop-conditions `:250-266`. Nothing compares a `Verify:` with the cut's.
- **F3. `gate_check.py`:** modes `--change`/`--base`/`--head` and `--tasks`, which rejects the others (`:449-469`); exits 0, 1, 2
  (`:7-10`); `cut_commit()` (`:110-119`); `--change` reads `tasks.md` at the cut commit alone (`:348`), ignoring amends.
- **F4. Tests:** `test_the_cut_and_the_build_carry_the_same_contract_ids` needs the ids unbroken (`tests/test_skills.py:128`);
  no test reads `I3`'s wording or Step 8's text (D42). The gate's `diff-cover` needs every new line covered (`pyproject.toml:26`).
  `git grep -c '^def test_' main -- tests/` totals 131.
- **F5. Decisions:** D7 (`docs/decisions.md:86-91`), D40 (`:220-228`), D46 names the build and converge as the standards'
  readers (`:294-303`); the principles' self-check exception (`docs/principles.md:40-41`).
- **F6. Scripts:** `skills/mf-cut-change/scripts/` does not exist; a sibling's script is resolved as `../mf-converge/scripts/…`
  from the skill's package (`skills/mf-cut-change/SKILL.md:118-119`).

## Goals / Non-Goals

**Goals:** every plan halt of 2026-11-02 to -04 caught at the cut, or named at once by the build; the cut cheaper for no gate.

**Non-Goals:** a cut that settles a decision; the build amending a check; the moved-only re-check (*lighter cut*).

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | `verify_check.py`: each search's pattern run at `HEAD` as argv; `I19`'s shape; exits 0, 1, 2 | Q3, Q4, Q12 | reading alone |
| [D2](#d2) | `I19` in both contract tables | Q4 | a rule in a memory |
| [D3](#d3) | `gate_check.py` compares every `Verify:` with the cut and its amends; the build runs it before each phase's first `Verify:` | Q8, Q13 | the build amending a check (Q9) |
| [D4](#d4) | Step 3 greps what a change deletes; the cut reads the standards, a target's own test rule first | Q5, Q6, Q17 | — |
| [D5](#d5) | A fresh read-only plan review after Step 8; the simple doubts fixed, one re-run; a decision to the person | Q7, Q10, Q11 | the cut reading its own plan |
| [D6](#d6) | No gate at the cut; `I3` reworded | Q18 | the full gate on a docs-only tree |
| [D7](#d7) | The record: D7, D38, D40, D46, the principles' exception | — | — |
| [D8](#d8) | A calibration of the review on replayed cuts, in the CHANGELOG | Q15 | a gate test of prose (D42) |

### D1

`skills/mf-cut-change/scripts/verify_check.py <tasks.md>`, a stdlib `uv run --script`. For each sub-task's `Verify:`, each backticked
command: `$(`, a backtick inside, `for `, `while `, `cd `, a `NAME=` or `$NAME` outside single quotes → an `I19` break; a quoted
operator ends no command. A `grep …` or `git grep …` command is split with `shlex`, run as argv with `-n` added and no shell, in the
repo at `HEAD` — a `git grep` at the revision it names, the first operand after its pattern that git resolves — and each match
printed `<sub-task>: <path>:<line>: <text>`. A search takes a fixed list of options, and no path that is absolute, holds `..` or
resolves outside the tree; any other option, a pager's among them, or such a path, is a break. An exact count (`prints <n>`, `reports <n>`) on a search beside more matches than `<n>` lines is a break too. Exit 1
on a break, naming the sub-task; 0 when none; 2 when a `Verify:` cannot be parsed, or git refuses its `git grep`.

### D2

`I19` — "make every `Verify:` one plain command — no `$(…)`, shell variable, loop or `cd`, and a search with `verify_check.py`'s
options alone and no path outside the repository — and an exact count only when the count is the point | `verify_check.py` in Step 8" — a row in `skills/mf-build/SKILL.md` and `skills/mf-cut-change/SKILL.md`; the diagram's
`I1 … I18` → `I1 … I19`.

### D3

`gate_check.py --verify --change <id>`: the `Verify:` lines of `tasks.md` in the working tree against those at the cut commit and at
each later commit whose subject is `docs(<id>): amend the change directory`, in order; a later merge of two parents that touches
`tasks.md` renumbers the plan's decision citations by `integrate.py decisions`' rule, so integrate's renumber is no edit and any
other edit of the merge is; a line that differs from the latest of them →
exit 1, printing the sub-task, the diff, and `uncommitted` when the working tree's line is not in `HEAD`. `--change` runs the same
comparison after its gate check. `skills/mf-build/SKILL.md` Step 2 runs `--verify` before a phase's first `Verify:`; exit 1 → halt,
naming it.

### D4

Step 3 adds: for each symbol, key or file a task deletes or renames, `git grep -nw <name>` at `HEAD`; each reader is named in a task
or the design's `## Tests` table. The header's reading list adds `CODING_STANDARDS.md` and `CONTRIBUTING.md`, named or not, as the
build reads them; a target's own test rule that conflicts with `T1`–`T6` wins, and Step 9 names the conflict. D46 names the cut.

### D5

After Step 8, a fresh read-only worker — the host's subagent, the session's model — gets the change directory, `HEAD` and one
question: can each task be built as written, and each `Verify:` pass after it? It answers with doubts and `path:line`. The cut fixes,
without asking, a check that cannot pass or breaks `I19`, a reader Step 3 missed, a task two readings would build differently, then
runs `verify_check.py` and the review once more; a doubt that changes a `design.md` decision or a brief's `## Decisions` row, or one
still standing, waits for the person in Step 9's table. A host with no worker: the cut reads it itself, named as its self-check.

### D6

Step 8's "`make gate` is green" goes; `I3` becomes "pass `openspec validate --strict`, the plan check and `verify_check.py` on the cut
commit | Steps 7 and 8" in both tables; the close-out's "the gate's exit code" becomes "the checks' exit codes". The build's last
phase owns the full gate, as before.

### D7

D7 gains the plan review and the search script; D38 waits on a plan-review doubt left to the person; D40 names the cut's reviewer
among the fresh workers; D46 names the cut among the standards' readers. *No station verifies its own work*'s exception: the cut's review is a fresh worker's.

### D8

The build runs the plan review, as a fresh subagent, on: MF `0060-gate-planning`'s change directory at its cut commit (its
backtick needle); a fixture of isekai `0093`'s drawer task beside its `min-width: max(50vw, 480px)` line; and `0061-conflict-resolve`'s
change at its cut. It records each doubt's `path:line`, and the CHANGELOG entry states the result. A host with no fresh worker
halts the phase.

**The isekai `0093` fixture**, word for word from isekai at `69687552`, `0093-the-tests-revisited`'s cut — the build writes
these three into a scratch change directory and repo for the review, and reads nothing outside MF:

- its task 3.2: "Add the drawer's viewport step and the pick's width step under their restored keys, and `0091·R4`'s and
  `0091·R9`'s steps in the merged import test, per [D5](design.md#d5)."
- its D5's sentence: "The drawer's step narrows the viewport with `page.set_viewport_size`, so one photograph's grid sets the
  width; `ui:compare:the-pick-holds-its-width` and `ui:sessions:the-drawer-fits-its-widest-grid` return."
- `ui/src/app.css:508-511`:

  ```css
  .drawer {
    width: max-content;
    min-width: max(50vw, 480px);
    max-width: calc(100vw - 100px);
  ```

The review should doubt the task: narrowing the viewport cannot make one photograph's grid set a width whose floor is
`max(50vw, 480px)`.

## Tests

`git grep -c '^def test_' main -- tests/` totals 131. Added, integration layer, no end-to-end (`T1`): `tests/test_verify_check.py`
— the `720px`, `"stock_wait"` and `(D25)` replays printing their stray lines, `for i in $(seq 20)` exiting 1, an unparsable check
exiting 2, no shell; in `tests/test_gate_check.py`, `test_an_edited_verify_halts`, a working-tree edit, a phase commit's edit and an
amend's. The contract-id test carries `I19` unchanged. Extended: `test_the_stations_run_the_bundled_metrics_script`'s
list with `verify_check.py`, and its scan test. None deleted or merged.

## Dependencies

None.

## Risks / Trade-offs

- **The review adds minutes to a cut;** D6's dropped gate and *lighter cut* pay for it.
- **A worker could commit an amend-titled edit:** the accepted class; converge reads the change.
- **A search run at `HEAD`** reads the repo; it runs no shell and writes nothing.

## Verdict

Ready to build.
