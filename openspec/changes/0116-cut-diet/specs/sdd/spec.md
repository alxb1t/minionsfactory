## ADDED Requirements

### Requirement: A cut reads one context pack

`skills/mf-cut-change/scripts/cut_context.py <brief> <change-id>` SHALL write `.minions/changes/<change-id>/context.md`, the **context pack**, holding in order: the brief; each fact of the brief as `facts.py`'s placer places it, with the lines it cites at `HEAD`, each cite cut at a fixed number of lines; the decisions `bundle.py --decisions` prints for the brief; each requirement of the living specs whose title the brief names, in full, and an index of every requirement title with its capability and line; each debt card whose `What it affects` names a path a fact cites, and each card whose id the brief's item lists; and the skeleton of each artifact. It SHALL write `.minions/changes/<change-id>/cut-notes.md` afresh, as `facts.py place` does, print one line naming the pack, exit 0 when every fact is placed, 1 when one is unplaced, and 2 when a file cannot be read. `skills/mf-cut-change/SKILL.md` SHALL have the cut read the pack once, and read the brief, the cited decisions, the living specs and the code a fact cites from it, and run no `openspec instructions` and read no archived change for an example.

#### Scenario: A brief whose facts stand
- **WHEN** every fact's file is untouched since its sha
- **THEN** the pack holds each fact as `stands` with its cited lines at `HEAD`, the notes file holds one line a fact, and `cut_context.py` exits 0

#### Scenario: An unplaced fact
- **WHEN** a fact cites a line that changed since its sha
- **THEN** the pack holds the fact as `unplaced` with its cited lines at `HEAD`, and `cut_context.py` exits 1

#### Scenario: A long cite
- **WHEN** a fact cites more lines than the cap
- **THEN** the pack holds the first lines up to the cap and a line saying where it cut

#### Scenario: A requirement the brief names
- **WHEN** the brief's text holds the title of a living requirement
- **THEN** the pack holds that requirement in full, and the index lists it beside every other title

#### Scenario: A debt card on a cited file
- **WHEN** a debt card's `What it affects` names a path a fact cites, or the brief's item lists the card's id
- **THEN** the pack holds that card; with no such card it holds `None.`

#### Scenario: The skeletons
- **WHEN** the pack is written
- **THEN** it holds the skeleton of the proposal, the design, the tasks and the spec delta, each with its headings in order

### Requirement: A cut starts from a scaffold of what the brief says

`skills/mf-cut-change/scripts/cut_context.py <brief> <change-id> --scaffold` SHALL write three files in `openspec/changes/<change-id>/`. `proposal.md` SHALL hold `bump:` frontmatter from the brief's item for the change's slug, and `after:`, `beside:` and `debt:` lines when the item lists some, then the title, the brief's one line, and `## Not in this change` from the brief's `## Not in this` items. `design.md` SHALL hold the title, a `## Decisions` table with a row `D<n>` for each `Q` or `C` row of the brief's `## Decisions`, and `## Dependencies`, `None.` or the brief's rows for the slug. `tasks.md` SHALL hold the title, a `## Progress` line for each phase of the brief's `## Phases` ending ` · hard` or ` · moderate`, and a `## <n> — <title>` heading for each phase. It SHALL write none and exit 1 when one of the three files exists or a phase has no rating, and exit 2 when the brief cannot be read. No file it writes SHALL name the brief's path. `skills/mf-cut-change/SKILL.md` SHALL have the cut run it before Step 6 and write the rest of each artifact into the files it wrote.

#### Scenario: A brief with a phase list
- **WHEN** the brief's `## Phases` holds a phase 1 line wrapped over two lines, ending `· hard`
- **THEN** `tasks.md` holds `- [ ] 1 — <the line, one space between words> · hard` and `## 1 — <the same title>`

#### Scenario: A decision table
- **WHEN** the brief's `## Decisions` holds rows `Q1` and `C1` and a row with `—` for an id
- **THEN** the design's table holds `D1` for `Q1` and `D2` for `C1`, a blank cell as `—`, and no row for the `—` row

