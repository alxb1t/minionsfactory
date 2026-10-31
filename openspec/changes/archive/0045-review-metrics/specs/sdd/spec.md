## ADDED Requirements

### Requirement: The review-metrics station charts past findings, read-only

`skills/mf-review-metrics/scripts/review_metrics.py` SHALL read the repos named in
`$XDG_CONFIG_HOME/minionsfactory/review-metrics.toml`, else `~/.config/minionsfactory/review-metrics.toml`, or in
`--config` and `--repo`, and SHALL halt naming the config path when neither names a repo. It SHALL read each repo's
`.minions/findings/` files without writing to any repo, parse each field it can, record a field it cannot as a gap —
never a zero — and write one self-contained HTML page, with no script, to the config's `out` or `--out`. The page
SHALL hold a table per repo and per tier × model, charts over changes drawn by `mf-build`'s `chart()`, and the list of
fields each repo lacked. It SHALL give numbers, never a recommendation.

#### Scenario: No config
- **WHEN** the script runs with no config file and no `--repo`
- **THEN** it exits 2, naming the config path it looked for, and writes nothing

#### Scenario: Files from every era
- **WHEN** a repo holds a findings file with no cards, one with cards and no tier, a status log, and a file with the
  tier, the verdict states and `## Refuted`
- **THEN** each record carries what its file holds, every missing field is a gap, and the page lists the gaps per repo

#### Scenario: A page from findings
- **WHEN** the script runs over repos with findings
- **THEN** the page holds a section per repo, a table per tier × model, and charts, and no repo has changed
