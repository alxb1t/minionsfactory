# Supervisor merge — design

The supervisor 0089 builds also settles an integrate note in spec or docs text, staged in the open merge for the integrate
station to commit, and reads the version's brief, which a passed cut now records in the home queue. Conductor code, skill and
decision text. Verdict at the end: ready to build.

## Context

Read at `bb4cf51`, the brief's own sha and this cut's `HEAD`: every fact citing a path stands. `C` is
`skills/mf-ship/scripts/conduct.py`, `I` is `skills/mf-integrate/SKILL.md`, `F` is `tests/fake_worker.py`, `T` is
`tests/test_conduct.py`. 0089-supervisor's design is read with `git show 0089-supervisor:openspec/changes/0089-supervisor/design.md`
and cited as `0089 D<n>`. See [the proposal](proposal.md) for why.

- **F1. The supervisor 0089 builds.** `Run.supervise(version, held, spent)` runs after `rescue()` returns False at both sites of
  `advance`; it starts no worker when `held == "integrating"` (0089 D1). Its prompt is `PROMPTS["supervise"]`, `"Run the
  mf-supervise skill for change {change} with decide=recommended."`; it judges with `_supervised`, logs
  `supervise — <id>: decided · <held> · <sha7>`, appends to `self.supervisor_decided`, and its `finally` runs
  `self.hold(version, tree, before, "supervise")` (0089 D4, D6). `skills/mf-supervise/SKILL.md` has Step 1 — read, Step 2 —
  decide, Step 3a — the amend, Step 3b — no answer, and Step 2's never list holds "an integrate or run-wide halt" (0089 D7).
  0089 adds D61 to `docs/decisions.md` and a supervisor paragraph to `THREAT_MODEL.md`'s *Out of scope*, ending "and a
  catch-up passes it by rule." (0089 D10).
- **F2. The integrate halt.** `stage_of` reads `integrating` with `semantic conflict: .minions/changes/<id>/integrate.md` while
  `MERGE_HEAD` and the note stand (`C:1094-1100`), and `red gate: …` for an `integrate.red` (`C:1090-1098`). `held()` maps a
  failed integrate check to its stage on disk (`C:3245-3247`); `RESCUED` holds `integrating` (`C:94`), so the rescue runs there
  and, with no amends (`_rescue_amends`, `C:2161-2166`), only diagnoses. `hold()` returns False on a stage in `HALTS`
  (`C:3195-3197`).
- **F3. The two merge paths.** `merge_in` leaves a merge open with its note when `_delta` names a moved requirement
  (`C:3502-3512`), git having merged with no conflict; `mf-integrate` halts with git's conflicts and its note (`I:124-154`).
  A resumed `mf-integrate` with the note standing reads "the person settled the note" (`I:90`), runs no rule again
  (`I:127-129`), and commits `<path>: the person` per path the note named (`I:169`); Step 4.5 deletes the note, `.red` and
  `.resolved` (`I:193-194`). `_check_integrate` wants the subject `chore(integrate): merge <default> into <id>` (`C:1190-1193`).
- **F4. The stage loop.** `advance` reads `stage_of` once a pass (`C:3323`), returns at `stop_at` before any spawn (`C:3339`),
  and formats `PROMPTS[stage]` with `grant=` (`C:3368`); `take` runs `advance(version, ("integrate", "release"))`, then
  `advance(version, ())` under `self.merging` (`C:3610-3613`). `PROMPTS["integrate"]` is
  `"Run the mf-integrate skill for change {change}."` (`C:182`).
- **F5. The cut's pass.** `cutting` deletes the reservation and unlinks the queue entry under `_queue_lock` (`C:3690-3693`);
  the entry's `brief` is the path `cut` wrote, resolved there (`C:4662-4670`); `_queue` is
  `~/.mf-ship-origin/<digest>.queue`, where no worker writes (`C:4533-4538`). A Claude worker has a bare `Read` (`C:134`).
  0088-paydown-2 edits `cutting`'s kept-worktree line above it, not the pass.
- **F6. The fake.** `_fake` records `<station> <id>` plus each `with`/`and` `key=value` clause whose value is a word
  (`F:289-295`); the prompt reaches it with `\n\nShell rules…` appended (`C:2432`). `_integrate` on an open merge takes
  `--theirs` everywhere and commits (`F:183-188`). `_cut` writes `models.toml` as `[build]\n[converge]\n[release]\n`
  (`F:281-282`). `test_a_dependents_delta_halts_as_integrating` builds the delta note (`T:838-904`);
  `test_a_queued_cut_is_cut_then_built` runs a passed cut (`T:2769-2832`).

