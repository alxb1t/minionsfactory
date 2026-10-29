# mf-ship — design

A script starts every station of every cut version as a fresh agent process and checks each from disk; a thin skill
starts the script and reports it; the release, the cut and integrate gain what an unattended run needs. Verdict:
ready to build. Scope is [the proposal](proposal.md); behaviour is [the delta](specs/sdd/spec.md).

## Context

Premises were re-checked on `main` at `c8136be` (v0.34.0) before the cut.

| evidence at the cut | implication |
|---|---|
| A worker is "a new host subagent or a fresh agent process" (`skills/mf-converge/SKILL.md:114`); no live skill runs a whole station in one | [D1](#d1)'s HALT CHECK, then [D2](#d2) |
| `claude --help` lists `-p`, `--model`, `--effort`, `--allowedTools`, `--disallowedTools`; `codex exec --help` lists `-m`, `-c <key=value>`, `-C <dir>`, `-s <sandbox>` | [D2](#d2)'s worker commands |
| The build's first HALT CHECK (2026-10-29): a headless `claude -p` subagent ran, and its write was denied — no permission flag | [D1](#d1) and [D2](#d2) carry the allowlist (the brief's Q23–Q31) |
| The second HALT CHECK, and a probe at the amend (2026-10-29): `--allowedTools` is variadic and swallows a prompt after it; `Write(path)` rules are ignored, `Edit(path)` covers every file tool; an absolute path needs `//`, symlink-resolved; `Bash(git:*)` allows `git commit`, the deny `Bash(git push --force:*)` wins (`Permission to use Bash with command git push --force origin main has been denied.`), a command off the list is refused (`… needs approval …`); `Skill` and `Agent` are the tool names | [D1](#d1)'s command, [D2](#d2)'s argv, list and denial strings |
| The third HALT CHECK (1.4) and a probe after it (2026-10-29): a compound command with a denied part is denied whole; a denial exits `0`; Claude Code's own guard refuses `$(…)`, shell variables, loops and `cd` before git whatever the list allows; redirects, pipes, `2>&1`, `git -C` and `pwd` pass; `cp`, `mv`, `touch` off the list are refused | [D2](#d2)'s shell rules, its added commands, and a denial reported, not halted on (the brief's Q32–Q35) |
| The phase-4 probe run and two probes after it (2026-10-29): a worker's shell commands are confined to its working directories — `ls` and `cat` of the primary's `.minions/` from a worktree were refused while an `Edit` rule let a write through; `--add-dir <container>` lifts it; with `Bash(rm:*)`, `rm` inside the container ran and `rm`, `rm -rf` outside it were refused (`needs approval. The path is outside the working directories`); the probe's `.gitignore` lacked `__pycache__/`; git fails under x86 binaries on this machine (`xcrun` architecture) | [D2](#d2)'s `--add-dir` and `rm`, [D9](#d9)'s prep (the brief's Q36–Q40) |
| Release Step 5 asks once (`skills/mf-release/SKILL.md:214-222`); its Never: "merge or push without the person's yes in this session" (`:274`); a hand-edit flag is for the human (`:133-134`, `:258-259`); Step 6's sentences name no worktree outcome (`:255-259`, `0038·N1`) | [D3](#d3) |
| The cut's suggestion "stays in chat" (`skills/mf-cut-change/SKILL.md:246-247`); its Never: "into the change, or into any file" (`:280`) | [D4](#d4) |
| Integrate's red gate halts with the merge open and no marker (`skills/mf-integrate/SKILL.md:109-110`); Step 2's table reads `MERGE_HEAD` with no note as an interrupted run (`:69`); Step 4.4 deletes the note (`:120`) | [D5](#d5) |
| `make install-skills` links every `skills/mf-*` (`Makefile:35-46`); `uninstall-skills` removes only links into its own checkout (`:52-59`) | `mf-ship` installs with no edit; phase 4 uninstalls from the worktree before restoring |
| D3 (`docs/decisions.md:39-46`) rejects "a deterministic runner"; D17 (`:197-207`) rejects "a merge without asking"; D41 (`:361-368`) keeps suggestions in chat | [D7](#d7) |
| `tests/test_skills.py:419-425` `_METRICS_SCRIPTS` pairs each station with its bundled script; `test_mf_integrate_runs_its_script` `:477` | [D6](#d6)'s pair joins it |
| `uv run pytest --collect-only -q \| tail -1` prints `58 tests collected` | [Tests](#tests) |

## Goals / Non-Goals

**Goal:** the person plans and cuts, starts `mf-ship`, and finds every version on the default branch with its
change-impact page.

**Non-goals:** see [the exclusions](proposal.md#not-in-this-change).

## Decisions

The grilling settled these choices (the brief's Q1–Q22); the build does not reopen them.

### D1

| id | decision | because | rejected |
|---|---|---|---|
| D1 | Phase 1 opens with a **HALT CHECK**: a fresh `claude -p` process dispatches a worker of its own | Converge, run as an agent process, must start its checkers; if it cannot, the design is wrong | Running stations as host subagents, which may not nest |

The check, run in a scratch directory:

```bash
d=$(cd "$(mktemp -d)" && pwd -P) && cd "$d" && claude -p "Start one subagent. It writes the word ok to probe.txt in the current directory. Wait for it to finish, then stop." --allowedTools "Read,Agent,Edit(/$d/**)" && cat probe.txt
```

`cat probe.txt` prints `ok`: a subagent can be started, and it inherits the process's allowlist. Anything else halts the
build: the plan is wrong.

### D2

| id | decision | because | rejected |
|---|---|---|---|
| D2 | `skills/mf-ship/scripts/conduct.py`, a stdlib `uv` script (PEP 723, `requires-python = ">=3.12"`, `dependencies = []`), is the loop; each station is one agent process, judged by a check on disk | Stations run for a long time; a script waits for free, and every loop decision is a check | An LLM session waiting on the workers; reimplementing a station |

**Commands.** Exits, as `integrate.py`'s: `0` done · `1` halt · `2` cannot run.

```
conduct.py status                        one line per open version: <change-id> · <branch> · <stage>
conduct.py check <stage> <change-id>     exit 0 when disk proves the stage; else 1 and a reason line
conduct.py log --verify <run-log>        exit 0 when the log is complete (below)
conduct.py run --executor claude|codex [--detach]   the loop; --detach starts it in a new session and returns
conduct.py agent --executor claude|codex <prompt>  one worker in the cwd, under the permissions below, its output to
                                                  .minions/runs/agent-<stamp>.log; its exit code
conduct.py report                        the last run's close-out lines
```

**An open version** is a `v*` branch the default branch does not contain, checked out in a linked worktree, holding
one active change directory under `openspec/changes/` outside `archive/`. Open versions sort by the change id's
number.

**The stage**, read in the version's worktree, first match wins:

| stage | when | the loop |
|---|---|---|
| `integrating` | `MERGE_HEAD` exists | halt: `.minions/integrate/<id>.red` → red gate; `.minions/integrate/<id>.md` → semantic conflict; neither → interrupted |
| `released` | `HEAD`'s subject is `chore(release): <tag>` and `<tag>` exists | halt: the release stopped before its merge |
| `human` | the first unticked `## Progress` line of `tasks.md` holds `**HUMAN` | halt, naming the phase |
| `build` | a `## Progress` box is unticked | `mf-build` |
| `converge-halted` | every box ticked; the newest `## Run` of `.minions/findings/<id>_status_log.md` has `· halt` on its first event line | halt |
| `converge` | every box ticked; the review and security files are not both `verdict: clean` with `head:` equal to `HEAD` | `mf-converge` |
| `integrate` | converge clean at `HEAD`; the default branch is not an ancestor of `HEAD` | `mf-integrate`, in the primary |
| `release` | converge clean at `HEAD`; the default branch is an ancestor of `HEAD` | `mf-release` with `merge=yes` |

A merge commit from integrate moves `HEAD` past the judged head, so the version reads `converge` again: that run
is the catch-up round.

**The checks**, run after each worker exits:

| stage | passes when |
|---|---|
| `build` | every `## Progress` box ticked; `git status --porcelain` prints nothing |
| `converge` | the review and security files are both `verdict: clean` with `head:` equal to `HEAD`; the tree clean |
| `integrate` | `HEAD`'s subject is `chore(integrate): merge <default-branch> into <branch>`; no `MERGE_HEAD`; the default branch an ancestor of `HEAD` |
| `release` | the default branch contains the branch; `<tag>` exists; with an `origin`, `git ls-remote --tags origin <tag>` prints a line |
| `probe` | the scratch repo's `HEAD` holds `probe.txt` reading `ok` |

**The loop** (`run`):

```
preconditions ─▶ status ─▶ every open version at a halt stage? ─ yes ─▶ halt, no worker
                    │ no
                  probe worker ─▶ check probe
                    │
  A · each version at build or converge, in parallel: spawn ─▶ wait ─▶ check, until integrate or release
                    │  every thread joined
  B · each open version, in change-id order: integrate ─▶ converge (catch-up) ─▶ release, by its stage
                    │
                  done
```

- **Preconditions** (exit 2): the cwd is the primary (`git rev-parse --path-format=absolute --git-dir` equals
  `--git-common-dir`), on the default branch, `git status --porcelain` empty; root `AGENTS.md` holds a line matching
  `\*\*Worktrees:\*\*`; the executor's CLI is on `PATH`, unless `MF_SHIP_AGENT` is set; no `.minions/runs/active`.
  `mkdir .minions/runs/active` claims the run; it is removed at `halt` and at `done`.
- **The probe** (Q11): a scratch repo under `tempfile.mkdtemp()` holding a `Makefile` whose `gate:` runs `true`,
  one commit; the probe worker's prompt is `In this directory, write the word ok to probe.txt, commit it with the
  message probe, then run make gate.`
- **A halt** — a failed check, a halt stage, a worker past its timeout — logs `halt`, starts no new worker, waits for
  the running ones, and exits 1. A halt never kills a worker that is still within its timeout.

**A worker.** The model and effort come from `.minions/models/<change-id>.toml` ([D4](#d4)): the station's table;
integrate uses `[release]`; a missing file or table passes no flag, and the log says `model: default`.

| executor | argv |
|---|---|
| `claude` | `claude -p <prompt> [--model <m>] [--effort <e>] --output-format stream-json --verbose --add-dir <tree> --allowedTools <allowed> --disallowedTools <denied>` — the prompt first: `--add-dir` and both list flags are variadic |
| `codex` | `codex exec [-m <m>] [-c model_reasoning_effort=<e>] -s workspace-write -c 'sandbox_workspace_write.writable_roots=["<run dir>","<git common dir>"]' -c sandbox_workspace_write.network_access=true -C <cwd> <prompt>` |
| `MF_SHIP_AGENT` set | `$MF_SHIP_AGENT <prompt>` — the injectable worker the tests use |

| station | cwd | prompt |
|---|---|---|
| build | the worktree | `Run the mf-build skill for change <change-id>.` |
| converge | the worktree | `Run the mf-converge skill for change <change-id>.` |
| integrate | the primary | `Run the mf-integrate skill.` |
| release | the worktree | `Run the mf-release skill for change <change-id> with merge=yes.` |

**Permissions.** Workers never bypass the harness's prompts; they act under a list — a guardrail, not a containment:
`make`, `uv` and `python3` run any code, and the line needs them.

| list | holds |
|---|---|
| allowed (Claude) | `Read`, `Glob`, `Grep`, `Agent`, `Skill`; `Edit(/<tree>/**)` — it covers every file-editing tool, and its leading `/` makes the absolute path `//`; `Bash(<cmd>:*)` for `git`, `uv`, `make`, `python3`, `openspec`, `gh`, `grep`, `sed`, `awk`, `head`, `tail`, `cat`, `ls`, `wc`, `echo`, `mkdir`, `rmdir`, `date`, `test`, `diff`, `find`, `sort`, `mktemp`, `cp`, `mv`, `touch`, `basename`, `dirname`, `readlink`, `tr`, `cut`, `rm`, and each command `AGENTS.md`'s `Ship tools:` line names |
| denied (Claude) | `Bash(git push --force:*)`, `Bash(git push -f:*)`, `Bash(git reset --hard:*)`, `Bash(git clean:*)`, `Bash(git branch -D:*)`, `Bash(git tag -d:*)`, `Bash(git worktree remove --force:*)` — deny wins over allow |
| Codex | `-s workspace-write`, the run directory and git's common directory writable, the network on |

`<tree>` is the directory `AGENTS.md`'s `Worktrees:` names, resolved from the primary — it holds the primary and
every version's worktree, since the cut writes into a new worktree and integrate into a version's; with no
`Worktrees:` (an `agent` call before a repo exists), the cwd. Every path is absolute and symlink-resolved (`Path.resolve()`) at run time. `Ship tools:` is an optional `AGENTS.md` line, `- **Ship tools:** \`npm\`, \`pnpm\``, read with
`\*\*Ship tools:\*\*`; MF declares none. `--add-dir <tree>` lets a worker's shell reach the run directory and the other worktrees; outside `<tree>` the shell's
file commands, `rm` among them, are refused. Code — `python3`, a `make` recipe — is not confined. Off the list:
`xargs` — it would run any command; `cd` — Claude Code refuses it before git whatever the list says, and the stations use `git -C`.

**A denial does not halt; the check decides.** Each denial — a `tool_result` with `is_error` holding `has been denied`
or `needs approval` in the worker's stream-json log — is logged as a `denied` event, named from its `tool_use`, and
listed in the report. A worker that adapted inside the list and passed its check did nothing off the list. A failed
check's `halt` line names the denials before it: `halt — build check fail — box 2.1 unticked · denied: Bash(rm -rf
build)`.

**The shell rules**, appended to every worker's prompt — `run` and `agent` alike — as one paragraph:

> Shell rules for this run: one command per Bash call; no `$(…)`, shell variables or loops — run the inner command
> first and use its output literally; use `git -C <dir>`, never `cd`; never retry a denied command in a rewritten
> form to get past the list.
The `start` line records `permissions: allowlist` or `permissions: workspace-write`.

Each worker runs in its own process group (`start_new_session=True`), stdout and stderr to
`.minions/runs/<stamp>/<change-id>_<station>.log`; past 3 hours (`TIMEOUT = 10800`) the group is killed and the run
halts.

**The run log** is `.minions/runs/<stamp>.md`, `<stamp>` the start as `%Y%m%d-%H%M%S`, `-2`, `-3`, … appended when
the name is taken. It opens `# Ship run
<stamp>`, then one line per event, appended under a lock (`mkdir .minions/runs/<stamp>.lock`, `rmdir` after):

```
<HH:MM:SS> · <change-id or run> · <event> — <detail>
```

Events: `start` · `spawn` (`<station> · model <m>`) · `finish` (`<station> · exit <code> · <seconds>s`) ·
`check` (`<stage> · pass` or `fail — <reason>`) · `denied` (`<station> · <tool>(<input>)`) · `halt` (`<reason>`) ·
`done`. `log --verify` exits 1 on an
unknown event, a `spawn` with no later `finish` for the same version and station, or a last line that is neither
`halt` nor `done`.

**The report** prints, per version the last run touched: its tag, the merge commit, `pushed` or `no origin`, the
review file's `round:`, the cards under its `## <change-id>` heading in `.minions/backlog.md`, and
`.minions/metrics/<change-id>.html` when it exists, else `metrics: none`; then the run's last line.

### D3

| id | decision | because | rejected |
|---|---|---|---|
| D3 | `mf-release` takes `merge=yes`: it prints the ask instead of asking; a hand-edit flag halts after the tag, before the merge; the close-out names the worktree's outcome | Starting `mf-ship` is the person's yes for the run (Q1, Q8); unread preamble prose must not ship unattended (Q4); `0038·N1` | A release that merges with nobody's yes |

`skills/mf-release/SKILL.md`:

- Frontmatter `description`: `then on the person's yes merge into the default branch and push` → `then on the
  person's yes, or merge=yes from mf-ship, merge into the default branch and push`.
- The opening blockquote: `you run them only on the person's yes, asked once in Step 5.` → `you run them only on the
  person's yes: asked once in Step 5, or given as \`merge=yes\` by the person who started \`mf-ship\`.`
- After *Parameter — the change id*, a new section:

  ```markdown
  ## Parameter — merge

  `merge=yes` is given only by `mf-ship`: the person who started it said yes to every merge and push of the run.
  It replaces Step 5's ask, never a check. Echo `merge: yes (mf-ship)`. Any other value → **halt**.
  ```

- Step 2, after the hand-edit paragraph: `Under \`merge=yes\`, a flag halts the release after Step 4 and before
  Step 5: the person reads the prose, then merges.`
- Step 5, after `In a linked worktree, ask the form below instead.`: `Under \`merge=yes\`, print the ask and take it
  as yes.`
- Step 6's sentences, after `and the merge and the push, or that there is no \`origin\``: `; and the worktree removed,
  kept or refused`.
- Never: `**Never merge or push without the person's yes in this session**` → `**Never merge or push without the
  person's yes in this session, or \`merge=yes\`**`.

### D4

| id | decision | because | rejected |
|---|---|---|---|
| D4 | The cut writes its suggestion to `.minions/models/<change-id>.toml` as well as showing it; never into the change | `mf-ship` reads it (Q10, Q16); run configuration the person may edit; model names would age in the archive | A file in the change; the session's model for every station |

`skills/mf-cut-change/SKILL.md`, *Suggesting models*: `Suggestions stay in chat, never in tracked prose.` → `Show the
suggestion in chat, then write it to \`.minions/models/<change-id>.toml\`, the run directory's, for \`mf-ship\`;
never into tracked prose.` After the existing suggestion block, add:

```toml
[build]
model = "<offered model>"
effort = "<effort>"        # only where the host exposes it
[converge]
model = "<offered model>"  # skip = true for "skip, read by hand"; mf-ship runs converge anyway
[release]
model = "<offered model>"
```

The Never line: `Never write the model suggestion into the change, or into any file.` → `Never write the model
suggestion into the change, or into a tracked file.`

### D5

| id | decision | because | rejected |
|---|---|---|---|
| D5 | Integrate's red gate writes `.minions/integrate/<change-id>.red`; Step 2 reads it as a resumed run; the commit deletes it | `conduct.py` tells a red gate from an interrupted run (Q9) | Reading the halt from chat |

`skills/mf-integrate/SKILL.md`:

- Step 4.1: `**Red → halt** with the merge open, commit nothing, and never weaken the gate to pass.` → `**Red →
  halt** with the merge open, commit nothing, write \`.minions/integrate/<change-id>.red\` holding \`gate red\` and
  the date, and never weaken the gate to pass.`
- Step 2's table gains a row after the note row: `| succeeds | \`.minions/integrate/<change-id>.red\` exists | the
  person fixed the merged tree: Step 3.3 |`.
- Step 4.4: `Delete \`.minions/integrate/<change-id>.md\` when it exists` → `Delete
  \`.minions/integrate/<change-id>.md\` and \`.red\` when they exist`.

### D6

| id | decision | because | rejected |
|---|---|---|---|
| D6 | `skills/mf-ship/SKILL.md` is the front door: it checks, starts `conduct.py run` detached, and reports; a second `/mf-ship` shows a live run's status, or reports the last run and starts the next | A skill session cannot wait hours for its workers (Q15); a re-run is the resume (Q4) | The skill running the stations |

The skill, written to the P rules, holds:

- **Frontmatter** — `name: mf-ship`; `description:` takes every cut version to the default branch unattended —
  builds and converges them in parallel, then integrates, runs the catch-up round and releases each in cut order,
  merging and pushing without asking. Use in the primary checkout once versions are planned and cut.
- **The role** — `Your role is SHIP.` You start one run and report it. You run no station yourself: the script starts
  each as a fresh agent process and checks it from disk. Starting a run is the person's yes to every merge and push
  in it.
- **A diagram** of the run, as [D2](#d2)'s loop.
- **Parameters** — none; the cwd is the primary. **The script** is `scripts/conduct.py`, run as `uv run --script
  <this package>/scripts/conduct.py <command>`, its exits as [D2](#d2)'s.
- **Step 1 — Preconditions** — read root `AGENTS.md` and its mandatory context; the primary; the default branch,
  clean; `Worktrees:` declared, else halt naming it; `uv` runs; the executor from runtime evidence — Claude Code →
  `claude`, Codex → `codex`, any other → halt naming it (D11).
- **Step 2 — State** — `conduct.py status`, pasted. `.minions/runs/active` exists → report the status and the run
  log's last lines, then stop: a run is live. Else run `conduct.py report` and keep its lines.
- **Step 3 — Start** — no open version → report `nothing to ship`, stop. Else start detached:
  `uv run --script <this package>/scripts/conduct.py run --executor <executor> --detach`, then
  confirm `.minions/runs/active` exists within 10 seconds, else halt. Say once that every worker acts under
  [D2](#d2)'s allowlist, with no permission prompt.
- **Step 4 — Report** — at most three sentences: the last run's report, or that a run started and its log path;
  the command to follow it, `tail -f .minions/runs/<stamp>.md`. Last line: `Next: /mf-ship again for its status, or
  its report once it ends.`
- **Never** — run a station, merge or push yourself; start a second run while one is live; edit or delete a run
  log; pass `merge=yes` anywhere but through the script.

`tests/test_skills.py:419-425`: `_METRICS_SCRIPTS` gains `("mf-ship", "scripts/conduct.py")`, and
`test_the_metrics_script_scan_reports_a_missing_script` expects
`"skills/mf-ship/SKILL.md: scripts/conduct.py: not named"` after the `mf-integrate` line in both expected lists.

### D7

| id | decision | because | rejected |
|---|---|---|---|
| D7 | D3, D17 and D41 amended in place; D47 added after D45 | The decisions say what holds (A7); titles kept, so no anchor moves | New decisions beside stale ones |

`docs/decisions.md`, each body, before → after:

- **D3:** the bold paragraph → `**The stations are the skills. A person conducts them, or \`mf-ship\`'s script starts
  each as a fresh agent process and checks it from disk (D47). No station is reimplemented: there is no third way to
  run the line.**`; *Rejected:* → `a runner that reimplements the stations · an LLM session waiting on long-running
  stations.`
- **D17:** `Then it asks once; on yes it merges` → `Then it asks once; on yes — or \`merge=yes\`, the yes the person
  gave by starting \`mf-ship\` — it merges`; *Rejected:* `a merge without asking` → `a merge nobody said yes to:
  \`merge=yes\` comes only from a run the person started`.
- **D41:** `Suggestions stay in chat and leave model selection` → `The cut shows the suggestion and writes it to
  \`.minions/models/<change-id>.toml\`, never into the change, for \`mf-ship\`; model selection`.

D47, after D45:

```markdown
### D47 · `mf-ship` takes cut versions to the default branch unattended

**Run in the primary, `mf-ship` starts `conduct.py`, which builds and converges every open version in parallel,
then integrates, runs the catch-up round and releases each in cut order with `merge=yes`. Each station is a fresh
agent process under `conduct.py`'s allowlist — Claude Code — or the workspace-write sandbox — Codex — never with
prompts bypassed, and is judged by a check on disk; the first failed check halts the run, and a re-run resumes from
disk.**

- **Why:** once versions are planned and cut, what follows is the line's; the pilot ran it by hand in a dozen
  commands.
- **Rejected:** an LLM conductor waiting on the workers · `mfa-*` copies of the stations · a state file · workers that
  bypass permission prompts: the list blocks what is off it, though `make`, `uv` and `python3` still run any code.
```

### D8

| id | decision | because | rejected |
|---|---|---|---|
| D8 | The front door, the map and the shared context name `mf-ship` | A station nobody can find is not shipped | — |

- `README.md:18`: `conducted by a person today · by an LLM conductor held by scripts: designed, not built` →
  `conducted by a person, or by mf-ship: a script that starts each station as a fresh agent process`; the skills
  table gains, after `mf-release`: `| [\`mf-ship\`](skills/mf-ship/SKILL.md) | take every cut version to the default
  branch unattended — build, converge, integrate, release |`.
- `AGENTS.md:29-30`: `and \`mf-integrate\`, which merges a moved base into the next version.` → `\`mf-integrate\`,
  which merges a moved base into the next version, and \`mf-ship\`, which takes cut versions to the default branch
  unattended.`
- `CONTRIBUTING.md`, after the *Side by side* bullet: `- **Unattended** — \`mf-ship\` takes cut versions to the
  default branch ([D47](docs/decisions.md#d47--mf-ship-takes-cut-versions-to-the-default-branch-unattended)).`
- `docs/README.md`, the `skills/` row: `the bundled metrics script` → `the bundled scripts`.

### D9

| id | decision | because | rejected |
|---|---|---|---|
| D9 | The acceptance run is the `mf_ship_probe` fixture: a container at `../mf_ship_probe/` from MF's primary, its primary `mf_ship_probe/mf_ship_probe/`; prep, two cuts from the briefs below, `/mf-ship` | Two features built side by side need disjoint files; fixed briefs make the run cheap and repeatable (Q20, Q21) | `/tmp`; grilling the probe's versions |

**The prep commit**, on the probe's `main` after `/mf-bootstrap`:

- `Makefile`, after the `openspec validate` line of `gate:`, a recipe line (tab-indented):
  `python3 -m unittest discover -s tests`.
- `tests/test_smoke.py`:

  ```python
  import unittest


  class Smoke(unittest.TestCase):
      def test_runs(self) -> None:
          self.assertTrue(True)
  ```

- `.gitignore`, a line `__pycache__/`: the gate's `unittest` writes it, and a station's check needs a clean tree.
- `AGENTS.md`, at its end:

  ```markdown
  ## Workspaces

  - **Worktrees:** `../` — a version's worktree is `<this path>/<branch>`, relative to the primary checkout.
  - **Workspace setup:** none.
  ```

- The commit: `chore: a unittest gate and worktrees`.

**The todo brief**, written to `../mf_ship_probe/briefs/todo.md`:

```markdown
# todo · a minor · hard · 2026-10-29

**`todo.py add "<text>"` appends an item to `todo.txt`; `todo.py list` prints the items, numbered.**

## Facts
- The repo holds no code; the gate runs `python3 -m unittest discover -s tests`.

## Decisions
| # | decision | the reason that settled it |
|---|---|---|
| Q1 | `todo.py`, stdlib only: `add <text>` appends one line to `todo.txt` in the cwd; `list` prints `<n>. <text>` per line from 1, and nothing when there is no file. | The smallest todo. |
| Q2 | `tests/test_todo.py`, `unittest`, a temporary directory per test: add then list; list with no file. | Unit tests only. |
| Q3 | One phase; no dependency; converge runs. | A probe. |

## Phases
1 · todo.py and its tests

## Not in this
- Done marks, deletion, `README.md`.

## For the cut
- Change `0001-todo` · version `v0.1` · branch `v0.1_todo`.
- Acceptance: `make gate` exits 0; `python3 todo.py add milk && python3 todo.py list` prints `1. milk`.
```

**The marks brief**, written to `../mf_ship_probe/briefs/marks.md`:

```markdown
# marks · a minor · hard · 2026-10-29

**`marks.py` marks an item done and unmarks it.**

## Facts
- The repo holds no code; the gate runs `python3 -m unittest discover -s tests`.

## Decisions
| # | decision | the reason that settled it |
|---|---|---|
| Q1 | `marks.py`, stdlib only: `mark(text)` returns `"[x] " + text`, unchanged when already marked; `unmark(text)` drops a leading `"[x] "`. | Independent of any other module. |
| Q2 | `tests/test_marks.py`, `unittest`: mark, mark twice, unmark, unmark an unmarked item. | Unit tests only. |
| Q3 | One phase; no dependency; converge runs. | A probe. |

## Phases
1 · marks.py and its tests

## Not in this
- A command line, `todo.txt`, `README.md`.

## For the cut
- Change `0002-marks` · version `v0.2` · branch `v0.2_marks`.
- Acceptance: `make gate` exits 0; `python3 -c "import marks; print(marks.mark('milk'))"` prints `[x] milk`.
```

**The hand-over** the build prints at phase 4: open a fresh session in MF's primary and prompt
`Run phase 4 of 0040-mf-ship's tasks.md, the checklist, step by step.`; read its report; then run
`/mf-build 0040-mf-ship` in `../v0.35_mf_ship`.

## Tests

`tests/test_conduct.py` is new; `tests/test_skills.py` extends `_METRICS_SCRIPTS` and its breach test (`T2`).

| layer | at cut | added | removed | proof |
|---|---:|---:|---:|---|
| Unit test functions | 58 | 10 | 0 | `uv run pytest --collect-only -q \| tail -1` prints `58 tests collected` at the cut, `68 tests collected` after |
| Integration tests | 0 | 0 | 0 | — |
| End-to-end runs | 0 | 0 | 0 | — |

The new tests, each over git repos built in `tmp_path` and a fake agent through `MF_SHIP_AGENT` — a Python script
that reads the prompt and does on disk what that station would (ticks boxes, writes findings, commits, merges):

| test | holds |
|---|---|
| `test_status_reads_each_stage_from_disk` | every row of [D2](#d2)'s stage table |
| `test_each_check_passes_only_on_disk_evidence` | each stage's check passes, and fails with its reason |
| `test_log_verify_finds_an_unpaired_spawn_and_an_open_end` | `log --verify` |
| `test_run_ships_two_versions_in_cut_order` | the whole loop: both merged, the later integrated and caught up first |
| `test_run_halts_on_a_human_phase` | the halt, no release after it |
| `test_run_halts_when_a_worker_claims_what_disk_does_not_show` | a worker exits 0 with a box unticked |
| `test_run_halts_on_a_timeout` | a worker past a shortened `TIMEOUT` is killed; the run halts |
| `test_a_rerun_resumes_from_disk` | after a halt is handled, finished stations do not run again |
| `test_run_refuses_without_worktrees_declared` | exit 2, no worker started |
| `test_a_worker_carries_the_allowlist_and_a_denial_is_named` | the argv per executor — the prompt first, `--add-dir` the resolved tree, `Bash(rm:*)` allowed, `Edit(//…)` on a resolved path, no `Write(` — `Ship tools:` added, the shell rules appended; each denial string in a log becomes a `denied` event, a passing check
still passes, and a failing check's `halt` names the denial |

The HALT CHECK, task 1.4's probe and the phase-4 run spend model tokens and stay outside the gate.

## Dependencies

None.

## Risks / Trade-offs

- **The allowlist is a guardrail, not a containment** — `make`, `uv` and `python3` run any code; Bash writes are not
  path-bound (old D24) → named, not solved; the probe worker proves a worker can act before any station runs.
- **A detached run outlives the session** → its log and `.minions/runs/active` show it; `/mf-ship` reports it.
- **The installed skills are `main`'s during this build** → phase 4 points them at this worktree, then back.
- **Parallel builds share the machine** → MF's gate binds nothing; a target whose gate does is a later trigger.
- **The Codex row is untested on this machine** → its flags are read from `codex exec --help`; phase 4 runs Claude only.
  The first Codex run is its check.

## Migration Plan

```
1 HALT CHECK · conduct.py ─▶ 2 release · cut · integrate ─▶ 3 mf-ship · decisions · docs ─▶ 4 HUMAN · METERED probe
```

Each phase ends on a green gate. Nothing is irreversible; the probe is deleted at its end.

## Verdict

Ready to build. Acceptance: the HALT CHECK prints `ok`; `conduct.py`'s tests pass with a fake agent; the release
takes `merge=yes`; the cut writes the models file; integrate marks a red gate; the probe's two versions reach its
`main` through `/mf-ship`.
