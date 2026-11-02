# Sandbox patch — tasks

Build the settled [design](design.md), one phase at a time, by hand per [D8](design.md#d8). The skill, decision and
threat-model text is the design's, word for word.

## Progress

- [x] 1 — The Codex project config
- [x] 2 — The sandbox fails closed
- [x] 3 — The release ledger
- [x] 4 — The stale lock
- [x] 5 — The cards
- [x] 6 — The record
- [ ] 7 — The proof

## 1 — The Codex project config

- [x] 1.1 Add `codex_trust` to `skills/mf-ship/scripts/conduct.py`, pass it in `argv` for Codex in place of the dotted
  entries, and edit `test_a_worker_carries_the_allowlist_and_a_denial_is_named`, per [D6](design.md#d6).
  Verify: `grep -c 'def codex_trust' skills/mf-ship/scripts/conduct.py` prints `1`, and
  `uv run pytest -q tests/test_conduct.py -k carries_the_allowlist` reports `1 passed`.
- [x] 1.2 Start the drill's Codex control, trusted twin and plant with `codex_trust` in `tests/escape_drill.py`, per
  [D6](design.md#d6)'s drill table.
  Verify: `grep -c -E '[^_]codex_trust\b' tests/escape_drill.py` prints a number above `0`.
- [x] 1.3 **HALT CHECK** Run `uv run --script tests/escape_drill.py`, and write its output over
  `openspec/changes/0053-sandbox-patch/evidence/escape.md`, per [D6](design.md#d6).
  Verify: `grep -c -E '^codex (control: fired|trusted plant: loaded|project config: not loaded|trust written: no)' openspec/changes/0053-sandbox-patch/evidence/escape.md`
  prints `4`.

## 2 — The sandbox fails closed

- [x] 2.1 Add `failIfUnavailable` to `worker_settings` in `skills/mf-ship/scripts/conduct.py`, and to
  `test_a_claude_worker_starts_in_the_sandbox`, per [D1](design.md#d1).
  Verify: `grep -c 'failIfUnavailable' skills/mf-ship/scripts/conduct.py` prints `1`, and
  `uv run pytest -q tests/test_conduct.py -k starts_in_the_sandbox` reports `1 passed`.
- [x] 2.2 Add the probe mark, the scratch recipe and `check_probe`'s mark to `conduct.py`, the `unsandboxed` mode to
  `tests/fake_worker.py`, edit `test_each_check_passes_only_on_disk_evidence`, and add `test_a_probe_halts_on_a_write_out`, per [D1](design.md#d1).
  Verify: `uv run pytest -q tests/test_conduct.py -k 'probe_halts_on_a_write_out or only_on_disk_evidence'` reports `2 passed`.

## 3 — The release ledger

- [x] 3.1 Add the release ledger to `conduct.py` — write, check, base, tags, push and close — and `ledger` to `EVENTS`, and edit
  `test_a_run_pushes_only_tagged_merges`, per [D2](design.md#d2).
  Verify: `grep -c 'def _record_release' skills/mf-ship/scripts/conduct.py` prints `1`, and
  `uv run pytest -q tests/test_conduct.py -k run_pushes_only_tagged_merges` reports `1 passed`.
- [x] 3.2 Add `test_a_forged_release_is_not_pushed`, per [D2](design.md#d2) and [Tests](design.md#tests).
  Verify: `uv run pytest -q tests/test_conduct.py -k forged_release_is_not_pushed` reports `1 passed`.

## 4 — The stale lock

- [x] 4.1 Clear a stale lock in `Run.ship`, read a lock halt as `converge` in `stage_of`, add `unlock` to `EVENTS`, and add
  the resume line to `skills/mf-converge/SKILL.md`'s *Resuming a run*, per [D3](design.md#d3).
  Verify: `grep -c 'LOCK_STALE' skills/mf-ship/scripts/conduct.py` prints a number above `0`, and
  `grep -c 'Step 9 when both findings files are clean' skills/mf-converge/SKILL.md` prints `1`.
- [x] 4.2 Add `test_a_stale_lock_is_cleared_and_converge_resumes`, per [D3](design.md#d3) and [Tests](design.md#tests).
  Verify: `uv run pytest -q tests/test_conduct.py -k stale_lock_is_cleared` reports `1 passed`.

## 5 — The cards

- [x] 5.1 Pay `0052·R6`, `R8`, `R13` and `R14` in `conduct.py`, add `unkept` to `EVENTS`, and add `R13`'s step to
  `test_no_worker_pushes`, per [D4](design.md#d4).
  Verify: `grep -c 'permissions = "allowlist"' skills/mf-ship/scripts/conduct.py` prints `0`, and
  `grep -c 'json.dump(_urls(primary), kept)' skills/mf-ship/scripts/conduct.py` prints `0`.
- [x] 5.2 Pay `0052·R10` in `conduct.py` and `skills/mf-ship/SKILL.md` Step 4, and edit `test_a_changed_git_config_halts_a_merge_in`
  and `test_no_worker_pushes`, per [D4](design.md#d4).
  Verify: `grep -c 'changed git config is the person' skills/mf-ship/SKILL.md` prints `1`, and
  `uv run pytest -q tests/test_conduct.py -k 'changed_git_config_halts_a_merge_in or no_worker_pushes'` reports `2 passed`.
- [x] 5.3 Pay `0052·R7` in `skills/mf-release/SKILL.md`, per [D4](design.md#d4).
  Verify: `grep -c 'leave the push to conduct.py' skills/mf-release/SKILL.md` prints `1`.
- [x] 5.4 Merge `test_a_stop_survives_a_death` into `test_a_rerun_recovers_a_dead_release`, per [Tests](design.md#tests).
  Verify: `grep -c 'def test_a_stop_survives_a_death' tests/test_conduct.py` prints `0`, and
  `uv run pytest -q tests/test_conduct.py -k rerun_recovers_a_dead_release` reports `1 passed`.

## 6 — The record

- [x] 6.1 Edit `THREAT_MODEL.md` per [D5](design.md#d5).
  Verify: `grep -c 'credentials denied on Claude' THREAT_MODEL.md` prints `1`, `grep -c 'anchors included' THREAT_MODEL.md`
  prints `1`, and `grep -c 'does not block on it' THREAT_MODEL.md` prints `0`.
- [x] 6.2 Amend D51 and D47 in `docs/decisions.md`, per [D5](design.md#d5).
  Verify: `grep -c 'by a ledger there' docs/decisions.md` prints `1`, and `grep -c 'Ship tools:. names runs' docs/decisions.md` prints `1`.
- [x] 6.3 Edit `skills/mf-converge/SKILL.md`'s anchor rule, `skills/mf-converge/references/generic-security.md` and
  `skills/mf-ship/SKILL.md` Step 3, per [D5](design.md#d5).
  Verify: `grep -c 'anchors included' skills/mf-converge/SKILL.md` prints `1`, `grep -c 'never blocking' skills/mf-converge/references/generic-security.md`
  prints `1`, and `grep -c 'sandbox cannot start does not run' skills/mf-ship/SKILL.md` prints `1`.

## 7 — The proof

- [ ] 7.1 Run `Run.probe` on each executor in `tests/escape_drill.py`, per [D7](design.md#d7).
  Verify: `grep -c 'probe: held' tests/escape_drill.py` prints a number above `0`.
- [ ] 7.2 **HALT CHECK** Run `uv run --script tests/escape_drill.py`, and write its output over
  `openspec/changes/0053-sandbox-patch/evidence/escape.md`, per [D7](design.md#d7).
  Verify: `grep -c -E '^(claude|codex) probe: held' openspec/changes/0053-sandbox-patch/evidence/escape.md` prints `2`, and
  `grep -c -E '^claude (worker|subagent): held' openspec/changes/0053-sandbox-patch/evidence/escape.md` prints a number above `1`.
