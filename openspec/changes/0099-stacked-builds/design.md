# Stacked builds — design

A dependent stacks on its dependency's built head once that build passes, builds, waits as `stacked`, and converges after
the dependency's release is merged in; a re-plan in the dependency resets it. Conductor code, an integrate rule, a gate
line, a run metric, skill and decision text. Verdict at the end: ready to build.

## Context

Read at `ed7298f`, the brief's own sha and this cut's `HEAD`: every fact citing a path stands. `C` is
`skills/mf-ship/scripts/conduct.py`, `I` is `skills/mf-integrate/scripts/integrate.py`, `T` is `tests/test_conduct.py`, `F` is
`tests/fake_worker.py`. See [the proposal](proposal.md) for why. This change is cut `after: [0098-beside]`, whose design adds
D69 and a `links` argument to `cut()`; nothing here reads `beside:`.

- **F1. `after:` today.** `_after` (`C:447-453`) reads the proposal's `after:`; `_dependencies` (`C:535-538`) reads it from
  the branch. `stage_of` (`C:1197-1258`) prints `waiting, after <ids>` while an id is not on the default branch
  (`C:1227-1233`). `take` (`C:4491-4508`) runs `catch_up`, then `ready` (`C:4357-4373`), which joins each lower dependency's
  whole thread, blocks on one unreleased, and `merge_in`s the default branch; then `advance(version, ("integrate",
  "release"))` (`C:4156-4301`), then the merging pass under `self.merging`. `STUCK` (`C:99`) is `HALTS` and `waiting`.
- **F2. The merge.** `merge_in(tree, change, default)` (`C:4375-4405`) compares the git config once (`C:4383`), merges
  `default` with `--no-commit`, has `settle` (`C:4407-4445`) run `I`'s rules — `CHANGELOG.md`'s on a conflict alone, the
  decisions rule on every merge — runs `I`'s `delta`, and commits `chore(integrate): merge <default> into <change>`
  (`C:4404-4405`). `I`'s rules read `merge-base HEAD MERGE_HEAD` and `MERGE_HEAD` (`I:317-321`), so they take any ref.
- **F3. The changelog rule** (`I:363-380`) keeps `HEAD`'s whole `[Unreleased]` and halts when `MERGE_HEAD` holds entries.
  Probed by reading: a stacked branch's base — the built head — holds the dependency's entries, and `HEAD`'s `[Unreleased]`
  holds them first and the dependent's after. The default branch, once the dependency released, holds them under its release
  heading. Git merges that `CHANGELOG.md` cleanly when the dependency's converge added no entry — the hunks are a release
  heading above the entries and the dependent's lines below them — so the rule never runs and the dependent's entries land
  under the dependency's release. `replay` (`I:696-759`) runs `changelog` on a conflict alone (`I:732-734`).
- **F4. The bases.** The build's gate check and metrics take `git merge-base <default-branch> HEAD`
  (`skills/mf-build/SKILL.md:177-178`, `:226-228`); `mf-simplify`'s range is `<merge-base>..HEAD`
  (`skills/mf-simplify/SKILL.md:33-34`); diff coverage is `--compare-branch=$(DIFF_BASE)`, `DIFF_BASE ?= main` (`Makefile:3`,
  `:21`); CI passes `DIFF_BASE=origin/main` (`.github/workflows/ci.yml:37`). `gate_run.py` keys a record by the tree and
  `make -n gate`'s output, so a base in the recipe line keys it too. `gate_check.py` compares the dry runs of the base and
  head trees (`tests/test_gate_check.py:143-152`).
- **F5. The gates on `after:`.** `I17` (`skills/mf-build/SKILL.md:66`, `:97`; `skills/mf-cut-change/SKILL.md`'s I17 row);
  release precondition 10 (`skills/mf-release/SKILL.md:152`); integrate's Ready (`skills/mf-integrate/SKILL.md:81`; `I`'s
  `unready`, `I:200-230`). Converge's base is the merge-base (`skills/mf-converge/SKILL.md:289`), and the catch-up's
  ancestry rule halts a merge whose second parent is not on the default branch
  (`skills/mf-converge/references/worker.md:115-116`); a stacked version runs no round before its dependency releases, so
  neither meets the stack merge.
