## ADDED Requirements

### Requirement: The gate holds the wider lint, the timeout rule and the docstring check

`make gate` and `make check` SHALL run `ruff check` with the families `UP`, `ERA`, `PERF`, `SIM`, `RET`, `PT`, `RUF`, `PLE`,
`PLC`, `PLR`, `PLW` and `BLE` added to the existing selection, the noisy rules `RUF001`, `RUF002`, `RUF003`, `RUF005`,
`PLR0911`, `PLR0912`, `PLR0913`, `PLR0915`, `PLR0917`, `PLR2004` and `PLW1510` ignored everywhere and `PT018` ignored in
`tests/`. Each deliberate blind `except` SHALL carry `# noqa: BLE001` and its reason. They SHALL also run `ast-grep scan`,
whose one rule, `subprocess-run-needs-timeout`, SHALL flag each `subprocess.run` call under `skills/` and `scripts/` that
passes no `timeout=`, and `scripts/docstrings.py`, which SHALL flag each docstring of a tracked Python file whose text runs
over 3 non-blank lines, and each whose first line is not one sentence. The recipe SHALL stay the only list of the commands.

#### Scenario: A run with no timeout
- **WHEN** a script under `skills/` calls `subprocess.run(argv, capture_output=True)`
- **THEN** `ast-grep scan` exits 1 naming the file and the line, and the gate is red

#### Scenario: A run with a timeout
- **WHEN** the call passes `timeout=` of any value
- **THEN** `ast-grep scan` flags nothing for it

#### Scenario: A docstring over the limit
- **WHEN** a function's docstring holds 4 non-blank lines
- **THEN** `scripts/docstrings.py` exits 1, naming the file, the line and the limit, and the gate is red
- **AND WHEN** a blank line separates its summary from 2 more lines
- **THEN** it flags nothing

#### Scenario: A first line of two sentences
- **WHEN** a docstring's first line reads `Return x. Then return y.`
- **THEN** `scripts/docstrings.py` flags it

#### Scenario: A blind except
- **WHEN** a script catches `Exception` and the line carries no `# noqa: BLE001`
- **THEN** `ruff check` flags it, and the gate is red

### Requirement: Converge writes the evidence of each freeze

At every freeze — round 1, each re-freeze after a fix, a catch-up — after `debt-cards.md` and before any dispatch, converge
SHALL write `.minions/changes/<change-id>/evidence.md` whole, from tools alone, and hand its path to every worker it starts
through the placeholder `{evidence}` of each reference's `## Prompt`. The file SHALL hold four sections, each a list of lines
or `None.`: **Gate integrity** — one line for each suppression, skip, removed test, removed assertion, edit to the gate's
configuration or swallowed error the frozen patch holds, by `skills/mf-converge/scripts/gate_integrity.py`; **Plan check** —
the whole output of `plan_check.py` for the freeze; **Stale-claim candidates** — each name the patch renames or deletes with
its `git grep` mentions outside the patch; **Test cost** — each test the patch adds with its seconds from the gate's junit
report, each `slow` marker and end-to-end `run` boot it adds, and each test it removes against the design's `## Tests`
section. Each line SHALL name a file by its path as Git names it, unquoted, and SHALL time a test by its module, its class
and its name. Converge SHALL judge nothing in it, and SHALL run each command under the sandbox runner.

#### Scenario: Round 1 writes the evidence
- **WHEN** converge freezes a range in round 1
- **THEN** `evidence.md` stands beside `diff.patch`, `bundle.md` and `debt-cards.md`, before the first checker starts

#### Scenario: A fix is re-frozen
- **WHEN** a fix commit is re-frozen
- **THEN** `evidence.md` is rewritten for the new range, and each worker of the next round is given it

#### Scenario: A new suppression
- **WHEN** the frozen patch adds a line holding `# noqa`, `# type: ignore`, `# ty: ignore` or `# pragma: no cover`
- **THEN** the Gate integrity section holds a line naming its path and line

#### Scenario: A removed test the design names
- **WHEN** the patch removes `def test_a` and the design's `## Tests` section names `test_a`
- **THEN** the Test cost section says the removed test is named in it

#### Scenario: A path Git spaces or quotes
- **WHEN** the frozen patch changes `tests/a b/x.py`, or `café.py`, which Git quotes
- **THEN** each line names the file by that path, whichever file comes before it in the patch

#### Scenario: One test name in two classes
- **WHEN** the patch adds `TestFast.test_main`, 0.1 s in the report, and the report holds `TestSlow.test_main` of the same module at 9.0 s
- **THEN** the Test cost section gives the added test 0.10 s

#### Scenario: Nothing found
- **WHEN** a tool finds nothing for a section
- **THEN** the section reads `None.`

### Requirement: The checkers start from the evidence and judge the rest

A conformance, adversarial or verify worker SHALL read `evidence.md` before its sections, SHALL NOT re-derive a line the file
holds, and SHALL judge each line that needs judgment: a suppression's reason, a swallowed error's harm, a stale mention's
falsehood, a removed test's retired proofs. A card the evidence's line supports SHALL cite the line. The coverage-trace
pass SHALL stay the worker's, since the gate's `diff-cover` reads changed lines only. A worker reference's statement that
converge judges nothing SHALL stay true: the evidence holds facts a tool found, never a verdict.

#### Scenario: A line judged
- **WHEN** `evidence.md` holds a Gate integrity line for an added `# noqa`
- **THEN** conformance judges whether its reason holds and cards it when it does not, and does not search for the `# noqa` itself

#### Scenario: A stale-claim candidate
- **WHEN** `evidence.md` lists a deleted name with a mention in a document outside the patch
- **THEN** conformance judges that mention and cards it as `drift` when the change made it false

#### Scenario: A removed test's proofs
- **WHEN** the patch removes a test
- **THEN** conformance still runs the coverage-trace pass

### Requirement: A queued cut prefetches the packages it approves

`conduct.py cut`, after it reads the brief's `## Dependencies` and before it reserves a number, SHALL fetch each package the
brief approves for the slug into `.minions/uv-cache`, wheels only, from PyPI's hosts only, so the sandboxed gate's offline
`uv sync --locked` finds it. It SHALL refuse a row whose package is not a plain name or whose constraint is not a plain
version specifier, each clause an operator and a version — a bare version, a URL, a path or a VCS reference included — and a fetch that
fails, exiting 2 and reserving nothing.
The fetch SHALL read no `uv` or `pip` setting of the person's environment or home folder, and SHALL have a timeout.

#### Scenario: An approved package
- **WHEN** the brief approves `ast-grep-cli` at `>=0.51.1,<0.52` for the slug
- **THEN** `conduct.py cut` runs one wheels-only fetch of `ast-grep-cli>=0.51.1,<0.52` against PyPI's index into `.minions/uv-cache`, and queues the cut

#### Scenario: A URL off PyPI's hosts
- **WHEN** a row's package or constraint is a URL whose host is not `pypi.org` or `files.pythonhosted.org`
- **THEN** `conduct.py cut` exits 2 naming the row, and runs no fetch and reserves nothing

#### Scenario: A bare version
- **WHEN** a row's constraint is `1.3.0`, with no operator
- **THEN** `conduct.py cut` exits 2 naming the row, and runs no fetch and reserves nothing

#### Scenario: A brief with no package
- **WHEN** the brief's `## Dependencies` is `None.` or holds no row for the slug
- **THEN** `conduct.py cut` runs no fetch

#### Scenario: A fetch that fails
- **WHEN** the fetch exits non-zero or times out
- **THEN** `conduct.py cut` exits 2 naming the package, and reserves nothing
