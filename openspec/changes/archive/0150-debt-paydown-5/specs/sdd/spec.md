## MODIFIED Requirements

### Requirement: Row V2 evaluates a `-k` expression

`cut_check.py`'s row `V2` SHALL evaluate each `-k` expression of a `pytest` `Verify:` against the name of each test a later sub-task adds, removes, merges or renames, an identifier being true when the name holds it, case apart, with `not`, `and`, `or` and parentheses read as pytest reads them. It SHALL halt only when the expression is true for such a name and an identifier outside every `not` holds in it, and leave an expression it cannot parse to the reviewer. An identifier under a `not` that the name does not hold may name a marker or a parent's name, which pytest also matches: it SHALL make the row silent for that name. An identifier under a `not` that the name holds, and every identifier outside every `not`, SHALL be read as before.

#### Scenario: A negated selection
- **WHEN** a sub-task verifies with `pytest -k "not widget"` and a later sub-task adds `test_widget`
- **THEN** `V2` does not halt

#### Scenario: A nested negation
- **WHEN** a sub-task verifies with `pytest -k "not (a and (b) and d)"` and a later sub-task adds `test_d`
- **THEN** `V2` does not halt

#### Scenario: A selection of a later test
- **WHEN** a sub-task verifies with `pytest -k "widget or gadget"` and a later sub-task adds `test_gadget`
- **THEN** `V2` halts, naming both sub-tasks

#### Scenario: A negated word the name does not hold
- **WHEN** a sub-task verifies with `pytest -k "widget and not slow"` and a later sub-task adds `test_widget`
- **THEN** `V2` does not halt, since `slow` may be a marker

#### Scenario: A positive term beside a negated one
- **WHEN** a sub-task verifies with `pytest -k "not widget and gadget"` and a later sub-task adds `test_gadget`
- **THEN** `V2` does not halt, since `widget` may be a marker, and the name does not hold it

#### Scenario: A negated word the name holds
- **WHEN** a sub-task verifies with `pytest -k "a or not b"` and a later sub-task adds `test_a_b`
- **THEN** `V2` halts, naming both sub-tasks
- **AND WHEN** the expression is `widget and not widget_old` and the later test is `test_widget_old`
- **THEN** `V2` does not halt, the expression being false for that name

#### Scenario: An expression it cannot parse
- **WHEN** a `-k` expression has an unclosed parenthesis
- **THEN** `V2` does not halt

### Requirement: A cut's mechanical steps are scripts

`skills/mf-cut-change/SKILL.md` SHALL have the cut run `cut_pre.py` for each precondition of Step 1, by hand and unattended,
printing one line a check and exiting 1 on any that fails; a failed precondition SHALL halt the cut. It SHALL have the cut
place the brief's facts with `facts.py`, name the deleted or renamed symbols to `facts.py readers`, and run `cut_check.py` for
the self-check. `cut_check.py` SHALL decide `I2`, `I3`, `I4`, `I11`, `I12`, `I13`, `I14`, `I17`, `I18` and `I19`, the headings
`A1` and `A2`, `P9` and `P13`'s three-line task, folding in `openspec validate --strict`, the gate-edit check, the search script
and the corpus check of `plan_check.py`; it SHALL also decide the `Verify:` sequencing rows `V1` to `V8` — a needle an earlier
task already adds, a `-k` that selects tests a later task adds or deletes, a `git grep` of a file not committed before its
phase ends, a needle its task never names, a `pytest` command that names no test path, a needle a later task removes from the
searched file, in the fenced `diff` block whose header names that file, a command
whose first word is no program on `PATH`, no path of the tree and no path a task names, and a `-k` that selects no test of the files it
names at `HEAD` and none a task names — and the record's consistency rows `K1` to `K7` — the proposal's `## Impact` against
the tasks' files, the design's `## Tests` against the tasks' test files, the decision index against the decision headings, each
decision a task cites, each cited Step and constant, two tasks on one line, and a line of `design.md` outside `## Tests`, or of
`proposal.md`, that names a backticked identifier a task removes with no removal word. It SHALL print each row it leaves to
judgment — `I5` to `I10`, `I15`, `I16`, `P12` and `P13`'s paragraphs — and a summary line, and exit 1 on a mechanical failure,
which the cut SHALL fix and run again. The self-check SHALL write that summary line and the judgment rows only.
`gate_check.py --tasks` SHALL be called the gate-edit check in the cut's prose. `facts.py readers` SHALL also take
`--signature <name>`, printing the stand-ins and the monkeypatches of that name; `--file <path>`, printing the lines that name
the file by its quoted basename and the imports of its module; and `--string <text>`, printing each line holding the text as
written; each kind SHALL print `none` when it finds nothing. `mf-plan`'s re-measure of a continued brief SHALL run `facts.py`
and re-read only the facts it leaves unplaced.

