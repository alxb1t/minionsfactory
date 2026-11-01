# Reliability paydown — design

What makes a Claude run safe on a real project, and the controls a person needs. Verdict at the end: ready to build.

## Context

- `_unpushed` returns the default branch when it is ahead of `origin`, and `Run.push_left` pushes it
  (`skills/mf-ship/scripts/conduct.py`), so a person's own commit on `main` goes too.
- `_release_tip` re-enters a release only when `_release_died` says so, and neither reads a flag or a person's refusal.
- `NO_HOOKS` covers the conductor's git alone. A worker's `git commit` runs a repo's hooks.
- `CONFIG_PLAIN` refuses `core.hookspath`. Measured: all 10 repositories the vault names pass today, so that is a future stop.
- `_refuse_origin` reads `mf-ship.localorigin`, and only `tests/test_conduct.py`'s `_allow_origin` helper sets it.
- `mf-converge`'s fixer ran in the background when `claude -p` exited 0 at 10m18s, and took the fixer with it.
- Measured with `uv run pytest -q --durations=12`: 169s; `test_after_waits_for_its_dependency` 25.4s,
  `test_a_rerun_recovers_a_dead_release` 23.3s, `test_an_include_changed_on_the_branch_halts` 13.2s. `_fake` lives in the test
  file, so every fake worker imports pytest.

## Goals / Non-Goals

**Goals:** a run cannot push what a person did not release; a person's stop stands through a death; a person can end a run
and grant a round with one command; resume has met a real death.

