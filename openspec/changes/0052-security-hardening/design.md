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
| [D9](#d9) | The conductor's remote calls read no repo's config, and go only to the URLs a run kept in the home folder | `R2`, `R3`, `R9`, `S3`, `S4`, `S10`, `S11`: it now pushes with workers alive, outside their sandbox, and a repo's config outlasts a run | holding the push until no worker lives: a release's check needs it, and a worker's background process outlives its exit · a person accepting a re-run's first read |

### D1

`argv`, for Claude, adds `--settings` with `worker_settings(primary, trees, common, network)`, and starts through `env` with `UV_CACHE_DIR`, as Codex
does. `allowlist` stays: the sandbox holds Bash, and the permission rules hold `Read`, `Edit` and `Write`, so `denied` gains
`Read(<path>)` and `Read(<path>/**)` for each entry of `SECRETS`: `denyRead` does not bind the `Read` tool, and the rule binds
`Grep` and `Glob` as far as the host does.

`argv` also passes `--setting-sources user`. A worker can write a project's `.claude/` and `.mcp.json`, and under `-p` the host
runs their hooks and connects their servers at a start, outside the sandbox. That pays `0050·S3`: what a Codex station wrote
reaches the next Claude station's sandbox, and never its start-up.

```python
SECRETS = (
    "~/.ssh",
    "~/.aws",
    "~/.config/gh",
    "~/.netrc",
    "~/.gnupg",
    "~/.kube",
    "~/.docker/config.json",
    "~/.git-credentials",
    "~/.config/git/credentials",
    "~/.npmrc",
    "~/.pypirc",
    "~/.codex/auth.json",
    "~/.claude/.credentials.json",
)
TOKENS = (
    *("GITHUB_TOKEN", "GH_TOKEN", "NPM_TOKEN", "NODE_AUTH_TOKEN"),
    *("UV_PUBLISH_TOKEN", "TWINE_PASSWORD"),
    *("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"),
    *("ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN", "OPENAI_API_KEY"),
)
NETWORK = ("pypi.org", "files.pythonhosted.org")
```

The host has no credential list of its own, so these are the whole of it. `NETWORK` holds hosts that take no write:
`registry.npmjs.org` takes a publish, and the proxy reads a hostname alone, so a repo that needs it names it in `Ship network:`.

```python
def worker_settings(
    primary: Path, trees: list[Path], common: Path | None, network: list[str]
) -> str:
    """Return the Claude worker's sandbox settings, as JSON."""
    writes = [*(str(tree) for tree in trees), *([str(common)] if common else [])]
    sandbox = {
        "enabled": True,
        "allowUnsandboxedCommands": False,
        "filesystem": {"allowWrite": writes, "denyRead": list(SECRETS)},
        "credentials": {"envVars": [{"name": name, "mode": "deny"} for name in TOKENS]},
        "network": {"allowedDomains": [*NETWORK, *network]},
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
as `executors` does. The plan also holds `AGENTS.md`'s `Ship network:` and `Ship tools:`, read once, and `argv` takes them from it: a worker can write that
file, so a later edit reaches no worker in this run. `Run.advance` takes the plan's triple, and a later `_models` that differs → `Stop(1, "conduct: halt —
models/<change>.toml changed during the run")`.

### D5

`Run.advance`, at `integrate`: `_foreign_commit(primary)`, the `_unpushed` walk over first-parent commits past `origin`, raises that
version's `Stop`, naming the commit.

### D6

`_refuse_config_commands`: the LFS remedy only when every held key holds the exact value LFS writes for it, `LFS_CONFIG`. A mixed
list, or a planted value under an LFS key, gets the plain halt.

### D7

D17, the bold paragraph: "and pushes the default branch and the tag" → "and pushes the default branch and the tag; under
`merge=yes`, `conduct.py` pushes". Its title stays, so its links hold.

D47, the bold paragraph: "under `conduct.py`'s allowlist — Claude Code — or the workspace-write sandbox — Codex — never with prompts
bypassed" → "in an OS sandbox, Claude Code's or Codex's, never with prompts bypassed". The **Rejected** clause: ", though `make`,
`uv` and `python3` still run any code" goes.

```markdown
### D51 · A worker runs in an OS sandbox, and no worker pushes

**Every worker runs in its host's OS sandbox: it writes to the repo and its worktrees alone, and its scripts reach no unlisted
domain. `conduct.py` holds the push: its remote calls read no repo's config, and go only to the URLs a run kept in the home
folder. The threat is a confused or prompt-injected agent; a hostile repo needs a container.**

- **Why:** measured, a script deleted a file in `~` under the allowlist and under auto mode, and the sandbox refused it. The
  conductor runs outside the sandbox, so what a worker wrote must steer none of its remote calls, and a repo's config outlasts
  the run that wrote it, so the URLs stand where no worker writes.
- **Accepts:** a Codex worker can read `~`, with its network off · a repo's `.claude/` settings, skills and `.mcp.json` reach no
  worker.
- **Rejected:** auto mode · a deny list for Codex · a container, until a repo is hostile.
```

D47, **Executors:**, gains "A mixed run's Codex station hands its writes to the next station's sandbox, never to its start: a
Claude worker loads no project settings." Its halts gain "a git config that changed during the run".

`THREAT_MODEL.md`, *Trust boundaries*, the allowlist bullet, after: "**Unattended workers run in an OS sandbox**
([D51](docs/decisions.md#d51--a-worker-runs-in-an-os-sandbox-and-no-worker-pushes)): writes stay in the repo and its worktrees,
network on a short list, no push. It holds Bash and what Bash starts; the permission rules hold `Read`, `Edit` and `Write`, each
of `SECRETS` denied to `Read`. A Claude worker loads user settings alone, so a project's settings and `.mcp.json` start nothing."
Two bullets follow it, for a mixed run and for the conductor. *Known gaps* gains "A Codex worker can read `~`." and what the cards
leave, and loses the paid cards.

`skills/mf-ship/SKILL.md`, Step 3's *Say once*, after: "every worker runs in an OS sandbox, Claude Code's or Codex's, each station on
the executor its models file names, with no permission prompt. `conduct.py` holds the push."

### D8

`tests/escape_drill.py`, a stdlib `uv` script no gate runs, working in `../mf_escape_probe/`. `escape.py`, in that repo, tries six
things and writes the results to `results-<label>.json` in the repo:

| try | Claude | Codex |
|---|---|---|
| write `~/mf-escape-<label>` | fails | fails |
| list `~/.ssh` | fails | passes, the stated gap |
| reach `https://example.com` | fails | fails |
| reach `https://pypi.org/simple/` | passes | fails |
| reach `https://registry.npmjs.org/` | fails | fails |
| read `GITHUB_TOKEN`, which the drill sets | fails | not judged |

`conduct.py agent --executor claude`, told to run `python3 escape.py worker`, then start one subagent that runs `python3 escape.py
subagent` in the foreground. Each also calls `Read` on an absent file under `~/.ssh`: a broken rule answers that it does not exist,
so no real key reaches a model, and the drill counts the denials. Then `conduct.py agent --executor codex`, the same. A Codex
converge on a one-line change follows, with its network off, ending in clean findings. It prints one line per label, and any
`~/mf-escape-*` it finds fails it, and is deleted.

The probe holds a `SessionStart` hook in `.claude/settings.local.json` and a server in `.mcp.json`, each marking `~`. A control
`claude -p` without the flag first proves both fire, or the drill stops; the workers' runs must then leave no mark.

`tests/drill_resume.py` then runs from this worktree, under the sandbox.

The last task re-judges `0049·S5`, `S7`, `0050·R5`, `R11` and `S7` against the sandbox, in `evidence/rejudge.md`, and adds each one
the sandbox makes moot to `proposal.md`'s `backlog:`.

### D9

Added at converge, for `R2`, `R3`, `S3` and `S4`, as `0049·S7` asks, and for `R9`, `S10` and `S11`. Since [D3](#d3) `conduct.py` pushes
on every release, with other versions' workers alive, and a worker can write the common directory. Three gaps follow: `origin`'s URL
steers a push, it carries what a worker put in it to the host it names on any remote call, and a key set after the refusal runs at
the operator's rights.

`Run.__init__` reads `_git_state` once, before the first worker, and `origin`'s push URLs, the kept ones where a run kept them.
`Run.push_left` halts the run, `the local git config changed during the run`, before any remote call, when `origin` stood at that
read and the state differs, and pushes `<sha>:<ref>` to those URLs. With no `origin` nothing leaves, so `merge_in` keeps its own
comparison. `Run.advance` skips the release's `check` when `push_left` halted the run.

`Run.ship`, once it has a version and past its first `push_left`, calls `_keep_origin`: `origin`'s fetch and push URLs, none being a
value too, go to `~/.mf-ship-origin/<digest>`, the digest of the primary's path, owner-only, since a URL can hold a key. A file that
stands stays, so a re-run is no first read. A first run that halts at the refusal keeps nothing, so a person's repoint needs no
second step.

`_refuse_origin` stands before every remote call, a run's or `status`'s, `check`'s and `report`'s, and halts while `origin` differs
from the kept URLs, naming the file and no URL. Nothing clears it but a person: they read `git remote -v`, then repoint `origin`, or
remove the file, and the next run keeps what it reads. The value compared is the value the call uses, so a worker's toggle steers
nothing. Before a repo's first run nothing is kept, and `status` takes the URL it reads, as that first run will.

Each remote call, `ls-remote` and `push`, goes through `_outside`: a new bare repo, no template, its alternates naming the primary's
objects, in a folder no worker can write. `git` there reads the operator's global config and that scratch's, and no repo's, so the
key a worker set is never read. A URL is passed behind `--`. The push updates `refs/remotes/origin/<default>` itself, since a URL
updates no remote-tracking ref.

The scratch stands in the home folder: both sandboxes write the temp folders, so a scratch there would stand in a worker's reach.
Where the home folder refuses it, `conduct.py` is itself in a sandbox, and the temp folder serves. There it keeps no URLs either: its
sandbox holds its network, and a run's own comparison stands.

This leaves `conduct.py`'s local git in the race, as `0049·S7` and `0050·R5` say: `status`, `merge` and `commit` still read the repo's
config after the refusal. *Known gaps* keeps both cards.

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
| `test_the_plan_is_read_once` | a fake worker rewrites `executor`: the version halts, naming the file; a domain it adds to `Ship network:` reaches no later worker's settings |
| `test_a_commit_during_a_run_halts_before_integrate` | a commit on `main` during a build: no `integrate` call, and the `halt` line names it |
| `test_a_mixed_key_list_gets_no_lfs_remedy` | an LFS key beside `core.sshCommand`: the plain halt |

Edited: `test_a_worker_carries_the_allowlist_and_a_denial_is_named`, for `network_access=false`, `env`, `--settings`, the `Read` rules
and the host's words for a denied `Read`. Converge's fixes are steps in the tests they name (`T2`):
`test_a_claude_worker_starts_in_the_sandbox`, for `TOKENS`, the lists and `--setting-sources`; `test_a_mixed_key_list_gets_no_lfs_remedy`,
for a planted value; `test_no_worker_pushes`, for a repointed `origin`, the URL each remote call receives, a re-run and a person's
remedy; `test_a_rerun_pushes_what_a_release_left`, for a key after the refusal, the first URL and the place of the scratch and the kept
URLs. No test is deleted or merged.

## Dependencies

None.

## Risks / Trade-offs

- **A real gate needs a domain or a path the sandbox refuses** → it fails loudly, and `Ship network:` adds a domain.
- **`gh` is out of reach** → `CI none` in the release's `Gate:` line.
- **A gate needs a project setting, a project skill or a token** → it fails loudly. `AGENTS.md`'s `Ship tools:` and `Ship network:`
  are the run's own lines for what a repo needs.
- **A push needs a repo-local credential helper** → it is already a held key, and that repo releases by hand.
- **A person moves `origin` on purpose** → the next run halts, naming the file; they remove it, and that run keeps the new URLs.
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
