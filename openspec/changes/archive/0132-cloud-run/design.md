# Cloud run — design

A run's start brings `origin`'s default branch and the tags its releases left onto the machine, a machine setting says whether the run pushes tags, the config guard allows `gc.auto`, and a missing Codex falls its checkers back to Claude. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

`skills/mf-ship/scripts/conduct.py` pushes what a release left, at a run's start and after each release, from `_unpushed` through `Run.push_left`. A cloud session halts there on a refused tag push, a `gc.auto` key, a stale default branch and a missing Codex, each read in a probe. This change handles each on the conductor's side; the session's own setup — signing off, MF installed at its tag, the poll that keeps the VM up — stays the session's.

**after** [0131-linux-runner](../0131-linux-runner/design.md): a run stands on Linux under `bwrap`. This change reads none of its code. Both edit `skills/mf-ship/SKILL.md`, `docs/decisions.md` and `THREAT_MODEL.md` at other spans, and `conduct.py` at other functions (`preconditions` is theirs).

```
a run's start (Run.ship)
  push_left ──▶ _unpushed(first_read, start)
                  ls-remote origin ──▶ base = origin's default tip
                  [start] fetch base if the primary lacks it ─ D3
                  [start] fast-forward the local default      ─ D3
                  [start] make the tag of each release commit base holds that has none ─ D2
                  found = default branch, then tags unless `tags = false` ─ D1
```

## Goals / Non-Goals

