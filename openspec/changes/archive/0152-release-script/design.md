# Release script — design

The release's fixed steps are `release.py`'s, run before and after a worker that only folds. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

A release is a worker's session today: it runs the preconditions, folds the spec delta, moves the change to the archive, cuts the changelog, bumps the version, runs the gate, commits, tags, clears the debt and merges. Every step but the fold and the reads of prose is a fixed command over files and git, and each release that halted did so on one of them: a lock file left out of the commit, a tag move the sandbox denied, a release stranded when the default branch moved.

The build's close has been a script since [D87](../../../docs/decisions.md#d87--the-conductor-runs-the-gate); this change gives the release the same shape. The code it edits is `skills/mf-ship/scripts/conduct.py` (the release stage of `advance`, `_release_tip`, `PROMPTS`) and `skills/mf-release/SKILL.md`; `skills/mf-release/scripts/next_tag.py` and `skills/mflib/debtfile.py` (`clear`, `lock`, `write`) are used as they stand.

```
conduct.py advance, stage release

  release.py pre ──▶ worker: fold, preamble, prose ──▶ release.py finish ──▶ release.py merge ──▶ push, check
   exit 1 = halt        never commits, tags, merges     one commit, one tag     --no-ff, trees equal   conductor's
   resume = no worker   writes release.flag if needed   release.flag stops it   release.flag stops it
```

## Goals / Non-Goals