- **F6. Amends and resets.** An amend is `docs(<id>): amend the change directory` (`_amends`, `C:952-974`); "changes a
  decision" is computed for a rescue alone — `proposal.md` touched, or `_decisions` (`C:2477-2489`) of `design.md` changed
  (`_amend`, `C:2520-2528`). `reset --hard` and `branch -D` are the conductor's alone (`C:175-178`). `cutting` drops a branch
  past `_config_changed` and `_refuse_config_commands` (`C:4556-4558`).
- **F7. Events and metrics.** `EVENTS` (`C:86-90`) lists every run-log event `verify_log` (`C:2136-2161`) accepts.
  `scripts/metrics/run.py`'s `METRICS` (`:617-655`) maps each run metric; `waits` (`:339-359`) is the pattern for a span of
  events; `metrics/catalogue.toml:323-330` declares `wait-minutes`.
- **F8. Decisions and debt.** D44 (`docs/decisions.md:582-592`) and D45 (`:594-611`) reject rebasing a judged branch; D47
  (`:613-656`); D57 (`:804-819`) lists a change folder's files; D63 (`:393-407`) says "The checkers keep the full plan"
  (`:399`, `0095·R6`). `0050·R5`: `merge_in` compares the config once, above the merge. `THREAT_MODEL.md:166` and `:175` name
  `0050·R5`. D69 is `0098-beside`'s; this change takes D70.

E1's "one catch-up round over what changed between the built head and the release" is E8's round 1: the dependent has no
round before it, and round 1's range starts at the default branch, which holds the dependency's release.

## Goals / Non-Goals

**Goals:** the brief's Acceptance — with the fake hosts, a dependency's build pass merges its built head into the dependent
(`merge_in` of a ref, no agent), the dependent builds, waits as `stacked` in `conduct.py status` until the dependency
releases, and its converge runs round 1 after the merge of the default branch; `stacked-on` holds the built head's sha, the
build's gate check, simplify and diff coverage take it as their base, and the merge back deletes it; `I17` passes on a
stacked-on head; integrate's Ready and release precondition 10 still refuse an unreleased dependency; a decision-changing
amend in the dependency resets the dependent and deletes `stacked-on`; `after-wait-minutes`; `grep -n "### D70"
docs/decisions.md` and `grep -n -i "stacked" THREAT_MODEL.md` print a line; `make gate` green.

