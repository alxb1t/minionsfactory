# Security hardening — design

How a worker on either executor gets a real OS boundary, and why no worker pushes. Verdict at the end: ready to build.

## Context

- Measured in a scratch repo, a worker told to run a script deleting a file in `~`: the allowlist let it, `--permission-mode auto`
  let it, and `--settings` with `sandbox.enabled` and `allowUnsandboxedCommands: false` refused it, `Operation not permitted`.
- Inside that sandbox, measured: `git commit`, `make gate`, `uv --version` and a write to an allowed folder work; `pypi.org` answers
  with `network.allowedDomains`, and `example.com` is refused; `ssh` to GitHub fails; `uv run` needs `UV_CACHE_DIR`.
- `argv` starts Claude under the allowlist and no sandbox, and Codex with `network_access=true`
  (`skills/mf-ship/scripts/conduct.py`).
- `mf-release` Step 5 pushes, and `_check_release` needs the tag on `origin`.
- `mf-release` Step 4.1 reads CI times with `gh`, which a sandboxed worker cannot reach.
- `_models` reads the models file at each spawn, and a worker can write it (`0050·S2`, `R6`).
- A person's commit during a run reaches `origin` through integrate (`0051·S4`).
- `_refuse_config_commands`'s LFS remedy covers any held key once one looks like LFS (`0051·S9`).

## Goals / Non-Goals

**Goals:** a worker's script cannot write outside its reach, read credentials on Claude, or call an unlisted domain; no worker can
push; both executors have the same boundary.

