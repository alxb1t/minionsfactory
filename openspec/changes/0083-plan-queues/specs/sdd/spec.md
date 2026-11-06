## ADDED Requirements

### Requirement: A hard brief is checked before it is queued

`skills/mf-plan/scripts/brief_check.py <brief>` SHALL exit 1, printing one line per problem, when the brief's title does not
say `hard`, when it has no `At <sha>, <YYYY-MM-DD>.` line with a sha of 7 to 40 lowercase hex digits, when its
`## For the cut` holds no line, or when a command of an `**Acceptance:**` or `Verify:` item in its `## Decisions` or
`## For the cut` breaks the shell rules of `skills/mf-cut-change/scripts/verify_check.py`: one plain command, no `$(…)`, shell
variable, loop or `cd`. A command is a backticked span that holds a space and is no output, as `verify_check.py` reads one. It
SHALL exit 0 printing `brief: ready for the cut` when none holds, and 2 when the brief cannot be read or a span cannot be
parsed. It SHALL run no command it reads.

#### Scenario: A brief out of shape
- **WHEN** a brief's title says `light`, or it has no `At` line, or a `Verify:` in its `## For the cut` holds `$(…)`
- **THEN** `brief_check.py` exits 1, naming each

#### Scenario: A hard brief
- **WHEN** a hard brief has its `At` line, a filled `## For the cut` and plain commands
- **THEN** `brief_check.py` exits 0 and prints `brief: ready for the cut`

### Requirement: The plan's close queues the cut on the person's yes

At a hard close, once the person confirms the settled table, `skills/mf-plan/SKILL.md` SHALL run `brief_check.py` on the
brief, and fix and run it again until it exits 0. It SHALL then ask once, "confirm, and queue it?", unless `then=ship` was
given. On yes, or `then=ship`, it SHALL run `conduct.py cut <slug> <bump> brief=<path> [after=<ids>] --executor <executor>
--model <m> --effort <e>` from the primary for each change of `## For the cut`, in order, an `after` that names an earlier
change of the brief given as the id its `cut` printed, and paste each line; that yes SHALL be the person's yes to cut, run,
merge and push each queued version. On no, it SHALL end on `Next: /mf-cut-change <id> <bump> brief=<path>`. It SHALL still
never cut: no branch, no change directory.

#### Scenario: The person says yes
- **WHEN** a hard close's brief passes `brief_check.py` and the person answers yes
- **THEN** `mf-plan` runs `conduct.py cut` for each change in order, pastes each line, and returns to the chat

#### Scenario: The person says no
- **WHEN** the person answers no
- **THEN** `mf-plan` queues nothing and ends on `Next: /mf-cut-change <id> <bump> brief=<path>`

## MODIFIED Requirements

### Requirement: The plan station writes the brief after every round

`mf-plan` SHALL require `brief=<path>` and SHALL write the brief there after every round, with the sections: a title
naming the version, its form, its depth (`light` or `hard`) and the date; one bold line; an `At <sha>, <YYYY-MM-DD>.` line naming
the commit the newest round read; `## Facts`, each with
`path:line` at a named commit; `## Decisions`, one row per settled question; `## Phases`; `## Not in this`;
`## Open`, the frontier still to ask; and `## For the cut`, filled when the frontier is empty. A hard brief's `## For the cut`
SHALL name, per change in cut order, its slug, bump, `after`, `debt:` ids, `decide: recommended` when the person delegates a
cut's doubts, its Acceptance as commands, and a model and effort for the build, converge, release and the cut station, from
the models the session offers. A hard brief SHALL end
on a settled table the person confirmed, with `## Open` removed. `from=<brief>` SHALL continue a brief. The station
SHALL NOT write the brief's path into the target.

#### Scenario: A thread ends mid-grilling
- **WHEN** a session ends after some rounds
- **THEN** the brief holds every settled decision and the open frontier
- **AND** a new session with `from=` continues from it

#### Scenario: No brief path
- **WHEN** `mf-plan` is started without `brief=`
- **THEN** it halts and asks for the path

#### Scenario: A hard close names the models
- **WHEN** a hard close fills `## For the cut`
- **THEN** each change's item names a model and effort for the build, converge, release and the cut station
