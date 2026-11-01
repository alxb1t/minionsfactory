# Codex as reviewer — design

How a station picks its executor, how far a worker reaches, and how a converge on Codex is proven. Verdict at the end: ready
to build.

## Context

- `conduct.py run --executor` sets `Run.executor` (`skills/mf-ship/scripts/conduct.py:832`), and `spawn` uses it
  (`:881`). `_models` reads a station's model and effort, integrate using `[release]` (`:630`).
- `edit_root` returns the directory `Worktrees:` names, and it feeds Codex's `roots`, Claude's `Edit` and `--add-dir`
  (`:659`, `:696`, `:707`): the container, so every sibling project.
- `_delta` starts `integrate.py` from disk mid-run, with the operator's rights (`:370`), and `merge_in` runs git merge and
  commit outside any sandbox (`:968`). `NO_HOOKS` closes hooks and `core.fsmonitor`, not other command-bearing keys.
- Measured on this machine, in scratch repositories: `conduct.py agent --executor codex` wrote, committed and ran
  `make gate`, exit 0, 16,089 tokens; `codex exec` started a subagent with `collaboration.spawn_agent`, waited, and read its
  file, which is the worker capability converge needs. `uv`'s Python is arm64. `timeout` and `python3` here are Intel builds,
  under which the `git` and `make` shims fail: never wrap a worker in them.
- 0042's [D10](../archive/0042-review-method/design.md) holds the calibration: fixtures, `conduct.py agent`, a 5-row key.

## Goals / Non-Goals

**Goals:** a version names each station's executor; a bad table fails before a worker; no worker reaches a sibling
project; a converge on Codex finds what Claude's found.

