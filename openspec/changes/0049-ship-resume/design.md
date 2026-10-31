# Ship resume — design

How `/mf-ship` alone recovers a halt with no decision in it. Verdict at the end: ready to build.

## Context

- `Run.spawn` logs a worker's exit, and nothing reads it (`skills/mf-ship/scripts/conduct.py:865`).
- `_check_converge` reads the findings and a `halt`, not a `done` (`conduct.py:471`). `_converge_halt` reads the newest
  run's top line (`:321`).
- `stage_of` returns `integrating` for an open merge with no note (`conduct.py:420`), though `mf-integrate` calls that an
  interrupted run, and resumes it.
- `_progress` reads `tasks.md` from the tree (`conduct.py:304`), so a release that moved the folder stops the stage.
- `released` is a halt (`HALTS`, `conduct.py:47`) whatever the base did.
- A version merged and unpushed is not open: `status` prints `none`, and `mf-ship` Step 3 stops.
- `run` holds an empty `active/` (`conduct.py:1048`), and `work` starts each worker in its own session (`:719`), so a killed
  conductor leaves the claim and live workers.
- A usage limit reads `api_error_status: 429`, `is_error: true`, in Claude's `result` event, its text naming `resets <time>`.

## Goals / Non-Goals

**Goals:** a dead worker never passes; each death in the table below recovers with `/mf-ship`; a limit is named.

**Non-Goals:** a run that waits out a limit; retries inside a run; `conduct.py stop`.

