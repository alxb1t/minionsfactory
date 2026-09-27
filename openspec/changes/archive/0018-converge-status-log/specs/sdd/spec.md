## ADDED Requirements

### Requirement: Converge keeps a status log

`skills/mf-converge/SKILL.md` SHALL have the conductor write `.minions/findings/<change-id>_status_log.md`: one line
per event, in the form `HH:MM:SS · round N · <event> — <detail>`, the time taken from `date`. Each run SHALL open
with a `## Run N` heading placed above the previous run, and each event SHALL be inserted directly under the latest
heading, so the newest run and the newest line are on top. No line SHALL be edited or deleted. The events SHALL be
`start`, `freeze`, `fan-out`, `verdicts`, `fix`, `verify`, `pickup`, `catch-up`, `backlog`, `halt` and `done`, and a
run SHALL end on `halt` or `done`. The log SHALL NOT be a findings file: no station writes it and no release reads it.

#### Scenario: Converge names the log, its order and its events
- **Key:** `sdd:converge-status:log`
- **Layers:** unit
- **WHEN** `skills/mf-converge/SKILL.md` is scanned
- **THEN** it names `_status_log.md`
- **AND** it names `newest on top`
- **AND** it names each event: `start`, `freeze`, `fan-out`, `verdicts`, `fix`, `verify`, `pickup`, `catch-up`,
  `backlog`, `halt`, `done`