#### Scenario: A precondition fails
- **WHEN** the tree is dirty, the id is taken, or `make -n gate` lists no command
- **THEN** `cut_pre.py` prints a line naming that check, exits 1, and the cut halts

#### Scenario: Every precondition holds
- **WHEN** each check holds
- **THEN** `cut_pre.py` prints one line per check and exits 0

#### Scenario: The readers of a deleted name
- **WHEN** a task deletes `_old_name`
- **THEN** `facts.py readers _old_name` prints each `git grep -nw` hit at `HEAD` with its `path:line`, or `none`, and the cut
  names each reader in a task

#### Scenario: The stand-ins of a changed signature
- **WHEN** a task changes the signature of `_run`, and a test holds `monkeypatch.setattr(mod, "_run", fake)`
- **THEN** `facts.py readers --signature _run` prints that line as a `monkeypatch of _run`, with its `path:line`, and the cut
  names that test in a task

#### Scenario: The readers of a changed file
- **WHEN** a task renames `scripts/tool.py`, a test loads it by `"tool.py"` and another holds `import tool`
- **THEN** `facts.py readers --file scripts/tool.py` prints the first as a `runpy reader` and the second as an `import reader`

#### Scenario: The readers of a changed string
- **WHEN** a task changes the text `Opus 5.5 · high`
- **THEN** `facts.py readers --string "Opus 5.5 · high"` prints each line holding it, `git grep -F` at `HEAD`

#### Scenario: A mechanical failure
- **WHEN** a sub-task of `tasks.md` has no `Verify:`, or the design has no `## Tests` section
- **THEN** `cut_check.py` prints the failed row, exits 1, and the cut fixes the file and runs it again

#### Scenario: A needle an earlier task adds
- **WHEN** a sub-task's `Verify:` greps a needle in a file that an earlier sub-task names and quotes the needle of
- **THEN** `cut_check.py` prints the failed row `V1` naming both sub-tasks, and exits 1

#### Scenario: A whole-suite pytest
- **WHEN** a sub-task's `Verify:` runs `pytest` with no test path, or with `-m "not slow"` alone
- **THEN** `cut_check.py` prints the failed row `V5` naming the sub-task and asking for the test files, and exits 1

#### Scenario: A needle a later task removes
- **WHEN** a sub-task's `Verify:` greps a needle in a file, and a later sub-task holds a fenced `diff` block with a header, a `--- ` line and a `+++ ` line, naming that file, and the needle is in a removed line of that file's section and in no added line of it
- **THEN** `cut_check.py` prints the failed row `V6` naming both sub-tasks, and exits 1

#### Scenario: A needle removed from another file
- **WHEN** a sub-task's `Verify:` greps a needle in one file, and a later sub-task's `diff` block removes the needle in a block whose header names another file
- **THEN** `V6` does not halt

#### Scenario: A block with no header
- **WHEN** a later sub-task's fenced `diff` block names no file by a header, and holds the needle in a removed line
- **THEN** the block takes no part, and `V6` does not halt

#### Scenario: A first word that names nothing
- **WHEN** a sub-task's `Verify:` runs `nosuchtool --check`, and no sub-task names a path `nosuchtool`
- **THEN** `cut_check.py` prints the failed row `V7` naming the sub-task, and exits 1
- **AND WHEN** the first word is `git`, a file of `HEAD`'s tree, or a path a sub-task names
- **THEN** the row holds

#### Scenario: A -k that selects nothing
- **WHEN** a sub-task's `Verify:` runs `pytest tests/test_a.py -k typo`, and neither `tests/test_a.py` at `HEAD` nor any sub-task names a test that `typo` selects
- **THEN** `cut_check.py` prints the failed row `V8` naming the sub-task, and exits 1
- **AND WHEN** the expression selects a test of that file at `HEAD`, or a `test_` name a sub-task names
- **THEN** the row holds

#### Scenario: A design line that names a removed name
- **WHEN** a sub-task says it deletes `_old_name`, and `design.md` outside `## Tests` has a line naming `_old_name` with no removal word
- **THEN** `cut_check.py` prints the failed row `K7` naming the line, and exits 1
- **AND WHEN** that line says the name is removed or renamed
- **THEN** the row holds

#### Scenario: A record that disagrees with itself
- **WHEN** a task links `design.md#d9` and `design.md` has no `### D9` heading
- **THEN** `cut_check.py` prints the failed row `K4` naming the task, and exits 1

#### Scenario: A clean change
- **WHEN** every mechanical row holds
- **THEN** `cut_check.py` exits 0, prints the rows to judge and its summary line, and the cut's self-check holds those alone

#### Scenario: A continued brief
- **WHEN** `mf-plan` continues a brief with `from=`
- **THEN** it runs `facts.py` and re-reads only the unplaced facts
