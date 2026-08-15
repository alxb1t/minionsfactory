# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0/).

## [Unreleased]

### Added

- Project scaffolding: role-independent `CLAUDE.md`, vault wiring (`.env` → `VAULT_PROJECT_DIR`), `.gitignore`, `.env.example`, and this changelog.
- Minimal `pyproject.toml` (uv-managed, run-from-source, no runtime deps) + committed `uv.lock`.
- Strict quality gate, dogfooded on this repo: `ruff` (format + lint with `D` docstrings and `ANN` annotations, `pep257` convention; `D` waived for `tests/`), `ty` in strict mode (`error-on-warning`), and `pytest` (`pythonpath` set for run-from-source imports) — all as a dev-only dependency group.
- `orchestrator/` package skeleton with a typed, docstringed `describe()` and a passing smoke test.
- GitHub Actions CI (`.github/workflows/ci.yml`) mirroring the gate on every push/PR: `uv sync --locked` → ruff format → ruff lint → ty → pytest.
- Proven role prompts copied into `prompts/` (`coder`, `reviewer`, `security`, `simplify`, `release`); v0.1 drives the coder, the rest ride along as reference.
- Provider seam (`orchestrator/provider.py`): a `Provider` Protocol the driver depends on, a real `ClaudeCodeProvider` (headless `claude -p --output-format json`, list-argv — never a shell string), and a scripted `FakeProvider` test double. Supported by a typed `RoleResult` (Pydantic, parsed from the CLI JSON and tolerant of unknown fields), a `Profile` permission profile (frozen dataclass), and a pure `build_command` argv builder — the pure parse/build halves are unit-tested; real `claude` is never spawned in tests.
- Runtime dependency `pydantic`, to model and validate the headless CLI result at the trust boundary.
- Developer docs under `docs/` (raw markdown, no build tooling): `architecture.md` (invariants + component/dependency graph), `data-flow.md` (sequence/flow diagrams for `run_role` and the planned loop), and a per-package API reference `modules/orchestrator.md`.
- Gate runner (`orchestrator/gate.py`): the orchestrator runs the target repo's own quality gate itself and returns a typed `GateResult` (`passed` + per-step `command`/`exit_code`/`output`). The ordered command list is read from the target's `minions.toml` (`tomllib`, language-neutral — a JS target needs no orchestrator change), each command runs with no shell (`shlex.split`), and the run stops at the first failing step. Exposed as a `Gate` Protocol with a real `SubprocessGate` (injectable command executor) and a scripted `FakeGate` double — the fail-fast logic is unit-tested; real tools are never spawned in tests.
- Plan-state reader (`orchestrator/state.py`): reconstructs "where are we" purely from disk into a typed `PlanState` (`current_phase` + `phaseN` flags + git `head`). Selects the highest-version plan (`vX.Y_*implementation_plan.md`, ignoring `archive/` via a shallow glob and integer version comparison), parses the plan's YAML frontmatter with a small stdlib-only extractor (no new dependency), and reads the target repo's git HEAD. The composition is unit-tested via an injected head reader — git is never spawned in tests.