#### Scenario: A brief with no dependency
- **WHEN** the brief's `## Dependencies` says `None.`
- **THEN** the design's `## Dependencies` says `None.`

#### Scenario: A file already there
- **WHEN** `proposal.md` exists in the change directory
- **THEN** `cut_context.py --scaffold` writes no file, prints the path, and exits 1

### Requirement: A plan review runs in the foreground

`skills/mf-cut-change/SKILL.md` SHALL have the cut run each plan review as a worker it waits for in the foreground, and start no background task for it, so no result wakes the cut after its turn ends.

#### Scenario: The first review
- **WHEN** the cut starts its first plan review
- **THEN** the review runs in the foreground and the cut's next act is that review's result

### Requirement: Row V2 evaluates a `-k` expression

`cut_check.py`'s row `V2` SHALL evaluate each `-k` expression of a `pytest` `Verify:` against the name of each test a later sub-task adds, removes, merges or renames, an identifier being true when the name holds it, case apart, with `not`, `and`, `or` and parentheses read as pytest reads them. It SHALL halt only when the expression is true for such a name and an identifier outside every `not` holds in it, and leave an expression it cannot parse to the reviewer.

#### Scenario: A negated selection
- **WHEN** a sub-task verifies with `pytest -k "not widget"` and a later sub-task adds `test_widget`
- **THEN** `V2` does not halt

#### Scenario: A nested negation
- **WHEN** a sub-task verifies with `pytest -k "not (a and (b) and d)"` and a later sub-task adds `test_d`
- **THEN** `V2` does not halt

#### Scenario: A selection of a later test
- **WHEN** a sub-task verifies with `pytest -k "widget or gadget"` and a later sub-task adds `test_gadget`
- **THEN** `V2` halts, naming both sub-tasks

#### Scenario: A positive term beside a negated one
- **WHEN** a sub-task verifies with `pytest -k "not widget and gadget"` and a later sub-task adds `test_gadget`
- **THEN** `V2` halts, naming both sub-tasks

#### Scenario: An expression it cannot parse
- **WHEN** a `-k` expression has an unclosed parenthesis
- **THEN** `V2` does not halt

## MODIFIED Requirements

### Requirement: A Claude worker starts with its station's tools and nothing of the operator's

`conduct.py` SHALL start each Claude station worker with `--tools` naming its station's tools: the cut `Bash`, `Read`, `Edit`,
`Write`, `Glob`, `Grep`, `Skill` and `Agent`; the probe `Bash` and `Read`; every other station, a converge worker among them,
`Bash`, `Read`, `Edit`, `Write`, `Glob`, `Grep` and `Skill`. Its `--settings` SHALL turn off
each plugin the operator's user settings enable, the operator's output style and auto-memory, and it SHALL start with
`--exclude-dynamic-system-prompt-sections`. Every station, the cut included, SHALL start with the 5-minute prompt cache
forced. A worker whose log shows a call to a tool its station lacks SHALL halt its
version, naming the tool, whatever its exit. The run's probe SHALL name in its check line the context of its worker's first
turn: the input, cache-read and cache-write tokens of its first assistant event, or a Codex log's first turn's input tokens.

#### Scenario: Each station's command line
- **WHEN** a run on the fake hosts spawns a version's cut, build and release on Claude, and its converge workers
- **THEN** each command line holds `--tools` with its station's tools, `--settings` with the plugins, the output style and
  auto-memory off, and `--exclude-dynamic-system-prompt-sections`
- **AND** every station's environment, the cut's included, forces the 5-minute cache

#### Scenario: The operator has a plugin and an output style
- **WHEN** the operator's user settings enable a plugin and name an output style
- **THEN** a Claude worker's `--settings` sets that plugin off and the default output style

#### Scenario: A worker calls a tool its station lacks
- **WHEN** a build worker's log holds a tool result `No such tool available: Agent`
- **THEN** the version halts, naming `Agent`

#### Scenario: The probe reports its first turn
- **WHEN** a Claude probe worker's first assistant event holds 3 input, 15000 cache-read and 4000 cache-write tokens
- **THEN** the probe's check line names a first turn of 19003 tokens