## Goals / Non-Goals

**Goals:** the brief's Acceptance with the fake worker — the brief path survives a passed cut and reaches the supervisor's
prompt; an integrate note the supervisor settled is committed by the integrate station, naming the supervisor; `make gate`
green.

**Non-Goals:** the supervisor at an integrate red gate; pruning the `briefs/` records; a brief for a hand cut; the supervisor
committing a merge.

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | A passed cut records its brief's path in `<queue>/briefs/<id>`; the supervisor's prompt names it `and brief=<path>` while it names a file | V12 | the path in `.minions/`, where a worker writes; the path in the change; the queue entry kept |
| [D2](#d2) | The trigger widens to an `integrating` halt on a semantic conflict, never a red gate, one try an open merge across runs | V2, V7, V10, V13, C1, C2 | a red gate, which is code; a try per run, which takes an earlier staging as its start |
| [D3](#d3) | Its own check, `_settled`, reads the open merge: `HEAD`, `MERGE_HEAD`, the note, the index's changed paths, the work tree, the mark | V2, V9, V10 | `_supervised`, which wants a commit; a check of the note's paths alone |
| [D4](#d4) | A taken settle goes on in the thread: `self.settled` makes the stage `integrate`, whose prompt carries `with settled=supervisor` | V8, V10 | deleting the note, which reruns integrate as interrupted; a mark file read by integrate |
| [D5](#d5) | `mf-integrate` at `settled=supervisor` commits the merge as staged, naming `<path>: the supervisor`, and deletes `integrate.settled` | V10, V14 | the supervisor committing the merge, which is integrate's (D45) |
| [D6](#d6) | `mf-supervise` gains `brief=` and Step 3c for an integrate note | V2, V3, V12 | a second skill |
| [D7](#d7) | The record: D45, D57, D61; `THREAT_MODEL.md`; `skills/mf-ship/SKILL.md`; `README.md` | V14 | a new decision id |

### D1

At a passed cut, inside `cutting`'s `_queue_lock` and before the reservation goes:

```python
folder = _queue(primary) / "briefs"
folder.mkdir(mode=0o700, exist_ok=True)
(folder / change).write_text(f"{entry['brief']}\n")
```

A module function beside `_queue` reads it:

```python
def _brief_of(primary: Path, change: str) -> str | None:
    """Return the brief path a passed cut recorded for `change`, while it names a file.

    The record stands in the home queue, where no worker writes; a version cut by
    hand has none. Why: 0090-supervisor-merge design D1.
    """
```

It returns None when the record cannot be read (`OSError`, `UnicodeDecodeError`), is empty, or names no file
(`Path(named).is_file()`).

- **The prompt.** `PROMPTS["supervise"]` becomes
  `"Run the mf-supervise skill for change {change} with decide=recommended{brief}."`. `_supervise_prompt(primary, change)`
  formats it with `brief=f" and brief={named}"`, or `""` with no record, and `Run.supervise` takes its prompt from
  `_supervise_prompt(self.primary, change)`.
- **No record.** A version cut by hand, as 0089's tests cut theirs, keeps 0089's prompt.
- **A branch checked, not cut again,** passes the same check, so it gets its record too. No record is ever deleted
  (Non-Goals).
- **`cutting`'s docstring**: "None on a pass, its queue entry and reservation deleted" → "None on a pass, its brief recorded,
  its queue entry and reservation deleted".

### D2

0089 D1's table row "the halt is a build's or `converge-halted`, never `integrating`" becomes the first row below, and the
second joins it:

| condition | read from |
|---|---|
| the halt is a build's, `converge-halted`, or `integrating` on a semantic conflict | `held != "integrating" or stage_of(self.primary, version)[1].startswith("semantic conflict")` |
| at `integrating`, no supervisor was spawned on this open merge, in this run or an earlier one | `not _merge_tried(self.primary, change, merge)`, `merge` the tree's `MERGE_HEAD` |

Every other row of 0089 D1 stands. At an integrate red gate `stage_of` reads `red gate: …`, so no supervisor starts and the
halt goes to the person, as today.

**One try an open merge.** Before it spawns at `integrating`, `Run.supervise` writes `MERGE_HEAD`'s full sha to
`<queue>/supervised/<id>` (folder made `0o700`), where no worker writes; `_merge_tried(primary, change, merge) -> bool`, beside
`_brief_of`, reads it, False when it cannot. So a later run's `_opened` never takes an earlier supervisor's staging as its
start: a refused settle, or a taken one whose run died before integrate committed, goes to the person. A new merge, after
the person aborts and integrate merges again, has a new `MERGE_HEAD` and gets its try. (Brief C2.)

### D3

A named tuple beside `ShipLines`, and two module functions beside `_supervised`:

```python
class Opened(NamedTuple):
    """An open merge as the supervisor found it: `HEAD`, `MERGE_HEAD`, the index, the mark."""

    head: str
    merge: str
    index: str
    written: int | None


def _opened(primary: Path, tree: Path, change: str) -> Opened:
    """Return the open merge in `tree` before its supervisor runs."""


def _settled(
    primary: Path, tree: Path, change: str, start: Opened
) -> tuple[str | None, str]:
    """Return the tree the supervisor staged in the open merge, or None and why.

    It takes Markdown under `openspec/` and `docs/` alone, with `HEAD`, the merge and
    the note as they stood, nothing unstaged or unmerged, and `integrate.settled`
    written since `start`. No mark is (None, ""). Why: 0090-supervisor-merge design D3.
    """
```

`_opened` reads `rev-parse HEAD`, `rev-parse MERGE_HEAD`, `ls-files -s` and `_mtime` of
`.minions/changes/<id>/integrate.settled`. `_settled` checks in this order, the first match winning:

| outcome | returns |
|---|---|
| `HEAD` is not `start.head` | `None, "supervisor moved HEAD off <head7>"` |
| no merge open, or `MERGE_HEAD` is not `start.merge` | `None, "supervisor closed the merge"` |
| no `.minions/changes/<id>/integrate.md` | `None, "supervisor removed .minions/changes/<id>/integrate.md"` |
| an index path whose `ls-files -s` entries differ from `start.index` and is not a `.md` under `SETTLES = ("openspec/", "docs/")` | `None, "supervisor touched <paths, sorted, space-joined>"` |
| a path `git diff --name-only` prints that `_conflicts` does not, or one `ls-files --others --exclude-standard` prints | `None, "supervisor left unstaged <paths, sorted, space-joined>"` |
| `_mtime` of `integrate.settled` is None or `start.written` | `None, ""` |
| `_conflicts(tree)` prints a path | `None, "supervisor left <paths, space-joined> unmerged"` |
| else | `git write-tree`'s sha, `""` |

`_conflicts` runs `_refuse_config_commands` first, so the plain `git diff` after it runs past the refusal, as `_conflicts`'s
own does. The mark is what tells a settle that stages nothing — a delta flag with no real conflict — from no answer. A file
under `tests/` or `skills/` is outside `SETTLES`, so the path rule refuses it.

The untracked read is not compared with `start`: an untracked file already in the worktree refuses the settle, as
`mf-integrate`'s Step 4.2 would halt on it before committing.

### D4

`Run.supervise` branches on `held` (0089 D4 otherwise):

```
held == "integrating" ─▶ start = _opened(...) ─▶ spawn ─▶ _settled(..., start)
         else         ─▶ before = HEAD       ─▶ spawn ─▶ _supervised(tree, change, before)
```

- **Taken.** It logs `supervise — <id>: decided · integrating · <tree7>`, clears the halts and `diagnosed`, appends the
  version to `self.supervisor_decided`, and records `self.settled[change] = sha` in `self.settled: dict[str, str]`, a new
  field of `Run.__init__` beside `self.supervisions`, keyed by change to the tree `_settled` took: the tree integrate must
  commit. It returns True.
- **Not taken.** No answer halts `supervisor settled nothing`; a refusal halts with its reason.
- **Held.** `before`, which `hold()` gets in the `finally`, is `start.head`. A refusal that left the note standing reads
  `integrating` there, in `HALTS`, so `hold()` returns False.

`Run.stage(version) -> tuple[str, str]` wraps `stage_of`: a version in `self.settled` whose stage reads `integrating` on a
semantic conflict reads `("integrate", SETTLED)`, `SETTLED = "the supervisor settled the note: integrate commits it"`.
`advance` reads `self.stage(version)` where it read `stage_of(self.primary, version)` (`C:3323`), so the first `advance` stops
at `integrate`, and the one under `self.merging` spawns it. `PROMPTS["integrate"]` becomes
`"Run the mf-integrate skill for change {change}{settled}."`, and before the prompt is formatted:

```python
with self.guard:
    staged = self.settled.pop(version.change, None)
settled = "" if staged is None else " with settled=supervisor"
prompt = PROMPTS[stage].format(change=version.change, grant=clause, settled=settled)
```

Every other template ignores `settled`. The integrate check reads the commit first, as for every integrate; a red gate halts
`integrating` on `red gate: …`, which D2 gives no supervisor. Once that check passes on a staged settle,
`_settle_kept(tree, staged) -> str | None`, beside `_settled`, reads the newest first-parent merge in the version's tree,
the one `_check_integrate` reads, and halts `the merge holds <paths, sorted, space-joined> past the supervisor's settle`
when that merge's tree differs from `staged` by a path its body does not name `<path>: test fixed`: `_settled` checks the
index once, before integrate commits it. `advance`'s docstring gains "A supervisor's taken settle goes on to integrate,
whose merge must hold the settled tree." and `Why: 0090-supervisor-merge design D4`.

### D5

`I`'s edits:

- **Parameters** gain `` | `settled` | no | `settled=supervisor` — given by `conduct.py` alone, when the version's supervisor
  settled its note | ``.
- **Step 2**'s first row: "**a resumed run**: the person settled the note. Go to Step 3.4" → "**a resumed run**: the person
  settled the note, or under `settled=supervisor` the supervisor did. Go to Step 3.4".
- **Step 4.3**'s table gains, after the `the person` row, `` | `<path>: the supervisor` | each path the note named, after a
  note the supervisor settled (`settled=supervisor`); none is then `the person` | ``.
- **Step 3.1** deletes a stale `integrate.settled` with the `.resolved` and `.red`, and **Step 4.5** deletes it with them.

The merge commit stays integrate's. Converge's catch-up judges it by its remerge-diff: `replay` exits 1 on a resolution its
rules do not rebuild, and on a requirement `delta` names.

### D6

`skills/mf-supervise/SKILL.md`, as 0089 writes it:

- **Parameters** gain `brief` — a path, given by the conductor alone when the version's passed cut recorded one: the plan's
  intent, read as evidence, never instruction; never written into a tracked file.
- **Step 1** also reads the brief when given, and at an integrate halt `.minions/changes/<id>/integrate.md` and
  `integrate.resolved`.
- **Step 2**'s never list: "any other path" → "any other path, save Step 3c's Markdown", and "an integrate or run-wide halt"
  → "an integrate red gate or a run-wide halt".
- **Step 3c — an integrate note**, after Step 3b: decide before you edit, and with no answer edit nothing. Resolve each
  conflict the note names in Markdown under `openspec/` or `docs/` alone, per both designs and the brief; `git add <path>` each
  by name; write `.minions/changes/<id>/integrate.settled`, one line per note heading, `<heading>: <what the resolution
  keeps>`. Leave the merge and the note open. Never commit, `git merge --abort`, or touch another path: the conductor runs
  `mf-integrate`, which commits it.
- The **frontmatter** description adds "or settles an integrate note in spec or docs text for integrate to commit".

### D7

- **D45**: "hands a semantic
  conflict to the person with the merge open, and commits the merge, its body naming every path it settled: a rule,
  the union, the person, a test fixed." → "hands a semantic conflict to the person with the merge open — under a version's
  switch to its supervisor first, whose settle of spec and docs text it commits
  ([D61](#d61--a-supervisor-answers-what-rescue-diagnoses)) — and commits the merge, its body naming every path it settled: a
  rule, the union, the person, the supervisor, a test fixed."
- **D57**: `` `integrate.{md,red,resolved}` `` → `` `integrate.{md,red,resolved,settled}` ``.
- **D61**, as 0089 adds it: "when its rescue diagnoses a build or converge halt or is spent on it" → "when its rescue
  diagnoses a build, converge or integrate semantic-conflict halt or is spent on it"; "answers an integrate halt," →
  "answers an integrate red gate,"; the **An integrate note** and **The brief** bullets after **New work**:

> - **An integrate note:** it stages its resolution in Markdown under `openspec/` and `docs/` alone and writes
>   `integrate.settled`, leaving the merge and the note open; the run checks the index and the work tree, then runs
>   `mf-integrate` `with settled=supervisor`, which commits the merge naming `the supervisor`.
> - **The brief:** a passed cut records its brief's path in the home queue's `briefs/<id>`, and the supervisor's prompt names
>   it, read as evidence.

  The first bullet ends "One try an open merge, across runs: the home queue's `supervised/<id>` records it."

  and its Rejected gains " · the supervisor committing the merge, which stays integrate's".
- **`THREAT_MODEL.md`**: the *Entry points* cut-queue bullet, after "so no worker names that brief.", gains "A passed cut's
  brief path stays there, in `briefs/<id>`, for its supervisor's prompt, and `supervised/<id>` names the open merge a supervisor
  tried, so no worker forges that record; a worker that moves the worktree's `MERGE_HEAD` reads as a new merge and gets it a
  try, each meeting the same settle bound."; *Out of scope*, after the sentence 0089 ends "and a
  catch-up passes it by rule.", gains:

> At an integrate note the supervisor stages spec and docs text the integrate station then commits, bounded by the index's
> changed paths — Markdown under `openspec/` and `docs/` alone — the open merge and note left standing, and the
> `integrate.settled` it writes; the run halts when integrate's merge holds a path past the checked tree but a test its
> body names fixed, and converge judges that merge by its remerge-diff, never by rule.

- **`skills/mf-ship/SKILL.md`**, Step 4: "An `integrating` halt is the person's: they settle the note," → "An `integrating`
  halt is the person's, save a note the version's supervisor settled under the switch, which `mf-integrate` commits in the
  run, `<change-id> · supervised integrating · <tree>` in `report`: they settle the note,". Its answered row, as 0089 writes
  it: "or the supervisor at a converge halt, left it answered" → "or the supervisor at a converge or integrate halt, left it
  answered", since a refused settle that removed the note or closed the merge reads no `HALTS` stage in `hold()`.
- **`README.md`**, 0089's `mf-supervise` row: "with one checked amend of its plan" → "with one checked amend of its plan, or
  a settle of an integrate note for integrate to commit".

`report`, the close and `supervisor-decided` need no edit: 0089's branches read the `supervise` event whatever its halt.

## Tests

At the cut, `git grep -c '^def test_' HEAD -- tests/test_conduct.py` prints 119; 0088 adds none there and 0089 adds six
(0089's `## Tests`), so the build starts from 125. Added: three conductor tests in `tests/test_conduct.py`, each at the
lowest layer that holds its behaviour (`T1`): the full runs use `tests/fake_worker.py`, as 0089's do, and each carries
`slow` only if it runs over 5 s. Extended: `test_a_queued_cut_is_cut_then_built`. No end-to-end test: the repo has no browser
layer. `T2`: no existing test runs a cut version under the switch to a supervisor, nor a supervisor at an integrate halt;
`test_a_dependents_delta_halts_as_integrating` reaches the note without the switch, and its setup is copied, not extended,
since its run must stay halted.

| test | layer | asserts |
|---|---|---|
| `test_a_queued_cut_is_cut_then_built` | extended | after the first run, `conduct["_queue"](root) / "briefs" / "0001-a"` reads `f"{brief}\n"` |
| `test_a_cut_brief_reaches_the_supervisor` | fake run, then unit | a cut queued with `brief`, modes `cut-decides`, `halt-0001-a`, `rescue-diagnose`, `supervise-delta`: the calls are `probe`, `cut-change 0001-a`, `build 0001-a`, `rescue 0001-a with decide=recommended`, `supervise 0001-a with decide=recommended and brief=brief.md`, `build 0001-a`, `converge 0001-a`, `release 0001-a`; the run exits 0. Then `_supervise_prompt(root, "0001-a")` ends `with decide=recommended and brief=<brief>.`; with `brief` deleted, and for `0002-none`, which has no record, it ends `with decide=recommended.` |
| `test_a_supervisor_settles_an_integrate_note` | fake run | `test_a_dependents_delta_halts_as_integrating`'s setup, `0002-marks`' models file `decide = "recommended"\n`, modes `rescue-diagnose`, `supervise-settle`: the `0002-marks` calls are `rescue 0002-marks with decide=recommended`, `supervise 0002-marks with decide=recommended`, `integrate 0002-marks with settled=supervisor`, `build 0002-marks`, `converge 0002-marks`, `release 0002-marks`; the log holds `run · supervise — 0002-marks: decided · integrating · <tree7>`, `<tree7>` the integrate merge commit's tree; that commit's body holds `sdd: First: the supervisor`; no `integrate.md` or `integrate.settled` stands; the last line ends `· run · done — released v0.1.0 v0.2.0 · supervised 0002-marks`; the run exits 0 |
| `test_a_supervisor_settle_outside_the_text_halts` | fake run, then unit | the same setup, modes `rescue-diagnose`, `supervise-settle-code`: a `0002-marks` halt line ends `halt — supervisor touched src.py`; no line holds `run · supervise — `; `MERGE_HEAD` verifies and the note stands; the run exits 1. A second run's `0002-marks` calls are `rescue 0002-marks with decide=recommended` alone, and it exits 1. Then `_merge_tried(root, "0002-marks", <MERGE_HEAD>)` is True, and with another sha False. Then `_settled` on a hand-made conflicted merge of `docs/a.md`, its note written, after `start = _opened(...)`: nothing done gives `(None, "")`; the mark alone gives `supervisor left docs/a.md unmerged`; `docs/a.md` resolved and added with the mark gives `git write-tree`'s sha; `src.py` added gives `supervisor touched src.py`; `docs/a.md` edited after its add gives `supervisor left unstaged docs/a.md`; the note removed gives `supervisor removed .minions/changes/<id>/integrate.md`; `git merge --abort` gives `supervisor closed the merge`; a commit gives `supervisor moved HEAD off <head7>`. Then
`_settle_kept` on a merge committed over a settle `_settled` took: nothing added, its body `docs/a.md: the supervisor`, gives
None; `src.py` added gives `the merge holds src.py past the supervisor's settle`; `tests/test_a.py` added, its body
`tests/test_a.py: test fixed — kept`, gives None. Each case starts from its own fresh conflicted merge, built by one helper in the test, so no case leans on another's edits (`T3`) |

The fake gains:

| where | what |
|---|---|
| `_cut` | mode `cut-decides`: `models.toml` opens `decide = "recommended"\n` |
| `_fake` | a `supervise` prompt holding ` and brief=<path>.` before whitespace adds ` and brief=<the path's file name>` to its call line |
| `_supervise` | a `primary` parameter; mode `supervise-settle` appends `Settled.\n` to `openspec/changes/<change>/specs/sdd/spec.md`, adds it, and writes `.minions/changes/<change>/integrate.settled` holding `sdd: First: the branch's block kept\n`; mode `supervise-settle-code` adds `src.py` holding `x = 1\n` and writes the same mark. Neither commits: they return before the amend commit 0089's modes make |
| `_integrate` | a `settled` parameter, the change's folder in the run directory when the prompt carries `with settled=supervisor`, else None: on an open merge it then commits the index as it stands, its body a `<heading>: the supervisor` line per `## ` heading of the note but `## Resolved`, and deletes `integrate.md` and `integrate.settled` |

These tests cover every line the change adds, as the gate's diff coverage requires; a line they leave uncovered gets a case
in the test of its phase. After: 128 in `tests/test_conduct.py`. No test is deleted or merged.

## Dependencies

None.

## Risks / Trade-offs

- **A wrong settle passes the check** → it is a worker's decision in the steering class the threat model accepts: the gate runs
  over the merge, converge's catch-up judges it by its remerge-diff, and the close and `report` name it.
- **A run that dies after a settle, before integrate commits** → the next run reads `integrating`, and `_merge_tried` starts
  no second supervisor on that merge: the halt is the person's, and `/mf-integrate` commits the merge naming `the person`,
  having read it.
- **A refused settle leaves its staging in the open merge** → its halt, `supervisor touched <paths>` or another refusal,
  names what it left, and no later run's supervisor starts on that merge ([D2](#d2)). The person undoes it before settling:
  `git restore --staged <path>` and the file removed for a path the merge does not hold, `git checkout -m -- <path>` for a
  conflicted one.
- **The `supervised/` records** grow as `briefs/` does, one small file an integrate halt the supervisor tried.
- **The mark is worker-writable** → only its write time during the supervisor's run counts, as the rescue's diagnosis does, and
  a forged mark settles nothing the index check refuses.
- **The `briefs/` records grow by one small file a passed cut** → none is deleted; the trigger to prune is their count.
- **The integrate merge with 0089** meets `Run.supervise` and the supervisor skill only through 0089's own lines, which this
  change edits after 0089 is merged in, per `after:`.

## Verdict

Ready to build.
