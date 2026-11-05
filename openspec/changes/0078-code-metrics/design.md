# Code metrics — design

`scripts/metrics/codebase.py` measures the codebase from the tree; the gate writes a junit report the test metrics read. Verdict at the
end: ready to build.

## Context

Read at `9f6b755` (v0.62.1); the brief carries no `At` line, so every fact was re-read.

- **F1. The tree** (measured at `61daff7`; `0075` has since grown `tests/test_conduct.py` to 5,736 lines): 34 tracked `.py` files, all under `skills/`, `scripts/`, `tests/`; physical lines — code (`skills`, `scripts`, as
  coverage's `source`) 8,068, tests 10,695, the largest `tests/test_conduct.py` 5,458 before `0075`, then
  `skills/mf-ship/scripts/conduct.py` 3,968 (at `61daff7`).
- **F2. Ruff `C901`:** `uv run ruff check --select C901 --config 'lint.mccabe.max-complexity = 10' --output-format json --no-cache
  --ignore-noqa skills scripts tests` (Ruff `0.16.3`) — exit 1 with findings, 0 with `[]`, 2 on a bad config; a missing path exits 0
  with a stderr warning; `filename` is absolute. 13 functions over 10 at `61daff7`; no `# noqa: C901`.
- **F3. Suppressions:** `# noqa` 0, `type: ignore` 0, `pragma: no cover` 1 (`skills/mf-converge/scripts/gate_check.py:302`);
  per-file-ignores in `pyproject.toml` are config, not inline.
- **F4. Dependencies:** `[project].dependencies = []`; `[dependency-groups].dev` 7; every script's PEP 723 header
  `dependencies = []` (`CODING_STANDARDS.md:14-15`).
- **F5. The gate:** `Makefile:18` `	uv run coverage run -m pytest -q -n auto`; under xdist pytest writes one merged junit file —
  root `<testsuites name="pytest tests">`, one child `<testsuite tests time>`, each `<testcase classname name time>` (setup, call
  and teardown), no markers. `coverage.xml`'s root
  `line-rate`. Both land in the worktree that ran the gate, gitignored (`.gitignore:5`, `:22`); the collector runs a script with
  `cwd` the worktree (`skills/mf-build/scripts/metrics.py:176`). `gate_run.py` reuses a green record and runs no make
  (`skills/mf-converge/scripts/gate_run.py:114-133`), so a report can be an earlier run's.
- **F6. I18:** a task naming `` `gate` `` and the `Makefile`, quoting each changed line in a fenced `diff` block, passes
  `gate_check.py` as planned — no `approve-gate`.
- **F7. Collisions:** `0077-run-metrics` appends at the end of `metrics/catalogue.toml` and of `tests/test_metric_scripts.py`, and
  edits the latter's imports.

## Goals / Non-Goals

**Goals:** the codebase's shape and the tests' health per release, in the tracked series.

**Non-Goals:** a page; complexity in the gate.

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | `scripts/metrics/codebase.py <kind>` over `skills/`, `scripts/`, `tests/`, physical lines | Q1, Q3 | non-blank lines |
| [D2](#d2) | The gate's pytest step writes `.minions/test-report.xml` | Q2 | a second pytest run in the metric |
| [D3](#d3) | The test metrics from the junit report, a stale one a gap | Q1, Q2 | file mtime |
| [D4](#d4) | The catalogue's `code` group, mid-file | Q1 | appending at the end |

### D1

`ROOTS = ("skills", "scripts", "tests")`, only those present; `CODE = ("skills", "scripts")`. Kinds: `largest-module-lines`,
`modules-over-1000-lines` (all roots), `complex-functions` (F2's command over the present roots; a pure
`complex_count(stdout, returncode, stderr)` reads the JSON on exit 0 or 1, else raises naming stderr), `suppressions` (comment tokens through `tokenize`
matching `noqa`, `type: ignore`, `pragma: no cover`), `test-to-code-lines` (tests over code, a float), `python-lines`,
`dependencies` (`[project].dependencies` and every PEP 723 header's), `dev-dependencies` (`[dependency-groups]`, summed), by
`tomllib`. A pure `count(root, kind)` returns the number; `__main__` prints it, or exits 1 naming why. The script is named `codebase.py`,
not `code.py`, which would shadow the standard library's `code` on `sys.path[0]`.

### D2

The gate's pytest line takes `--junitxml=.minions/test-report.xml`. `AGENTS.md`'s gate account names the report.

### D3

`test-seconds` the testsuite's `time`; `slowest-test-seconds` the largest testcase `time`; `test-seconds-summed` their sum — wall
time per test, not CPU, renamed from the brief's `test-cpu-seconds`; `slow-tests` the testcases over 5 s, the `slow` marker's own
rule (`pyproject.toml:38`); `total-coverage` `coverage.xml`'s `line-rate` × 100. The report's `<testsuite>` is read under the
root `<testsuites>`. A missing or unparsable file exits 1; so does a report whose `tests` differs from the tree's collected count —
`uv run pytest --collect-only -q`, its `(\d+) tests? collected` read by the script's own copy of `tests_collected.py`'s regex —
the comparison a pure `stale(report_tests, collected)`. `total-coverage` takes the same check: a stale report means a stale
`coverage.xml`.

### D4

The entries, `group = "code"`, `script = "scripts/metrics/codebase.py"`, `args = ["<id>"]`, go after `gate-seconds`
(`metrics/catalogue.toml:54`), not at the end, and the tests after `test_tests_collected_is_unavailable_on_a_broken_collection`
(`tests/test_metric_scripts.py:77`), the imports untouched, so `0077`'s appends merge clean:

| id | title | unit | better |
|---|---|---|---|
| `largest-module-lines` | Largest Python module | lines | lower |
| `modules-over-1000-lines` | Python modules over 1,000 lines | modules | lower |
| `complex-functions` | Functions over complexity 10 | functions | lower |
| `suppressions` | Inline lint, type and coverage suppressions | suppressions | lower |
| `test-to-code-lines` | Test lines per code line | ratio | higher |
| `python-lines` | Python lines | lines | lower |
| `dependencies` | Runtime dependencies | packages | lower |
| `dev-dependencies` | Development dependencies | packages | lower |
| `test-seconds` | The suite's seconds | seconds | lower |
| `slowest-test-seconds` | The slowest test | seconds | lower |
| `test-seconds-summed` | The tests' summed seconds | seconds | lower |
| `slow-tests` | Tests over 5 s | tests | lower |
| `total-coverage` | Total line coverage | percent | higher |

The entries go in the table's order; `dependencies` also carries `watch = 0`.

## Tests

`git grep -c '^def test_' 9f6b755 -- tests/test_metric_scripts.py` counts the file at the cut. Added, on fixture trees:
`test_code_metrics_read_the_tree` (sizes, suppressions as comments only, dependencies), `test_complex_functions_are_read_from_ruff`
(the pure parser over a captured JSON, a non-zero Ruff exit, and a missing root), `test_test_metrics_read_the_junit_report` (a report, a missing one, a
stale count, through `stale`), and `test_the_code_script_runs_as_the_collector_runs_it` — `[sys.executable,
scripts/metrics/codebase.py, <kind>]` in a fixture tree, as `test_backlog_cards_are_unavailable_without_a_backlog` runs `backlog.py`,
covering `__main__` and the Ruff and collect-only subprocesses — `T2`: no test reads the tree's shape. None
deleted.

## Dependencies

None.

## Risks / Trade-offs

- **A reused gate record:** the report may be an earlier run's of the same tree, which is equivalent; another tree's is caught by its
  count.

## Verdict

Ready to build.
