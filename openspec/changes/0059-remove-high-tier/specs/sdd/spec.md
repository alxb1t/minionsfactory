## ADDED Requirements

### Requirement: Converge runs one depth

`skills/mf-converge/SKILL.md` SHALL run one depth: each role's one fresh worker SHALL judge the change from a packet given up
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

## MODIFIED Requirements

### Requirement: Independent workers have fresh contexts

A checker SHALL be a new host subagent or fresh agent process receiving explicit role inputs without the build
transcript. A resumed worker, inherited build conversation or fork carrying that conversation SHALL NOT satisfy
freshness. The conductor SHALL dispatch, observe completion and read each role's findings from shared disk.

Converge SHALL prefer parallel dispatch and permit sequential independent workers over the same frozen head,
completing every checker of a round before a fix begins, and SHALL record `mode: parallel` or `mode: sequential`. The
station SHALL halt before work requiring an unavailable worker capability, naming that
capability.

#### Scenario: A generic host executes workers sequentially
- **WHEN** review completes before a fresh security worker starts
- **THEN** both judge the same frozen head and neither receives the build transcript
- **AND** a fix starts after both findings files are complete

#### Scenario: The host cannot provide independent workers
- **WHEN** neither a suitable subagent nor a fresh agent process can be dispatched and awaited
- **THEN** convergence halts rather than reviewing in the conductor's context

#### Scenario: A host runs one worker at a time at high
- **WHEN** converge runs on a host that cannot run workers in parallel
- **THEN** it runs the review worker, then the security worker, over the same frozen head, and the findings files record
  `mode: sequential`

### Requirement: The review-metrics station charts past findings, read-only

`skills/mf-review-metrics/scripts/review_metrics.py` SHALL read the repos named in
`$XDG_CONFIG_HOME/minionsfactory/review-metrics.toml`, else `~/.config/minionsfactory/review-metrics.toml`, or in
`--config` and `--repo`, and SHALL halt naming the config path when neither names a repo. It SHALL read each repo's
`.minions/findings/` files without writing to any repo, parse each field it can, record a field it cannot as a gap —
never a zero — and write one self-contained HTML page, with no script, to the config's `out` or `--out`. The page
SHALL hold a table per repo and per model, charts over changes drawn by `mf-build`'s `chart()`, and the list of
fields each repo lacked. It SHALL read no tier, and SHALL count a file's `inconclusive` sections only when the file holds
`## Refuted`, the review method's mark. It SHALL give numbers, never a recommendation.

#### Scenario: No config
- **WHEN** the script runs with no config file and no `--repo`
- **THEN** it exits 2, naming the config path it looked for, and writes nothing

#### Scenario: Files from every era
- **WHEN** a repo holds a findings file with no cards, one with cards and no `## Refuted`, a status log, and a file with
  the verdict states and `## Refuted`, with or without a `tier:` line
- **THEN** each record carries what its file holds, every missing field is a gap, and the page lists the gaps per repo

#### Scenario: A page from findings
- **WHEN** the script runs over repos with findings
- **THEN** the page holds a section per repo, a table per model, and charts, and no repo has changed

## REMOVED Requirements

### Requirement: Converge runs at a tier

**Reason**: one depth stays. The high tier found what the standard one found — 5 of 5 on v0.37's seeded calibration — with
89 workers and 55.6 M tokens against 2 and 4.2 M (change `0042-review-method`'s `evidence/calibration.md`). The person,
2026-10-31 and 2026-11-03.

**Migration**: drop `tier=` from any `/mf-converge` call and `tier` from any models file; an old models file's `tier` is
ignored. *Converge runs one depth* holds what stays, the 1,500-line cap among it.
