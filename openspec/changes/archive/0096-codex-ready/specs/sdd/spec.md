## MODIFIED Requirements

### Requirement: The ship station judges every station from disk

`skills/mf-ship/scripts/conduct.py` SHALL decide each version's stage from git and the run directory alone, and SHALL
pass a station only when the worker exits 0 and its check on disk passes — never on the worker's report. The converge
check SHALL need `done` as the newest run's latest status-log event. Before the
first station it SHALL run a probe worker that must edit, commit and run `make gate` in a scratch repo, or halt. The scratch
gate's recipe SHALL try a write to a file `conduct.py` made outside the worker's reach, and SHALL pass only when that write is
refused; `conduct.py` SHALL halt the run when the file changed, and SHALL remove it. The recipe SHALL also pass only
when the shell's `uname -m` is the host's native architecture, so a worker whose shell runs translated halts the run, naming
its executor. A Codex probe that passes SHALL then run one conformance checker over a fixture change in a second scratch
repo, and SHALL pass only when the checker leaves `.minions/changes/0001-probe/conformance.md`, a file and no link, whose
frontmatter holds every key of the findings file contract, `type: conformance` and `plan: 0001-probe`, and when its log holds
a usage event; the checker's verdict SHALL be logged and never judged.
It SHALL log every worker's start, end and check to `.minions/runs/<stamp>.md`, and `conduct.py log --verify` SHALL
fail on a worker with no end, a run that ends on neither `halt` nor `done`, or an unknown event.

#### Scenario: A worker reports success that disk does not show
- **WHEN** a build worker exits 0 and a `## Progress` box is still unticked
- **THEN** the build check fails and the version halts

#### Scenario: A run's log is complete
- **WHEN** a run ends
- **THEN** `conduct.py log --verify` exits 0 on its log

#### Scenario: A worker dies after clean findings
- **WHEN** a converge worker exits 1 with both findings files clean at `HEAD` and no `done` in its status log
- **THEN** the version halts, naming the exit, and nothing is released

#### Scenario: A probe worker runs unsandboxed
- **WHEN** the probe worker's write outside its reach lands
- **THEN** the run halts naming the probe's executor, no version starts a worker, and the file is gone

#### Scenario: A worker's shell runs translated
- **WHEN** the probe worker's shell reports `x86_64` on an `arm64` host
- **THEN** the run halts, naming the executor and both architectures, and no version starts a worker

#### Scenario: A Codex checker probe writes no findings file
- **WHEN** a Codex probe passes its scratch edit, and its checker exits 0 leaving no `conformance.md`
- **THEN** the probe fails, naming the missing file, and no station runs on Codex
- **AND WHEN** the checker leaves a findings file with every contract key and `verdict: clean` over the fixture's defect
- **THEN** the probe passes, and its check line names the verdict

### Requirement: A station's executor comes from the models file

`.minions/changes/<change-id>/models.toml` MAY name `executor = "claude"` or `"codex"` in any station's table; absent, the station
runs on the run's executor. Integrate SHALL use the `[release]` table. `conduct.py` SHALL halt a version, before its
worker starts, on an `executor` it does not know and on a `codex` station with a `claude-*` model. It SHALL run one probe
worker per distinct executor named across the open versions and the run's own; a failed probe at the start SHALL stop the
run, and one for a joining version SHALL halt only the versions on its executor.
A station on Codex SHALL report each denial, its usage limit with the reset time, its tokens and its priced cost from its JSON
event log, as a station on Claude does from its own; converge's per-role tokens SHALL read `unavailable` on Codex.

#### Scenario: Converge on Codex beside a build on Claude
- **WHEN** a version's models file names `executor = "codex"` under `[converge]`
- **THEN** its converge runs as `codex exec`, and its build and release as `claude -p`
- **AND** the run probes both executors before any station

#### Scenario: A model the executor cannot run
- **WHEN** a table names `executor = "codex"` and `model = "claude-opus-5-5"`
- **THEN** that version halts naming the table, and no worker starts for it

#### Scenario: A Codex worker is refused a command
- **WHEN** a Codex worker's command fails with the sandbox's `Operation not permitted`
- **THEN** the run log holds a `denied` line naming the command, and the report lists it

#### Scenario: A Codex worker meets its usage limit
- **WHEN** a Codex worker exits 1 after a failed turn whose error names its usage limit and a time to try again
- **THEN** its version halts with `stopped by a usage limit · resets <time>`

### Requirement: A worker's reach stops at the repository

