# Version at merge — tasks

Build the settled [design](design.md), one phase at a time. The skill, decision and config text is the design's, word
for word.

## Progress

- [x] 1 — next_tag and metrics
- [x] 2 — Identity
- [x] 3 — Skill text
- [x] 4 — The record

## 1 — next_tag and metrics

- [x] 1.1 Write `skills/mf-release/scripts/next_tag.py`, per [D2](design.md#d2).
  Verify: `uv run --script skills/mf-release/scripts/next_tag.py minor` prints `v0.41.0`.
- [x] 1.2 Write `tests/test_next_tag.py`'s `test_next_tag_follows_the_bump`, per [Tests](design.md#tests).
  Verify: `uv run pytest -q tests/test_next_tag.py` reports `1 passed`.
- [x] 1.3 In `skills/mf-build/scripts/metrics.py`, add `UNRELEASED` and use it in `change_version` and `version_key`, per
  [D4](design.md#d4); add the step to `tests/test_metrics.py`'s `test_previous_is_the_highest_version_below`.
  Verify: `grep -c 'previous_release(tmp_path, "unreleased")' tests/test_metrics.py` prints `1`.

## 2 — Identity

- [x] 2.1 In `skills/mf-ship/scripts/conduct.py`, make the branch the change id, per [D1](design.md#d1), and read the tag
  from the tip, per [D3](design.md#d3).
  Verify: `grep -c 'def _change_on' skills/mf-ship/scripts/conduct.py` prints `0`.
- [x] 2.2 In `skills/mf-integrate/scripts/integrate.py`, drop `change_of` and read branches named by a change id, per
  [D1](design.md#d1).
  Verify: `grep -c 'def change_of' skills/mf-integrate/scripts/integrate.py` prints `0`.
- [x] 2.3 Edit `tests/test_conduct.py`'s `_version`, `_fake` and its tests, per [Tests](design.md#tests).
  Verify: `grep -c 'v0.1_todo' tests/test_conduct.py` prints `0`.
- [x] 2.4 Edit `tests/test_integrate.py`'s `_version` and its tests, per [Tests](design.md#tests).
  Verify: `grep -c 'next: 009-early' tests/test_integrate.py` prints `2`.

## 3 — Skill text

- [x] 3.1 Edit `skills/mf-cut-change/SKILL.md`, per [D5](design.md#d5).
  Verify: `grep -c 'v<version>_' skills/mf-cut-change/SKILL.md` prints `0`.
- [x] 3.2 Edit `skills/mf-build/SKILL.md`, `skills/mf-converge/SKILL.md` and `skills/mf-simplify/SKILL.md`, per
  [D5](design.md#d5).
  Verify: `grep -l 'its proposal version' skills/mf-build/SKILL.md skills/mf-converge/SKILL.md skills/mf-simplify/SKILL.md` prints nothing.
- [x] 3.3 Edit `skills/mf-release/SKILL.md`, and add its row to `tests/test_skills.py`'s `_METRICS_SCRIPTS`, per
  [D5](design.md#d5).
  Verify: `grep -c 'scripts/next_tag.py' skills/mf-release/SKILL.md` prints `1`.
- [x] 3.4 Edit `skills/mf-plan/SKILL.md`, `skills/mf-integrate/SKILL.md` and `skills/mf-ship/SKILL.md`, per
  [D5](design.md#d5).
  Verify: `grep -c 'a crash stops the run' skills/mf-ship/SKILL.md` prints `1`.

## 4 — The record

- [x] 4.1 Amend D19, D20 and D44 in `docs/decisions.md`, per [D6](design.md#d6).
  Verify: `grep -c 'numbered at its cut' docs/decisions.md` prints `0`.
- [x] 4.2 Edit `openspec/config.yaml` and `README.md`, per [D6](design.md#d6).
  Verify: `grep -c 'v0.33_<slug>' README.md` prints `0`.
