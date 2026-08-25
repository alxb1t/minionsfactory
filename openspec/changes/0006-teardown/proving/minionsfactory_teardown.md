---
type: teardown
repo: "minionsfactory"
head: "94a5322"
profile: python-uv
round: 3
criteria_total: 23
open_gaps: 0
open_blocking: 0
open_required: 0
verdict: compliant
---

# minionsfactory — MinionsFactory compliance (mf-teardown, round 3)

## Summary

**A 6/6 · B 6/6 · C 4/4 · `python-uv` 7/7 — 23 of 23, no open gap at any severity.** `verdict: compliant`.

**Why there is a round 3.** The review round-1 fix pass widened `wiring:claude-md`'s (J) layer to own the repo's
**prose gate account** — the clause `gate:contract-agrees`' prose boundary had been deferring to without it
existing. `wiring:claude-md` is `blocking`, so round 2's `compliant` had been measured against a rubric whose (J)
layer did not carry that clause, and the evidence had to be honest about the rubric it was measured against.
This round re-measures against the repaired rubric.

**The gap the widening opens is closed in the same pass.** `CLAUDE.md`'s quality-gate section stays **prose** —
phase 2 decided that, and `uv sync` is environment setup rather than a quality *axis* — but it now states that
the gate leads with a locked lock-sync step, names all six steps in order, and its one literal command reads
`uv run python -m orchestrator specs check --strict`, the flag the array, the `Makefile`, the README and CI all
run. So `wiring:claude-md` passes on the new clause rather than in spite of it.

Nothing was withheld: `.minions/minions.toml` is at the path the orchestrator reads and its array is readable, so
the absent-subject rule never triggered. **`criteria_total: 23` — 23 − 0 not measured.** No group D–G criterion
was measured or reported.

Round 2 cleared its three `verified` entries at `compliant`, so this round opened with none carried forward, and
nothing failed — the report stays clear and the resolution log below carries the whole history.

## Gaps

None open.

## Passing