A Codex worker's writable roots and a Claude worker's `Edit` and `--add-dir` SHALL be the primary and each open worktree,
from `git worktree list`, and never the directory holding them. A listed worktree whose `.git` file does not point back to
an entry under the common directory SHALL be no worktree. `conduct.py` SHALL take the primary and its common directory once,
before the first worker, and SHALL never take a worker's reach from git's answer in a worktree. It SHALL refuse a run in a
checkout whose `.git` names another repository, and SHALL halt a Codex worker when the primary's `.git` no longer resolves to
that common directory. Directly before each Codex worker starts, `conduct.py` SHALL halt its version when any writable root
or its working directory is a link or no longer resolves to itself, naming the path. `conduct.py` SHALL load `integrate.py`
once, before the first worker, and SHALL halt a version's merge when the local git config or `info/attributes` changed since
then.

#### Scenario: A sibling project
- **WHEN** a worker runs in a repository whose parent holds other projects
- **THEN** no writable root and no `--add-dir` names that parent

#### Scenario: A worker forges a worktree entry
- **WHEN** a worker adds an entry under the common directory's `worktrees/` naming a directory outside the repository
- **THEN** no writable root and no `--add-dir` names that directory, and no version runs in it

#### Scenario: A worker repoints a worktree
- **WHEN** a worker rewrites a worktree's `.git` file or its entry's `commondir` to name another repository
- **THEN** no writable root and no `--add-dir` of the next worker names that repository

#### Scenario: A worker plants git config
- **WHEN** a worker changes the common directory's config during a run
- **THEN** the conductor merges nothing for a dependent, and that version halts, naming the change

#### Scenario: A worker swaps a writable root for a link
- **WHEN** a worker moves a listed worktree aside and puts a link to a sibling project in its place, and the next station of
  a version runs on Codex
- **THEN** that version halts naming the link, and no Codex worker starts with the sibling among its writable roots

### Requirement: A worker runs in an OS sandbox

A Claude worker SHALL run with Claude Code's sandbox on, `allowUnsandboxedCommands` false and `failIfUnavailable` true, writing
only to the primary, the open worktrees and the common directory: a sandbox that cannot start SHALL end the worker, never run
it unsandboxed. The operator's credential paths SHALL be denied to its scripts and to its `Read` tool,
and the credential variables unset for its scripts. It SHALL load user settings alone, so a project's settings, hooks and
`.mcp.json`, which a worker can write, start nothing, and SHALL start with `--strict-mcp-config` and no `--mcp-config`, so the
MCP servers of the operator's own config start nothing; the run's probe SHALL fail when a Claude worker's `init` event lists an
MCP server, naming it. Its network SHALL reach only `pypi.org`, `files.pythonhosted.org` and the
domains `AGENTS.md`'s `Ship network:` line names, and its sandbox SHALL never have `allowLocalBinding`: it binds no
loopback port, in any repo. A Codex worker SHALL run with its network off, and SHALL
start with its working directory and every tree it reaches marked untrusted, whatever the operator's Codex config says, so a
project's `.codex/` config, hooks and rules, which a worker can write, start nothing. A Codex worker SHALL start with
`--ignore-user-config`, so the operator's Codex config — its MCP servers, plugins, profiles and model — starts nothing and
sets nothing, and with `--json`, so its log is one event a line; the run's probe SHALL fail when a Codex worker's log holds an
MCP tool call, naming its server. A Codex worker SHALL never have `/tmp` as a writable root. Both SHALL keep `uv`'s cache in
the run directory, and both SHALL start with `TMPDIR` naming `.minions/tmp/`, which a run empties at its start, halting when
`.minions` is a link; a Claude worker's sandboxed command may take Claude Code's own `TMPDIR` instead, inside its sandbox, and a
Codex worker SHALL never take `TMPDIR` as a writable root of its own. Neither SHALL inherit the conductor's `VIRTUAL_ENV`.

#### Scenario: A script tries to leave
- **WHEN** a worker or its subagent runs a script that writes outside its reach, reads `~/.ssh`, reads a credential variable and
  calls an unlisted domain, the npm registry among them
- **THEN** each fails, on Claude; on Codex the read may pass, and that is a stated gap

#### Scenario: A worker uses its Read tool on a credential
- **WHEN** a Claude worker or its subagent calls `Read` on a path under `~/.ssh`
- **THEN** the call is denied, and the report lists the denial

#### Scenario: A worker plants a start-up
- **WHEN** a worker leaves a `SessionStart` hook in `.claude/settings.local.json`, or a server in `.mcp.json`
- **THEN** neither runs at the next Claude start

#### Scenario: The operator has MCP servers
- **WHEN** the operator's user config names an MCP server
- **THEN** a Claude worker's command line holds `--strict-mcp-config` and no `--mcp-config`
- **AND WHEN** a Claude probe worker's `init` event lists an MCP server all the same
- **THEN** the probe fails, naming the server, and the run halts

