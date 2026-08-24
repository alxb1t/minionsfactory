---
type: teardown
repo: minionsfactory
head: 6c159e56dc2b3101fbdc6febb07eb3c8f7411f71
profile: python-uv
round: 2
criteria_total: 23
open_gaps: 0
open_blocking: 0
open_required: 0
verdict: compliant
---

# minionsfactory — MinionsFactory compliance (mf-teardown, round 2)

## Summary

**A 6/6 · B 6/6 · C 4/4 · `python-uv` 7/7 — 23 of 23, no open gap at any severity.** All three gaps round 1
found are closed at source and confirmed by an independent blind re-measurement. `verdict: compliant`.

Nothing was withheld: `.minions/minions.toml` is at the path the orchestrator reads and its array is readable,
so the absent-subject rule never triggered. **`criteria_total: 23` — 23 − 0 not measured.** No group D–G
criterion was measured or reported.

Per the report contract, the three `verified` entries are **cleared** now that the report reads `compliant`;
the append-only resolution log below carries their history.

## Gaps

None open.

## Passing

- **A · loop wiring — 6/6.** `wiring:git-repo` (HEAD `6c159e5`); `wiring:gate-config` (`.minions/minions.toml`
  tracked at that exact path, no root-level `minions.toml`, 6-entry `gate` array); `wiring:vault-perms`;
  `wiring:claude-md` (no placeholder, no vault path, no retired model, and its account of progress matches the
  tree); `wiring:env-example` (placeholder value only); `wiring:gitignore` (`.env`; the `.minions/*` +
  `!.minions/minions.toml` pair; no lockfile entry, and `uv.lock` tracked).
- **B · SDD layout — 6/6.** 11 capabilities under `openspec/specs/`; `openspec/changes/archive/` with three
  archived changes; the active change `0006-teardown` carrying all four artifacts, a `## Progress` checklist at
  `tasks.md:37` and `version: v0.6` in `proposal.md` frontmatter; 118 scenarios, none missing a `Key:` or
  `Layers:` bullet; 144 `spec` + 14 `spec_exempt` markers across 13 test files with both names registered at
  `pyproject.toml:28-31`; and the spec checker as the array's last entry.
- **C · gate quality — 4/4.** `gate:covers-axes` (all four axes, in check mode, no `|| true`);
  `gate:contract-agrees` (`README.md` reproduces all six array entries in order, flag for flag);
  `gate:make-mirrors` (`Makefile:7-13` runs the same six in the same order); `gate:no-gaming` (the only waiver in
  gate-read config is `[tool.ruff.lint.per-file-ignores] "tests/**" = ["D"]` — a docstring rule over the test
  tree, the case the rubric names defensible; zero `noqa`, zero `type: ignore`, no `addopts`, no suppression).
- **`python-uv` — 7/7.** `py:manifest`, `py:lockfile`, `py:gate-commands` (all five uv-form entries present),
  `py:pinned-runtime` (`.python-version` = `3.12`, tracked), `py:lint-select` (`["E", "F", "I", "D", "ANN"]`),
  `py:dev-deps-isolated`, `py:import-resolution` (exactly one mechanism — `pythonpath = ["."]`, no `src/` and no
  `[build-system]`, so nothing competes with it).

## Resolution log

- 2026-08-24 · round 1 · first measurement, no prior report. 3 gaps opened at `open` (1 blocking, 2 required);
  0 withheld. `verdict: gaps-found`.
- 2026-08-24 · determinism re-run against the unchanged tree returned the same gap-id set, the same severities
  and the same (empty) withheld set. No criterion flipped, so no rubric defect to record.
- 2026-08-24 · `py:gate-commands` **open → verified**. Resolved under R11 cause *"minionsfactory is genuinely out
  of compliance"* — not a rubric defect: isekai's array leads with the same `uv sync --locked`, so the criterion
  is satisfiable and satisfied by the other proving target, and relaxing it to make this repo pass is what R11
  forbids. Closed by adding the step to the gate array. Because the gate is declared in four places and policed
  by two criteria, the step landed in `.minions/minions.toml`, `Makefile` and `README.md` in one commit;
  `.github/workflows/ci.yml` already ran it. `CLAUDE.md` was deliberately untouched — it states quality *axes*
  in prose, `uv sync` is environment setup rather than an axis, and prose is outside this criterion's scope.
- 2026-08-24 · `gate:contract-agrees` **open → verified**. The `README.md` block is now the array verbatim, six
  commands in order, flags included.
- 2026-08-24 · `py:pinned-runtime` **open → verified**. `.python-version` pins `3.12`, consistent with
  `requires-python = ">=3.12"` and with CI's `python-version`.
- 2026-08-24 · round 2 · `verdict: compliant` (0 blocking, 0 required, 0 advisory). The three `verified` entries
  are cleared into this log per the report contract.
- 2026-08-24 · after this measurement, `gate:contract-agrees` gained a second boundary paragraph — a command
  block illustrating what *another* repo should configure is not a declaration of *this* repo's gate. Prompted by
  both measurers independently flagging `README.md:42-49` (an `e.g.` block under "The target repo it drives must
  provide"). Recorded as a **sharpening, not a relaxation**: both runs already read it the same way, so the
  criterion did not flip and was not a defect under R5, and the clarification changes no result for any of the
  four repos measured in this round.
