# Sandbox patch — design

How a run proves its sandbox, how a forged merge is told from a real one, and how a stale lock stops costing a round. Verdict
at the end: ready to build.

## Context

Read at `136aa1e`. `conduct.py` is `skills/mf-ship/scripts/conduct.py`.

- `worker_settings` sets `enabled` and `allowUnsandboxedCommands: False`, and no `failIfUnavailable` (`conduct.py:1160-1177`).
  Claude Code's [sandboxing docs](https://code.claude.com/docs/en/sandboxing), read 2026-11-02: by default a sandbox that
  cannot start runs commands unsandboxed; `failIfUnavailable: true` exits at startup instead, and refuses each command if the
  sandbox goes later. `-p` is not covered, and a `-p` run skips a settings value it rejects. No status field reports the sandbox.
- The probe edits, commits and runs `make gate` in a scratch repo whose recipe is `touch .gated` (`conduct.py:1720-1745`);
  `check_probe` reads `probe.txt` and `.gated` alone (`:967`). An unsandboxed worker passes it.
- A push needs a shape alone: two parents, the second tagged and saying `chore(release): <tag>`, equal trees
  (`_release_merge`, `_merges_a_release`, `:891-906`). Any worker can write that shape.
- `_foreign_commit` walks the local `origin/<default>..<default>` (`:909-922`), and a worker can move that ref.
  `push_left` re-reads each sha after the check (`:1765`).
- `~/.mf-ship-origin/` holds the kept URLs, out of every worker's write reach (`_kept_file`, `:763`). Nothing there records a head.
- `.minions/backlog.lock` is an empty directory, in prose alone (`skills/mf-converge/SKILL.md:432-433`,
  `skills/mf-release/SKILL.md:227-229`). A usage limit killed `0052`'s converge 46 seconds after it took the lock, and the resume
  halted on it at Step 9 with both verdicts clean. `stage_of` reads a top `halt` as `converge-halted` (`:647-650`), `grant`
  takes only `cap reached` (`:1927`), and a hand `/mf-converge` refuses to resume a halt (`skills/mf-converge/SKILL.md:127`).
- The anchor rule, "Anchors always block", is in `skills/mf-converge/SKILL.md:314`; `generic-security.md` defers to it (`:10`).
  `THREAT_MODEL.md:44-45` accepts a class, then says "A review cards a new route in this class and does not block on it".