**Non-Goals:** the hostile-worker cards; a run that waits out a limit; conflict resolve.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | A run pushes only merges of tagged releases | a person's commit on `main` is theirs | pushing what `main` holds |
| [D2](#d2) | A stop survives a death | a person's no stays a no | re-entering on a death alone |
| [D3](#d3) | No hook runs in a run, set through git's environment | one gate, no hidden checks; a hook is repo code | hooks left to the repo |
| [D4](#d4) | `mf-ship.localorigin` goes, and the allowed keys grow | no repository needs a local `origin` | recording the setting |
| [D5](#d5) | `conduct.py stop` | stopping took hand commands | killing by hand |
| [D6](#d6) | `conduct.py grant` | an extra round took a hand-written prompt | a higher cap |
| [D7](#d7) | A run stops on an unlinked skill | `mf-build` resolves skills from the installed package | a release that installs |
| [D8](#d8) | Converge stays in the foreground | a host can kill background work when a turn ends | a resume alone |
| [D9](#d9) | The fake worker leaves the test file | every fake worker imports pytest | fewer run tests |
| [D10](#d10) | A drill kills real workers, in a script | fake workers cannot prove a real death | a `**HUMAN` phase |
| [D11](#d11) | The drift cards, in one sweep | each is one line | a card at a time |

### D1

`_unpushed` opens, once `origin` is known and the config is refused:

```python
default = default_branch(primary)
ahead = f"origin/{default}..{default}"
for sha in _git(primary, "rev-list", "--first-parent", ahead).split():
    if not _merges_a_release(primary, sha):
        raise Stop(1, f"conduct: halt — {default} holds {sha[:7]}, not a release")
```

`_release_merge(primary, tip)` is true when a `TAG`-shaped tag points at `tip`, and its subject is `chore(release): <tag>`.
`_merges_a_release(primary, sha)` is true when `sha` has two parents, the second passes `_release_merge`, and `sha^{tree}` is
that parent's: `mf-release` Step 5.3's check, so a merge it refused stays home. A `TAG`-shaped tag `origin` lacks halts the same
way, naming the tag, unless its commit's subject is `chore(release): <tag>`.
`Run.push_left` already turns that `Stop` into a `run` halt. `status` prints it.

### D2

`_release_tip`: a `.minions/release/<change>.held` file → `released`, naming the mark. `mf-release`:

- Step 5, a person's anything but yes: "write `.minions/release/<change-id>.held` holding the reason"; a yes deletes it.
- `## A resumed release`, the first bullet, adds before "Then go to Step 5": "Read the preamble against the archived delta, as
  Step 2 does. Under `merge=yes`, a flag → **halt**, before Step 5; by hand, name it beside the ask." A hand release is the way
  out the halt names, so it reads the flag and asks.

### D3

```python
HOOKS_OFF = (
    "GIT_CONFIG_COUNT=2",
    *("GIT_CONFIG_KEY_0=core.hooksPath", "GIT_CONFIG_VALUE_0=/dev/null"),
    *("GIT_CONFIG_KEY_1=core.fsmonitor", "GIT_CONFIG_VALUE_1=false"),
)
```

`argv` starts both executors through `env`, `*HOOKS_OFF` first, so `claude` joins Codex there. `make gate` runs inside a worker,
and no hook sits in it. `AGENTS.md`'s template stays silent: a repo's hook is simply not run.

### D4

`CONFIG_PLAIN` gains `core\.hookspath`. `lfs\.repositoryformatversion` stays off it: LFS uploads from a `pre-push` hook, D3 turns
hooks off, and a push would then send pointers with no objects, so the key's halt stands until a run uploads, and an `lfs.*` or
`filter.lfs.*` key's halt says keep it and release by hand, not move or remove it. `LOCAL_ORIGIN`
goes, and `_refuse_origin` halts on any URL `NETWORK_URL` refuses. A fake worker's fixtures use a local `origin`, so `_refuse_origin` returns at once when
`MF_SHIP_AGENT` is set: a worker cannot set the conductor's environment. `_allow_origin` in `tests/test_conduct.py` goes.

### D5

`run` writes the conductor's `ps -o lstart=` to `active/start`, beside `active/pid`. `_conductor(active)` returns the pid while it
is above 1 and keeps that start time, else None; `_claim` reads None as `stale`. A reused number, 0 and -1 are then no run.

`_ps` fixes `TZ` and `LC_ALL`, since `lstart` follows both and a run outlives a clock change. `_started(pid)` reads the start
time, and a process `ps` cannot read that `kill -0` still finds stops with exit 2 in `status`, `run`, `stop` and `_clear`: a
failed read is not a stale claim. `run` stops the same way when it cannot read its own, before it clears or claims anything.

`conduct.py stop`: `_conductor` None → `stop: none — no run is live`, exit 0, and the claim stays. Else SIGKILL that pid, first,
so it spawns nothing more; `_clear` the groups; append `run · halt — stopped by the person` to the newest run log; print the log.
`verify_log` passes unpaired spawns when the last event's detail is that text. Q1's order is reversed, conductor first, for that
reason. When `_clear` stops, `stop` still appends the line, then exits 2 naming the group, the claim kept: the conductor is
dead, so a second `stop` could not write it.

`_clear` stops with exit 2, naming the group and keeping the claim, when a group keeps its start time and its leader names no
executor, after killing the groups it can: a launcher's `node` is such a leader, and it may be a live worker. `run` clears before
it detaches, so that exit reaches `mf-ship` Step 3, which halts on it, and `status` says a run may stop there.

`skills/mf-ship/SKILL.md`, `## Parameters`, the table:

| form | does |
|---|---|
| bare | Steps 1–4 |
| `stop` | runs `conduct.py stop`, reports it, and stops |
| `grant <change-id>` | Step 1, then `conduct.py grant <change-id> --executor <executor>`, then Step 4 |

### D6

`conduct.py grant <change> --executor <executor>`: `stage_of` is `converge-halted`, and the halt holds `cap reached`, else exit 2,
naming the stage. It writes `.minions/grants/<change>`, then starts a run as `run --detach` does.

`stage_of`: a grant file beside a cap halt → `("converge", "granted")`. `advance`: a grant file at `converge` → the tier clause
gains ` and grant=yes`, and the file is deleted before the spawn, so one spend.

`skills/mf-converge/SKILL.md`, a section before `## Resuming a run`:

```markdown
## A granted round

`grant=yes`, from `mf-ship grant`: the person's one more round past the cap. Open a run marked `· grant`, naming it in its
first event. Send the open blocking findings to a fresh Step 6 fixer by id, then verify in one Step 7 round. Both `clean` →
Step 9, never Step 8. A blocker left → halt with `cap reached`.
```

### D7

`preconditions` calls `_unlinked(executor)` for the run's executor, and `ship` for each other. It lists `mf-*` directories beside
`Path(__file__).resolve().parents[1]`, and looks in `~/.claude/skills` for `claude`, `~/.agents/skills` for `codex`. Any missing →
`Stop(2, f"run: cannot run — {name} is not linked; make install-skills")`. It returns nothing when `MF_SHIP_AGENT` is set.

### D8

`skills/mf-converge/SKILL.md`, the `## The tier and the workers` section, adds: "Dispatch in the foreground, and wait: never end
your turn with a worker running. A host can end its background work with your turn." Step 6 names the same.

### D9

`_fake`, and what it alone needs, moves to `tests/fake_worker.py`, importing no pytest. `fake` points `MF_SHIP_AGENT` at it.

The bar: `uv run pytest -q --durations=5` measured before and after, in `evidence/gate.md`. Below 169s is the aim. A test past 20s
after it is named there, with its reason.

### D10

`tests/drill_resume.py`, a stdlib `uv` script no gate runs. It works in `../mf_resume_probe/`, a repo with `Worktrees: ../`, a
one-line gate, no `origin`, and one cut change with its phase ticked, at stage `converge`.

1. `conduct.py run --executor claude` in the background. Poll the status log for `fan-out`.
2. SIGKILL the converge worker's group, from the claim. The run halts, naming the exit.
3. `conduct.py run` again, and wait. It exits 0.
4. Assert: one `## Run` heading, no finished round repeated, `done` in the log, the change released.
5. A second change, the same to its `fan-out`, then SIGKILL the conductor. `status` reads `run · stale`.
6. `conduct.py run` clears it, kills the orphan, and ends on `done`.

It prints one line per drill, and the build writes them to `evidence/drill.md`. The probe is deleted at its end.

The first run, read from its worker logs: both resumes worked, the re-run continuing at the fan-out. The conductor drill then
failed because a review subagent's shell variable was denied, and review gave up. `SHELL_RULES` reaches the converge worker
and stops there, so it gains: "Give these rules, word for word, to every subagent you start." The status log's later times look
impossible because that worker invented them, so a drill asserts nothing about times.

### D11

| card | edit |
|---|---|
| `0038·N2` | `CHANGELOG.md`: "per its design's D7" → "per 0034's D7" |
| `0044·R12` | closed by a line in this CHANGELOG's phase 1 entry: the archive is frozen |
| `0047·S3` | `_pushed` reads `ls-remote`'s lines as pairs, and passes only on `ref` or `ref^{}` |
| `0048·R8`, `0050·R3`, `0050·S4` | `THREAT_MODEL.md`, *Known gaps*, after: "Carded in `.minions/backlog.md`, accepted until paid down: `0049·S5`, `0049·S7`, `0049·R15`, `0050·R5`, `0050·R6`, `0050·R11`, `0050·S2`, `0050·S3`, `0050·S7`, `0034·R9`. D47 accepts `Ship tools:`.", then a line each on what stays of `0049·S5` and `0049·R15` |
| `0049·R6` | `## A resumed release`: "go to Step 4.6, then Step 5" |
| `0049·R7` | `## Resuming a run`: `start` → Step 2; `pickup` with `none` → Step 9 |
| `0049·R8` | `_clear`: `ProcessLookupError` stays silent; any other refusal stops the run, and so does a group [D5](#d5) cannot name |
| `0049·R9` | `dies-integrate` in `tests/fake_worker.py`, and a step in `test_a_rerun_recovers_a_dead_release` |
| `0049·R10` | `mf-ship` Step 3: missing `active` and a new `run: done` or `run: halt` line in `detached.log` → Step 4 |
| `0049·R11` | `status`'s help: "the claim, what is unpushed, and each open version's stage" |
| `0049·R13` | D47: "only a stage left in `HALTS`, a git config key or `origin` URL the run refuses, a default-branch commit or version tag no release made, a claimed group it cannot kill, or a precondition it stops on, a skill with no link among them, needs the person" |
| `0050·R1` | `test_a_station_runs_on_its_executor` spies on `argv`, and asserts the executor per station |
| `0050·R2` | D11, and `AGENTS.md`: "Workers follow the host, or the models file's `executor`" |
| `0050·R4` | `mf-cut-change`'s models template: `# executor = "codex"`, commented out |
| `0050·R9` | `_points_back` keeps a path only when the entry's `HEAD` names the listed branch |
| `0049·R16`, `S10` | [D4](#d4) |
| `0049·S4`, `S8` | [D1](#d1), [D2](#d2) |

Narrowed, and left open in *Known gaps*: `0049·S5`, whose reuse route `_clear`'s `ps -o comm=` test and [D5](#d5) close while a
worker can still write the claim; `0049·R15`, whose `core.hookspath` route [D4](#d4) closes while an LFS key still halts.

## Tests

Fake-worker tests in `tests/test_conduct.py` (`T1`). `T2`: no test reaches these states.

| layer | at cut | added | removed | proof |
|---|---:|---:|---:|---|
| Unit test functions | 86 | 6 | 0 | `uv run pytest --collect-only -q \| tail -1` prints `86 tests collected` at the cut, `92 tests collected` after |
| Integration tests | 0 | 0 | 0 | — |
| End-to-end runs | 0 | 0 | 0 | — |

| test | holds |
|---|---|
| `test_a_run_pushes_only_tagged_merges` | a bare `origin`: a local commit on `main`, a release's merge with another tree, or a version tag on no release of that name halts naming it, nothing pushed; a release's merge is pushed |
| `test_a_stop_survives_a_death` | `dies-release-tag` with a `.held` mark reads `released`, and no merge happens |
| `test_no_hook_runs_in_a_worker` | a `pre-commit` hook's marker stays absent after a fake worker commits under `argv`'s environment; `core.hookspath` in a repo's config does not halt, and `lfs.repositoryformatversion` does, its halt naming a hand release |
| `test_stop_ends_a_live_run` | a pid at or below 1, or one with another start time, is no run and nothing is signalled; a running conductor `ps` cannot read exits 2 and signals nothing, and a changed `TZ` still reads `live`; a sleeping worker's group is gone, the last line is the stop, the claim is gone, `log --verify` exits 0; a group it cannot end exits 2 with the last line written and the claim kept |
| `test_a_grant_buys_one_round` | refused off the cap; a granted run spawns converge with `grant=yes`, and a second spends nothing |
| `test_a_missing_skill_stops_a_run` | a scratch `HOME` with one link gone: exit 2, naming it |

Tests edited: `test_a_rerun_recovers_a_dead_release`, `test_a_station_runs_on_its_executor`, `test_a_stale_claim_is_cleared`,
`test_a_worker_carries_the_allowlist_and_a_denial_is_named` for `env`, and every test using `_allow_origin`. No test is deleted or
merged. `_fake` moves with its modes intact.

## Dependencies

None.

## Risks / Trade-offs

- **`S4` halts a person who commits to `main` by hand** → that is the rule, and the halt names the commit. A version tag of
  theirs halts the same way, until they push or delete it.
- **A real repo's hooks stop running in a run** → the gate must hold what they enforced.
- **An LFS repo whose key is gone passes the config check** → its push uploads nothing, so a person does not remove the key to
  get a run through, and the halt says so; `0049·R15` stays open for it.
- **Liveness rests on `ps`** → a read that fails on a running process exits 2, so a person waits on a broken `ps` rather than a
  second conductor starting beside the first.
- **The size** → five phases on recovery code, so converge may need a grant. The drill runs before converge, so it can fail first.
- **The drill spends Claude tokens** → two short converges on a one-line change.
- **`git`'s environment overrides** → they need git 2.31 or later.

## Migration Plan

```
1 drift sweep ─▶ 2 what a run may do ─▶ 3 the features ─▶ 4 gate speed ─▶ 5 the drill ─▶ release
```

Each phase ends on a green gate. Nothing is irreversible.

## Verdict

Ready to build. Acceptance: a person's commit is never pushed; a stop survives a death; no hook runs; `stop` and `grant` work;
a real worker and a real conductor die and a re-run finishes.
