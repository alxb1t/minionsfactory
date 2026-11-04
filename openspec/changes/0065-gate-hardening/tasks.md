# Gate hardening — tasks

Build the settled [design](design.md), one phase at a time. Every `Makefile` line a task adds or removes is quoted.

## Progress

- [x] 1 — Speed
- [x] 2 — Pins
- [x] 3 — Lint
- [x] 4 — Coverage
- [x] 5 — Secrets
- [ ] 6 — The push
- [ ] 7 — Targets

## 1 — Speed

- [x] 1.1 Add `pytest-xdist` to the dev group (`uv add --dev 'pytest-xdist>=3.8.0'`), the isolation fixture in `tests/conftest.py`
  with `test_the_isolation_fixture_holds_home_under_tmp_path`, and fix each test the parallel run shows sharing state, per
  [D1](design.md#d1).
  Verify: `uv run pytest -q -n auto` reports no failure.
- [x] 1.2 Register `slow` in `pyproject.toml` and mark each test *The measurement* lists over 5 s, per [D1](design.md#d1).
  Verify: `uv run pytest -q --collect-only -m slow` reports `17 tests collected`.
- [x] 1.3 Run the gate's tests on every core and add a `check` target, in `Makefile`, `gate` named, per [D1](design.md#d1):
  ```diff
  - .PHONY: fix gate install-skills uninstall-skills
  + .PHONY: fix gate check install-skills uninstall-skills
  - 	uv run pytest -q
  + 	uv run pytest -q -n auto
  + check:
  + 	uv run ruff format --check .
  + 	uv run ruff check .
  + 	uv run ty check
  + 	uv run pytest -q -n auto -m "not slow"
  ```
  Verify: `make -n check` prints `uv run pytest -q -n auto -m "not slow"`.
- [x] 1.4 Run `make check` after each phase but the last in `skills/mf-build/SKILL.md`; reword `I8` there and in
  `skills/mf-cut-change/SKILL.md`; add the `slow` line beside `T1` in both, per [D2](design.md#d2).
  Verify: `uv run pytest -q tests/test_skills.py` reports no failure, and `grep -n 'make -n check' skills/mf-build/SKILL.md` prints a line.

## 2 — Pins

- [x] 2.1 Pin uv in `pyproject.toml`, and pin CI in `.github/workflows/ci.yml`, per [D3](design.md#d3).
  Verify: `grep -n 'required-version' pyproject.toml` prints a line, and `grep -n 'fetch-depth: 0' .github/workflows/ci.yml` prints a line.
- [x] 2.2 Add `zizmor` to the dev group (`uv add --dev 'zizmor>=1.32.0'`), and run it in the gate, in `Makefile`, `gate` named, fixing
  each finding in `ci.yml`, per [D3](design.md#d3):
  ```diff
  + 	uv run zizmor .github/workflows/ci.yml
  ```
  Verify: `uv run zizmor .github/workflows/ci.yml` exits 0.

## 3 — Lint

- [x] 3.1 Select `B` and `S` with the ignores and their reasons, and `--strict-markers`, in `pyproject.toml`; fix the `B023` and
  `B904` hits, per [D4](design.md#d4).
  Verify: `uv run ruff check --select B,S .` exits 0, and `grep -n -- '--strict-markers' pyproject.toml` prints a line.

## 4 — Coverage

- [x] 4.1 Add `coverage` and `diff-cover` to the dev group (`uv add --dev 'coverage>=7.17.1' 'diff-cover>=11.0.1'`), their config in
  `pyproject.toml`, their files in `.gitignore`, and the coverage lines in `Makefile`, `gate` named, per [D5](design.md#d5):
  ```diff
  + DIFF_BASE ?= main
  - 	uv run pytest -q -n auto
  + 	uv run coverage run -m pytest -q -n auto
  + 	uv run coverage combine -q
  + 	uv run coverage xml -q
  + 	uv run diff-cover coverage.xml --compare-branch=$(DIFF_BASE) --fail-under=100
  ```
  Verify: `make -n gate` prints `uv run diff-cover coverage.xml --compare-branch=main --fail-under=100`.
- [x] 4.2 **HALT CHECK** The combined report covers a line a fake-worker test reaches only through a subprocess, per
  [D5](design.md#d5).
  Verify: `uv run coverage report --include='skills/mf-ship/scripts/conduct.py'` prints a total above `0%`.
- [x] 4.3 Run `make gate DIFF_BASE=origin/main` in CI, per [D5](design.md#d5).
  Verify: `grep -n 'DIFF_BASE=origin/main' .github/workflows/ci.yml` prints a line.

## 5 — Secrets

- [x] 5.1 Add the scan to the gate in `Makefile`, `gate` named, and `.betterleaks.toml` with each allowlisted path's reason, per
  [D6](design.md#d6):
  ```diff
  + 	betterleaks dir . --no-banner --redact
  ```
  Verify: `grep -n 'betterleaks dir' Makefile` prints a line, and `betterleaks dir . --no-banner --redact` exits 0.
- [x] 5.2 Install Betterleaks by checksum in `.github/workflows/ci.yml`; add the operator-tooling decision to `docs/decisions.md`;
  record `betterleaks 1.9.0` and the new gate steps in `AGENTS.md`, per [D6](design.md#d6).
  Verify: `grep -n 'f8b185a39ffcece2a1ca82bf3a4e7435cd81963ffd16b7a9128daf75f35f6de7' .github/workflows/ci.yml` prints a line.
- [x] 5.3 Retire the four key shapes from `_SHAPES` and their cases in `tests/test_guardrails.py`, and add
  `test_betterleaks_finds_a_planted_key`, per the design's `## Tests` table.
  Verify: `grep -n 'ant-' tests/test_guardrails.py` prints nothing, and `uv run pytest -q tests/test_guardrails.py -k planted_key` reports `1 passed`.

## 6 — The push

- [ ] 6.1 Add `_scan` and its call in `Run.push`, and the start's Betterleaks check in `preconditions`, in
  `skills/mf-ship/scripts/conduct.py`; add `test_a_secret_in_the_push_range_halts_the_run` and
  `test_a_run_without_betterleaks_stops_at_start` to `tests/test_conduct.py`; name the halt in `skills/mf-ship/SKILL.md` and the scan
  in `THREAT_MODEL.md`, per [D7](design.md#d7).
  Verify: `uv run pytest -q tests/test_conduct.py -k "secret_in_the_push_range or without_betterleaks"` reports `2 passed`.

## 7 — Targets

- [ ] 7.1 Add the scan and a `check` target to `skills/mf-bootstrap/templates/Makefile.tmpl`, `gate` named; the `betterleaks version`
  precondition to `skills/mf-bootstrap/SKILL.md`; the recipes, the any-stack rule and the `slow` rule to
  `skills/mf-bootstrap/templates/CODING_STANDARDS.md.tmpl`; a step in `test_the_bootstrap_templates_cover_the_target_layout`, per
  [D8](design.md#d8):
  ```diff
  - .PHONY: gate
  + .PHONY: gate check
  + 	betterleaks dir . --no-banner --redact
  + check:
  + 	openspec validate --all --strict --no-interactive
  ```
  Verify: `uv run pytest -q tests/test_skills.py -k bootstrap_templates_cover` reports `1 passed`.
