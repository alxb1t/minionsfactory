---
bump: minor
after: [0064-lighter-catch-up]
backlog: [0051·S6]
---

# Gate hardening

Harden the gate on two sides — MF's own and the one MF gives a target's builders — and make it fast: the tests on every core, a
quick check between build phases, the full gate at the end.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

`make gate` grew from 155 s at v0.45 to 378 s at this cut, on one of ten cores, and every build phase runs it: `0063`'s build spent
about half its 62 minutes in gates. Meanwhile the gate checks five home-grown key shapes, no bug-pattern or security lint, no
coverage, and CI runs unpinned actions; a target's bootstrap gate checks only its specs, and a push leaves with no secret scan.

## What Changes

- **Speed** — `pytest-xdist -n auto`; every test isolated by a fixture; the slow tests marked; `make check` between phases.
- **Pins** — uv by `required-version`; CI's actions by commit SHA, with `timeout-minutes`, `fetch-depth: 0` and uv's version;
  `zizmor` in the gate.
- **Lint** — Ruff `B` and `S`, noisy rules ignored with a reason; `--strict-markers`.
- **Coverage** — `coverage` across the parallel run and `diff-cover`, 100% of changed lines.
- **Secrets** — Betterleaks in the gate and in CI by checksum; a gate tool off PyPI is operator tooling; the guardrail's key shapes
  retire to it.
- **The push** — `conduct.py` scans each push range, and a run stops at its start without Betterleaks (`0051·S6`).
- **Targets** — the bootstrap's gate scans for secrets and gains `check`; `CODING_STANDARDS.md.tmpl` carries the stack recipes.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *The build runs a quick check between phases* — ADDED: `make check` after each phase but the last; `I8`.
  - *The conductor scans a push for secrets* — ADDED: the scan, the halt, the start without Betterleaks.
  - *The bootstrap writes the target layout* — MODIFIED: the gate template's scan and `check` target.

## Impact

Changes `Makefile`, `pyproject.toml`, `uv.lock`, `.github/workflows/ci.yml`, `.betterleaks.toml` (new), `.gitignore`,
`tests/conftest.py` (new), the tests, `skills/mf-ship/scripts/conduct.py`, the `mf-build`, `mf-cut-change` and `mf-bootstrap`
skills and templates, `AGENTS.md`, `docs/decisions.md` and `THREAT_MODEL.md`.

Dependencies: `coverage`, `diff-cover`, `zizmor`, `pytest-xdist`, dev-only, approved by the person. Betterleaks is operator
tooling. The gate recipe changes, every line quoted in [tasks](tasks.md).

## Not in this change

mise; deptry in MF's gate; OSV-Scanner; agnix; TS security patterns and other stacks' recipes; isekai's, gpunit's and
lepalace's own gates; `0034·R9`; parallel gate steps (`make -j`).