#### Scenario: The operator has a Codex config
- **WHEN** the operator's `~/.codex/config.toml` names a model, an MCP server and a plugin
- **THEN** a Codex worker's command line holds `--ignore-user-config` and `--json`
- **AND WHEN** a Codex probe worker's log holds an MCP tool call all the same
- **THEN** the probe fails, naming the server, and no station runs on Codex

#### Scenario: A worker plants a Codex project config
- **WHEN** a worker leaves an `[mcp_servers]` entry in `.codex/config.toml`, in a tree the operator's Codex config trusts
- **THEN** it does not run at the next Codex worker's start
- **AND** no Codex worker's start writes a trust entry to the operator's Codex config

#### Scenario: The sandbox cannot start
- **WHEN** a Claude worker starts on a machine where Claude Code's sandbox cannot start
- **THEN** the worker ends without running a command, and its version halts on the exit

#### Scenario: A repo's gate serves on loopback
- **WHEN** a Claude worker runs a gate that binds `127.0.0.1`
- **THEN** the bind is refused, and the worker's sandbox has no `allowLocalBinding`

#### Scenario: A worker makes a scratch file
- **WHEN** a worker on either executor runs `mktemp`
- **THEN** the file is made inside its sandbox: under the primary's `.minions/tmp/` on Codex, and on Claude there or under
  Claude Code's own `TMPDIR`
- **AND WHEN** the next run starts
- **THEN** `.minions/tmp/` is empty, and a link there is replaced by a folder, its target untouched
- **AND WHEN** a run starts with `.minions` a link
- **THEN** it halts, naming the link, and its target's `tmp` keeps its files

#### Scenario: A worker links the scratch folder out
- **WHEN** a worker replaces `.minions/tmp` with a link to a folder outside its reach, and a Codex worker starts
- **THEN** that worker's command line excludes `TMPDIR` from its writable roots, so the link's target is not one

#### Scenario: The conductor runs in a uv environment
- **WHEN** `conduct.py` runs with `VIRTUAL_ENV` set, and starts a worker on either executor
- **THEN** the worker's environment holds no `VIRTUAL_ENV`

### Requirement: Each release records its run

`metrics/catalogue.toml` SHALL declare the run metrics, each one script, `scripts/metrics/run.py <kind>`, which the release's
`metrics.py collect` runs: minutes from the run logs for the lead (the cut commit to the release's spawn), each stage — build,
converge, catch-up, integrate — and the person's waits (a halt until a rejoin, a person's grant or a later run's start names the
version); converge's rounds outside catch-up and amend runs, the amend rounds, round 1's blockers and the grants; the halts by
station; the rescues fixed and diagnosed; build and
fix commits, split at the build's `.done` head along the first parent; cost and tokens, all turns, total and per station, and the
cost per changed line; per role — conformance and adversarial, each metric id named for its role — the confirmed and refuted
cards and the tokens per confirmed card; the escapes — cards whose
`repeat of` names an earlier change, save the cards the change pays; and the cards it carried to the debt and paid. A metric whose
data a run did not leave — no run log, a log a spawn overwrote, the release's own stage — SHALL exit non-zero, a gap, never a
zero. A Codex station's tokens SHALL be the sum over its log's `turn.completed` events of their input and output tokens, and
its dollars those tokens priced by `skills/mf-review-metrics/prices.toml` under the model its log's spawn line names; a model
with no row there, or no model named, SHALL make the cost metrics a gap naming it, and SHALL leave the token metrics read. The
cut's `diff-lines` and `diff-files` SHALL be the collector's station values.

#### Scenario: A version with its run
- **WHEN** a version's run log, status log, findings and station logs are on disk at its release's collect
- **THEN** its data file holds the minutes per stage, the rounds, the cost per station and each checker's yield, under
  `conformance-confirmed` and `adversarial-confirmed`

#### Scenario: An amend round
- **WHEN** a version's status log holds a run marked `· amend`
- **THEN** `amend-rounds` counts it, and `converge-rounds` reads no round of it

#### Scenario: A version released by hand
- **WHEN** a version has no run log
- **THEN** every minute, cost and halt metric is a gap, and the commit and card metrics are read

#### Scenario: A converge on Codex
- **WHEN** a version's converge log is a Codex JSON log whose spawn line names a model the price table holds
- **THEN** `cost-usd-converge` holds its priced dollars and `tokens-converge` its summed tokens
- **AND WHEN** the price table holds no row for that model
- **THEN** `cost-usd-converge` is a gap naming the model, and `tokens-converge` is read

### Requirement: The review-metrics station charts past findings, read-only

