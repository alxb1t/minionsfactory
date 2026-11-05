## ADDED Requirements

### Requirement: A live run holds the machine awake

At a run's start, `conduct.py` SHALL start `caffeinate -is -w <its own pid>`, never with `-d`, so the machine neither idles to sleep
nor, on AC power, sleeps, and the hold ends with the conductor. With no `caffeinate` on `PATH` the run SHALL go on. The `start` line
SHALL end `· awake: held`, or `· awake: not held — caffeinate not on PATH`. A run of fake workers (`MF_SHIP_AGENT`) SHALL start no
hold and name none. `skills/mf-ship/SKILL.md` SHALL say that a closed lid sleeps the Mac whatever the run holds, unless it is in clamshell mode.

#### Scenario: A run on a Mac
- **WHEN** a run starts with `caffeinate` on `PATH`
- **THEN** it starts `caffeinate -is -w <the conductor's pid>` once, and its `start` line ends `· awake: held`

#### Scenario: No caffeinate
- **WHEN** no `caffeinate` is on `PATH`
- **THEN** the run goes on, and its `start` line ends `· awake: not held — caffeinate not on PATH`