- **Goals:** a release whose every halt is a named check; a tag, a lock, a commit and a merge no worker can slip; a second run after a death at any step that ends in the commit, tag and merge an unbroken run makes; `/mf-release` by hand calling the same script.
- **Non-Goals:** a script for the spec fold, or a check of the fold against the delta; the attended push; the worktree's removal; any plan halt; the build's ticks, commit subjects and trailers.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | One script, `skills/mf-release/scripts/release.py`, with the subcommands `pre`, `finish` and `merge`, and the read-only `findings` | the build's close is this shape; each step a release halted on is a fixed command | a conductor function for each step: `/mf-release` by hand would carry its own copy |
| [D2](#d2) | Each subcommand prints `release: ok — <what>`, `release: halt — <why>` or `release: cannot run — <why>`, exits 0, 1 or 2, and `pre` prints a line per check | a script's exit 1 is the version's halt and its line the reason | a JSON report: the halt reason is read by people |
| [D3](#d3) | The conductor passes `--run`, and `--origin held` or `--origin free`; by hand neither is given | a worker-writable repo config must not steer a remote read, and the conductor already reads `origin` through its kept URLs | the script reading `origin` under a run |
| [D4](#d4) | The marks `release.pre`, written by `pre`, and `release.flag`, written by the worker, in the change's run folder | `finish` needs the tag and the gate's time `pre` found; the preamble's flag must outlive a death | the flag in the report only: a re-run lost it |
| [D5](#d5) | `finish` commits the worker's paths under `openspec/specs/` and its Markdown files, and halts naming any other changed path | a release edits no code, and a forgotten `git add` is no halt | the worker staging by name: the slip this change removes |
| [D6](#d6) | The version file and its lock are bumped by fixed pairs: `pyproject.toml` with `uv.lock`, `package.json` with `package-lock.json`; none found is `none` | the skill named no lock, so releases forgot it | the worker bumping by judgement |
| [D7](#d7) | `finish` runs in a fixed order: paths, archive, changelog, version, metrics, stage, fresh gate, no unstaged change, commit, clean tree, tag, debt, flag | the commit must hold exactly the tree the gate judged, and the tag is made only over a clean tree | tagging before the tree is known clean |
| [D8](#d8) | A run again reads where a dead release stopped from git alone: `HEAD`'s subject, the tag, the index | a re-run must end in the commit, tag and merge an unbroken run makes | a state file of the steps done: it can disagree with git |
| [D9](#d9) | The script moves a release tag only when it is this release's own, on no branch and not on `origin`; a tag `origin` or the default branch holds halts | a dead release left a tag on an orphan commit; moving any other tag rewrites history people hold | `git tag -f` by the worker, denied in the sandbox |
| [D10](#d10) | `pre` drops a release commit the default branch moved past, tag and commit, and the stage reads `release` while it may; the version goes back to integrate | a stranded release waited nine hours for a person's `git tag -d` and `git reset --hard` | a halt naming the commands |
| [D11](#d11) | `merge` runs the default-branch, clean-primary, `--no-ff` and equal-trees checks, and the merge commit carries `Change:` alone | the conductor's own merges carry `Change:` alone; the release's checks are fixed commands | the worker merging |
| [D12](#d12) | The conductor runs `pre`, the worker, `finish` and `merge` in the version's thread, then pushes and checks as today | the push, the check and the worktree's removal stay the conductor's | a second station for the script's steps |
| [D13](#d13) | `mf-release` keeps the fold, the preamble and the prose, and names the script's commands; [D17](../../../docs/decisions.md#d17--the-release-verifies-folds-archives-tags-and-on-the-persons-yes-merges-and-pushes) and [D19](../../../docs/decisions.md#d19--one-version-line) are reworded, and `release.pre` and `release.flag` join [D57](../../../docs/decisions.md#d57--one-folder-per-change-in-minions) | a decision in force is edited where it lives | a new decision beside D17 |
| [D14](#d14) | `findings <file>` prints a findings file's role, verdict and head, and has a corpus case | `pre` reads run data; the corpus rule asks a reader of run data for a case | no case: a findings file the reader cannot parse found only in a run |

### D1

`release.py` is a `uv` script with `dependencies = []`, run as `uv run --script skills/mf-release/scripts/release.py <subcommand> <change-id>`. It takes the repository from the current directory, and the primary checkout and the run directory from `mflib.layout`. `pre`, `finish` and `merge` run in the version's worktree; `merge` reaches the primary with `git -C <primary>`.

### D2

Exit 0 is done, exit 1 a halt the plan or a person answers, exit 2 a script that could not run (no `git`, no `uv`, a missing file). `pre` prints one line per check, in the order below, and last `release: tag — <tag>`, `release: resume — <tag>` ([D8](#d8)) or `release: drop — <tag> and its commit` ([D10](#d10)); each of the three is exit 0.

```
old layout ─▶ HEAD a release commit? ─┬─ default moved, bounds hold ─▶ drop (exit 0)
                                       ├─ default moved, a bound fails ─▶ halt naming it
                                       └─ else tree clean, validity, findings at HEAD~1, mark ─▶ resume (exit 0)
              HEAD no release commit ─▶ restore (--run) ─▶ tree clean ─▶ gate · findings · converge ─▶ bump, tag ─▶ the rest
```

```
release: ok — old layout
release: ok — gate · 41s
release: halt — conformance: not clean at HEAD
```

### D3

`--run` is `merge=yes`'s mark: `pre` restores a dead release's derived work ([D8](#d8)), and `finish` writes `CI not read under mf-ship` in the `Gate:` line. `--origin held` or `--origin free` says whether `origin` holds the release's tag or commit ([D9](#d9), [D10](#d10)); a hand run gives none, and the script reads `git ls-remote --tags origin <tag>` and `refs/remotes/origin/<default>` itself, halting when `origin` cannot be read. No `origin` is `free`. The conductor reads `origin` through the URLs it keeps, as `_pushed` and `_on_default` do.

### D4

`release.pre` holds `tag:`, `version:`, `gate:` (the seconds precondition 1's gate took), `head:` (the `HEAD` it ran at). `finish` halts when it is missing or its `head:` is not `HEAD` and `HEAD` is no release commit. `release.flag` is any text naming the prose to hand-edit. Both are written and found through `change_dir` of `skills/mflib/layout.py`, `release.pre` staged through `mflib.statefile.write`.

### D5

The worker's paths are those of `git status --porcelain` before `finish` writes anything: a path under `openspec/specs/`, or any path ending `.md`. Any other path, a rename, or an untracked file outside both sets halts, naming the path. `finish` stages the worker's paths and its own writes by name, never `git add -A`.

### D6

`pyproject.toml`: the first `version = "<x>"` line under `[project]` is set to the tag without its `v`, then `uv lock --offline` runs: the sandbox is offline, and only the project's own version changed. A failing `uv lock` halts naming its last line; the gate's own `uv sync --locked` would halt on that lock too.

`package.json`: its `version` key is set, and `package-lock.json`'s top `version` and `packages[""].version` are set by the same edit, no `npm` run. A `package-lock.json` with no integer `lockfileVersion`, no top `version` or no `packages[""]` entry halts naming it.

A repository with none of these records `version file: none`; another version file (`Cargo.toml`, `setup.cfg`) is not read. The cut chose the `package-lock.json` edit because a worker's `npm` runs offline from a cache ([D81](../../../docs/decisions.md#d81--an-npm-package-is-approved-at-an-exact-version-and-installed-offline)) and the lock's own version needs no resolution.

### D7

```
paths ─▶ archive+version: ─▶ changelog ─▶ version file+lock ─▶ metrics ─▶ stage by name
   ─▶ fresh gate ─▶ no unstaged change, no untracked file ─▶ commit ─▶ clean tree ─▶ tag ─▶ debt ─▶ flag
```

The `Gate:` line sits under the renamed changelog heading, before its entries: `Gate: local <XmYs> · CI <XmYs> (<workflow> at <short sha>) · <previous version>: <its times>`. Local is `release.pre`'s `gate:` seconds.

CI is the longest, over the workflows, of the latest successful run's `updatedAt − startedAt` from `gh run list --branch <default-branch> --status success --limit 50 --json workflowName,headSha,startedAt,updatedAt`. `gh` failing, no `origin` or no run reads `CI none`, and `--run` reads `CI not read under mf-ship`.

The previous version's times are copied from the `Gate:` line under the previous release heading, else `<previous version>: none`.

A red gate halts with nothing committed or tagged. The commit is `chore(release): <tag>`, its body the skip lines (`converge: skipped — by plan`, `converge: skipped — no findings files`, `<role>: skipped`) when any, its trailer `Change: <change-id>` alone. The tag is `git tag -a <tag> -m <tag>`, local only.

Under `--run` every git call of `pre`, `finish` and `merge` carries `-c commit.gpgsign=false -c tag.gpgsign=false -c core.hooksPath=/dev/null -c core.fsmonitor=false`, through one helper: the conductor's sandbox cannot reach the machine's signer, and no hook runs. By hand the person's own config stands.

### D8

A **release commit** is a `HEAD` whose subject is `chore(release): <tag>`, whose parent is the `head:` of `release.pre`, and whose changed paths are all in the **derived set**: the paths of [D5](#d5), `CHANGELOG.md`, the version file and its lock, `metrics/changes/<change-id>.json` and `openspec/changes/`. `release.pre` is required there: missing, it halts naming it, and a commit with any other path halts naming the path. `pre` and `finish` share one function for this.

`pre` at a release commit with a clean tree prints `release: resume — <tag>` after the findings check at `HEAD~1`, so the conductor starts no worker, and leaves `release.pre` and `release.flag` as they are. Before `finish` tags a release commit it runs `gate_run.py` on its tree, a recorded green reused, so a commit no gate judged is gated.

At a `HEAD` that is no release commit, under `--run`, a dirty tree whose changed and untracked paths are all in the derived set is first saved, untracked files included, as `release.discarded.<n>.patch` in the change's run folder, no earlier patch replaced, and then restored: `git restore --source=HEAD --staged --worktree -- .`, the untracked paths of the set removed, `openspec/changes/archive/<change-id>` and the data file removed, and `release.flag` and `release.pre` removed. A dirty path outside the set halts the clean-tree check naming it.

`finish` at a release commit skips every step before the tag, tags a missing tag, clears the debt again (an id not found is reported) and reads the flag.

### D9

A tag of this release is one named `<tag>` that `release.pre` gives. It is **own** when it is on a commit that is no ancestor of any branch and `--origin` is `free`. A tag the default branch holds merged, and a tag `origin` holds, halt naming which.

`pre` lets an existing tag pass only when it is own, or when `HEAD` is the release commit it names; any other existing tag halts naming it. `finish` moves an own tag to the release commit at its tag step, and makes a missing one.

### D10

`pre` drops when `HEAD` is a release commit, the default branch is no ancestor of `HEAD`, `HEAD` is no ancestor of the default branch, the tag (when it exists) is on `HEAD`, `--origin` is `free`, and the tree is clean: `git tag -d <tag>`, `git reset --hard HEAD~1`, `release.pre` and `release.flag` removed, and the line `release: drop — <tag> and its commit`, exit 0. Anything else that moved halts with the check that failed.

`_release_tip` reads `release` while those hold, and `released` (a halt naming the person) for the rest, and for a tip whose `release.flag` stands. After the drop the stage reads `integrate`.

### D11

`merge` checks, in order: `HEAD` is the release commit its subject names, with `<tag>` on it; `release.flag` absent; the default branch an ancestor of `HEAD`; the primary's `git status --porcelain` empty. Then it merges with `git -C <primary> merge --no-ff <branch>`, message `Merge branch '<branch>'`, trailer `Change: <change-id>`, and checks `git -C <primary> diff --quiet <branch> <default-branch>`.

The primary is this checkout → `git switch <default-branch>` first. It pushes nothing and removes no worktree. It is unsigned under a run, as [D7](#d7) says.

### D12

In `advance`, stage `release`: record the head in the ledger as today, run `pre` under `_boxed`. For `pre`, `finish` and `merge` alike, exit 1 halts the version with the line and exit 2 halts it as `release cannot run`; a `drop` line of `pre` makes the loop read the stage again, `resume` skips the worker, else the worker is spawned with the prompt it has, which the skill under `merge=yes` reads as the fold alone.

Before `finish` the conductor runs `_config_changed` and `_refuse_config_commands` on the tree, as `remove_tree` does, so a key the worker planted halts before any git call of the script. Then `finish`, `merge`, `push_left` and the check run. Each script's exit 1 is a `judge` reason, so the halt reads `release check fail — release: halt — …`.

Each script run is logged as `spawn — release · script <subcommand>` and `finish — release · script <subcommand> · exit <n> · <s>s`. `mflib.runlog.release_died` reads those lines too: the release died unless the newest `release · script` line is a `merge` with exit 0, whatever the worker's own lines say.

### D13

The skill's steps keep what a script cannot: the fold of the spec delta, the preamble read by eye with its flag written to `release.flag`, the prose that states the version, the ask, and the attended push and worktree removal. It names `release.py`'s commands where it named their parts. [D17](../../../docs/decisions.md#d17--the-release-verifies-folds-archives-tags-and-on-the-persons-yes-merges-and-pushes) says the commit, tag and merge are the script's under a run, unsigned; [D19](../../../docs/decisions.md#d19--one-version-line) says `release.py pre` computes the tag.

### D14

`findings <file>` exits 0 for any file it can parse and prints `release: ok — <role> verdict <verdict> head <sha>`; a file it cannot parse is exit 2. `pre` reads each findings file through the same function. The corpus case runs it over every `conformance.md` and `adversarial.md` of the run directory.

## Tests

The tests are at the lowest layer that can fail for the behaviour ([T1](../../../skills/mf-cut-change/SKILL.md#rules-for-tests)): the script's checks are unit tests over a temporary git repository. The conductor's flow is tested where it already is, in `tests/test_conduct.py`, with a fake worker. No test runs a browser, and the end-to-end runs added are none.

| layer | where | adds | command that counts them |
|---|---|---|---|
| unit | `tests/test_release.py` (new) | `pre`, `finish`, a run again, `merge` and `findings`, the tests the tasks name | `grep -c '^def test_' tests/test_release.py` |
| integration | `tests/test_conduct.py` | `test_the_release_script_runs_boxed_with_run_and_origin`, `test_a_script_run_is_logged_as_a_release_spawn_and_finish`, `test_the_release_stand_in_makes_the_commit_tag_and_merge`, `test_a_script_halt_is_the_versions_halt`, `test_a_resume_starts_no_worker`, `test_a_script_that_cannot_run_halts_the_version`, `test_a_drop_line_reads_the_stage_again`, `test_a_key_planted_by_the_release_worker_halts_before_finish`, `test_a_droppable_tip_reads_release`, `test_a_flagged_tip_reads_released` | `uv run pytest tests/test_conduct.py -q --collect-only -k "test_the_release or test_a_script or test_a_resume_starts or test_a_drop_line or test_a_key_planted_by_the_release or test_a_droppable or test_a_flagged_tip"` |
| unit | `tests/test_runlog.py` | `test_release_died_reads_the_scripts_lines` | `uv run pytest tests/test_runlog.py -q --collect-only -k "test_release_died_reads_the_scripts_lines"` |
| structure | `tests/test_structure.py`, `tests/test_skills.py` | no new test; each keeps passing against the new row and station | `uv run pytest tests/test_structure.py tests/test_skills.py -q` |

`tests/fake_worker.py` is rewritten so its release branch folds alone, and the new `tests/fake_release.py` stands in for `release.py` in the conductor's full-run tests, making the commit, tag and merge the worker made. `tests/test_conduct.py` holds the slow tests `test_a_rerun_recovers_a_dead_release` and `test_a_release_cut_short_is_recovered`: they stay by name and are rewritten to the script's deaths. Their assertions of a stranded release's hand recovery move to `test_a_stranded_release_is_dropped` of `tests/test_release.py` ([D10](#d10)). No test is deleted, so no `I16` row is owed.

## Dependencies

None.

## Risks / Trade-offs

- A requirement that names `skills/mf-release/SKILL.md` for a fixed step (the gate time, the metrics, the clean-tree halt, the push) stays as written and is held by the script: the added requirement says so. A stale reading is the reviewer's.
- *No worker pushes* keeps its scenario of a release worker that merges: the worker no longer merges, so the scenario's forger is the only one that can; the push and the ledger are unchanged.
- [D5](#d5)'s Markdown bound is the brief's: a worker's edit of any Markdown file lands in the release commit unreviewed, `AGENTS.md` and `THREAT_MODEL.md` included, because release runs after converge. A repository that wants the bound tighter says so at a later plan.
- Metrics collected by `finish` record the model as `unidentified`: the script knows no worker's model.
- A repository whose version lives in a file [D6](#d6) does not read records `version file: none`; the worker's prose correction is the only edit.
- The `package-lock.json` edit ([D6](#d6)) covers the lock's own version fields; a lock file of another shape halts the release, naming it, rather than being guessed at.
- A release that dies inside `finish` after the commit and before the tag is the case [D8](#d8) tests at every step; the one case it cannot undo is a tag `origin` already holds, which halts for a person.

## Verdict

Ready to build in the phases of [tasks](tasks.md): `pre`, `finish`, a release run again, `merge` with the conductor, then the skill and the record. The test cost is the new `tests/test_release.py` and the rewritten slow release tests of `tests/test_conduct.py`.
