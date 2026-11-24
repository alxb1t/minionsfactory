## ADDED Requirements

### Requirement: The run log's lines carry a build's phase, the load and a halt's cause

`conduct.py` SHALL write a build worker's spawn line with its phase right after the station word — `spawn — build · phase <n> · model …`, `spawn — build · close · model …` and `spawn — build · repair · model …` — for the build station's three kinds of worker, and the spawn line of no other station SHALL carry a phase. Every spawn and finish line the conductor writes, the converge script's pair among them, SHALL end ` · load <n>`, the 1-minute load to one decimal, and SHALL leave the field out where the load cannot be read.

Every halt line of a version or of the run, the `final` halt and the line of a conductor crash among them, SHALL end ` · cause <word>`, `<word>` one of `plan-text`, `gate-red`, `check-red`, `worker`, `limit`, `probe`, `merge`, `cut`, `amend`, `cap`, `human`, `release` and `run`, or `other` for a halt that fits none. The run's closing summary line and the person's stop line SHALL carry no cause. A halt SHALL be classed by the start of its reason before its other words, so text a worker wrote after `check fail` is never read as a cause. A converge halt, whether written as a stage text or as `converge check fail — the status log halts: <text>`, SHALL be classed by the words of its text: `cap reached` by `cap`, `amend needed` by `amend`, a worker's exit or timeout by `worker`, `verify: halt` by `plan-text`, a red gate by `gate-red` and a usage limit by `limit`, and any other by `other`; a rescue's diagnosis, a missing worktree and a `waiting` stage SHALL be `other`.

#### Scenario: A phase, the close and the repair
- **WHEN** the conductor spawns a build worker for phase 3, for the close, and for the repair of a red gate
- **THEN** the spawn lines read `build · phase 3 · model …`, `build · close · model …` and `build · repair · model …`
- **AND** a release's spawn line holds no phase

#### Scenario: The load on a spawn and a finish
- **WHEN** a worker runs and the converge script runs
- **THEN** each spawn and finish line of both ends ` · load <n>`, one decimal
- **AND WHEN** the machine gives no load
- **THEN** the lines end as they did before

#### Scenario: A halt of each cause
- **WHEN** a version halts on a worker's exit, a red gate, a failed check, a usage limit, a plan text, a merge, a release, a human phase, a cap, an amend and a cut, and the probe and a crash halt the run
- **THEN** each halt line ends ` · cause <word>` of its row in the list
- **AND** a halt that fits none ends ` · cause other`

#### Scenario: A worker's text after a failed check
- **WHEN** a build check fails and its reason quotes a worker's text holding `usage limit`
- **THEN** the halt line ends ` · cause check-red`

#### Scenario: An integrate red gate and a probe's limit
- **WHEN** a version stops at `integrating — red gate`, and a probe halts on `codex limited until`
- **THEN** the first ends ` · cause gate-red` and the second ` · cause limit`

#### Scenario: The final halt, the closing line and the stop line
- **WHEN** a version ends on its first halt, the run closes, and a person stops a run
- **THEN** the `final — needs <action> · <reason>` line ends with the cause of that reason
- **AND** the closing `run · halt — halted … · released …` line and the `halt — stopped by the person` line carry no cause

### Requirement: The conductor and converge log each gate they run

The conductor SHALL log `check — gate · start` before each gate it starts, the rerun after a load wait among them. `converge.py` SHALL write one `check — gate` line through its host for each gate it runs — before round 1, after the fix, after the pickup, after each fixer pass and at its close — as `check — gate · pass · <n>s` or `check — gate · fail — red · <n>s`, `<n>` the seconds converge timed itself; a reused gate record SHALL be written as any other pass, and converge SHALL write no start line.

#### Scenario: The conductor's gate
- **WHEN** the conductor runs a gate that is red, waits for the load, and runs it again green
- **THEN** the log holds a start, the red line, the wait lines, a second start and the pass line, in that order

#### Scenario: Converge's gates
- **WHEN** converge runs its gate before round 1, after a fixer pass, after the fix, after the pickup and at its close
- **THEN** the run log holds a `check — gate` line with its seconds for each, and no start line

#### Scenario: A reused record
- **WHEN** a converge gate reuses a green record of the same tree
- **THEN** the line reads as a pass with converge's own seconds

### Requirement: The viewer shows a build's phase, a running gate and a halt's cause

`viewer.py project` SHALL give each worker the phase its spawn line names, or none, and each version a `gate_running` flag that is true while the version's last line of the newest run log is `check — gate · start` and the run's claim is live, and the cause its last halt line ends with, or none. The page SHALL show each of them as text.

#### Scenario: A worker with a phase
- **WHEN** the newest run log holds an unfinished `spawn — build · phase 3 · model m` of a version
- **THEN** its worker shows the phase `phase 3`

#### Scenario: A running gate
- **WHEN** a version's last line of the newest run log is `check — gate · start`
- **THEN** the version shows its gate running while the claim is live
- **AND WHEN** a `check — gate · pass · 40s` line follows, or the claim is stale
- **THEN** it does not

#### Scenario: A halt's cause
- **WHEN** a version's last line is `halt — build check fail — … · cause check-red`
- **THEN** the version shows the cause `check-red`

### Requirement: Review metrics books a build's cost by its phase

`review_metrics.py` SHALL match each build log of a change to the spawn line of the run log its name stamps, by the stamp and the ordinal the log's name holds, and SHALL write one row of `phases` in `review-metrics.json` for each build log: its repo, change, phase, dollars, turns, tokens, seconds and first-turn context, the phase `null` where the spawn line names none. The page SHALL show a build cost table by phase per repo.

#### Scenario: A build booked by phase
- **WHEN** a change's run log holds two build spawn lines naming `phase 1` and `close`, and its logs hold `<stamp>-build.log` and `<stamp>-build-2.log`
- **THEN** `phases` holds a row for `phase 1` with the first log's cost and a row for `close` with the second's

#### Scenario: An older log
- **WHEN** a build's spawn line names no phase
- **THEN** its row's phase is `null`