`skills/mf-review-metrics/scripts/review_metrics.py` SHALL read the repos named in
`$XDG_CONFIG_HOME/minionsfactory/review-metrics.toml`, else `~/.config/minionsfactory/review-metrics.toml`, or in
`--config` and `--repo`, and SHALL halt naming the config path when neither names a repo. It SHALL read each repo's
`.minions/changes/<change-id>/` files and its worker logs, `.minions/changes/<change>/logs/<stamp>-<station>.log` and
`<stamp>-<station>-<n>.log` — in a repo no run has moved, the old `.minions/findings/` and `.minions/runs/<stamp>/<change>_<station>.log`
and `-<n>.log` alike — and the operator's Codex sessions,
`~/.codex/sessions/**/*.jsonl`, without writing to any repo,
parse each field it can, record a field it cannot as a gap —
never a zero — and write one self-contained HTML page, with no script, to the config's `out` or `--out`. It SHALL read a change's
`conformance.md`, else its `review.md`, and its `adversarial.md`, else its `security.md`, and SHALL record each role by the name
its file or line carries. The page
SHALL hold a table per repo and per model, a cost table per repo — each change's stations with their dollars, turns, tokens and
seconds — charts over changes drawn by `mf-build`'s `chart()`, and the list of fields each repo lacked. A log's dollars and tokens
SHALL be its last result event's cumulative `total_cost_usd` and `modelUsage`, its turns and seconds the sum over its result events;
a Codex JSON log's tokens SHALL be the sum over its `turn.completed` events of their input and output tokens, its dollars those
tokens priced by `skills/mf-review-metrics/prices.toml` under the model its spawn line names, a gap with no such row, and its
turns and seconds gaps;
a station with no log and a log with neither result nor `turn.completed` event SHALL be a gap, and a station the run log shows spawned more times than
the logs read SHALL be marked `<read> of <spawns>`. The status log's tokens SHALL be read per role, in every form a `verdicts` line
holds; a line naming both roles SHALL be recorded under the role `both`, credited to neither. A Codex worker's tokens SHALL be read from its session — the
last `token_count` event's totals, its model and effort from `turn_context` — matched to its round by its parent's `cwd` — the change's worktree, or the primary
when no other version's round overlaps — and the round's freeze-to-verdicts window, the guardian sessions left out, and never
into a round its line names `executor claude`. It SHALL write `review-metrics.json`
beside the page: one record per round and role, with its executor, model, effort, tokens and source, a gap as `null`. It SHALL read no tier, and SHALL count a file's `inconclusive` sections only when the file holds
`## Refuted`, the review method's mark. It SHALL give numbers, never a recommendation.

#### Scenario: No config
- **WHEN** the script runs with no config file and no `--repo`
- **THEN** it exits 2, naming the config path it looked for, and writes nothing

#### Scenario: A repo of each layout
- **WHEN** one repo holds `.minions/changes/<id>/` and another the old `.minions/findings/` and `runs/<stamp>/` logs
- **THEN** both repos' changes are read, with their cost, and neither is written

#### Scenario: Both role names
- **WHEN** one change's folder holds `conformance.md` and `adversarial.md`, and another's `review.md` and `security.md`
- **THEN** both changes are read, each round recorded under the role names its files and lines carry

#### Scenario: Files from every era
- **WHEN** a repo holds a findings file with no cards, one with cards and no `## Refuted`, a status log, and a file with
  the verdict states and `## Refuted`, with or without a `tier:` line
- **THEN** each record carries what its file holds, every missing field is a gap, and the page lists the gaps per repo

#### Scenario: Cost from the run logs
- **WHEN** a repo's run directory holds a converge log with two result events, a build log with none, and a run log naming two
  converge spawns
- **THEN** the converge cell holds the last cumulative dollars and the summed turns, marked as one log of two, and the build cell
  is a gap

#### Scenario: Cost from a Codex log
- **WHEN** a station's log is a Codex JSON log with two `turn.completed` events, and its spawn line names a model the price
  table holds
- **THEN** its cell holds the priced dollars and the summed tokens, its turns and seconds gaps
- **AND WHEN** the spawn line names a model the table lacks
- **THEN** its dollars are a gap and its tokens are read

#### Scenario: Tokens per role
- **WHEN** a status log holds `tokens review 45426, security 41346`, `tokens 128126 + 115356`, `tokens 115k (review 63k, security
  52k)` and a line naming one role with `tokens 97960`
- **THEN** each role's tokens are read from its own figure, and none is summed into the other

#### Scenario: A Codex worker
- **WHEN** a Codex session's parent ran in the repo's worktree inside a round's window, its path naming `conformance`
- **THEN** `review-metrics.json` holds that round's conformance record with the session's tokens, model and effort, `source:
  codex-session`

#### Scenario: A page from findings
- **WHEN** the script runs over repos with findings
- **THEN** the page holds a section per repo, a table per model, and charts, and no repo has changed
