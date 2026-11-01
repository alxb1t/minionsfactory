# Reliability paydown — tasks

Build the settled [design](design.md), one phase at a time. The skill, decision and threat-model text is the design's, word for
word.

## Progress

- [x] 1 — The drift sweep
- [x] 2 — What a run may do
- [x] 3 — The features
- [ ] 4 — Gate speed
- [ ] 5 — The drill

## 1 — The drift sweep

- [x] 1.1 Apply [D11](design.md#d11)'s rows for `CHANGELOG.md`, `THREAT_MODEL.md`, `AGENTS.md`, `skills/mf-cut-change/SKILL.md`,
  `skills/mf-release/SKILL.md`, `skills/mf-ship/SKILL.md`, `skills/mf-converge/SKILL.md` and `docs/decisions.md`.
  Verify: `grep -c '0050·S7' THREAT_MODEL.md` prints `1`.
- [x] 1.2 Apply [D11](design.md#d11)'s rows for `skills/mf-ship/scripts/conduct.py`: `0047·S3`, `0049·R8`, `0049·R11`, `0049·S5`,
  `0050·R9`, and `tests/test_conduct.py`'s `0050·R1`.
  Verify: `grep -c 'the claim, what is unpushed' skills/mf-ship/scripts/conduct.py` prints `1`.

## 2 — What a run may do

- [x] 2.1 In `skills/mf-ship/scripts/conduct.py`, push only tagged merges, per [D1](design.md#d1), and add
  `test_a_run_pushes_only_tagged_merges` to `tests/test_conduct.py`.
  Verify: `uv run pytest -q tests/test_conduct.py -k pushes_only_tagged` reports `1 passed`.
- [x] 2.2 Add the mark to `conduct.py` and `skills/mf-release/SKILL.md`, per [D2](design.md#d2), and add
  `test_a_stop_survives_a_death`.
  Verify: `uv run pytest -q tests/test_conduct.py -k stop_survives` reports `1 passed`.
- [x] 2.3 Start both executors with `HOOKS_OFF`, per [D3](design.md#d3), add `test_no_hook_runs_in_a_worker`, and edit
  `test_a_worker_carries_the_allowlist_and_a_denial_is_named`.
  Verify: `uv run pytest -q tests/test_conduct.py -k no_hook_runs` reports `1 passed`.
- [x] 2.4 Grow `CONFIG_PLAIN`, drop `LOCAL_ORIGIN`, and drop `_allow_origin` from `tests/test_conduct.py`, per [D4](design.md#d4).
  Verify: `grep -c 'localorigin' skills/mf-ship/scripts/conduct.py` prints `0`.

## 3 — The features

- [x] 3.1 Add `conduct.py stop`, per [D5](design.md#d5), and `test_stop_ends_a_live_run`.
  Verify: `uv run pytest -q tests/test_conduct.py -k stop_ends` reports `1 passed`.
- [x] 3.2 Add `conduct.py grant` and `## A granted round` to `skills/mf-converge/SKILL.md`, per [D6](design.md#d6), and
  `test_a_grant_buys_one_round`.
  Verify: `uv run pytest -q tests/test_conduct.py -k grant_buys` reports `1 passed`.
- [x] 3.3 Add `_unlinked`, per [D7](design.md#d7), and `test_a_missing_skill_stops_a_run`.
  Verify: `uv run pytest -q tests/test_conduct.py -k missing_skill` reports `1 passed`.
- [x] 3.4 Add the foreground rule to `skills/mf-converge/SKILL.md`, per [D8](design.md#d8), and the forms to
  `skills/mf-ship/SKILL.md`, per [D5](design.md#d5).
  Verify: `grep -c 'never end' skills/mf-converge/SKILL.md` prints `1`.

## 4 — Gate speed

- [ ] 4.1 Move `_fake` to `tests/fake_worker.py`, and add its `dies-integrate` mode with `0049·R9`'s step, per
  [D9](design.md#d9) and [D11](design.md#d11).
  Verify: `grep -c 'def _fake' tests/test_conduct.py` prints `0`.
- [ ] 4.2 Write `openspec/changes/0051-reliability-paydown/evidence/gate.md`, per [D9](design.md#d9).
  Verify: `grep -c '^after: ' openspec/changes/0051-reliability-paydown/evidence/gate.md` prints `1`.

## 5 — The drill

- [ ] 5.1 Write `tests/drill_resume.py`, per [D10](design.md#d10).
  Verify: `uv run --script tests/drill_resume.py --help` exits 0.
- [ ] 5.2 **HALT CHECK** Run it, and write `openspec/changes/0051-reliability-paydown/evidence/drill.md`, per
  [D10](design.md#d10).
  Verify: `grep -c '^worker killed: done' openspec/changes/0051-reliability-paydown/evidence/drill.md` prints `1`, and
  `grep -c '^conductor killed: done' openspec/changes/0051-reliability-paydown/evidence/drill.md` prints `1`.
- [ ] 5.3 Confirm the drill deleted its probe.
  Verify: `test ! -e ../mf_resume_probe` exits 0.
