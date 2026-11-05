## ADDED Requirements

### Requirement: Each release records its codebase

`metrics/catalogue.toml` SHALL declare the code metrics, each `scripts/metrics/codebase.py <kind>`, read from the tree over
`skills/`, `scripts/` and `tests/`: the largest module's lines, the modules over 1,000 lines, the functions over McCabe 10 by Ruff's
`C901`, inline suppressions (`noqa`, `type: ignore`, `pragma: no cover`) as comments, test lines per code line, Python lines, and
the runtime and development dependencies. MF's gate SHALL write a junit report, `.minions/test-report.xml`, from its pytest step;
the test metrics SHALL read it — the suite's seconds, the slowest test, the tests' summed seconds, the tests over 5 s — and
`total-coverage` the gate's `coverage.xml`, under the same report's check. A report that is missing, unreadable, or whose test count differs from the tree's
collected tests SHALL be a gap, never a zero.

#### Scenario: The codebase measured
- **WHEN** the collector runs the code metrics on a tree with a module over 1,000 lines and one function over complexity 10
- **THEN** `modules-over-1000-lines` and `complex-functions` each read 1

#### Scenario: A stale test report
- **WHEN** the worktree's junit report counts fewer tests than the tree collects
- **THEN** every test metric and `total-coverage` is a gap