| dies | on disk | a re-run, after this change |
|---|---|---|
| build, mid-phase | a dirty tree | continues, as today |
| converge, mid-run | a run with neither `halt` nor `done` | `converge`, the same run |
| integrate, conflicts open, no note | `MERGE_HEAD`, unmerged paths | `integrate` |
| release, before its commit | a staged fold and archive move | `release`, restored, started over |
| release, after its commit | release commit, no tag | `release`, tagged, then its merge |
| release, tagged, base unmoved | release commit and tag | `release`, from its merge |
| release, base moved | release commit | `released`, a halt |
| release, stopped on purpose or refused | release commit, the worker's exit 0 or no worker | `released`, a halt |
| release, merged, before its push | `main` ahead of `origin` | pushed at the run's start |
| the conductor | a stale claim | groups killed, claim cleared, run starts |

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | A non-zero exit halts the version, and the converge check needs `done` | a dead worker's clean findings prove nothing | reading the exit in `check` alone: a probe must halt too |
| [D2](#d2) | An unfinished run is stage `converge`, and the skill continues it | the run's own log says where it stopped | starting a new run: it would spend judged rounds |
| [D3](#d3) | No classifier: a decision is a stage left in `HALTS`, on disk | stages are already derived | a halt reason parsed into kinds |
| [D4](#d4) | `mf-release` restores its own fold, and re-enters at its merge | all of that work is derived | a person's recovery |
| [D5](#d5) | The conductor pushes what a release left, at the run's start | starting `mf-ship` is the yes to every push | a worker for one push |
| [D6](#d6) | The claim holds the conductor's pid and worker groups | a killed conductor must clear itself, and an orphan would race the new run | `rmdir` by hand |
| [D7](#d7) | A limit is named in the halt, and the run does not sleep | a weekly limit would hang a run for days, each version holding a worktree | a run that waits |
| [D8](#d8) | D47 is edited where it lives | A7 | a new decision |

### D1

`Run.spawn`, after its `finish` and `denied` events and the timeout's halt:

```python
if code != 0:
    self.halt(who, f"{station} worker exit {code}{usage_limit(out)}")
    return None
```

`Run.spawn`'s docstring says a timeout or a failed exit halted `who`.

```python
def _run_end(runs: Path, change: str) -> str | None:
    """Return the newest converge run's top event line, or None with no run."""


def _converge_done(runs: Path, change: str) -> bool:
    """Return whether the newest converge run ends on `done`."""
```

`_converge_halt` uses `_run_end`. `_check_converge`, after its halt: not `_converge_done` → `the status log has no done`.

### D2

`stage_of`, after `converge-halted`: a `_run_end` line that is neither `· halt` nor `· done` →
`("converge", f"unfinished run: {line}")`.

`skills/mf-converge/SKILL.md`, a section before `## Catch-up round`:

```markdown
## Resuming a run

Check first. The newest run's top line is neither `halt` nor `done` → this invocation continues that run: open no new
`## Run` heading, keep its round, and go on from its latest event. Workers stay fresh, and read the same frozen head.
**A verify round** is a round in a catch-up run, or after a `fix` line in this run: its checkers need Step 7's inputs.

| latest event | go on at |
|---|---|
| `start` | Step 2, or a catch-up run's freeze |
| `freeze` | a verify round → Step 7; else Step 3 |
| `fan-out` | the same, for each role whose findings file has not judged this round's freeze |
| `verdicts` | Step 5 |
| `fix` | a commit since the freeze → Step 6's re-freeze, then Step 7; else Step 6, a fresh fixer continuing a dirty tree |
| `verify` | Step 7 |
| `pickup` | Step 8 item 4, the same ids |
| `backlog` | Step 10 |
| `catch-up` | [Catch-up round](#catch-up-round) |
```

### D3

`HALTS` keeps its stages, and `released` narrows, per [D4](#d4). `stage_of`: an open merge with unmerged paths and no note →
`("integrate", "interrupted: a merge is open with no note")`.

`_progress` reads `HEAD`:

```python
tasks = _show(tree, "HEAD", f"openspec/changes/{change}/tasks.md") or ""
```

No retry is added: `/mf-ship` is the retry.

### D4

`stage_of`, a tip whose subject is `chore(release): <tag>`, tagged or not, goes to `_release_tip`. The re-entry merges and
pushes unasked, so it is `release` only for a death: `<tag>` on `HEAD` or missing, both findings clean at `HEAD~1`, the
default branch an ancestor of `HEAD`, and `_release_died`. Else `released`.

```python
def _release_died(runs: Path, change: str) -> bool:
    """Return whether the change's newest release worker ended any way but exit 0."""
```

`_release_died` reads the run logs, newest first: a `spawn` with no `finish`, or a `finish` that is not `exit 0`. So a
person's no, which ran no worker, and a preamble flagged under `merge=yes`, which exits 0, stay halts, with nothing to write:
absent proof of a death reads as a stop.

`skills/mf-release/SKILL.md`, after *Where the constants come from*, a section:

```markdown
## A resumed release

Check first. `mf-ship` re-runs a release that died.

- **`HEAD`'s subject is `chore(release): <tag>`** → that is the tag. When converge ran, both findings files must say
  `verdict: clean` with `head:` at `HEAD~1`, and `<tag>`, when it exists, must be on `HEAD`; else **halt**. `<tag>`
  missing → run Step 4.5. Then go to Step 5.
- **Under `merge=yes`, `git diff --cached --name-status` shows `tasks.md` renamed from `openspec/changes/<change-id>/`
  to `openspec/changes/archive/<change-id>/`, and the tree is dirty only under `openspec/`, in `CHANGELOG.md`, in the
  version file, or in `metrics/changes/<change-id>.json`** → a dead release's own work, all of it derived:
  `git restore --source=HEAD --staged --worktree -- .`, then `rm -rf openspec/changes/archive/<change-id>` and
  `rm -f metrics/changes/<change-id>.json`, then start over. Anything else dirty → precondition 6 halts.
```

A hand release never restores: precondition 6 keeps a person's edits. A release that died before Step 3's move leaves no
rename, so precondition 6 halts it for the person, as today.

### D5

```python
def _unpushed(primary: Path) -> list[str]:
    """Return the default branch when `origin` lacks it, and each merged tag it lacks."""


def push_left(self) -> None:
    """Push what a release merged and left; a rejection halts the run."""
```

`_unpushed`: no `origin` → an empty list. The default branch, when `rev-list --count origin/<default>..<default>` is not
`0`. Each `vX.Y.Z` tag merged into the default branch that `git ls-remote --tags origin` lacks. `Run.push_left` pushes them
with `git push origin <name>`, never forcing, and writes a `push` event, which `EVENTS` gains. A failure halts `run`.

`ship` calls it after its `start` event, before `if not versions`, and stops on a halt. `status` adds
`run · unpushed <names>` above its lines, and prints `status: none` only when there is nothing at all.

A worker can write `.git/config`, and `ls-remote` and `push` run outside its sandbox. So `_unpushed` and `_pushed` first run
`_refuse_config_commands`: a `CONFIG_COMMANDS` key at `local` or `worktree` scope stops with 1, `status` printing it and the
run halting, and the conductor makes no remote call. Overriding one key would leave the rest, and a snapshot cannot serve:
`status` and `push_left` run before any worker of their run, and a file under `.minions/` is the worker's to write.

`skills/mf-ship/SKILL.md`, Step 3: `status` prints `status: none — no open version` stays the only stop.

### D6

`run` writes `active/pid`, its own pid, after `mkdir`, and `shutil.rmtree`s the claim in its `finally`. `work` gains
`claim: Path | None`: after `Popen`, it writes the worker's `ps -o lstart=` to `claim / str(worker.pid)`, and unlinks it
when the worker ends. `Run.spawn` passes `self.runs / "active"`, and `agent` passes None. `_clear` kills a group only while
its leader keeps that start time: after a reboot the number can name anyone's process.

```python
def _claim(active: Path) -> str:
    """Return `none`, `live` or `stale`: stale has no pid file, or a dead pid."""


def _clear(active: Path) -> None:
    """Kill the stale claim's worker groups, then remove it."""
```

`preconditions` stops only on `live`. `run` calls `_clear` on `stale` before its `mkdir`. `status` adds `run · stale — a run
clears it` or `run · live` above its lines.

`skills/mf-ship/SKILL.md`, Step 2's table, after:

| `status` prints | then |
|---|---|
| `run · live` | a run is live: report the status and the run log's last lines, then stop |
| anything else | run `report` and keep its lines for Step 4 |

### D7

```python
def usage_limit(log: Path) -> str:
    """Return ` · stopped by a usage limit · resets <time>`, or "" for any other exit.

    e.g. a `result` event with `api_error_status: 429`, its text naming `resets 5:50pm`
    """
```

`report` prints every `halt` line, so the limit reaches the person with no further edit.

### D8

`docs/decisions.md`, D47's bold paragraph, before → after: "is judged by a check on disk;" → "is judged by its exit and a
check on disk;"; "and a re-run resumes from disk." → "and a re-run resumes from disk: only a stage left in `HALTS` needs the
person."

## Tests

Fake-worker tests in `tests/test_conduct.py` (`T1`: the lowest layer that reaches a run).

| layer | at cut | added | removed | proof |
|---|---:|---:|---:|---|
| Unit test functions | 78 | 5 | 0 | `uv run pytest --collect-only -q \| tail -1` prints `78 tests collected` at the cut, `83 tests collected` after |
| Integration tests | 0 | 0 | 0 | — |
| End-to-end runs | 0 | 0 | 0 | — |

`T2`: no test reaches a worker dying with state left behind, so each is a new test.

| test | holds |
|---|---|
| `test_a_dead_converge_halts_and_a_rerun_finishes_it` | with `dies-converge`: exit 1, clean findings, no `done`; the run halts, naming the exit; no `release` call; a re-run spawns `converge`, then `release`, with no `build` call |
| `test_a_rerun_recovers_a_dead_release` | with `dies-release-fold`: a staged fold; `status` reads `release`; a re-run tags once. With `dies-release-tag`: a re-run merges; a moved default branch reads `released`. With `dies-release-commit`: `release`; a re-run tags and merges. With `stops-release-tag`, exit 0: `released`, and no release worker. A tip forged on an old tag or with no tag, and a tagged tip no worker ran: `released` |
| `test_a_rerun_pushes_what_a_release_left` | a bare `origin`, a merged tag not pushed, no open version: `status` prints `run · unpushed`; a run pushes the branch and the tag, and ends on `done`. A planted `remote.origin.uploadpack`: `status` exits 1 naming it, a run halts, and the program never runs |
| `test_a_stale_claim_is_cleared` | `active/` with a dead pid and a live `sleep` group: `status` reads `stale`; a run kills the group and starts. A live pid refuses. A group whose entry holds another start time, or none, lives |
| `test_a_usage_limit_is_named` | with `dies-limit`, a `result` event with 429: the `halt` line ends ` · stopped by a usage limit · resets 5:50pm (Europe/Athens)` |

Tests edited:

| test | edit |
|---|---|
| `test_status_reads_each_stage_from_disk` | an open merge with no note reads `integrate` |
| `test_each_check_passes_only_on_disk_evidence` | a step for `the status log has no done` |
| `test_a_worker_carries_the_allowlist_and_a_denial_is_named` | `work`'s new argument, and the start time in its entry |

`_findings` also writes a status log ending on `done`. `_fake` gains `dies-<station>`, leaving that station's state and
exiting 1, and `stops-release-tag`, leaving a tag and exiting 0. No test is deleted or merged.

## Dependencies

None.

## Risks / Trade-offs

- **A hand converge while a run is dead** → it would continue the same run. That is the rule by hand too.
- **A recycled pid** → `os.kill(pid, 0)` reads it live, so the claim stands until the person looks. A false stale cannot
  happen.
- **A stale claim's kill** → a worker killed mid-commit leaves what any death leaves, and the table above covers it. A group
  whose leader is gone is left alive: nothing proves it is ours.
- **`git restore` over a dirty tree** → only under `merge=yes`, with the archive move staged, and under the paths
  [D4](#d4) names; anything else still halts.
- **A repo-local `core.sshCommand` or credential helper** → an operator who keeps one must move it to the global config, or
  `mf-ship` halts; `CONFIG_COMMANDS` is a list, so a key git adds later needs adding. `remote.origin.url` stays allowed: a
  worker pointing it at a local repo still gets that repo's receive hooks run on a push.
- **`converge-reading-set` is past its watch** → [D2](#d2) adds one short section.

## Migration Plan

```
1 a dead worker ─▶ 2 integrate and release ─▶ 3 the conductor ─▶ release
```

Each phase ends on a green gate. Nothing is irreversible. A claim with no pid file reads stale, so a run live across the
upgrade must end first.

## Verdict

Ready to build. Acceptance: each row of the table above recovers in a fake-worker test; a dead worker never passes; a limit
is named; D47 says so.
