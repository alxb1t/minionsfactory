# Run log — design

The run log and the claim each get one module that writes and parses them; the conductor reads and writes both through it. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The conductor writes the run log, `.minions/runs/<stamp>.md`, through its log class and a stop-line writer, and reads it in the release's death, the verify, the rescue, `report` and `wait`. It writes the claim, `.minions/runs/active`, in `run` and in `work`, reads it in `_claim`, `_conductor` and `_clear`, and removes it in `_clear`, `_close` and `stop_run`. No site goes through `skills/mflib/statefile.py`.

The viewer borrows `EVENT`, `last_log` and `_claim` from the loaded conductor. Its own readers of the log, and those of `scripts/metrics/run.py` and `skills/mf-review-metrics/scripts/review_metrics.py`, are the readers' version, not this one.

The region's mutants ran at the base; each real survivor is a case of phase 1, listed in [the pin's cases](#the-pins-cases). Debt cards 0137·S1 and 0137·S2 sit in `wait_run`, and this change pays them there.

```
conduct.py ──▶ mflib/runlog.py ─┐
           └─▶ mflib/claim.py  ─┼─▶ mflib/statefile.py
                                 │   (read · write · append · folder)
 viewer.py ──▶ conduct.py        │
   EVENT · last_log · _claim ◀───┘   names the conductor keeps
```

## Goals / Non-Goals

- **Goals:** one module for the run log and one for the claim, each the only writer and parser of its file; the conductor's reads and writes of both through them; the right side of each place the copies disagreed, in a phase of its own; the gate's format rule holding the run log's names; the record in step.
- **Non-Goals:** no behaviour changes but the named right sides; no edit to the viewer or the metrics' readers; no process call, `ps` or kill in a module; no edit to the debt file.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `skills/mflib/runlog.py` holds the run log and `skills/mflib/claim.py` the claim, each on `statefile` and naming no state path. The kill of a group, `ps` and what a stale claim means stay the conductor's. | Q157: one module a format; the process calls are the platform port's side. | one module for both; the claim's process rules in the module |
| [D2](#d2) | Phase 2 builds each module with the behaviour the conductor has today; phase 3 moves the conductor onto them and changes no assert; phase 4 gives each right side. The conductor keeps `EVENT`, `last_log` and `_claim`. | Q26, Q4, Q170: an unchanged assert over moved code proves the move; the viewer takes those names from the loaded conductor. | a fix inside the move; editing the viewer |
| [D3](#d3) | Phase 1 adds each case of [the pin's cases](#the-pins-cases) to `tests/test_runlog.py` and `tests/test_claim.py`, green on the code as it stands. The hand-typed logs of `tests/test_conduct.py` take stamp names. | Q25, Q171, Q175: a region moves when its mutants' survivors are cases; a log with a non-stamp name stops being a log in phase 4. | the mutant tool kept in the repo; a new fake `ps` for the suite |
| [D4](#d4) | `sync` and `codex` join the event list: the verify passes a run that wrote one. | Q158: both are written today and neither is listed, so the verify calls such a run incomplete. | dropping both lines |
| [D5](#d5) | The log's lock folder, its wait and its limit are removed. One conductor's threads append under a lock in the process, each line one `O_APPEND` write, and the stop line has one writer, the module's append. | Q159, Q160: only one conductor's threads take the lock; a folder planted at its name stops the run and nothing breaks a stale one; the stop line is spelled twice and appended past the lock. | breaking a stale lock folder |
| [D6](#d6) | The create, the append and the stop line open the log under the runs folder's descriptor, follow no link, take a regular file alone and do not block. `statefile` gains `append` and an offset on its bounded read. | Q161, Q174: the append writes through a link at the log's name today and blocks on a pipe there. | a path check before the open |
| [D7](#d7) | Every conductor reader of a log takes `statefile.read`: no link, no block, a regular file alone, a bad byte replaced. `wait` keeps its log open across the polls of one log, reads at most `262,144` bytes a poll from its offset and prints whole lines, passing over a line longer than the bound. | Q162, Q172, Q101, C11: most readers raise on a bad byte, and `wait` follows a planted newer link and reads the whole log at each poll; a line past the bound would stall it. | a bound for every reader; printing a part line |
| [D8](#d8) | A run log is a file of `runs/` whose name is a stamp with its `-<n>` suffix or none. The newest log, the release's death and `report` pass over any other `*.md`. | Q163: `notes.md` is the newest log today. | a rule in the viewer |
| [D9](#d9) | The claim's reads take `statefile.read` by a bound of `4,096` bytes and its writes `statefile.write` under the folder's descriptor, which opens the claim's parent and reaches `active` beneath it, never creating it. A claim that is no folder halts `run`, `stop` and a worker's start, naming it, and `stop` then kills nothing and writes no stop line. | Q164, Q172, Q177, Q178, C12: every claim read and write goes by pathname through a link today, and a link at the claim raises out of `_clear` and `_close`. | a claim read with no bound |
| [D10](#d10) | The verify passes an open spawn only when the log's last line is `run · halt — stopped by the person`; a finish with no spawn stays a pass. | Q168: any last line with that detail passes today, a version's own halt included. | refusing a finish with no spawn |
| [D11](#d11) | Left as they are and named: a worker's instant between its start and its claim entry, a converge by hand whose own log becomes the newest beside a live run, and a held event's clock, which its flush sets. | Q165: each is a station's behaviour, not a format's. | pinning them as formats |
| [D12](#d12) | The format kind of the gate's sixth rule gains the run log: outside `skills/mflib/` no string constant contains `# Ship run` or the event's clock in either spelling. Its list holds the clock pairs of `run.py` and `review_metrics.py`. `_claim` stays on `PRIVATE_REACH`. | Q166, Q173: Q106 and Q119 for the third format; the readers are the readers' version. | a rule for the event names |
| [D13](#d13) | `docs/decisions.md` amends D83 and D57 where they live. The spec delta, the threat model and the recipes follow. No task edits a debt card: cards 0137·S1 and 0137·S2 are closed by their premise and deleted by the release. | Q167, Q155: the debt file is written under its lock by converge and the release alone. | a task that edits `.minions/debt.md` |
| [D14](#d14) | The tasks and this design name by identifier only what stands after the diff; no `Verify:` filters by `-k`; an edit a phase's check needs sits in that phase. | Q176: the close's plan check halted earlier versions on a removed helper's name. | naming a helper the diff removes |

### D1

The run log's module, `skills/mflib/runlog.py`, holds:

- the title, the event line and its one pattern, the event list, the stop text;
- the order of logs and the newest log;
- the verify, the stop line, the release's death read and the rescue's read;
- the log object, and the tail `wait` follows.

The claim's module, `skills/mflib/claim.py`, holds the claim's entries, written and read: the take, the conductor's `start` and `pid`, a group's entry, the groups, the removal. Neither module names `.minions`: the conductor finds each path through `skills/mflib/layout.py`, which names `runs_dir` and `claim_file` already. The conductor keeps the group's kill, `ps` and the stale test, because each is a call to the platform or a meaning to the run.

The shapes of both modules, each function the conductor's own as it stands:

```
runlog.py
  STOPPED · EVENT · EVENTS
  class Event(NamedTuple)          line · who · name · detail
  title(stamp) -> str              "# Ship run <stamp>"
  line(who, event, detail) -> str  "<HH:MM:SS> · <who> · <event> — <detail>", no newline
  parse(text) -> Event | None      EVENT's match; detail is what follows it
  order(log) -> tuple[str, int, str]
  newest(runs) -> Path | None
  events(log) -> list[Event]       each line of the log that parses
  release_died(runs, change) -> bool
  rescuing(runs, change) -> bool
  verify(log) -> str | None
  stop(runs) -> Path | None
  class RunLog(runs, stamp, busy)  .stamp · .path · .held · .event(who, event, detail)
  class Tail(runs)                 .poll() -> list[str], the new whole lines · .close()
claim.py
  class Refused(Exception)         .path; added in the fix
  take(active) -> None             the one atomic mkdir
  present(active) -> bool          whether a claim stands
  mark(active, start, pid) -> None
  conductor(active) -> tuple[int, str] | None
  groups(active) -> list[tuple[int, str]]
  enter(active, pid, start) -> Path
  leave(entry) -> None
  remove(active) -> None
```

`busy` is the error the log object raises when its lock folder is held past its wait, the caller's own; `held` is the list of events held while the start's push runs. The parameter is removed in the fix.

`report` reads `events` and uses `Event.name`, `Event.detail` and `Event.line` where it used a match's groups and string. The viewer keeps `EVENT.match`.

### D2

Where the conductor's copies differ from the right side, the module is born with today's. These stand until phase 4:

- the log object takes a lock folder and a wait, `LOCK_SECONDS`, and both are removed in phase 4; the error a held lock raises is its caller's, `busy`, and the conductor passes one that makes `Stop` with code 2 and today's text;
- every reader reads by pathname, and the newest log is any `*.md`;
- the claim's reads follow a link, and a file at the claim reads as a stale claim.

The conductor binds `EVENT` and `last_log` to the module's and keeps `_claim` as its own function over the module's reads. The viewer is not edited.

### D3

The pin reaches the conductor through its loader, `tests/conduct_load.py`, as the status log's pin does. Its cases that hold today's block on a pipe run in a child joined within `10 s` and carry the `slow` marker, which phase 4 lifts when the fix makes them end at once. `run`'s own pid and start in the claim are pinned through `tests/test_claim.py`'s own fake `ps`, which knows the test's own pid, with a start no other pid has, and exits 1 for any other pid, so a wrong pid's start fails the pin; the suite's fake answers one start for every pid it does not know, and the real `ps` is refused by the sandbox the gate and the workers run in.

### D4

Both events are written by the conductor's sync step and by its Codex probe. The module lists them with the rest, and the unit case and the pin of the verify turn to the passing side.

### D5

The module's log object holds a lock of the process around each append. A held event, written after `start` with the clock of its flush, stays as it is ([D11](#d11)).

### D6

`statefile.append(path, text, folder=None)` opens with `O_WRONLY | O_APPEND | O_NOFOLLOW | O_NONBLOCK`, refuses what is no regular file, and writes the whole text in one call. `statefile.read` and `read_bytes` gain an `offset`, and `statefile.open_regular(path, folder=None)` returns a descriptor that follows no link and does not block, and refuses what is no regular file, for a reader that keeps its file open. The create of a log's title opens `O_EXCL | O_NOFOLLOW` beneath the descriptor and takes the next suffix when the name stands. The runs folder is opened only when a log is written or stands: `stop` over no log makes nothing.

### D7

The conductor's readers are the release's death, the verify, the rescue, `report` and `wait`. Each takes no bound but `wait`'s. `Tail` opens its log once through `statefile.open_regular`, reads from its offset with `os.pread`, and a poll returns the whole lines it read; a part line waits for its newline, and a newer log is read from its start.

A line longer than the bound is passed over whole: a poll that reads a span of the bound with no newline prints nothing of it and moves the offset past it, and the next polls discard bytes up to the line's newline, so `wait` never stalls and never prints the line's tail. C11 decides it.

A newest log that `open_regular` refuses, a link or a pipe, is read as no log: nothing is printed and no error is raised. `Tail.close` closes the descriptor, and a newer log closes the old one before it opens its own.

### D8

A log's name is `<stamp>.md` or `<stamp>-<n>.md`, `<stamp>` of the form the conductor's `STAMP` writes. The order of logs is unchanged: stamp, then suffix number.

### D9

The claim's `start` holds the conductor's start time and `pid` its pid; a group's entry is named by the leader's pid and holds its start time. A bad byte in `pid` or `start` stays a stale claim, an entry over the bound is passed over, and the pid floor stays the conductor's.

The module opens the claim's parent through `statefile.folder`, no part named, and `active` beneath it with `os.open` under `O_NOFOLLOW | O_DIRECTORY`, never creating it. A claim whose parent is missing is no claim, and nothing is made. A link or a file at `active` raises `claim.Refused`, which is no `OSError`, so no read of the conductor takes it for a stale claim.

The conductor turns `Refused` into `Stop` where it reads or removes the claim: `_conductor`, which `_claim` and `stop_run` read through, and `_clear`. `_close` prints a `Refused` from `claim.remove` as it prints a `Stop`, and makes no second removal in its handler. The viewer catches `Stop` around its own call.

C12 decides that `work` ends its worker's group and halts naming the claim when `enter` refuses, because the worker has started by then. Q178 amends Q169.

### D10

The stopped run's last line is the one the stop line writes. A version's own halt is another line, and an open spawn under it is incomplete.

### D11

Each is pinned nowhere and fixed nowhere in this change.

### D12

The clock's spellings are `\d\d:\d\d:\d\d` and `(\d\d):(\d\d):(\d\d)`, and the rule names both by one name, the first. The list lands with the rule, in one phase, because the rule fails the tree until it holds the pairs. After the move no script outside `skills/mflib/` holds the title.

The gate's rule has a planted-breach twin for the title, one for each spelling of the clock, and one for a listed site that is gone.

### D13

D83's text gains the run log's title and the event's clock beside the card head. D57's text names the run log and the claim as written and parsed by `skills/mflib/runlog.py` and `skills/mflib/claim.py`. The threat model's sentences on the conductor's writes, the claim and the `skills/mflib/*` surface follow the code. `docs/recipes.md` names both modules beside the status log's.

### D14

A search for a name the diff removes is a `Verify:` pattern, and names a helper by its text. A design's or spec's line that names one carries the word that says it is removed.

## The pin's cases

Each case is green on the code as it stands. The cases of the run log are in `tests/test_runlog.py`, those of the claim in `tests/test_claim.py`.

| case | pins |
|---|---|
| a | The event list is exactly its names; a log holding any one of them before a `done` passes the verify. The pattern reads `converge skipped` as one name and a who with hyphens, starts the detail after the first ` — `, and refuses a clock with no seconds, a hyphen for either separator, a missing space after the dash and a missing middle dot. An unlisted name matches the pattern and only the list refuses it. |
| b | The release's death: the newest log by the log order is read first, and `-2` is newer than its base stamp. In a log the change's last release line decides: a spawn last reads died; a finish reads died unless it starts `release · exit 0 · `; a check or a denial is no finish. Another change's lines and a `releaser` station do not count. A newer log with no release line passes the read to the older one. A worker that died before its finish line reads died. |
| c | The verify skips blank lines and `# ` lines alone. A finish with no spawn passes and banks nothing; a finish by another who or station closes nothing. The station is the detail up to its first ` · `. An open spawn passes only under a last line whose detail is exactly the stop text. A complete log returns `None`. |
| d | The log object: logs made on one stamp are `<s>.md`, `<s>-2.md`, `<s>-3.md`, each titled with its own stamp and locked by its own lock folder; a standing file is never written over; a detail's whitespace folds to one space; held events write nothing; a held lock is waited for, and past the limit the append stops with code 2. |
| e | The stop: the stop line goes to the newest log alone, after its lines, with a newline, and the stopped log passes the verify; with no log no file is made. `stop_run` kills, removes the claim and names the log; a conductor gone reads `stop: stopped · no run log`; one that refuses the kill is a stop with code 2 and the claim kept; a group that survives still gets the stop line. |
| f | The rescue's read: spawn and finish alone count, so a denial after a spawn leaves the version rescuing; rescue and supervise both count; only the newest log is read. |
| g | `wait`: a stale claim is no run; old lines are not printed and a part line waits for its newline; a newer log, and a log where there was none, is read from its start. |
| h | The order and the newest: newest by stamp, then by suffix number, `-10` after `-9`; by name, never by modification time; `None` with no `*.md`; folders, the claim and the detached log passed over. |
| i | `report`'s reads: the run's denials and waits; each version's `blocked` part; the versions by number; the tail's lines — halt, `rejoined`, `skipped — `, `rescued` for `fixed`, `supervised` for `decided`, the change split at `: `; the closing line; `report: none — no run yet`; `<log>: no event`. |
| j | The claim's read: a `start` with a trailing newline or a padded `pid` reads live; an empty `start` is stale even for a dead pid; the pid's floor is above 1; a file at the claim is a stale claim. |
| k | `_clear`: an entry that is no decimal is left unread; one with a trailing newline still names its group; an empty entry for a dead pid is skipped; a group gone before the kill is passed over; a foreign group is named in a stop with code 2 and left alive while an executor's beside it is killed. |
| l | `run`'s claim, `_close` and `_start_run`: `run` clears a stale claim, stray entries with it, then holds `start` equal to the start the file's fake `ps` gives its own pid and `pid` its own pid and nothing else; a live claim is refused with code 2 and left whole. `_close` removes the claim, a stop before the removal included; a request starts the next run; a cut seen or halted starts nothing. `_start_run` returns once the claim is live and reads the detached log's new lines. |
| m | `work`'s entry and the spawn lines: while a worker runs the claim holds one entry, named by its pid, holding its start; it is gone when the worker ends, and with no claim there is none. The spawn, finish, denied and limited lines are pinned in the same file. |

What no mutant reaches, pinned beside them as today's behaviour:

- **A bad byte in a log:** the verify, the release's death and `report` raise; the rescue's read replaces it; `wait` prints the line with the replacement character.
- **A link at `<stamp>.md`:** the append and the stop line write through it; the create refuses a dangling link and takes the next suffix.
- **A pipe at `<stamp>.md`:** the verify, the release's death, the rescue's read, `report`, the append and the stop line block, each in a child; `wait` blocks at its first poll.
- **A `*.md` that is no stamp:** the newest log takes `notes.md`, so the rescue's read, `report`'s closing line and the stop line use it, and the release's death reads it first. A digit-led name sorts before a stamp.
- **`sync` and `codex` lines:** `log --verify` exits 1 with `log: incomplete — unknown event: …`.
- **A planted lock folder:** the append waits out the limit and stops with code 2, the log unchanged; the stop line is appended with the lock standing.
- **A bad byte or a pipe in the claim:** a bad byte in `pid` or `start` reads stale and `_clear` removes the claim whole; a pipe at `pid` blocks `_claim`, in a child.
- **A link at the claim:** `_claim` follows it; `_clear` raises an `OSError` from the removal and leaves link and target; a dangling link reads none and the take then raises; `_close` lets the error out; `stop_run` kills the conductor first, and then the error escapes before the stop line is written.

## Tests

The change adds unit tests at the lowest layer that can fail for each behaviour, and no end-to-end test: no browser and no engine is involved.

| layer | file | what it holds |
|---|---|---|
| unit | `tests/test_runlog.py` | the pin's cases a to i and the log's pins in phase 1; the module's cases in phase 2; each right side of phase 4 |
| unit | `tests/test_claim.py` | the pin's cases j to m and the claim's pins; the module's cases; each right side |
| unit | `tests/test_statefile.py` | the append and the offset |
| unit | `tests/test_structure.py` | the format rule's run-log names, its planted-breach twins and its list |
| integration | `tests/test_conduct.py` | the lines that reach a moved name, the hand-typed logs renamed to stamps, and each assert the fix turns |

No test is deleted or merged. A test of the base the fix turns changes its assert in phase 4 and keeps its name. A new test that waits on a child over `5 s` carries the `slow` marker, as `T1` says, and loses it in phase 4 when the fix makes it end at once.

## Dependencies

None.

## Risks / Trade-offs

- A move over every call site of the log's event writer in the conductor is large; the pin's cases and an unchanged assert are its proof, and phase 3 re-points lines alone.
- The module born with the lock folder and the caller's error is dead weight for a phase; the other order would put a fix inside a move, against [D2](#d2).
- `statefile.append` refuses what is no regular file, which a FIFO pin shows; a log on a filesystem that reports another type would halt the run, and none is known.
- The viewer still reads the log and the claim its own way until the readers' version, so a plant the conductor now refuses can still reach the viewer's child.

## Verdict

Ready to build in the phases of [tasks](tasks.md): the pin, the modules, the stations, the fix, and the rule with the record. Nothing is left open.
