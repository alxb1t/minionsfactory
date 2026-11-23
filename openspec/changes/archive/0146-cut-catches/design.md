# Cut catches — design

The conductor checks each cut itself, the cut's rows grow by three, and a person's phase never reaches a build. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The conductor reads a cut's commit subject, its tree and its models file, and runs no row of `cut_check.py`: a row binds only as far as the cutter obeys its skill. The plan check finds a plan's own faults only after the build, when each costs a halt, a rescue and a new run. The brief's table of halts names the classes a cut can see: design text naming a removed name, a `Verify:` line that cannot run, text the gate rejects, a phase a person must do.

## Goals / Non-Goals

- Goals: a failing row reaches the cutter before the build; the repository's own text checks run at the cut; a build that needs an unnamed file says so and goes on.
- Non-goals: a cut row over files a test ties together; a gate at the cut; any change to the conductor's, the plan check's or the build's reading of a phase marked for a person, which a version cut before keeps.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | The conductor runs `cut_check.py` after the cut commit, under the sandbox | a row binds only as far as the cutter obeys its skill | a row inside `_check_cut` · a worker's own check alone |
| [D2](#d2) | A failed check cuts again from the default branch, once; a second failure resets the branch and halts | the cut's preconditions refuse a branch ahead of the default | an amend by a second cutter · a third try · a reset of a rejoin's branch |
| [D3](#d3) | New rows: `K7`, `V7`, `V8` | each is a class of halts in the brief's table, readable at the cut | `V8` inside `V2` · `K7` over the delta specs |
| [D4](#d4) | `verify_check.py` spares a search's patterns from the range rule and reads an Oxford comma and an `e.g.` as the plan check does | cards `0143·S6` and `0143·S9` | a looser plan check |
| [D5](#d5) | A phase marked for a person is refused by `I14` and by the brief check | halts that idled for a person; nothing may answer one | dropping `I14` · removing the conductor's reading |
| [D6](#d6) | A repository declares `**Cut checks:**`; the conductor runs them after the checker | text the gate rejects reached isekai's build twice | the cut running them · reading the cut's own `AGENTS.md` |
| [D7](#d7) | The build edits a file no task names when a red check needs it, and lists it; conformance judges such files of the build's commits, `CHANGELOG.md`, the change's own folder and a fix commit's files aside | the largest class of halts, and no pairs are declared anywhere | a cut row over declared pairs · a pass over every unnamed file |
| [D8](#d8) | The records: new ids, the module map, one new decision | the living spec lists the row ids; the map is held by `tests/test_structure.py` | none |

### D1

**After `_check_cut` and `_unapproved` pass, `Run.cutting` runs `cut_check.py <id> --bump <bump>` through `_boxed` in the cut's tree, on the conductor's own Python.** A clean exit passes. A failed check — exit 1 with a `cut_check: halt — ` line — has its output as the failing lines. An exit above that, an exit 1 with no such line, which is the checker crashed, or a run that cannot start, halts the cut as `the cut check cannot run — <line>`: the last line of its output, where a crash says what broke, or the first line of the error that kept it from starting. Each run of the checker and of a [D6](#d6) command ends after `CUT_TIMEOUT`, 1800 s, keeps its last 2000 lines, and writes to the cut's tree and the run directory alone. The log gets `check — cut-check · pass` or `· fail — <first failing line>`. `_check_cut` stays as it is: the branch's tip is still the land commit.

- **Why:** at the base the conductor reads disk alone; the checker is a script the run can start (Q55).
- **Rejected:** a row in `_check_cut`, which runs nothing · the cutter's own Step 8 alone.

### D2

**The first failure of a branch this call cut writes the failing lines to `cut.red` in the change's run folder, resets the tree with `git reset --hard <default>` and `git clean -fd`, removes `cut.halt`, and starts the cutter once more, on the same `after` and `beside`.** The prompt gains a tail naming `cut.red`, after its backticked part; the checks then run again. A second failure resets and cleans the tree the same way, so the branch holds no change and a rejoin cuts it fresh, then halts the cut through `cut_halted` as `the cut check failed twice — <first failing line>`; `cut.red` stays as evidence. A branch the run found already holding the change fails to a halt at once: a person's amend stays, and nothing is reset.

- **Why:** `cut_pre.py` wants `HEAD` an ancestor of the default branch and the number above every open version's, so a second cutter cannot amend a branch already ahead. One more cut costs less than a halt a person answers.
- **Accepts:** a failed first cut is paid for twice.
- **Rejected:** an amend · a third try · a reset of a rejoin's branch.

### D3

**The new rows, each a new id in the checker's `ROWS`, in the cut's Step 8 sentence and in the living spec's list; none is a shared id.**

| row | fails when |
|---|---|
| `K7` | a backticked name of one identifier with `_` or a capital, in a sub-task line holding a removal word (the plan check's `REMOVAL`), stands on a line of `design.md` outside `## Tests`, or of `proposal.md`, with no removal word |
| `V7` | the first word of a `Verify:` command is no program on `PATH`, no path of `HEAD`'s tree and no path a sub-task names |
| `V8` | a `-k` expression of a `pytest` command selects no function, class or module name of the test files it names at `HEAD`, and no `test_` name a sub-task names; a command naming no test file is `V5`'s |

- **Why:** the plan check does `K7` only after the build; `V7` fails there as exit 127; `V8` as pytest's exit 5.
- **Accepts:** `K7` reads a rename's new name as removed, so the cutter rewords; `V8` misses a parametrize id, as `V2` does.
- **Rejected:** `V8` inside `V2`, which asks about later tasks, not `HEAD` · `K7` over the delta specs, which the plan check keeps.

### D4

**`unplain` skips a search's patterns in the range test, as the line-number test does. `after_verb` exempts a `, and` or `, or` only when an output verb follows the span, and reads no `e.g.` or `i.e.` as a sentence end.**

- **Why:** `git grep -n origin/main... -- docs/` is refused today, and probe 7's Oxford form passes the cut and fails the build with exit 127.
- **Rejected:** loosening the plan check, which stays the judge.

### D5

**`cut_check.py`'s `I14` fails each phase line of `tasks.md` holding `**HUMAN`, under `## Progress` or not: a person's step comes after the release. The exemptions of `I4` and `I12`, and `verify_check.py`'s, go with it, so such a line fails `I4` for its missing rating as well. `brief_check.py` reads `## Phases` and halts a line holding `**HUMAN`.** The `I14` row of both skills is reworded to the refusal, the id kept so the ids run unbroken. The conductor's `human` stage, the plan check's skip and the build's checklist stay, for a version cut before.

- **Why:** a halt at such a phase idles until a person comes, and no worker may answer it (Q15, Q46, Q60).
- **Rejected:** dropping `I14`, which breaks the ids · removing the conductor's reading.

### D6

**A repository may declare `**Cut checks:**` in its root `AGENTS.md`: backticked commands, as `Ship tools:` is.** The conductor reads the primary's file, not the cut's, which a cutter can write. After the checker passes it runs each command, split by `shlex`, in the cut's tree through `_boxed`. A non-zero exit, or a command that cannot start, fails the check with the command and the last 20 lines of its output, on [D2](#d2)'s route, never as `the cut check cannot run`. Each runs under [D1](#d1)'s bounds. A file the checker or a command leaves in the tree, which `_check_cut` found clean, fails the check on the same route, naming the files: the first build phase would halt on it. MF's own `AGENTS.md` declares none; the bootstrap template names the line. The cut still runs no gate.

- **Why:** isekai's halts were text the gate rejects, a long line and a code block the formatter refused; MF's skills may assume no target's tools.
- **Rejected:** the cut running them, which binds as far as the cutter obeys · a formatter named in MF's own skills.

### D7

**In `mf-build`'s check step, a red `make check` whose output names a file no task of the phase names, and whose edit turns it green, is edited, and the commit body lists the file on an `Unplanned: <path>` line before the trailer block.** Conformance gains an `unplanned-file` pass in `worker.md`: each file of the freeze's diff that no task names, save `CHANGELOG.md` and the change's own `openspec/changes/<change-id>/` folder, and save a file changed only by a commit the status log names as a fix's, stands on an `Unplanned:` line of a commit in range. A file listed and needed by a red check is a `nit`; one changed with no line, or past what the check needed, is `blocking`. The `I6` and `I7` rows of both skills still ask tasks to name files; the build answers a miss.

- **Why:** seven of the halts, the largest class; no pairs are declared anywhere, and the rule covers a fixture or a coverage test nobody named. The build writes `CHANGELOG.md` and ticks `tasks.md` every phase, and `I12` bars a task for either, so the pass leaves them out. A fix commit answers cards, edits files no task names and carries no such line: an amend round reads it in its range, so the pass leaves its files out too (R10).
- **Rejected:** a cut row over declared pairs · a pass over every unnamed file, which raises a blocker no build can clear.

### D8

**The living spec's list of row ids, the cut's Step 8 sentence and the checker's `ROWS` agree; `docs/modules.md`'s `conduct.py` row names `cut_check.py`; one decision is added after the decision on closing halts, `The conductor checks the cut`; the decisions on the cut's rows, the mechanical steps and the halts of a run heal are edited where they live.** MF's `AGENTS.md` declares no cut checks.

- **Why:** `tests/test_structure.py` holds the map to the scripts' names; the living spec lists the ids.

## Tests

Every new test is a unit test in a file that exists. The change adds no end-to-end run and merges no test. It deletes one case, the `I14` defect `_human_without_tasks`, which held that a person's phase needs a `Verify:` sub-task; the other cases that held the exemptions flip to hold the refusal.

| file | adds | layer |
|---|---|---|
| `tests/test_conduct.py` | an autouse stub of `CUT_CHECK`; the cut check passes; fails once and cuts again; fails twice; cannot run; fails on a branch the run did not cut; a declared command passes, fails, and none is declared | unit |
| `tests/test_cut_check.py` | `K7` on a design line, with a removal word, in a diff block; `V7` on a program, a file, neither; `V8` on `HEAD`, the plan, none; `I14` on a phase marked for a person | unit |
| `tests/test_cut_check.py` | the `I14` no-`Verify:` case, `_human_without_tasks`, deleted: `retired by removing A HUMAN phase is handed over as a checklist of commands` | unit |
| `tests/test_verify_check.py` | a search for a range's text; an Oxford comma and an `e.g.` after an output verb; the flipped phase step | unit |
| `tests/test_brief_check.py` | a brief whose `## Phases` marks a person's phase | unit |
| `tests/test_structure.py` | none; its map check holds the new `conduct.py` row | unit |

Baseline `def test_` lines, from `git grep -c "def test_" -- <file>`: `tests/test_cut_check.py` 26, `tests/test_verify_check.py` 8, `tests/test_brief_check.py` 13.

## Dependencies

None.

## Risks / Trade-offs

- `V7` halts a first word that resolves only inside the build's own environment; the cutter rewrites the check with `uv run`.
- `K7` can flag a rename's new name; the cost is one reworded line at the cut, the cost it prevents later.
- A declared command runs commands of the primary's `AGENTS.md`, the operator's file as the `Makefile` is, under the worker sandbox; the threat model names the line.
- A second cut spends one more cutter on a plan that failed once.

## Verdict

Ready to build in the phases of [tasks](tasks.md): the conductor's first and hardest; the rest are rows, skill text and records.
