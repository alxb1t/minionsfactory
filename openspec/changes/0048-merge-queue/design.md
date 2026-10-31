# Merge queue — design

How versions merge in the order they are ready, and how one declares that it builds on another. Verdict at the end: ready
to build.

## Context

- `ship()` runs stage A in threads, then `deliver` in change-id order (`skills/mf-ship/scripts/conduct.py:870`, `:844`).
  `advance` re-reads the stage each turn (`:811`), so a version whose base moved integrates and catches up already.
- `closing` and `report` carry `held` and `held behind` (`conduct.py:763`, `:1031`, `:1069`).
- `PROMPTS["integrate"]` names no change (`conduct.py:72`). `next_version` picks the lowest open id
  (`skills/mf-integrate/scripts/integrate.py:163`), and `mf-integrate` has no parameter.
- `mf-release` precondition 10 halts on an open lower id (`skills/mf-release/SKILL.md:121`).
- A cut touches only `openspec/changes/<id>/`, so the default branch merges into a cut-only branch with no git conflict.
  Its delta can still modify a requirement the default branch changed, and the release fold replaces that text byte for
  byte.
- A release puts `openspec/changes/archive/<id>/` on the default branch: a tree holds a dependency exactly when it holds
  that folder.
- `I10` asks every file and symbol a design names to exist at `HEAD`, which a dependent's design cannot meet for what its
  dependency adds.

## Goals / Non-Goals

**Goals:** a ready version never waits for an unrelated one; a halt costs only what declared a dependency on it; a
dependency cannot be skipped, by `mf-ship` or by hand.