**Non-Goals:** a hostile repo; Codex's reads of `~`; a sandbox for a person's session.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | Claude workers run in the sandbox | the allowlist reads text, and the kernel reads the act | auto mode, which blocked nothing; a container, for now |
| [D2](#d2) | Network: a short list, `Ship network:`, Codex off | nowhere to send anything | open network |
| [D3](#d3) | No worker pushes | a sandboxed worker cannot, so force-push needs no deny list | a deny list on Codex |
| [D4](#d4) | The plan is read once | a worker can write the models file | a check at each spawn alone |
| [D5](#d5) | A person's commit halts before integrate | `0051·S4` | narrowing the rule to a run's start |
| [D6](#d6) | The LFS remedy needs every held key to be LFS's | `0051·S9` | — |
| [D7](#d7) | D47, D51 and `THREAT_MODEL.md` state the boundary | A7 | leaving "a guardrail" in force |
| [D8](#d8) | An escape test and the drill, on real workers | the design rests on a subagent's Bash being sandboxed | a `**HUMAN` phase |

### D1

`argv`, for Claude, adds `--settings` with `worker_settings(primary, trees)`, and starts through `env` with `UV_CACHE_DIR`, as Codex
does. `allowlist` stays: the sandbox holds Bash, and the permission rules hold `Read`, `Edit` and `Write`.

```python
SECRETS = (
    "~/.ssh",
    "~/.aws",
    "~/.config/gh",
    "~/.netrc",
    "~/.gnupg",
    "~/.kube",
    "~/.docker/config.json",
)
NETWORK = ("pypi.org", "files.pythonhosted.org", "registry.npmjs.org")
```

```python
def worker_settings(primary: Path, trees: list[Path], common: Path | None) -> str:
    """Return the Claude worker's sandbox settings, as JSON."""
    extra = _agents_values(primary, "Ship network") or []
    writes = [*(str(tree) for tree in trees), *([str(common)] if common else [])]
    sandbox = {
        "enabled": True,
        "allowUnsandboxedCommands": False,
        "filesystem": {"allowWrite": writes, "denyRead": list(SECRETS)},
        "network": {"allowedDomains": [*NETWORK, *extra]},
    }
    return json.dumps({"sandbox": sandbox})
```

`filesystem.denyRead` is untested here: the escape test proves it, or halts.

### D2

`Ship network:` in `AGENTS.md`, backticked domains, as `Ship tools:` is. A wildcard or a value with a path is refused, a `Stop`.
Codex: `sandbox_workspace_write.network_access=false`. Codex as a builder is unproven and may need its network on: that is a later
choice.

### D3

`skills/mf-release/SKILL.md`, Step 5: items 4 and 5 open "Under `merge=yes`, skip this: `conduct.py` pushes." Item 6 stays. Step 4.1 already
writes `CI none` when `gh` fails.

`Run.advance`, at `release`, after the worker and before `check`: `self.push_left()`. `Run.push_left` stays the one push, through
v0.45's tagged-merges rule. A resume works the same: a run's start pushes what a dead release left.

`tests/fake_worker.py`'s `release` pushes nothing.

### D4

`Run.ship`, before its first probe: `self.plan = {(change, station): _models(...)}` for each open version, a refused table left out
as `executors` does. `Run.advance` takes the plan's triple, and a later `_models` that differs → `Stop(1, "conduct: halt —
models/<change>.toml changed during the run")`.

### D5

`Run.advance`, at `integrate`: `_foreign_commit(primary)`, the `_unpushed` walk over first-parent commits past `origin`, raises that
version's `Stop`, naming the commit.

### D6

`_refuse_config_commands`: the LFS remedy only when every held key is in an exact list of the keys LFS writes. A mixed list gets the
plain halt.

### D7

D47, the bold paragraph: "under `conduct.py`'s allowlist — Claude Code — or the workspace-write sandbox — Codex — never with prompts
bypassed" → "in an OS sandbox, Claude Code's or Codex's, never with prompts bypassed". The **Rejected** clause: ", though `make`,
`uv` and `python3` still run any code" goes.

```markdown
### D51 · A worker runs in an OS sandbox, and no worker pushes

**Every worker runs in its host's OS sandbox: it writes to the repo and its worktrees alone, and its scripts reach no unlisted
domain. `conduct.py` holds the push. The threat is a confused or prompt-injected agent; a hostile repo needs a container.**

- **Why:** measured, a script deleted a file in `~` under the allowlist and under auto mode, and the sandbox refused it.
- **Accepts:** a Codex worker can read `~`, with its network off.
- **Rejected:** auto mode · a deny list for Codex · a container, until a repo is hostile.
```

`THREAT_MODEL.md`, *Trust boundaries*, the allowlist bullet, after: "**Unattended workers run in an OS sandbox**
([D51](docs/decisions.md#d51--a-worker-runs-in-an-os-sandbox-and-no-worker-pushes)): writes stay in the repo and its worktrees,
network on a short list, no push. It holds Bash and what Bash starts; the permission rules hold `Read`, `Edit` and `Write`." *Known
gaps* gains "A Codex worker can read `~`." and loses the paid cards.

`skills/mf-ship/SKILL.md`, Step 3's *Say once*, after: "every worker runs in an OS sandbox, Claude Code's or Codex's, each station on
the executor its models file names, with no permission prompt. `conduct.py` holds the push."

### D8

`tests/escape_drill.py`, a stdlib `uv` script no gate runs, working in `../mf_escape_probe/`. `escape.py`, in that repo, tries four
things and writes the results to `results-<label>.json` in the repo:

| try | Claude | Codex |
|---|---|---|
| write `~/mf-escape-<label>` | fails | fails |
| list `~/.ssh` | fails | passes, the stated gap |
| reach `https://example.com` | fails | fails |
| reach `https://pypi.org/simple/` | passes | fails |

`conduct.py agent --executor claude`, told to run `python3 escape.py worker`, then start one subagent that runs `python3 escape.py
subagent` in the foreground. Then `conduct.py agent --executor codex`, the same. A Codex converge on a one-line change follows, with
its network off, ending in clean findings. It prints one line per label, and any `~/mf-escape-*` it finds fails it, and is deleted.

`tests/drill_resume.py` then runs from this worktree, under the sandbox.

The last task re-judges `0049·S5`, `S7`, `0050·R5`, `R11` and `S7` against the sandbox, in `evidence/rejudge.md`, and adds each one
the sandbox makes moot to `proposal.md`'s `backlog:`.

## Tests

Fake-worker tests in `tests/test_conduct.py` (`T1`). `T2`: no test reaches these states.

| layer | at cut | added | removed | proof |
|---|---:|---:|---:|---|
| Unit test functions | 92 | 5 | 0 | `uv run pytest --collect-only -q \| tail -1` prints `92 tests collected` at the cut, `97 tests collected` after |
| Integration tests | 0 | 0 | 0 | — |
| End-to-end runs | 0 | 0 | 0 | — |

| test | holds |
|---|---|
| `test_a_claude_worker_starts_in_the_sandbox` | `argv`'s `--settings` holds the reach, `SECRETS`, `NETWORK` and a `Ship network:` domain; a wildcard is refused |
| `test_no_worker_pushes` | a bare `origin`: the fake release pushes nothing, a `push` event follows, and the check passes |
| `test_the_plan_is_read_once` | a fake worker rewrites `executor`: the version halts, naming the file |
| `test_a_commit_during_a_run_halts_before_integrate` | a commit on `main` during a build: no `integrate` call, and the `halt` line names it |
| `test_a_mixed_key_list_gets_no_lfs_remedy` | an LFS key beside `core.sshCommand`: the plain halt |

Edited: `test_a_worker_carries_the_allowlist_and_a_denial_is_named`, for `network_access=false`, `env` and `--settings`. No test is
deleted or merged.

## Dependencies

None.

## Risks / Trade-offs

- **A real gate needs a domain or a path the sandbox refuses** → it fails loudly, and `Ship network:` adds a domain.
- **`gh` is out of reach** → `CI none` in the release's `Gate:` line.
- **`.claude/` appears in a sandboxed repo** → measured in the probe; the drill shows whether a run minds it.
- **A subagent's Bash is outside the sandbox** → the escape test is a `**HALT CHECK**`, and the design stops there.
- **This change's own run is unsandboxed** → its build uses the installed conductor, and the drills use the worktree's.

## Migration Plan

```
1 the sandbox ─▶ 2 no worker pushes ─▶ 3 the cards ─▶ 4 the record ─▶ 5 the proof ─▶ release
```

Each phase ends on a green gate. Nothing is irreversible.

## Verdict

Ready to build. Acceptance: a real worker and a real subagent cannot write out, read secrets on Claude, or call an unlisted domain; no
worker pushes; the drill passes under the sandbox; the record states the boundary.