- **Phase 1's first run, 2026-11-02:** a Codex worker started through `argv` loaded an `[mcp_servers]` entry planted in its
  tree's `.codex/config.toml`, and the server ran; the planted `notify` did not. `~/.codex/config.toml` trusts that path, and
  MF scratch paths besides, among them a `mf-ship-probe-*` scratch no person opened. Codex's
  [config reference](https://learn.chatgpt.com/docs/config-file/config-reference), read 2026-11-02: "Codex loads
  project-scoped config files only when you trust the project", "Untrusted projects skip project-scoped `.codex/` layers,
  including project-local config, hooks, and rules", and `projects.<path>.trust_level` marks a path either way; a project file
  cannot set notification keys. Codex 0.163 has no flag that skips project config.
- A sandboxed worker's network is `pypi.org` and `files.pythonhosted.org` (`NETWORK`, `:109`), so no `mf-ship` worker can run
  `tests/escape_drill.py`, which starts real Claude and Codex workers.

## Goals / Non-Goals

**Goals:** a Claude worker runs sandboxed or not at all, and a run proves it; `conduct.py` pushes only a release a run took to
its release; a dead worker's lock costs no round; the record claims what a run holds.

**Non-Goals:** Linux, stated as unproven; a hostile repo; a guard against a release forged inside its own window; any non-cap
converge halt but the lock's.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `failIfUnavailable`, and a probe whose gate needs a write out refused | the key alone proves nothing under `-p`; the recipe reaches the sandbox with no model choice | a `touch ~/…` the model runs: the allowlist may stop it first · a Linux phase now |
| [D2](#d2) | A release ledger in `~/.mf-ship-origin/` | no worker writes there, as the kept URLs show; the push is the one sink that cannot be withdrawn | the ledger in `.minions/`: every worker writes it · accepting `S8` in the accepted class |
| [D3](#d3) | A run clears a lock older than ten minutes; a lock halt resumes at Step 9 | the incident needed nothing more | a pid in the lock · `grant` for every halt |
| [D4](#d4) | The cards | their triggers fire here | — |
| [D5](#d5) | The record: `THREAT_MODEL.md`, D47, D51, the anchor rule | A7; `S9`, `R18`, `0051·R11` | deleting the reviewer sentence alone: it brings back blocking on anchors |
| [D6](#d6) | `S12` is settled by a planted `.codex/config.toml`, first; it loaded, so a Codex worker starts with its trees untrusted | Codex skips an untrusted project's `.codex/` layers; it mirrors Claude's `--setting-sources user` | a `**HUMAN` phase: the person's 2026-11-02 call · refusing a repo the operator trusts: it halts on every repo used with Codex · refusing a `.codex/` in a tree: a race on worker-written state · accepting the gap |
| [D7](#d7) | The proof: the drill and a real probe on each executor | the fake worker cannot hold a sandbox | — |
| [D8](#d8) | Built by hand: `/mf-build`, `/mf-converge`, `/mf-release` | a sandboxed worker cannot run the drill; a change to the push guard does not run under it | `/mf-ship` |

### D1

`worker_settings` adds `"failIfUnavailable": True` to the sandbox.

`Run.probe` writes, before it spawns, an empty **probe mark**: `~/.mf-ship-origin/probe-<executor>-<pid>`, mode `0o600`. The
scratch `Makefile` becomes:

```make
gate:
	! echo escaped >> '<probe mark>'
	touch .gated
```

`make gate` is on the allowlist, so the write reaches the sandbox, never a permission rule. A refused write fails, `!` passes,
`.gated` appears. After the worker, `check_probe(scratch, mark)` fails when the mark is not empty:
`"<executor> wrote outside its reach: it runs unsandboxed"`, a run halt. The mark is removed in the `finally`, written or not.
Codex runs the same recipe: `workspace-write` refuses the home folder.

`tests/fake_worker.py`'s `probe` makes each `probe-*` mark under `$HOME/.mf-ship-origin/` read-only before `make gate`, standing
in for the sandbox; a new mode, `unsandboxed`, leaves it writable.

### D2

The **release ledger** is `~/.mf-ship-origin/<digest>.released/`, one file per change holding its head; `<digest>` is
`_kept_file`'s, through a shared `_digest(primary)`. Directory `0o700`, files `0o600`.

- **Write** — `Run.advance`, at `release`, before `self.spawn`, when `_tag_of` finds no tag: `_record_release(primary, change,
  head)`, `head` the version tree's `HEAD`, overwriting any older entry for the change. Log event `ledger`, detail
  `<change> <head>`. A dead release's re-entry writes nothing: its entry stands.
- **Check** — `_foreign_commit(primary, base)` walks `base..<default>`, first-parent. Each commit passes `_merges_a_release`, and
  its second parent's first parent is a ledger head. Else `Stop(1, "conduct: halt — <default> holds <sha7>, no run's release:
  a person reads it, then git push origin <default>")`.
- **Base** — `_unpushed(primary, first_read)` reads `origin`'s `refs/heads/<default>` with `_listed`, and passes that sha. With
  no read allowed (`status` in a repo no run kept), the local `origin/<default>`, as today. A push read that fails →
  `Stop(1, "conduct: halt — cannot read origin: nothing pushed")`. A sha `origin` lists that is not in this repo →
  `Stop(1, "… origin's <default> is at <sha7>, which this repo lacks: a person fetches")`. An `origin` with no default
  branch → `Stop(1, "… origin has no <default>: a person pushes it first")`.
- **Tags** — a merged tag `origin` lacks passes when its commit says `chore(release): <tag>` and its parent is a ledger head.
- **Push** — `_unpushed` returns `(ref, sha)` pairs; `push_left` pushes those shas, re-reading nothing.
- **Close** — after `push_left`'s pushes succeed, each entry whose release's tag is now on `origin` is removed.

The integrate-time call (`conduct.py:1606`) keeps the local base and gains the ledger check. A hand release pushes itself on the
person's yes; one left unpushed now halts a run, where today a run pushes it.

**The window**, a stated gap: from the entry's write to its push, another worker could merge a forged release on that head.

### D3

`Run.ship`, after `_keep_origin` and before `read_plan`, under the claim: `.minions/backlog.lock` a directory whose mtime is more
than `LOCK_STALE = 600` seconds old → `os.rmdir`, event `unlock`, detail its age in seconds. A younger lock stays.

`stage_of`: a converge halt whose text holds `.minions/backlog.lock` → `("converge", "halted on the backlog lock: resumes at
Step 9")`, before the `converge-halted` return. `grant` is unchanged.

`skills/mf-converge/SKILL.md`, *Resuming a run*, gains: "The top line is a `halt` naming `.minions/backlog.lock` → continue
that run at Step 9 when both findings files are clean at `HEAD`; else halt, naming the file." A hand resume with the lock still
there halts on it again: the person removes it when no converge or release runs.

### D4

| card | edit |
|---|---|
| `0052·R6` | `Run.ship`'s `start` line says `permissions: sandbox`; the `permissions` variable goes |
| `0052·R7` | `skills/mf-release/SKILL.md`: the description reads "…then on the person's yes merge into the default branch and push; under merge=yes from mf-ship, merge and leave the push to conduct.py"; Step 6's "and the merge and the push, or that there is no `origin`" → "and the merge and the push — under `merge=yes`, that `conduct.py` pushes — or that there is no `origin`" |
| `0052·R8` | `PUSH_TIMEOUT = 1800`; `_outside` takes a `timeout` and passes it to `_run`; `push_left` uses it |
| `0052·R10` | `CONFIG_CHANGED` names the file that differs, `.git/config` or `.git/info/attributes`, and no URL; `skills/mf-ship/SKILL.md` Step 4 gains: "A halt naming a changed git config is the person's: read that file, and repoint `origin` if a worker moved it, before a re-run." |
| `0052·R13` | `_keep_origin` passes on `FileExistsError` alone, and returns any other `OSError`'s text; `Run.ship` logs it as event `unkept` |
| `0052·R14` | `_keep_origin` reads `_urls` before it opens the file |
| `0051·R14` | `test_a_stop_survives_a_death` merges into `test_a_rerun_recovers_a_dead_release` at its `0002-marks` step, per [Tests](#tests) |
| `0051·R13`, `0051·S8` | moot, no edit: `0051`'s archive is frozen, and its Step 9 ran with `0049·S5` kept |

`EVENTS` gains `ledger`, `unlock` and `unkept`.

### D5

`THREAT_MODEL.md`:

- *Trust boundaries*, the sandbox bullet: after "no push.", add "A Claude worker whose sandbox cannot start does not run, and
  each run's probe proves a write out refused, per executor."
- The conductor bullet: "no remote call runs" → "no remote call of `conduct.py` runs"; "A changed config halts a run before its
  next remote call." → "A changed config halts a run before its next push."; and add "It pushes only a release a run took to its
  release: the release ledger in the home folder holds each version's head from its release worker's start until its push."
- *Entry points*: after `Ship network:`, add "(D51 accepts it: every worker of the repo reaches what it lists)".
- *Out of scope*, its last two sentences → "The person accepted this class on 2026-11-01, for confused and prompt-injected
  agents, with credentials denied on Claude; a Codex worker reads `~`, its network off. A route in this class is carded; only a
  new class blocks, anchors included."
- *Trust boundaries*, the mixed-run bullet: add "A Codex worker starts with its trees untrusted, so a worker-written `.codex/`
  starts nothing."
- *Known gaps*: "stays readable by a script" → "stays readable by a script or the `Read` tool"; the line "Whether a Codex start
  reads a worker-written `.codex/config.toml` is not read from its docs." is deleted; add "Linux and WSL2 are unproven: the fail-closed start and the probe are measured on macOS alone." and "A
  worker can forge a release on a head while that head's release runs: the ledger holds the head until its push."

`docs/decisions.md`:

- **D51**, its statement: after "reach no unlisted domain.", add "A Claude worker whose sandbox cannot start does not run, and
  each run's probe proves a write out refused."; after "kept in the home folder.", add "It pushes only a release a run took to
  its release, by a ledger there." **Accepts** gains "a domain `Ship network:` lists · a release forged on a head during that
  head's release".
- **D47** gains "- **Accepts:** what a command `Ship tools:` names runs, inside the sandbox." (`0051·R11`).

`skills/mf-converge/SKILL.md:314`, after "Outside the anchors, the grade is the station's.": "Save one class: a route in a class
the threat model's *Out of scope* accepts by name is carded and does not block, anchors included."
`skills/mf-converge/references/generic-security.md`, *Inspect* item 1, after "never as a settled bar.": "A route in a class its
*Out of scope* accepts by name is carded, never blocking, per the contract's anchors."

`skills/mf-ship/SKILL.md` Step 3's "Say once" gains "A Claude worker whose sandbox cannot start does not run, and the probe
proves a write out refused."

### D6

`tests/escape_drill.py` gains a Codex step, run before anything else is built. A **control** passes, with `-c`, a `notify`
program and an `[mcp_servers]` entry, each touching its own mark in the probe folder, and must see both marks. The **plant**
writes the same entries to `.codex/config.toml` in the worker's tree and starts a Codex worker there. The first run loaded the
plant's server (see [Context](#context)): the person's call, 2026-11-02, is the fix below, inside this patch.

**The fix.** `argv`, for Codex, passes `-c 'projects."<path>".trust_level="untrusted"'` for its working directory and each tree
it reaches, after the sandbox keys. The operator's own Codex config still loads.

**The drill**, after the fix, starts the plant three ways and prints a line each:

| run | how | must print |
|---|---|---|
| the trusted twin | `argv`'s command with `trust_level="trusted"` in place of `untrusted` for the tree | `codex trusted plant: loaded` |
| the plant | `conduct.py agent --executor codex`, the production `argv` | `codex project config: not loaded` |
| the trust write | `~/.codex/config.toml` read before and after the runs, comparing only whether a `[projects."<tree>"]` header appeared | `codex trust written: yes` or `codex trust written: no` |

The drill edits no Codex config, and prints no line of it. `openspec/changes/0053-sandbox-patch/evidence/escape.md` records the
lines. The plant loaded under the production `argv` → the build halts on the `**HALT CHECK**`, and the person decides.

The stale MF trust entries in `~/.codex/config.toml` are the operator's to remove; no task edits that file.

### D7

`tests/escape_drill.py` also runs `Run.probe` once per executor in a scratch repo, printing `claude probe: held` and
`codex probe: held`, and every label it has. Its output goes to `evidence/escape.md`.

### D8

The build runs by hand, in a session with network: `/mf-build`, then `/mf-converge`, then `/mf-release`. Not `/mf-ship`.

## Tests

Counted at `136aa1e`: `uv run pytest --collect-only -q | tail -1` prints `97 tests collected`;
`grep -c '^def test_' tests/test_conduct.py` prints `32`. All below are integration tests in `tests/test_conduct.py`,
through `fake_worker.py`; none is end-to-end, and none runs on an engine.

| test | change | holds |
|---|---|---|
| `test_a_probe_halts_on_a_write_out` | added | D1: mode `unsandboxed` → the run halts naming the executor, the mark is gone; the default run passes |
| `test_a_forged_release_is_not_pushed` | added | D2: a forged tagged merge, a moved `refs/remotes/origin/main`, a release on a pushed head — each halts and `origin` receives nothing |
| `test_a_stale_lock_is_cleared_and_converge_resumes` | added | D3: a lock older than ten minutes is removed and logged; a lock halt resumes at Step 9 with no new round; a younger lock stays |
| `test_a_claude_worker_starts_in_the_sandbox` | edited | D1: `failIfUnavailable` |
| `test_a_worker_carries_the_allowlist_and_a_denial_is_named` | edited | D6: the Codex command marks its working directory and each reached tree untrusted; its twin is the drill's trusted plant, which loads |
| `test_a_run_pushes_only_tagged_merges` | edited | D2: its releases recorded in the ledger; a hand release left unpushed halts naming `git push` |
| `test_a_rerun_recovers_a_dead_release` | edited | `0051·R14`: carries `test_a_stop_survives_a_death`'s `.held` steps |
| `test_a_changed_git_config_halts_a_merge_in` | edited | `0052·R10`: the file named |
| `test_no_worker_pushes` | edited | `0052·R10`: the file named; `0052·R13`: a refused home folder logs `unkept` |
| `test_each_check_passes_only_on_disk_evidence` | edited | D1: its scratch `Makefile` takes the new recipe, and `check_probe` the mark |
| `test_a_stop_survives_a_death` | merged | per the table below |

| removed test | carried by | its assertions |
|---|---|---|
| `test_a_stop_survives_a_death` | `test_a_rerun_recovers_a_dead_release`, at its `0002-marks` step | a `.held` mark survives the death; the stage reads `released`; a re-run merges nothing |

Net: three added, one merged; `test_conduct.py` goes from `32` to `34`. Each guard's twin is a step in its own test, per `T6`.

## Dependencies

None.

## Risks / Trade-offs

- **The window** — a release forged on a head during that head's release passes. Stated in `THREAT_MODEL.md` and D51.
- **A hand release left unpushed now halts a run.** The halt names `git push`.
- **A lock younger than ten minutes** is left: a re-run right after the halt halts again, until the lock ages.
- **`-c` may not reach a `projects` entry** the operator's config holds. The plant through the production `argv` then still
  loads, and 1.3's `**HALT CHECK**` stops the build for the person.
- **Linux is unproven.** `failIfUnavailable`'s `-p` behaviour is undocumented; the probe holds the run either way.
- **The fake worker stands in for the sandbox** by a read-only mark: the gate proves the conductor's logic, and the drill
  proves the sandbox.

## Verdict

Ready to build.