**Non-Goals:** an order among versions waiting for the lock; `major`; stopping a run.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | One thread per version, and one lock around integrate, catch-up and release | `advance` already re-reads the stage, so stage B's loop can go | a queue structure: any order among the ready will do |
| [D2](#d2) | `after: [<ids>]`, read by `_after`; each id open and lower at the cut | a lower id rules out cycles, and `ready` joins no other, so an edit past the cut blocks and cannot hang | a dependency graph file |
| [D3](#d3) | The dependent joins its dependency's thread, and `conduct.py` merges the default branch, running `integrate.py delta` on the open merge | a cut-only branch cannot conflict in git, so only a requirement both sides changed needs judgement, and that is the person's | an agent for it; merge-order-only dependencies, since a dependent needs the code; a commit in one step, which loses the dependency's requirement text at the fold |
| [D4](#d4) | `waiting` in `status`; `blocked — by <id>` down a chain; `held` goes | nothing waits on order any more | keeping `held` for dependents |
| [D5](#d5) | `mf-integrate` takes a `change-id`; bare, the lowest-id ready | the conductor names the version it holds the lock for | the lowest open id, which a halted version would block |
| [D6](#d6) | `I17` in `mf-build` and `mf-release`, in place of precondition 10; the exceptions in `I9` and `I10` | a dependency cannot be skipped by hand | trusting the conductor alone |
| [D7](#d7) | The cut's text, and `mf-plan`'s *parallel with* | Q34 and Q41 of the plan | — |
| [D8](#d8) | D20, D44, D45 and D47 are edited where they live | A7 | a new decision |

### D1

`Run` gains `self.merging = threading.Lock()` and `self.blocked: list[str] = []`, `block` and `take`. `deliver` goes.

```python
def take(self, version: Version, threads: dict[str, threading.Thread]) -> None:
    """Take one version to its release, a halt or a block."""
    try:
        if not self.ready(version, threads):
            return
        self.advance(version, ("integrate", "release"))
        if not self.stopped(version.change):
            with self.merging:
                self.advance(version, ())
    except Stop as stop:
        self.halt(version.change, str(stop))
    except Exception as error:
        self.halt("run", f"conduct.py failed: {error}")
```

`ship` starts a thread for every version, whatever its stage, in change-id order. A dict of threads is built before the
first starts, so a dependent can join a lower id.

`ship`'s status test reads `STUCK = (*HALTS, "waiting")`. With every version in it nothing can start, so no probe runs:
each `waiting` version is blocked by the first id it names, and each other halts. The branch before the threads becomes
`if not (self.halts or self.blocked)`.

```python
threads: dict[str, threading.Thread] = {}
for version in versions:
    threads[version.change] = threading.Thread(
        target=self.take, args=(version, threads)
    )
for thread in threads.values():
    thread.start()
for thread in threads.values():
    thread.join()
```

A run with `self.halts` or `self.blocked` writes the closing event and returns 1. `PROMPTS["integrate"]` becomes
`"Run the mf-integrate skill for change {change}."`.

### D2

`mf-cut-change`, the parameters table gains `| `after` | no | `after=<id>[,<id>]` — the versions this one builds on |`.
`proposal.md` then holds `after: [0047-x, 0048-y]`. `conduct.py` and `integrate.py` each hold the reader, as each holds
`_frontmatter`.

```python
def _after(text: str) -> list[str]:
    """Return the change ids a proposal's `after:` names.

    e.g. "---\nafter: [0047-x, 0048-y]\n---\n" → ["0047-x", "0048-y"]
    """
    found = re.search(r"^after:\s*\[(.*)\]", text.split("\n---", 1)[0], re.MULTILINE)
    return re.findall(r"[^,\s]+", found[1]) if found else []


def _shipped(cwd: Path, rev: str, change: str) -> bool:
    """Return whether `rev` holds the change's archive folder."""
    path = f"{rev}:openspec/changes/archive/{change}"
    return _maybe(cwd, "cat-file", "-e", path) is not None
```

### D3

```python
def ready(self, version: Version, threads: dict[str, threading.Thread]) -> bool:
    """Wait for the version's dependencies, then bring the default branch in."""
    change, default = version.change, default_branch(self.primary)
    after = _dependencies(self.primary, change)
    for dependency in after:
        if dependency in threads and _change_number(dependency) < version.number:
            threads[dependency].join()
    if self.stopped(change):
        return False
    for dependency in after:
        if not _shipped(self.primary, default, dependency):
            self.block(change, dependency)
            return False
    tree = version.tree
    if tree and not all(_shipped(tree, "HEAD", name) for name in after):
        self.merge_in(tree, change, default)
    return True


def merge_in(self, tree: Path, change: str, default: str) -> None:
    """Merge the default branch into a dependent, once the delta check passes."""
    note = self.primary / ".minions" / "integrate" / f"{change}.md"
    opened = _merge_open(tree)
    if opened and note.is_file():
        return
    if not opened:
        _git(tree, "merge", "-q", "--no-ff", "--no-commit", default)
    if moved := _delta(tree):
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text(_note(tree, change, moved))
        return
    message = f"chore(integrate): merge {default} into {change}"
    _git(tree, "commit", "-q", "-m", message, "-m", f"Change: {change}")
```

`_dependencies(primary, change)` is `_after` over the proposal on the branch; after a release it reads nothing, and returns
an empty list. A chain follows: a blocked version's thread ends unreleased, so its dependent finds it unshipped. A failed
merge raises `Stop`, which halts the version. The cut's lower-id rule does not hold an `after:` edited past the cut, so
`ready` joins only a lower id: a mutual, own or higher id would hang or raise, and falls through to `blocked` instead.

`merge_in` is the conductor's first commit in a target repo, and a Codex worker can write the common directory. So `_run`
passes `NO_HOOKS`, `-c core.fsmonitor=false -c core.hooksPath=/dev/null`, to every git command `conduct.py` runs.

`_delta(tree)` runs `integrate.py delta`, the one copy of the check, from the sibling package, as `mf-release` runs
`gate_check.py`; exit 2 raises `Stop`, and so does exit 1 with no `MOVED` line, which is a crash and never a pass. It must
run here: once the merge commits, the merge base has moved past the
dependency, and no later check sees what it changed. `_note` writes one `mf-integrate` note section per title, naming both
changes. `ready` then returns, `advance` reads `integrating` from the open merge and its note, and the version halts, as
`mf-integrate` Step 3's does. A re-run leaves the note and the merge as they stand, and a merge left open with no note runs
the check again. The person settles it, and `/mf-integrate <change-id>` commits it; see [D5](#d5).

### D4

`EVENTS` gains `blocked`. `stage_of`, after the `released` check:

```python
missing = [
    name
    for name in _dependencies(primary, change)
    if not _shipped(primary, default_branch(primary), name)
]
if missing:
    return "waiting", f"after {' '.join(missing)}"
```

`closing` takes no argument, and returns `halted <ids> · blocked <ids> · released <tags>`, `none` for an empty list.
`report` reads each `blocked` event and ends that version's line ` · blocked by <id>`; the closing-line parse and `held`
go. `ready` passes every `after:` id, so `advance` meets `waiting` on a worker's edit of `after:` alone, and halts that
version on it.

### D5

`integrate.py`: `next` takes an optional `change`. `next_version(cwd, change)`, named → that version, and `unready` halts as
today; a name that is not open → `next: <change> · not open`, exit 1. Bare → the lowest id `unready` passes; none passes →
the lowest id's line, exit 1, as today. `unready` adds, after the boxes: each id of the proposal's `after:` that
`_shipped(cwd, change, id)` denies → `after <id>`. A named version whose merge is open with its note is ready, since a
dependent's merge opens before its build; a bare `next` keeps to `unready`, so it takes no unsettled dependent. Every
hand-over names the version — the note line, `mf-ship` Step 4, both `mf-release` way-outs — so the merge settled is the one
committed when several versions halt with a note. The commit of a version with an unticked phase ends
`Next: /mf-ship, in the primary.`, since its build comes next.

`skills/mf-integrate/SKILL.md`:

- The description: "pick the lowest-id open version" → "take the named version, or the lowest-id ready one".
- The diagram's first line: `next version (the named id, or the lowest ready id) ─▶ ready? ─ no ─▶ halt, naming it`.
- `## Parameters`, before → after: "None. The current directory" → a table row `| `change-id` | no | the version to merge;
  `mf-ship` and every hand-over name it |`, then "The current directory".
- Step 2: "Run the script's `next`, with `<change-id>` when given."; the exit-1 row: "**halt**, copying the line: the named
  version is not ready, or none is". **Ready** adds "and every `after:` id in its tree", and the named version with an open
  merge and its note.
- `## Never`: the "Never skip ahead" line goes.

### D6

`I17`, in both contract tables, the change-must column: "name in `after:` only open versions with a lower id, each one's
archive folder in `HEAD` before its build". `mf-cut-change`'s column: "Step 1, for each `after` id; reading `proposal.md`".
`mf-build`'s column: "yes — the archive folder". `mf-build` Step 1 adds:

> - **`I17`** — for each id in `proposal.md`'s `after:`, `git cat-file -e HEAD:openspec/changes/archive/<id>` exits 0.

`mf-release`, precondition 10, the whole item, after:

> 10. **Its dependencies have shipped** (`I17`) — for each id in `proposal.md`'s `after:`,
>     `git cat-file -e HEAD:openspec/changes/archive/<id>` exits 0. Else → halt, naming the id.

`I10`, both tables, after "every file and symbol `design.md` names exists": ", or the design of an `after:` change adds it".
In `mf-cut-change`'s column: "checking each one in Step 3; an `after:` change's design read with `git show <id>:…`".

`I9`, both tables, after "A MODIFIED title matches an existing requirement exactly": ", or the delta of an `after:` change
adds it". In `mf-cut-change`'s column, added: "; an `after:` change's delta read with `git show <id>:…`". The default branch
changed that title, so the dependent's merge stops at `integrate.py delta` for the person, per [D3](#d3).

`mf-cut-change`'s diagram and Step 8 say `I17` where they say `I16`.

### D7

`mf-cut-change`:

- Step 1 adds: "each `after` id is an open version, listed by `git branch --no-merged <default-branch> --list '[0-9]*'`,
  and its number is lower than `change-id`'s."
- Step 6 adds: "A version cut with `after` also lists them: `after: [0047-x]`."
- Step 11, the last line: "The last line: `Next: /mf-ship, in the primary.` when root `AGENTS.md` declares `Worktrees:`, else
  `Next: /mf-build <change-id>, in a fresh session.` Then stop."

`mf-plan`, the *parallel with* row, "a pair touching a file in common is proposed in an order, naming the file" → "a pair
touching a file in common is warned of, naming the file, with `after:` suggested when one needs the other's code".

`mf-ship`, the description: "and release each in cut order" → "and release each as it is ready". The diagram, after:

```
preconditions ─▶ status ─▶ every open version at a halt stage or waiting? ─ yes ─▶ halt, no worker
                    │ no
                  probe worker ─▶ check probe
                    │
  each version, in parallel: wait for its after: ─▶ build ─▶ converge
      a halt stops only its version, and blocks what names it; a crash stops the run
                    │  ready, one at a time
  integrate ─▶ converge (catch-up) ─▶ release, by its stage
                    │  every thread joined
                  done
```

Step 4: "`halted <ids> · held <ids> · released <tags>`" → "`halted <ids> · blocked <ids> · released <tags>`".

### D8

`docs/decisions.md`:

- **D20**, the title: "numbered in ship order" → "numbered in cut order". The bold paragraph: "; versions ship in cut order;
  a version" → "; a version".
- **D44**, the bold paragraph: ", and versions ship in cut order. Every" → ". Every".
- **D45**, the bold paragraph: "into the lowest-id open version's worktree" → "into a version's worktree". Add to the end of
  the paragraph: "`conduct.py` alone merges it into a dependent's cut-only branch, which cannot conflict in git: it runs
  `integrate.py delta` on the open merge, commits when that passes, and else leaves the merge open with its note."
- **D47**, the bold paragraph: "then integrates, runs the catch-up round and releases each in cut order with `merge=yes`" →
  "then integrates, runs the catch-up round and releases each as it is ready, one at a time, with `merge=yes`"; and "a failed
  check halts its version, a halt holds every version behind it at the merge, a failed probe halts the run" → "a failed check
  halts its version, a halt blocks only what names it in `after:`, a failed probe halts the run".

## Tests

Fake-worker tests in `tests/test_conduct.py` (`T1`: the lowest layer that reaches a run) and `tests/test_integrate.py`.

| layer | at cut | added | removed | proof |
|---|---:|---:|---:|---|
| Unit test functions | 76 | 2 | 0 | `uv run pytest --collect-only -q \| tail -1` prints `76 tests collected` at the cut, `78 tests collected` after |
| Integration tests | 0 | 0 | 0 | — |
| End-to-end runs | 0 | 0 | 0 | — |

`T2`: no test reaches a dependent's wait or a blocked chain, so each is a new test.

| test | holds |
|---|---|
| `test_after_waits_for_its_dependency` | `status` prints `0002-marks · waiting`; a run exits 0; `release 0001-todo` before `build 0002-marks` in the calls; `chore(integrate): merge main into 0002-marks` in that branch's log; both tagged; a delta on a requirement the dependency changed halts `integrating` with no build, the merge open and a note naming both changes, a re-run halts again, and a settled merge builds; a planted `post-commit` hook fires on a worker's commit and not on the conductor's merge; a crash of `integrate.py delta` halts the version with no build and the merge open, and a re-run commits it |
| `test_a_halted_dependency_blocks_a_chain` | with `liar-0001-todo`, `0002-marks` after it and `0003-more` after `0002-marks`: no `build 0002-marks` or `build 0003-more` call; each logs `blocked — by <id>`; the last line `… · run · halt — halted 0001-todo · blocked 0002-marks 0003-more · released none`; `report` ends their lines ` · blocked by <id>`; the same chain on a `**HUMAN` phase starts no worker, with no probe; a mutual `after:` and a self-reference block under a bounded subprocess while a free version ships; `after-self-0001-todo` halts on `waiting` while `0002-marks` ships |

Tests renamed and rewritten, in place:

| test | becomes | holds |
|---|---|---|
| `test_run_ships_two_versions_in_cut_order` | `test_a_ready_version_ships_past_a_slow_one` | with `slow-0001-todo`: `release 0002-marks` before `release 0001-todo`; `integrate 0001-todo` and `converge 0001-todo` between them; `0002-marks` tagged `v0.1.0`, `0001-todo` `v0.2.0`; the rest of its log and report steps |
| `test_an_earlier_version_halts_and_the_later_is_held` | `test_a_later_version_ships_past_a_halted_one` | with `liar-0001-todo`: `release 0002-marks` called; the last line `… · run · halt — halted 0001-todo · blocked none · released v0.1.0` |
| `test_next_picks_the_lowest_open_id_and_halts_on_an_unready_one` | `test_next_picks_the_named_or_the_lowest_ready_id` | bare `next` passes over `009-early`, unticked, to `0010-later`; `next 009-early` exits 1, naming it; `next 7-fix-login` is `not open`; an `after:` id missing → `not ready — after <id>`; an open merge with its note is ready by name, and a bare `next` passes over it |

Tests edited:

| test | edit |
|---|---|
| `test_a_later_version_halts_and_the_earlier_ships` | runs with `slow-0001-todo` too, so its `halt` line stays before the earlier's `spawn — release` |
| `test_run_halts_on_a_human_phase` | `release 0002-marks` called, and the last line `… · halted 0001-todo · blocked none · released v0.1.0` |
| `test_run_halts_on_a_timeout`, `test_run_halts_when_a_worker_claims_what_disk_does_not_show`, the crash step | `held none` → `blocked none` |

`_version` in `tests/test_conduct.py` gains `after: str = ""`, written as an `after:` line. `_primary` sets the repo's
`user.name`, `user.email` and `commit.gpgsign`, since `conduct.py` now commits. `_fake` gains `slow-<change>`, a build that
sleeps 2 seconds, and `after-self-<change>`, a build that adds its own id to `after:`, and its `integrate` takes the change
the prompt names. No test is deleted or merged.

## Dependencies

None.

## Risks / Trade-offs

- **A release lands while another version converges** → in MF's own repo a worker may read a newer skill mid-station.
  Target repos are unaffected. It already happens at catch-up.
- **`v0.42.0` can come from a higher id than `v0.43.0`** → the number follows the merge, and the id stays the identity.
- **A dependent's design goes stale** → it is written before its dependency's code exists. The build halts, as it should.
- **The longest version catches up last** → its catch-up holds the lock, and has its own count.
- **`next` bare skips a halted version** → that is the rule, by hand and in a run.

## Migration Plan

```
1 the cut and I17 ─▶ 2 the merge side ─▶ 3 the conductor ─▶ 4 the record ─▶ release
```

Each phase ends on a green gate. Nothing is irreversible, and no version is open when this one lands. The live proof of
the order is the next run with more than one version.

## Verdict

Ready to build. Acceptance: a ready version ships past a slow one; a halted one blocks only what names it; `after:` waits,
merges the default branch and builds; a chain blocks; `cut order` is gone from `docs/` and `skills/`.
