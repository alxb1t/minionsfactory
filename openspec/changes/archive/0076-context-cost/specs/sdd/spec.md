## MODIFIED Requirements

### Requirement: The card is defined in converge alone

`skills/mf-converge/references/worker.md`, converge's worker reference, SHALL own the card: a `## The card` section whose
table rows are the card's fields, one per row, the first cell holding the field's label in bold (`**Why it's a problem**`). No
other shipped skill SHALL carry a `## The card` section.

#### Scenario: Only converge carries the card
- **WHEN** every `skills/*/SKILL.md` and converge's worker reference are scanned for a `## The card` section
- **THEN** the worker reference carries one, with at least one label
- **AND** no other skill carries one

### Requirement: The build owns the rules for tests, and the cut and converge carry them

`skills/mf-build/SKILL.md` SHALL own the rules for tests: a `## Rules for tests` section whose table rows are the
rules, one per row, the first cell holding the rule's id in bold (`**T1**`). `skills/mf-cut-change/SKILL.md` and
`skills/mf-converge/references/worker.md` SHALL each carry a `## Rules for tests` section with a row for the same ids. The id
sets SHALL be equal, non-empty, and numbered from `T1` with no gap.

#### Scenario: The three skills carry the same test-rule ids
- **WHEN** the ids are read from the first cell of each table row in the `## Rules for tests` section of
  `mf-build`, `mf-cut-change` and converge's worker reference
- **THEN** each carrier's set equals `mf-build`'s, and none is empty
- **AND** each runs from `T1` upward with no number missing

### Requirement: Bundled generic role references resolve

The shipped skills SHALL explicitly load their role resources: converge's review, security and worker references on every
executor, and `mf-simplify` in the build, whose link SHALL resolve from the build's installed package, not the
target's cwd; a missing target SHALL halt the build, naming it.
Their `references/` Markdown targets SHALL resolve to nonempty files within the referring skill's package, a
`#section` after a target ignored by the check, and the
build's link to `mf-simplify` to a nonempty file in that skill's package.
Missing, empty and escaping targets SHALL fail the gate's resource-integrity check.

#### Scenario: The generic instruction package is incomplete
- **WHEN** a referenced role resource is missing, empty or resolves outside its skill package
- **THEN** the resource-integrity check reports the referring skill and the invalid target

#### Scenario: The package contains valid role resources
- **WHEN** the shipped resource references resolve within their packages to nonempty files
- **THEN** the resource-integrity check passes without treating illustrative change-document links as resources

#### Scenario: The build cannot load mf-simplify
- **WHEN** the build's link to `mf-simplify` finds no file from its installed package
- **THEN** the build halts naming it, and takes no copy of that name from the target

### Requirement: A worker runs in an OS sandbox

A Claude worker SHALL run with Claude Code's sandbox on, `allowUnsandboxedCommands` false and `failIfUnavailable` true, writing
only to the primary, the open worktrees and the common directory: a sandbox that cannot start SHALL end the worker, never run
it unsandboxed. The operator's credential paths SHALL be denied to its scripts and to its `Read` tool,
and the credential variables unset for its scripts. It SHALL load user settings alone, so a project's settings, hooks and
`.mcp.json`, which a worker can write, start nothing, and SHALL start with `--strict-mcp-config` and no `--mcp-config`, so the
MCP servers of the operator's own config start nothing. Its network SHALL reach only `pypi.org`, `files.pythonhosted.org` and the
domains `AGENTS.md`'s `Ship network:` line names, and its sandbox SHALL never have `allowLocalBinding`: it binds no
loopback port, in any repo. A Codex worker SHALL run with its network off, and SHALL
start with its working directory and every tree it reaches marked untrusted, whatever the operator's Codex config says, so a
project's `.codex/` config, hooks and rules, which a worker can write, start nothing. Both SHALL keep `uv`'s cache
in the run directory, and neither SHALL inherit the conductor's `VIRTUAL_ENV`.

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

#### Scenario: The conductor runs in a uv environment
- **WHEN** `conduct.py` runs with `VIRTUAL_ENV` set, and starts a worker on either executor
- **THEN** the worker's environment holds no `VIRTUAL_ENV`

### Requirement: The review-metrics station charts past findings, read-only