- **A · loop wiring — 6/6.** `wiring:git-repo` (HEAD `94a5322`); `wiring:gate-config` (`.minions/minions.toml`
  tracked at that exact path, no root-level `minions.toml`, 6-entry `gate` array); `wiring:vault-perms`;
  `wiring:claude-md` — no placeholder, no absolute vault path, no retired model, its account of progress matches
  the tree, and **its account of the gate matches the array**: `CLAUDE.md:58-75` names the lock-sync step plus the
  four axes and states *"Six steps in all — the sync, format, lint, typecheck, test, and the spec checker last"*,
  the array's exact shape and order, with its one full literal command (`CLAUDE.md:70`) matching array entry 6
  verbatim, `--strict` included; `wiring:env-example` (both files declare exactly one key, `VAULT_PROJECT_DIR`,
  and the example's value is a placeholder — compared by key name, no value reproduced); `wiring:gitignore`
  (`.env`; the `.minions/*` + `!.minions/minions.toml` pair; no lockfile entry, and `uv.lock` tracked).
- **B · SDD layout — 6/6.** 11 capabilities under `openspec/specs/`; `openspec/changes/archive/` with three
  archived changes; the active change `0006-teardown` carrying all four artifacts, a `## Progress` checklist and
  `version: v0.6` in `proposal.md` frontmatter; 118 scenarios, none missing a `Key:` or `Layers:` bullet; 151
  test functions across 13 files, every one carrying `spec` or `spec_exempt`, both names registered at
  `pyproject.toml:28-31`; and the spec checker as the array's last entry. No existence criterion failed, so no
  universally-quantified criterion passed vacuously — each had a real, non-empty subject.
- **C · gate quality — 4/4.** `gate:covers-axes` (all four axes, in check mode, no `|| true`);
  `gate:contract-agrees` (**(M+J)** as of this round) — its **(J)** half excludes `README.md:42-49`, the TOML
  block introduced at `:40` as what *"the target repo it drives must provide … e.g."*, which describes a
  different repo and correctly differs from this array; its **(M)** half compares `README.md:65-72`, this repo's
  own declaration, and finds it matches command-for-command in order and flags. `CLAUDE.md` carries no fenced
  block at all, so its prose axis list is out of the (M) comparison's scope and covered by `wiring:claude-md`
  instead. `gate:make-mirrors` (`Makefile:7-13` runs the same six in the same order, byte-identical to the
  array); `gate:no-gaming` (the only waiver in gate-read config is
  `[tool.ruff.lint.per-file-ignores] "tests/**" = ["D"]` — the case the rubric names defensible; no `exclude`, no
  lint `ignore`, no `addopts`, and `[tool.ty.terminal] error-on-warning = true` tightens rather than relaxes;
  zero `noqa`, zero `type: ignore`, zero `skip`/`xfail`).
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
  `.github/workflows/ci.yml` already ran it. `CLAUDE.md` was deliberately untouched — it states quality *axes* in
  prose, `uv sync` is environment setup rather than an axis, and prose is outside this criterion's scope.
- 2026-08-24 · `gate:contract-agrees` **open → verified**. The `README.md` block is now the array verbatim, six
  commands in order, flags included.
- 2026-08-24 · `py:pinned-runtime` **open → verified**. `.python-version` pins `3.12`, consistent with
  `requires-python = ">=3.12"` and with CI's `python-version`.
- 2026-08-24 · round 2 · `verdict: compliant` (0 blocking, 0 required, 0 advisory). The three `verified` entries
  are cleared into this log per the report contract.
- 2026-08-24 · after that measurement, `gate:contract-agrees` gained a second boundary paragraph — a command
  block illustrating what *another* repo should configure is not a declaration of *this* repo's gate. Prompted by
  both measurers independently flagging `README.md:42-49`. Recorded as a **sharpening, not a relaxation**: both
  runs already read it the same way, so the criterion did not flip and was not a defect under R5.
- 2026-08-25 · **review round 1 (R2) — the rubric changed under this report, so it was re-measured.**
  `wiring:claude-md`'s (J) layer gained a third clause: its account of the gate must match what the `gate` array
  actually runs, the axes it names and any literal command it quotes, flags included. Round 2's `compliant` had
  been measured before that clause existed, and `wiring:claude-md` is `blocking` — so the evidence was retaken
  rather than left standing on the older rubric.
- 2026-08-25 · **review round 1 (R2) — the gap that clause opens is closed at source.** `CLAUDE.md:56-75` now
  states the locked lock-sync step, names all six gate steps in order, and corrects its one literal command to
  `... specs check --strict`. It stays **prose**, so it remains outside `gate:contract-agrees`' (M) scope; the
  other three declarations were **not touched** and remain byte-identical, so `gate:make-mirrors` never moved.
- 2026-08-25 · **review round 1 (R3) — `gate:contract-agrees` retagged (M) → (M+J)**, with the split written into
  the criterion. Its second boundary decides by reading what a command block is *for*, which is judgment; both
  phase-6 measurers had to exercise it before the rubric authorised it. A tag correction, not a scope change —
  the criterion's result is unchanged for every repo measured in this change.
- 2026-08-25 · round 3 · blind re-measurement at `94a5322` against the repaired rubric: **nothing failing,
  nothing withheld, 23 of 23.** No criterion outside the two touched by R2/R3 changed its result — no rubric
  defect under R5. `verdict: compliant` (0 blocking, 0 required, 0 advisory), no `verified` entries to carry or
  clear.
- 2026-08-25 · **determinism, across the fix pass.** Two independent blind measurements were taken, at `9c63858`
  (every rubric and skill edit landed) and at `94a5322` (two later commits touching only `design.md`,
  `CHANGELOG.md`, `README.md` prose and the change tree — no criterion's subject among them). Both returned the
  same result: 23/23, no failing id, no withheld id. Every (M) criterion decided the same way twice.
- 2026-08-25 · **isekai was not re-run, deliberately.** Its `wiring:claude-md` already fails for a different
  reason — its root `CLAUDE.md` still instructs a cold agent to read the retired
  `$VAULT_PROJECT_DIR/implementation_plans/` model, and mentions `openspec` zero times — so the new (J) clause
  changes neither its result nor any count in `proving/isekai_teardown.md`. Its `criteria_total: 19`,
  `open_gaps: 8` and `verdict: gaps-found` stand as committed.