**Non-Goals:** Codex as the builder, proven; `--json`; a Codex limit's wording.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `executor` per table in the models file; absent, the run's | per-version choices live in the file | an `mf-ship` flag |
| [D2](#d2) | An unknown executor, or `codex` with a `claude-*` model, halts that version | only the mismatches a table can show | a list of model names |
| [D3](#d3) | One probe per distinct executor; any failure stops the run | a Codex fault shows at minute one, for 16k tokens | a probe per version |
| [D4](#d4) | Codex logs stay plain text | its sandbox has no denial event | parsing `--json` now |
| [D5](#d5) | `reach` feeds Codex's roots and Claude's `Edit` and `--add-dir` | `0040·S2` is `0040·S4` on the Claude side | two lists |
| [D6](#d6) | `integrate.py` is loaded once; a changed git config halts a dependent's merge | `0048·S2` and `0048·S3` are the routes left out of a sandbox | a sandboxed merge worker |
| [D7](#d7) | The proof runs as build tasks in `../mf_codex_probe/` | a probe directory, as 0042's calibration did; nothing needs a person | a `**HUMAN` phase |
| [D8](#d8) | D47 gains a bullet, and the cut's text names `executor` | A7 | a new decision |

### D1

`_models(runs, change, station, run)` returns `(executor, model, effort)`, `run` being the run's executor when the table
names none. `Run.spawn`'s `models` becomes that triple, and its worker is `argv(executor, prompt, cwd, model, effort)`.

The `spawn` event adds ` · executor <name>` only when it differs from the run's, so a run on one executor logs as today.

### D2

`_models`, once it has the executor and the model:

```python
file = f"models/{change}.toml"
if executor not in EXECUTORS:
    raise Stop(1, f"conduct: halt — {file}: executor {executor!r} unknown")
if executor == "codex" and (model or "").startswith("claude"):
    raise Stop(1, f"conduct: halt — {file}: {station} on codex, model {model}")
```

`EXECUTORS = ("claude", "codex")`. `advance` already turns a `Stop` into that version's halt. Any other wrong name fails the
worker, then its check.

### D3

`Run.executors(versions)` returns the run's executor, then each other `executor` any open version's models file names.
`ship` probes each in turn, in place of its one `self.probe()`. `Run.probe(executor)` spawns station `probe` for the run's
executor, and `probe-<executor>` for another, whose `_executor_missing` halts `run` first.

### D4

`argv` keeps Codex's output as it is, so `denials` reads nothing from it. `mf-converge` already writes `tokens unavailable`
when it has no count.

`argv` starts Codex through `env`, with login shells off, so the worker's commands find a writable cache and system tools:

```python
system = "/usr/bin:/bin:/usr/sbin:/sbin"
path = f"PATH={system}:{os.environ.get('PATH', '')}"
env = ("env", f"UV_CACHE_DIR={run_dir(cwd) / 'uv-cache'}", path)
```

`argv` adds `-c allow_login_shell=false`: a login shell re-reads the person's profile, and puts `PATH` back. Measured in a
scratch repo: `PATH` alone left `which bash` on an Intel build; both together ran `git`, `make`, `uv`, `codex` and `openspec`,
each through `bash` too, with no `xcrun` error. `SHELL` did nothing, so it goes.

`mf-converge` needs `uv`, and `~/.cache/uv` is outside a worker's reach. Adding it would break [D5](#d5) and let a sandboxed
worker poison a cache that unsandboxed `uv` trusts. Codex can reach an Intel `bash` through the person's `PATH`, under which the
`git` and `make` shims fail. `work` stays as it is. Added after 4.2's first run stopped on both.

### D5

`edit_root` goes.

```python
def reach(cwd: Path) -> list[Path]:
    """Return the directories a worker may edit: the primary and each linked worktree."""
    root = _root(cwd)
    if _common_dir(cwd) is None:
        return [cwd.resolve()]
    linked = [path for path in _worktrees(root).values() if path != root]
    return [root, *linked]
```

`allowlist(cwd, trees)` gives one `Edit(/{tree}/**)` per tree. `argv` gives `--add-dir` once per tree, and Codex's `roots` are
`run_dir`, the common directory, then `reach`. The second half of `0040·S2`'s fix falls away: with `edit_root` gone, a
`Worktrees:` path widens nothing. A changed `Ship tools:` line is out: `make`, `uv` and `python3` run any code, and D47 says the
list is a guardrail.

### D6

`Run.__init__` loads the script once, and `_delta` calls it in process:

```python
self.delta = runpy.run_path(str(INTEGRATE))["delta"]
```

`_delta` keeps its return: `integrate.py`'s `Stop` carries what its exit and output carry today. `Run.ship`, before its first
probe, keeps `_git_state(primary)`: the common directory's `config` and `info/attributes`, read
as text, a missing file as empty. `merge_in` opens by comparing: changed → `Stop(1, "the local git config changed during the
run")`, that version's halt.

### D7

Under `../mf_codex_probe/`, from this worktree, under the shell rules, per
[0042's D10](../archive/0042-review-method/design.md) and its answer key:

- **`seeded`, `clean`** — D10's files, on the branch `0002-discount`, the proposal `bump: minor`.
- **The calibration** — for each, `uv run --directory ../mf_codex_probe/<fixture> --script
  ../../0050-codex-review/skills/mf-ship/scripts/conduct.py agent --executor codex "Run the skill at
  ../../0050-codex-review/skills/mf-converge/SKILL.md for change 0002-discount with tier=standard."`
- **The bar** — Claude's: `seeded` 5 of 5, `clean` no blocker.
- **`cross`** — a repo with `Worktrees: ../` and a one-line `make gate`, one cut change `0001-note` with one phase, and
  `.minions/models/0001-note.toml` naming `executor = "codex"` under `[converge]`. `uv run --directory ../mf_codex_probe/cross
  --script ../../0050-codex-review/skills/mf-ship/scripts/conduct.py run --executor claude`. The worktree's script, since the
  installed one lacks `executor` until this ships. Its log names `converge · … · executor codex`, and the run ends on `done`.

`openspec/changes/0050-codex-review/evidence/calibration.md` holds one line a run, with no absolute path. The probe is
deleted at its end.

### D8

`docs/decisions.md`, D47, a bullet before **Rejected**:

> - **Executors:** the models file names a station's executor, absent meaning the run's. One probe runs per executor, and a
>   worker reaches the primary and the open worktrees alone.

`skills/mf-ship/SKILL.md`, Step 3's *Say once*, after "(Codex),": "each station on the executor its models file names,".

`skills/mf-cut-change/SKILL.md`, the models TOML, under `[converge]`: `executor = "codex"  # optional, per table; absent, the
run's. A cross-host pairing is usually the person's edit`.

## Tests

Fake-worker tests in `tests/test_conduct.py` (`T1`).

| layer | at cut | added | removed | proof |
|---|---:|---:|---:|---|
| Unit test functions | 78 | 3 | 0 | `uv run pytest --collect-only -q \| tail -1` prints `78 tests collected` at the cut, `81 tests collected` after |
| Integration tests | 0 | 0 | 0 | — |
| End-to-end runs | 0 | 0 | 0 | — |

`T2`: no test holds a models file with an executor, or a changed git config. Each goes directly before
`test_run_halts_on_a_timeout`.

| test | holds |
|---|---|
| `test_a_station_runs_on_its_executor` | `executor = "codex"` under `[converge]`: `probe` and `probe-codex` spawned; the `spawn — converge` line names `executor codex`, the build's does not; exit 0 |
| `test_a_models_mismatch_halts_its_version` | an unknown executor, then `codex` with `claude-opus-5-5`: that version halts, no worker for it; another version ships |
| `test_a_changed_git_config_halts_a_merge_in` | a dependent, with `git config` changed by the fake dependency's release: it halts naming the change, and no merge commit exists |

Tests edited:

| test | edit |
|---|---|
| `test_a_worker_carries_the_allowlist_and_a_denial_is_named` | `Edit`, `--add-dir` and `roots` name the primary and worktrees, never `container` |
| `test_after_waits_for_its_dependency` | `integrate.py` runs in process |

No test is deleted or merged.

## Dependencies

None.

## Risks / Trade-offs

- **`git worktree remove` under a narrower reach** → a Codex release is not proven here; the release stays on Claude.
- **Merging beside ship resume** → both edit `Run.spawn`'s `work(…)` line. A text conflict there stops as `integrating`, one
  small hand merge.
- **Fixture spend** → the calibration and the cross-host run spend Codex tokens in the build, small next to a real converge.
- **Codex scores below the bar** → a `**HALT CHECK**`: the plan is wrong, and the version halts.
- **The probe's stations read installed skills** → `~/.agents/skills` holds all of them, linked to the primary.

## Migration Plan

```
1 the executor ─▶ 2 the reach ─▶ 3 the record ─▶ 4 the proof ─▶ release
```

Each phase ends on a green gate. Nothing is irreversible. A models file with no `executor` runs as today.

## Verdict

Ready to build. Acceptance: a station runs on its executor; a bad table halts its version; no worker reaches the container;
the calibration meets Claude's bar on Codex; a cross-host run ends on `done`.