`skills/mf-review-metrics/scripts/review_metrics.py` SHALL read the repos named in
`$XDG_CONFIG_HOME/minionsfactory/review-metrics.toml`, else `~/.config/minionsfactory/review-metrics.toml`, or in
`--config` and `--repo`, and SHALL halt naming the config path when neither names a repo. It SHALL read each repo's
`.minions/findings/` files and its run logs, `.minions/runs/<stamp>/<change>_<station>.log`, without writing to any repo,
parse each field it can, record a field it cannot as a gap —
never a zero — and write one self-contained HTML page, with no script, to the config's `out` or `--out`. The page
SHALL hold a table per repo and per model, a cost table per repo — each change's stations with their dollars, turns, tokens and
seconds — charts over changes drawn by `mf-build`'s `chart()`, and the list of fields each repo lacked. A log's dollars and tokens
SHALL be its last result event's cumulative `total_cost_usd` and `modelUsage`, its turns and seconds the sum over its result events;
a station with no log, a log with no result event and a Codex log SHALL be a gap, and a station the run log shows spawned more than
once in a stamp SHALL be marked as read from its last log. It SHALL read no tier, and SHALL count a file's `inconclusive` sections only when the file holds
`## Refuted`, the review method's mark. It SHALL give numbers, never a recommendation.

#### Scenario: No config
- **WHEN** the script runs with no config file and no `--repo`
- **THEN** it exits 2, naming the config path it looked for, and writes nothing

#### Scenario: Files from every era
- **WHEN** a repo holds a findings file with no cards, one with cards and no `## Refuted`, a status log, and a file with
  the verdict states and `## Refuted`, with or without a `tier:` line
- **THEN** each record carries what its file holds, every missing field is a gap, and the page lists the gaps per repo

#### Scenario: Cost from the run logs
- **WHEN** a repo's run directory holds a converge log with two result events, a build log with none, and a run log naming two
  converge spawns
- **THEN** the converge cell holds the last cumulative dollars and the summed turns, marked as one log of two, and the build cell
  is a gap

#### Scenario: A page from findings
- **WHEN** the script runs over repos with findings
- **THEN** the page holds a section per repo, a table per model, and charts, and no repo has changed

### Requirement: Anchored harms block, and drift has its own tier

`skills/mf-converge/references/worker.md`, converge's worker reference, SHALL name the **anchors** — data loss or an irreversible delete, spend, exposure of
personal data or secrets, silent wrong output — and SHALL grade an anchored finding `blocking` in review and at least
`high` in security, save a route in a class the threat model's *Out of scope* accepts by name, which is carded and does
not block, anchors included. Review SHALL grade `blocking | drift | nit`, where `drift` is docs, comments, README or CHANGELOG
text the code contradicts; `drift` SHALL NOT block. A spec scenario the code contradicts SHALL stay `blocking`.

#### Scenario: Converge and the method page name the anchors and the drift tier
- **WHEN** review or security finds data loss or an irreversible delete, spend, exposure of personal data or
  secrets, or silent wrong output
- **THEN** review grades it `blocking` and security at least `high`, so the loop fixes it

#### Scenario: Prose the code contradicts
- **WHEN** review finds docs, comments, README or CHANGELOG text the code contradicts
- **THEN** it grades the finding `drift`, which does not block
- **AND** a spec scenario the code contradicts stays `blocking`

#### Scenario: A route in the accepted class
- **WHEN** security finds a route in a class the threat model's *Out of scope* accepts by name, with an anchored harm
- **THEN** it cards the route, and the card does not block
- **AND WHEN** the route is in no accepted class
- **THEN** the anchor blocks as before

### Requirement: Converge runs one depth

`skills/mf-converge/SKILL.md`, with its worker reference `skills/mf-converge/references/worker.md`, SHALL run one depth: each role's one fresh worker SHALL judge the change from a packet given up
front, reading beyond the diff only to trace a named angle, and SHALL run review's stale-claim, test-cost and coverage-trace
passes itself. It SHALL take no `tier=`, and SHALL halt, naming the parameter as removed, when one is given. The review and
security files' frontmatter SHALL record `mode`, `workers`, `model` and `packet`, and no tier. The cut SHALL write no `tier` into
`.minions/models/<change-id>.toml`; `mf-ship` SHALL read none from it, and SHALL pass none to converge.

#### Scenario: Converge runs
- **WHEN** converge runs
- **THEN** each role is one fresh worker, and the findings files and the status log record no tier

#### Scenario: A tier is given by hand
- **WHEN** a person runs `/mf-converge <change-id> tier=high`
- **THEN** converge halts, naming `tier` as removed, and dispatches no worker

#### Scenario: An old models file holds a tier
- **WHEN** a version's models file's `[converge]` table holds `tier = "high"`
- **THEN** `mf-ship` ignores it, and the converge prompt carries no tier

#### Scenario: A granted round
- **WHEN** the person grants a round past the cap
- **THEN** the converge prompt ends `and grant=yes`, with no tier clause

#### Scenario: A diff is large
- **WHEN** a change exceeds 1,500 changed lines
- **THEN** it is reviewed anyway, and each file's Summary says it is over the standard cap and to consider a split