**Non-Goals:** stacking on two dependencies; stopping a running build at a re-plan; any reader of `beside:`.

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | A dependent stacks on one unreleased, lower dependency with a built head, no halt, holding the dependent's base; a dependency's stage read past its build wakes it | E1, E8; C1 | polling the disk alone — a test's order would hang on the poll · stacking on two heads · a head lacking the base, which makes a criss-cross merge |
| [D2](#d2) | `merge_in` takes a ref; `Run.stack` writes `stacked-on` and merges the built head with no delta check, committing `chore(stack): …`; `merge_in` compares the config again before its commit | E8, E9; `0050·R5` | a rebase (D44, D45) · a separate merge function · the delta check on a stack merge — a build folds no delta |
| [D3](#d3) | A new stage, `stacked`; `take` loops ready → advance while a version is stacked or sent back; the merge back removes `stacked-on`; a stacked version gets no gate merge | E8 | `stacked` in `STUCK` — a stacked run would start no worker · a separate catch-up round |
| [D4](#d4) | The changelog rule keeps the branch's entries past a stacked base's, and runs on every merge whose base holds `[Unreleased]` entries | E8; C2 | the rule on every clean merge — it would rewrite today's merges and their replays |
| [D5](#d5) | `stacked-on` is the base of the build's gate check and metrics, `mf-simplify`'s range and the gate's diff coverage; `I17` takes it | E9, E10 | `DIFF_BASE` passed by each station — `gate_run.py` takes no argument |
| [D6](#d6) | A decision-changing amend in the dependency past the stacked-on head resets the dependent to its cut commit, read between stations | E3, E11 | killing a running build · a reset on any amend |
| [D7](#d7) | `after-wait-minutes` from the run log's `wait` events | E13 | the time from the cut — it counts the build |
| [D8](#d8) | The record: D70; D44, D45, D47, D57 and D63 edited; the threat model; `mf-ship`'s flow | E12; `0095·R6` | — |

### D1

The **built head** of a version is the commit its `build.done` names while that build stands. A new module function in `C`:

```python
def _built_head(primary: Path, change: str) -> str | None:
    """Return the full sha `build.done`'s `head:` names while that build stands, else None.

    It stands when that commit is the branch's tip or its ancestor, every `## Progress`
    box is ticked at it, and no amend of the change directory past it changes a decision.
    Why: 0099-stacked-builds design D1, D6.
    """
```

It reads `build.done` as `_closed` does (`C:799-809`), resolves the head with `rev-parse -q --verify <head>^{commit}`, checks
`_ancestor(primary, head, "refs/heads/<change>")`, reads `tasks.md` at the head with `_show` and `PROGRESS`, and returns None
when `_replanned(primary, change, head)` ([D6](#d6)).

A new method, `Run.stackable(self, version: Version, unreleased: list[str]) -> str | None`, "Return the built head a
version may stack on, else None", returns it when all hold:

| condition | read |
|---|---|
| one `after:` id is unreleased | `unreleased` holds one id |
| that id is lower than the version's | `_change_number(id) < version.number` |
| the run records no halt for it | `not self.stopped(id)` |
| it has a built head | `_built_head(primary, id)` |
| that head holds the version's base | `_ancestor(primary, <git merge-base default change>, head)` |

A version not yet stacked ([D3](#d3)) stacks on what it returns; else an unreleased dependency blocks it once its thread has
ended, as today. The base rule keeps the stack merge's base the dependent's cut base, so the later merge of the default
branch has one merge-base, the built head (C1).

**The wake.** `Run.__init__` gains `self.built = threading.Condition()`, commented "notified when a version's thread reads its
stage past the build, and when it ends", and `self.ended: set[str] = set()`, the changes whose `take` has returned.
`Run.notify_built()` notifies all under it. `advance` calls it after each stage read other than `build`, `human` and
`waiting`, `stacked` among them, so a chained dependent wakes too. `take` discards its change from `self.ended` under
`self.built` as it starts, and in a `finally` adds it and notifies: a waiter reads a dependency ended when its thread is
gone, not alive, or in `self.ended`. A new method:

```python
def until(
    self, version: Version, dependency: str, threads: dict[str, threading.Thread], stack: bool
) -> None:
    """Wait while the dependency's thread lives; with `stack`, until `stackable` names a head.

    It waits on `self.built`, at most `REJOIN_POLL` a time, and logs `wait — after <id>` once.
    Why: 0099-stacked-builds design D1.
    """
```

`ready` calls `until` in place of `threads[dependency].join()` (`C:4361-4363`), for a version not stacked alone, `stack`
true when one id is unreleased; `until` then asks `self.stackable(version, [dependency])`. At each wake it reads the thread
from `threads` again: a dependency taken back runs in a new one. A built head the version may not stack on keeps it waiting
for the thread's end, as today. The timeout bounds a notify that is lost.

### D2

- **`merge_in(self, tree: Path, change: str, ref: str, stacked: str | None = None)`** — `default` becomes `ref`, merged by
  `git merge -q --no-ff --no-commit <ref>`, passed to `settle` as today. With `stacked`, the dependency's id, it runs no
  `_delta` — a build folds no delta, and the merge back meets what the release folded — and the commit reads
  `chore(stack): merge <stacked> at <ref[:7]> into <change>`; else `chore(integrate): merge <ref> into <change>`, as today.
  Every caller passing the default branch keeps its call. Without the skip, a note on a stack merge would leave a merge whose
  commit fails `_check_integrate`'s default-branch ancestry (`C:1310-1311`).
- **`0050·R5`** — right before its `commit`, `merge_in` runs `_config_changed(self.primary, self.git_state)`, raising it, and
  `_refuse_config_commands(tree)` again; a refusal leaves the merge open, as a delta note does, and a re-run's `merge_in`
  commits it. The docstring names `0050·R5`.
- **`Run.stack(self, tree: Path, change: str, dependency: str, head: str) -> None`** — "Mark a version stacked, then merge
  its dependency's built head in." Writes `f"{head}\n"` to `STACKED_ON = "stacked-on"`, a module constant, through
  `_write_in_change`; runs `merge_in(tree, change, head, dependency)` unless `_ancestor(tree, head, "HEAD")`; logs `(change,
  "stacked", f"on {dependency} at {head[:7]}")`. A merge that halts leaves a file naming no ancestor of `HEAD`, which
  `_stacked_on` reads as none.

### D3

- **`_stacked_on(primary: Path, change: str, tree: Path, unreleased: list[str]) -> str | None`** — the full sha
  `.minions/changes/<change>/stacked-on`'s first word names, when that word fullmatches `[0-9a-f]{40}`, resolves to a commit
  that is an ancestor of the tree's `HEAD`, and holds `openspec/changes/<id>/tasks.md` for each `unreleased` id; else None. A
  file it cannot read is None.
- **`stage_of`** — with `missing` the ids unreleased on the default branch and `lacking` the ids whose archive `HEAD` lacks:
  `missing` non-empty and no `_stacked_on(primary, change, tree, missing)` → `waiting` as today. A version with a
  `_stacked_on` head and `lacking` non-empty goes on to the unticked and closing checks, and built — every box ticked and
  closed as below, or a converge run read — returns `("stacked", f"built on {' '.join(lacking)} at {sha[:7]}: waits for its
  release")`, so a dependency released mid-build still gets its merge back before converge. `stacked` joins no tuple: not
  `HALTS`, not `STUCK`.
- **`_merged_back(tree: Path, done: str, default: str) -> bool`** — "Return whether `HEAD` merges the default branch into the
  head `build.done` names: two parents, the first that head, the second on the default branch." `stage_of`'s closing check
  (`C:1239-1241`) reads a version closed when `_closed` or `_merged_back` holds, so the merge back — the conductor's, or one a
  person commits after a conflict — spawns no second build; `_check_build` stays on `_closed`. No station but `mf-build` and
  `conduct.py` reads `build.done`.
- **`advance`** returns `str | None`: the stage of `stop_at` it stopped at; `stacked` whenever it reads it, whatever
  `stop_at`; `waiting` after a reset ([D6](#d6)), and from no other read — a `waiting` stage read halts as today; else None.
  Before it spawns converge or the release it removes a `stacked-on` that stands, through `_remove_in`.
- **`Run.landed(self, version: Version, threads: dict[str, threading.Thread]) -> bool`** — "Wait while a stacked version's
  dependency thread lives; True to be ready again." Logs `wait — stacked on <id>`, waits on `self.built` at most
  `REJOIN_POLL` a time, re-reading the thread from `threads`; True once the thread ends with the dependency released or a
  reset sent the version back; else `self.block(change, dependency)` and False.
- **`take`**:

  ```python
  self.catch_up(version)
  stop: str | None = "waiting"
  while stop in ("waiting", "stacked"):
      if stop == "stacked" and not self.landed(version, threads):
          return
      if not self.ready(version, threads):
          return
      stop = self.advance(version, ("integrate", "release"))
  if stop is not None and not self.stopped(version.change):
      with self.merging:
          self.advance(version, ())
  ```

- **`ready`**, in order: `unreleased` and `stacked` read; for a version not stacked, `until` per lower dependency with a live
  thread ([D1](#d1)) and `unreleased` read again; a halt returns False. None left → `merge_in` of the default branch as today,
  then, once `HEAD` holds every id's archive, `_remove_in` of `stacked-on`; True. Stacked → True, waiting on no thread, so a
  stacked version re-run before its build builds on. `self.stackable(version, unreleased)` names a head →
  `self.stack(...)`; True. Else block by the first unreleased id; False.
- **`catch_up`** returns at once for a version whose `_stacked_on(primary, change, tree, [])` stands: a gate merge of the
  default branch would give the later merge back two merge-bases.
- **`EVENTS`** gains `wait` and `stacked`, then `reset` with [D6](#d6).

```
cut ─▶ waiting ──(dependency built)──▶ stack merge ─▶ build ─▶ stacked
          │                                                     │
          └──(dependency released)──▶ merge main ◀──(released)─┘
                                          ▼
                                 converge round 1 ─▶ integrate ─▶ release
```

### D4

- **`changelog(tree)`** (`I:363-380`) — with the base's `[Unreleased]` entries, stripped, non-empty: when `HEAD`'s entry lines,
  stripped, begin with the base's entry lines, line for line, those lines are dropped and the rest kept, stripped of leading
  and trailing blank lines; else
  `Stop(1, "changelog: halt — the branch's [Unreleased] entries do not hold the base's")`. A build appends under the
  heading, and a stacked branch stacks before its build, so the base's entries come first. An empty base block keeps today's
  path. The docstring's why cites `0099-stacked-builds design D4`.
- **`unreleased(tree: Path) -> bool`**, new in `I` — "Return whether the open merge's base holds `## [Unreleased]` entries: a
  stacked branch's base." A base with no `CHANGELOG.md` or no heading is False.
- **The callers** — `replay` runs `changelog` when `CHANGELOG.md` is unmerged or `unreleased(scratch)`; `conduct.py`'s `Run`
  loads `self.unreleased = integrate["unreleased"]`, and `settle` runs the `CHANGELOG.md` rule when the path is in `first` or
  `self.unreleased(tree)`. `mf-integrate` runs `changelog` on every merge already
  (`skills/mf-integrate/SKILL.md:106-111`).
- **The stack merge itself** — its base is the dependent's cut base ([D1](#d1)), whose `[Unreleased]` is empty, so the rule
  does not run and git takes the built head's entries.

### D5

- **`Makefile`** — `DIFF_BASE ?= main` becomes, quoted for the build in [tasks](tasks.md):

  ```make
  # A stacked build's base is its dependency's built head: 0099-stacked-builds design D5.
  STACKED_ON = $(shell git rev-parse --verify --quiet "$$(grep -sxE '[0-9a-f]{40}' "$$(git rev-parse --path-format=absolute --git-common-dir)/../.minions/changes/$$(git branch --show-current)/stacked-on")^{commit}")
  DIFF_BASE ?= $(or $(STACKED_ON),main)
  ```

  `grep -x` passes a line of 40 hex digits alone, inside `"$(…)"`, never re-parsed, and the recipe gets only `rev-parse`'s
  output: a sha or nothing. Text such as `--since=…` never reaches `rev-parse`. CI's `DIFF_BASE=origin/main` still overrides.
  In the primary, or a detached tree, no file is found: `main`.
- **`skills/mf-build/SKILL.md:228`** — "where `<base>` is `git merge-base <default-branch> HEAD`" → "where `<base>` is the sha
  `.minions/changes/<change-id>/stacked-on`, the run directory's, names while it stands — a stacked build's — else `git
  merge-base <default-branch> HEAD`". Step 2's item 5 and the resume table already take `<base>` "as in Step 3.5".
- **`I17`**, `skills/mf-build/SKILL.md:97` — append: "Or, while `.minions/changes/<change-id>/stacked-on` stands, `git
  merge-base --is-ancestor <its sha> HEAD` exits 0 and `git cat-file -e <its sha>:openspec/changes/<id>/tasks.md` exits 0."
  The I17 row (`:66`) → "name in `after:` only open versions with a lower id, each one's archive folder in `HEAD` before its
  build, or its change in the head `stacked-on` names" · "yes — the archive folder, or the stacked-on head".
- **`skills/mf-cut-change/SKILL.md`'s I17 row** — "each one's archive folder in `HEAD` before its build" → "each one's archive
  folder in `HEAD` before its build, or its change in the head `stacked-on` names".
- **`skills/mf-simplify/SKILL.md:33-34`** — "The **range** is `<merge-base with the default branch>..HEAD`" → "The **range** is
  `<base>..HEAD`, `<base>` the sha `.minions/changes/<change-id>/stacked-on` names while it stands, else the merge-base with
  the default branch"; the sentence on how the default branch is named stays.
- **Release and integrate stay** (E10): precondition 10 and Ready still need the archive folder.

### D6

- **`_replanned(primary: Path, change: str, since: str) -> bool`** — "Return whether an amend of the change directory past
  `since` on its branch changes a decision." For each commit of `git rev-list --no-merges <since>..refs/heads/<change>` whose
  subject is the amend's: `openspec/changes/<change>/proposal.md` among its `diff-tree` paths, or `_decisions` of `design.md`
  differing between `<sha>^` and `<sha>`, is True.
- **`_cut_commit(tree: Path, change: str) -> str | None`** — the newest commit of `git log --first-parent --format=%H %s
  HEAD` whose subject is `docs(<change>): land the change directory`.
- **`Run.reset_stack(self, version: Version) -> bool`** — "Reset a stacked version whose dependency re-planned past its
  stacked-on head, or left it; True if so." It acts when the version has exactly one unreleased id, a `_stacked_on` head, and
  either `_replanned(primary, dependency, head)` or that head no longer an ancestor of `refs/heads/<dependency>` — the
  dependency was itself reset, so a chain resets with it. Else False. Acting: no cut commit → `Stop(1, f"conduct: halt —
  {change}: no cut commit to reset to")`; else `_config_changed` raised, `_refuse_config_commands(tree)`, `git reset -q --hard
  <cut>`, `_remove_in` of `stacked-on`, and `(change, "reset", f"{dependency} re-planned past {head[:7]}: {left[:7]} →
  {cut[:7]}")`, `left` the `HEAD` it left.
- **Where it is read** — at the top of `advance`'s loop, before the stage read, returning `waiting`; and in `landed`'s wait.
  `ready`'s next `until` then waits for a built head past the amend, which `_built_head`'s re-plan rule holds back.

### D7

- **`Version.after_waits(self) -> Number`** in `scripts/metrics/run.py` — "Return the minutes from each `wait` event of the
  version to its next event, summed; none is 0." Events of the version are `self.events`; a wait with no later event counts
  nothing. `METRICS` gains `"after-wait-minutes": Version.after_waits` after `wait-minutes`.
- **`metrics/catalogue.toml`** — after `wait-minutes`:

  ```toml
  [[metric]]
  id = "after-wait-minutes"
  title = "Time a dependent waits on its after: ids"
  group = "run"
  unit = "minutes"
  better = "lower"
  script = "scripts/metrics/run.py"
  args = ["after-wait-minutes"]
  ```

### D8

D70 is added to `docs/decisions.md` after D47, and `, D70` after `D67` in the map's Repo conventions list:

```markdown
### D70 · A dependent builds on its dependency's built head

**Once a version's one unreleased `after:` dependency passes its build check, with no halt, and its built head holds the
version's base, `conduct.py` merges that head into the version with no agent, writes its sha to
`.minions/changes/<id>/stacked-on`, and the version builds. Built, it waits as `stacked`; once the dependency releases, the
run merges the default branch in, removes `stacked-on`, and converge runs round 1. While `stacked-on` stands, the build's gate
check and metrics, `mf-simplify`'s range and the gate's diff coverage take it as their base. An amend of the dependency's
change directory past that head that changes a decision resets the version to its cut commit; it stacks again on the
dependency's next build.**

- **Why:** a dependent waited through its dependency's converge, about 45 minutes, which rarely changes the code it builds on.
- **Accepts:** a dependent built on code its dependency's converge has not judged — it never converges or releases before
  that converge and release · a reset that drops the dependent's build and any amend of its own · a forged `stacked-on`,
  which narrows the build's gate check and diff coverage alone: the run removes it before converge and the release.
- **Rejected:** rebasing the dependent onto the built head (D44, D45) · stacking on two dependencies, or on a head that lacks
  the dependent's base · stopping a running build at a re-plan.
```

- **D44** — after "Ids are reserved … under its lock (D58)." add: "A stacked dependent takes its dependency's built head by a
  merge ([D70](#d70--a-dependent-builds-on-its-dependencys-built-head))."
- **D45** — "`conduct.py` alone merges it into a cut-only branch — a dependent's, or one the default branch passed before its
  first worker — and into a started one whose base the default branch passed changing its gate." → "… changing its gate, save
  a stacked one; it also merges a dependency's built head into its stacked dependent
  ([D70](#d70--a-dependent-builds-on-its-dependencys-built-head))." And "It settles a conflict in `CHANGELOG.md` or
  `docs/decisions.md` by `integrate.py`'s rules" → "It settles a conflict in `CHANGELOG.md` or `docs/decisions.md`, and a
  stacked branch's `CHANGELOG.md` on any merge, by `integrate.py`'s rules".
- **D47** — "builds and converges every open version in parallel," → "builds and converges every open version in parallel, a
  dependent building on its dependency's built head ([D70](#d70--a-dependent-builds-on-its-dependencys-built-head)),".
- **D57** — "`build.{done,halt,closing,discarded.patch}`," → "`build.{done,halt,closing,discarded.patch}`, `stacked-on`,".
- **D63** (`0095·R6`) — "The checkers keep the full plan" → "Conformance keeps the full plan".
- **`THREAT_MODEL.md`** — a *Trust boundaries* bullet after the mixed-run one: "**A stacked build runs on code no converge has
  judged** ([D70](docs/decisions.md#d70--a-dependent-builds-on-its-dependencys-built-head)): a dependent builds on its
  dependency's built head, and never converges or releases before that dependency's converge and release. A worker can write
  `stacked-on`, which narrows the build's gate check and diff coverage: the gate reads it through `git rev-parse` alone, and the
  conductor removes it before converge and the release, which judge against the default branch." `0050·R5` leaves the
  *Known gaps* opening line, and the config-race gap reads "The config race, what is left: a run's remote calls are out of the
  race, and `merge_in` compares the config again right before its commit; its local `status`, `merge` and `commit` still read
  the repo's config after the refusal."
- **`skills/mf-ship/SKILL.md:22`** — "each version, in parallel: wait for its after: ─▶ build ─▶ converge" → "each version, in
  parallel: wait for its after:'s build ─▶ build, stacked on it ─▶ wait for its release ─▶ converge".
- **The spec** — [the delta](specs/sdd/spec.md); the release folds it.

## Tests

`git grep -c '^def test_' HEAD -- tests/` sums to 278 at the cut; `0098-beside` adds 1, and this change adds 2, so the build
ends at 281. Each other step extends a test that already reaches its state (`T2`), at the lowest layer that holds it (`T1`):
a `Run` method called on a scratch repo, the fake worker for a whole run, `make -n gate` for the recipe. No end-to-end test:
the repo has no browser layer, so no end-to-end run is added.

| test | gains |
|---|---|
| `test_after_waits_for_its_dependency` (`T:838`) | under the new fake mode `hold-converge-0001-todo`, released by `_when_logged` on `" · 0002-marks · wait — stacked on 0001-todo"`; inside the hold, `conduct["status"](root)` prints `0002-marks · stacked`, `stacked-on` holds `0001-todo`'s `build.done` head, and `release 0001-todo` is not called; after the run, `build 0001-todo` < `build 0002-marks` < `release 0001-todo` < `converge 0002-marks` in the calls, `build 0002-marks` called once, `0002-marks`'s log holds `chore(stack): merge 0001-todo at <sha7> into 0002-marks` and `chore(integrate): merge main into 0002-marks`, neither in the hook's file, `stacked-on` is gone, and the run log holds `0002-marks · stacked — on 0001-todo at <sha7>` ([D1](#d1)–[D3](#d3)); its `release`-before-`build` assertion goes, the behaviour it held retired by D70 |
| `test_a_merge_in_refuses_a_planted_hook` (`T:981`) | after `hook.probe.event` and `hook.probe.command` are unset and `held_run.git_state` read again, a step whose `held_run.delta` writes a key into `.git/config` and returns: `merge_in` raises `the local git config changed during the run: .git/config differs`, the merge stays open, and no `chore(integrate)` commit lands (`0050·R5`, [D2](#d2)) |
| `test_a_stacked_dependent_resets_and_merges_back` (new, `T`) | on a scratch repo with a `Run`, `ready` called with no threads: `0001-todo` built, its `CHANGELOG.md` `[Unreleased]` holding `- d1`; `0002-marks` cut as `docs(0002-marks): land the change directory` stacks — `stacked-on`, the `chore(stack)` subject; `0003-more`, naming both, and `0004-late`, cut after a `main` commit the built head lacks, are blocked ([D1](#d1)); a `tasks.md`-only amend of `0001-todo` leaves `reset_stack` False; one touching `proposal.md` makes it True, `HEAD` the cut commit, `stacked-on` gone, the `reset` event logged, and `_built_head` None ([D6](#d6)); a new `build.done` at `0001-todo`'s tip restacks it; `0002-marks` adds `- x1`; `0001-todo` released with `- d1` under `## [0.1.0]`, `ready` merges `main`, `stacked-on` is gone, and `CHANGELOG.md`'s `[Unreleased]` holds `- x1` alone ([D4](#d4)) |
| `test_changelog_keeps_the_branch_entries_above_the_released_sections` (`tests/test_integrate.py:203`) | a stacked base: the base's `[Unreleased]` holds `- d1`, `HEAD`'s `- d1` and `- x1`, the default branch's none: `changelog` keeps `- x1` alone; `HEAD`'s entries lacking `- d1` halt with the rule's message ([D4](#d4)) |
| `test_replay_reproduces_a_rule_settled_merge` (`tests/test_integrate.py:407`) | a stacked branch's clean merge of the default branch, settled by `changelog`, replays `by rule — CHANGELOG.md` ([D4](#d4)) |
| `test_diff_coverage_takes_the_stacked_base` (new, `tests/test_gate_run.py`) | the repo's `Makefile` in a scratch repo with a linked worktree on `0002-marks`, `make` run with `MAKEFLAGS`, `MFLAGS`, `MAKELEVEL` and `DIFF_BASE` dropped from its environment — CI's `make gate DIFF_BASE=origin/main` would pass them in: no `stacked-on` → `make -n gate` prints `--compare-branch=main`; a commit's sha → `--compare-branch=<sha>`; text `x"; touch <a path>; "` → `--compare-branch=main`, and the path is not made ([D5](#d5)) |
| `test_run_metrics_read_the_run_logs` (`tests/test_metric_scripts.py:492`) | `_RUN_B` gains `09:08:30 · 0003-z · wait — after 0001-x` before its `09:09:00` build spawn: `after-wait-minutes` reads `0.5` for `0003-z` and `0` for `0001-x` ([D7](#d7)) |

The existing tests whose dependent would now stack — the code path they hold is the unstacked dependent's — keep it by a
commit of `main.txt` on `main` before the dependent's cut, which its dependency's built head lacks ([D1](#d1)'s base rule),
commented "`main` moves past the dependency's base: the dependent waits unstacked". `main.txt` is no `GATE_FILES` path, and
each dependency holds a commit past its cut, so `catch_up` merges `main` into neither (`C:4462-4489`):

| test | edit |
|---|---|
| `test_a_dependents_delta_halts_as_integrating` (`T:877`) | the `main.txt` commit before `0002-marks`'s cut; `0001-todo` holds its fold commit already |
| `test_a_crashed_integrate_script_halts_and_a_rerun_merges` (`T:947`) | a `build: a first part` commit on `0001-todo`, then the `main.txt` commit, both before `0002-marks`'s cut; its `crash.py` gains `def unreleased(tree):` returning `False`, which `Run` now loads ([D4](#d4)) |
| `_delta_noted` (`T:2466`), for `test_a_supervisor_settles_an_integrate_note` and `test_a_supervisor_settle_outside_the_text_halts` | the `main.txt` commit before `0002-marks`'s cut; `0001-todo` holds its fold commit already |
| `test_a_changed_git_config_halts_a_merge_in` (`T:4415`) | each case runs under `hold-converge-0001-todo`, released by `_when_logged` on `" · 0002-marks · wait — stacked on 0001-todo"`, so the release plants its key after the dependent's build; `"build 0002-marks" not in` → `"converge 0002-marks" not in` |
| `test_a_run_goes_on_while_origin_is_down` (`T:6506`) | the call list becomes: `probe` first, the same six calls as a set, `build 0001-todo` before `build 0002-marks`, and `release 0001-todo` before `converge 0002-marks`; a `main` commit there would read as a commit no release made |

`tests/fake_worker.py`'s converge gains `hold-converge-<change>`, waiting for `FAKE_HOLD` as `hold-<change>` does for a build
(`F:527-530`). No test is deleted or merged.

**Guards.** None: every step goes red before its code, the `0001-x` metric aside, which reads `0` once the metric exists.

## Dependencies

None.

## Risks / Trade-offs

- **A `stacked-on` left past its dependency's release** — a hand-run build or gate there takes the stale base → the run
  removes it at the merge back and before converge and the release; converge's own base is the merge-base whatever stands.
- **A reset drops the dependent's own plan amends** → the `reset` event names the head it left, so a person can recover them
  from it; a re-plan is rare after the build.
- **A notify lost between the alive check and the wait** → the wait's `REJOIN_POLL` timeout bounds it.
- **A dependent cut from a newer default branch than its dependency's built head** → it does not stack, and waits as before:
  a criss-cross merge would give `integrate.py`'s rules two bases.
- **A forged `stacked-on`** → the threat model's new bullet: it narrows the build's own checks alone.
- **`stacked` is new to `report` and `status` readers** → it is a stage like `build`, read by `stage_of` alone.

## Verdict

Ready to build.