- **Goals:** a release lands on `origin` with no tag push where the machine sets `tags = false`; a fresh clone numbers its next version right; a stale default branch is brought up; `gc.auto` does not halt; a plan with Codex checkers runs where Codex is not installed.
- **Non-Goals:** commit signing, the install at a tag, the poll, attribution, the record coming home, a Codex station in the cloud. See [the proposal](proposal.md#not-in-this-change).

## Decisions

`D<n>` here is the brief's `Q<n>` for `D1`–`D5`: `D1` and `D2` are `Q12` and `Q19`, `D3` is `Q14`, `D4` is `Q13`, `D5` is `Q15`. `D6`–`D8` state scope and the plan's close, with no task.

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `tags = false` under `[push]` in `ship.toml`, read by the cap's reader: a run on that machine pushes no tag and halts on none; a release's check passes with its tag on no remote; `status` says so. A value that is neither `true` nor `false` stops the run with exit 2 | the cloud's proxy refuses a tag push, and the setting is a fact of the machine, as the cap is | a switch in `AGENTS.md` or in `.minions/`: a worker writes both |
| [D2](#d2) | A run's start, on any machine, makes the local tag of each release commit `origin`'s default branch holds that has none, annotated as the release makes it, and pushes it where the machine pushes tags. Only a commit `origin`'s default already holds, in the shape the push guard asks of a release, gets one | a fresh cloud session then numbers its next version right, and the MacBook's next run pushes the cloud's tags with no hand step; the tag rests on what `origin` accepted, not on a worker's commit | a tag made by the release's worker for the cloud: the worker pushes none and the proxy refuses it anyway |
| [D3](#d3) | A run's start fetches `origin`'s default branch, when the primary lacks its tip, through the one door for remote git, and fast-forwards the local default branch: only where it is behind; equal, ahead and diverged leave it; never a merge. `origin` out of reach is a wait, as a push's is | a stale default passes today, versions are cut from it and the release's push is rejected | a fetch in the primary's own git, which reads the repo's config ([D51](../../../docs/decisions.md#d51--a-worker-runs-in-an-os-sandbox-and-no-worker-pushes)); a merge of a diverged branch |
| [D4](#d4) | `gc.auto` joins the keys the config guard allows | the cloud writes it into every clone; a number names no program | a halt the person clears by hand each session |
| [D5](#d5) | Where Codex is not on `PATH`, a checker a plan gives to Codex runs on Claude, as on a usage limit, and the run says so once; a station on Codex still halts | a brief planned with Codex checkers runs in the cloud unchanged | a halt at the start; a Codex stand-in |
| [D6](#d6) | Commit signing stays the session's, a git setting. Cloud commits are unsigned. Left to a later version: MF's own setup script and install, the session's URL in commit trailers, the run's record coming home | the cloud signs through a loopback service the worker's sandbox refuses; each of the rest needs what probe 4 shows, or the state layout | a loopback hole in the sandbox |
| [D7](#d7) | A minor, built on Opus 5.5 high with both Codex checkers, chained `after: 0131-linux-runner` | it edits the push path and extends the reader `0129-queue-cap` added | — |
| [D8](#d8) | The table is confirmed, and this version is queued when `0129-queue-cap` is released | the person, 2026-11-16 | — |

### D1

`conduct.py` gains `_ship_file() -> tuple[Path, dict[str, Any]]`, which holds the read `_cap` makes today: the path under `$XDG_CONFIG_HOME/minionsfactory/`, the parsed data or an empty dict for no file, `Stop(2, f"{path}: {error}")` for a file it cannot read. `_cap` calls it and keeps its checks. `_pushes_tags() -> bool` calls it too: no `[push]` table and no `tags` key give `True`, a `bool` gives itself, any other value raises a `Stop` with code 2 that names the file and says `tags` is not true or false.

`run()` reads `tags = _pushes_tags()` beside `cap = _cap()`, and sets `conductor.tags = tags` beside `conductor.cap = cap`; `Run.tags` is `True` until then. With `tags` false:

- `_unpushed` and `_local_releases` take `push_tags: bool = True`, a name that leaves their own `tags` variable alone; false drops the tag loop of one and the tag names of the other, so the push, the close's `unpushed` line and the offline list name the default branch alone.
- `Run.advance` asks the release check `ask(True, self.offline or not self.tags)`: `offline` already skips the check that the tag is on `origin`, which no tag can meet here.
- `status` calls `_unpushed(primary, push_tags=_pushes_tags())` and adds the line `run · tags — this machine pushes none`.

### D2

`_release_commits(primary, base) -> dict[str, str]` returns `{tag: commit}` for each first-parent merge of `base` whose second parent has the subject `chore(release): <tag>`, `<tag>` a full match of `TAG`, and whose tree equals that parent's tree: the shape `_merges_a_release` asks, read through `_history` so no worker-written ref reaches it. `_make_tags(primary, base) -> list[str]` runs `git tag -a -m <tag> <tag> <commit>` for each entry whose `refs/tags/<tag>` does not exist, and returns the tags made. A tag that exists, wherever it points, is left as it is; the push guard names it, as today, if it is a stray.

A commit that `origin`'s default branch lacks gets none: the walk starts at `base`, the tip `ls-remote` lists. `git tag` needs an identity; where it fails, `_git` raises `Stop(2, …)` and `push_left` halts the run with git's line.

`_unpushed` calls `_make_tags` under `first_read and start`, after `_close_releases` and before it reads `_release_tags`. The made tags are then local tags on commits that are ancestors of `base`, and the loop that already finds a tag `origin` lacks pushes them: `_release_merge` holds, and `commit not in released and not _history_ancestor(primary, commit, base)` is false.

### D3

`_outside` and `_remote` take `keep: bool = False`. With it, the scratch repo's environment holds `GIT_OBJECT_DIRECTORY` naming the primary's object folder, so what a fetch downloads lands in the primary, while the refs and the config stay the scratch repo's. Git then reads alternates from that folder's own `info/alternates`, so `_outside` writes none for it. `_fetch_default(primary, url, default, base, notes)` is called by `_unpushed` under `first_read and start`, after `base` is read and before the check that the primary holds it:

```
local = the sha of refs/heads/<default>, read in the primary
primary lacks base ──▶ fetch --no-tags --no-write-fetch-head --negotiation-tip=<local sha>
                        -- <url> refs/heads/<default>        (keep=True, PUSH_TIMEOUT)
                        a failure is Unreachable
local is an ancestor of base, not base ──▶ git merge --ff-only <base> in the primary
equal, ahead, diverged ──▶ nothing
```

`notes` collects `fetched <default> <sha7>` and `fast-forwarded <default> to <sha7>`, which `push_left` logs as `run · sync — …`. A diverged branch is left: its push is refused and halts the run as it does today. The `merge --ff-only` runs in the conductor with `NO_HOOKS`, as the conductor's other merges do, and only after `preconditions` found the primary on the default branch with a clean tree.

`push_left` takes no new parameter: `Run.fresh` is `False` until `ship()` sets it around its first `push_left(RETRIES)`, and `push_left` passes `start=self.fresh`. The stand-in of `push_left` in `test_a_push_that_lands_before_origin_flaps_passes` keeps its signature.
Fix note (2026-11-16, S1): the `merge --ff-only` carries `--no-overwrite-ignore`, so an ignored file the incoming tree tracks stays and the start stops.
Fix note (2026-11-16, S2): `_fetch_default` sets `refs/remotes/origin/<default>` to `base`, so integration's guard judges against what `origin` holds.

### D4

`CONFIG_PLAIN` gains `|gc\.auto` after `pull\.(rebase|ff)`. `gc.autodetach` and every other `gc.` key stay off the list.

### D5

`CHECKERS` is the checker tables of `WORKERS` without `FIXER`. `Run.named` leaves `codex` out when `_executor_missing("codex")` and only a station of `CHECKERS`, or the shadow of one, names it, so the start does not probe it and halt. `Run.codex_ready` returns `False` first when `_executor_missing("codex")`, so `checker` falls back to Claude on converge's model and effort, as for a limit. `read_plan` logs `run · codex — not on PATH: a checker a plan gives Codex runs on Claude` the first time it reads a checker table on Codex while Codex is missing; `Run.codex_said` holds that it said so. A station on Codex — a build, a cut, a rescue, the converge conductor, the fixer — still names `codex` and halts at the probe.
Fix note (2026-11-16, R1): `checker` stops a shadow on Codex only for a limit; with Codex missing the shadow falls back to Claude as a checker does.

### D6

A statement of scope, with no task. The session's setup holds `commit.gpgsign false` and the other git settings; the person starts the session.

### D7

The models of this version are `models.toml`'s, not a task.

### D8

A statement of the plan's close, with no task.

## Tests

Each test sits at the lowest layer that can fail. The reader, the tag walk, the fast-forward states and the roster of executors are unit tests over a real git repo or a built `Run`; a run of the conductor against a local bare `origin` with the fake worker holds only what a unit cannot: the order of a start, a release with `tags = false`. No test boots a browser.

| test | file | layer | holds |
|---|---|---|---|
| `test_a_refused_tag_push_halts_the_run` | `tests/test_conduct.py` | e2e | pin: an `origin` hook refuses `refs/tags/*`, the run pushes the default branch and halts `git push origin v0.1.0 failed`; phase 2 adds the `tags = false` step: no halt |
| `test_a_local_default_behind_origin_passes` | `tests/test_conduct.py` | e2e | pin: a local default behind `origin`, its objects held, stays; phase 4 turns it to a fast-forward |
| `test_the_config_guard_refuses_a_gc_key` | `tests/test_conduct.py` | unit | pin: `gc.auto` in the repo's config makes `status` exit 1; phase 5 turns it to `gc.auto` allowed and `gc.autodetach` refused |
| `test_ship_toml_reads_tags` | `tests/test_conduct.py` | unit | no file, no table, no key, `true`, `false`; a string, a number, an unreadable file stop with exit 2 naming the file |
| `test_cap_file_that_is_bad_stops_the_run` | `tests/test_conduct.py` | e2e | extended: a bad `tags` stops `run` with exit 2 before a claim |
| `test_status_says_a_machine_pushes_no_tag` | `tests/test_conduct.py` | unit | `status` with `tags = false` names the default branch alone and prints the line; with none it prints none |
| `test_a_release_with_tags_false_lands_without_its_tag` | `tests/test_conduct.py` | e2e | a version released, its default branch pushed, no tag on `origin`, no halt, the worktree removed, the check passed |
| `test_the_tags_origin_holds_are_made_locally` | `tests/test_conduct.py` | unit | a missing tag made annotated on the release commit; several missing tags each made; a tag that points elsewhere left; a local-only release commit given none; a subject or a tree that is not a release's given none |
| `test_a_start_makes_a_missing_tag_and_pushes_it_where_tags_go` | `tests/test_conduct.py` | e2e | a clone with no tag: the start makes it; with `tags` true it reaches `origin`, with `false` it stays local |
| `test_a_start_fetches_and_fast_forwards_the_default` | `tests/test_conduct.py` | unit | behind with the objects absent, behind with them held, equal, ahead, diverged — a merge made in none; `origin` out of reach is `Unreachable`; the primary's tree follows a fast-forward |
| `test_a_diverged_default_halts_at_the_push` | `tests/test_conduct.py` | e2e | a diverged local default: the run halts as before, the branch unmoved |
| `test_a_checker_on_codex_runs_where_codex_is_missing` | `tests/test_conduct.py` | unit | `named` and `codex_ready` with Codex missing and present; a build, a cut and the fixer on Codex still name it |
| `test_a_codex_checker_falls_back_where_codex_is_not_installed` | `tests/test_conduct.py` | e2e | a run with a conformance checker on Codex and no Codex: it ends 0, the checker on Claude, one `run · codex` line; a build on Codex halts the start |

- **Pins that already stand:** `test_a_tag_alone_starts_one_run` holds that a start pushes a tag left, and `test_a_station_runs_on_its_executor` that a station on a missing Codex halts the start. Neither is edited.
- **Renamed in a later phase:** the pin `test_a_local_default_behind_origin_passes` becomes `test_a_local_default_behind_origin_is_brought_up` in phase 4, and `test_the_config_guard_refuses_a_gc_key` becomes `test_the_config_guard_allows_gc_auto` in phase 5.
- **Counted by** `git diff main --stat -- tests`: the table's rows.
- **End to end:** the rows marked e2e, each a run of the conductor against a local bare `origin` and the fake worker, no browser, so no engines. T1: each is at the lowest layer that fails. T2: the pin tests extend existing starts; `test_a_release_with_tags_false_lands_without_its_tag` is new because no existing test releases a version to a reachable `origin` and judges the tag, and its commit body says so.
- **Runs added:** none by CI; the e2e rows carry the `slow` marker and run in the gate.
- **Removed:** none. The pin tests are edited by their later phases, never deleted.

## Dependencies

None.

## Risks / Trade-offs

- `GIT_OBJECT_DIRECTORY` in the scratch repo is the one new way objects reach the primary; the unit test of [D3](#d3) proves a commit `origin` holds lands in the primary's object store. A git that ignores it would fail that test, not a run.
- The fetch names the local branch's sha in `--negotiation-tip`, the scratch repo holding no ref, so a long history is not downloaded again; a server that ignores it sends more, not less. The fetch's connectivity check, which has no ref to stop at, walks the fetched history: its cost grows with the repository, and a start makes it only when the primary lacks `origin`'s tip.
- The fast-forward updates the primary's tree with the conductor's rights, outside the sandbox, as the conductor's merges into a version's worktree do; the guard has refused every key that names a program before it runs.
- A diverged default branch is no new halt: its push is refused and halts, as today.
- `status` now reads `ship.toml`: a bad file stops it with exit 2, as it stops a run.
- Probe 4 reads what the plan could not: whether the cloud's signing accepts the conductor's own commits, whether the cloud rewrites `.git/config` in a long session, whether a session may clone MF.

## Verdict

Ready to build, in the phases of [tasks](tasks.md): the pin, the setting, the tags, the fetch, the guard and Codex, the record.
