# Security hardening — tasks

Build the settled [design](design.md), one phase at a time. The skill, decision and threat-model text is the design's, word for word.

## Progress

- [x] 1 — The sandbox
- [x] 2 — No worker pushes
- [x] 3 — The cards
- [x] 4 — The record
- [x] 5 — The proof
- [x] 6 — The converge's fixes

## 1 — The sandbox

- [x] 1.1 In `skills/mf-ship/scripts/conduct.py`, add `worker_settings`, `SECRETS` and `NETWORK`, per [D1](design.md#d1), and
  `Ship network:` and Codex's network off, per [D2](design.md#d2).
  Verify: `grep -c 'def worker_settings' skills/mf-ship/scripts/conduct.py` prints `1`.
- [x] 1.2 Add `test_a_claude_worker_starts_in_the_sandbox` to `tests/test_conduct.py`, and edit
  `test_a_worker_carries_the_allowlist_and_a_denial_is_named`.
  Verify: `uv run pytest -q tests/test_conduct.py -k starts_in_the_sandbox` reports `1 passed`.

## 2 — No worker pushes

- [x] 2.1 Edit `skills/mf-release/SKILL.md` and `Run.advance`, and stop `tests/fake_worker.py`'s `release` pushing, per
  [D3](design.md#d3).
  Verify: `grep -c 'skip this: `conduct.py` pushes' skills/mf-release/SKILL.md` prints `2`.
- [x] 2.2 Add `test_no_worker_pushes` to `tests/test_conduct.py`.
  Verify: `uv run pytest -q tests/test_conduct.py -k no_worker_pushes` reports `1 passed`.

## 3 — The cards

- [x] 3.1 Read the plan once, per [D4](design.md#d4), and add `test_the_plan_is_read_once`.
  Verify: `uv run pytest -q tests/test_conduct.py -k plan_is_read_once` reports `1 passed`.
- [x] 3.2 Halt a person's commit before integrate, per [D5](design.md#d5), and add
  `test_a_commit_during_a_run_halts_before_integrate`.
  Verify: `uv run pytest -q tests/test_conduct.py -k halts_before_integrate` reports `1 passed`.
- [x] 3.3 Narrow the LFS remedy, per [D6](design.md#d6), and add `test_a_mixed_key_list_gets_no_lfs_remedy`.
  Verify: `uv run pytest -q tests/test_conduct.py -k mixed_key_list` reports `1 passed`.

## 4 — The record

- [x] 4.1 Amend D17 and D47, and add D51, in `docs/decisions.md`, per [D7](design.md#d7).
  Verify: `grep -c '^### D51' docs/decisions.md` prints `1`, and `grep -c 'under .merge=yes., .conduct.py. pushes' docs/decisions.md` prints `1`.
- [x] 4.2 Edit `THREAT_MODEL.md` and `skills/mf-ship/SKILL.md`, per [D7](design.md#d7).
  Verify: `grep -c 'A Codex worker can read' THREAT_MODEL.md` prints `1`.

## 5 — The proof

- [x] 5.1 Write `tests/escape_drill.py`, per [D8](design.md#d8).
  Verify: `uv run --script tests/escape_drill.py --help` exits 0.
- [x] 5.2 **HALT CHECK** Run it, and write `openspec/changes/0052-security-hardening/evidence/escape.md`, per [D8](design.md#d8).
  Verify: `grep -c '^claude subagent: held' openspec/changes/0052-security-hardening/evidence/escape.md` prints `1`,
  `grep -c '^claude worker: held' openspec/changes/0052-security-hardening/evidence/escape.md` prints `1`, and
  `grep -c '^codex converge: clean' openspec/changes/0052-security-hardening/evidence/escape.md` prints `1`.
- [x] 5.3 **HALT CHECK** Run `tests/drill_resume.py`, and write `openspec/changes/0052-security-hardening/evidence/drill.md`.
  Verify: `grep -c 'killed: done' openspec/changes/0052-security-hardening/evidence/drill.md` prints `2`.
- [x] 5.4 Write `openspec/changes/0052-security-hardening/evidence/rejudge.md`, and add each moot card to `proposal.md`'s
  `backlog:`, per [D8](design.md#d8).
  Verify: `grep -c '0050·R11' openspec/changes/0052-security-hardening/evidence/rejudge.md` prints `1`.

## 6 — The converge's fixes

- [x] 6.1 Pay `0050·S3`: start a Claude worker with `--setting-sources user`, per [D1](design.md#d1), record the crossing in
  `THREAT_MODEL.md` and D47, per [D7](design.md#d7), and prove it in the drill, per [D8](design.md#d8).
  Verify: `grep -c 'setting-sources' skills/mf-ship/scripts/conduct.py` prints `1`, and
  `grep -c -i 'mixed run' THREAT_MODEL.md` prints `1`.
- [x] 6.2 Deny `SECRETS` to the `Read` tool, and take `registry.npmjs.org` off `NETWORK`, per [D1](design.md#d1).
  Verify: `uv run pytest -q tests/test_conduct.py -k starts_in_the_sandbox` reports `1 passed`.
- [x] 6.3 Take the LFS remedy only on LFS's own values, per [D6](design.md#d6).
  Verify: `uv run pytest -q tests/test_conduct.py -k mixed_key_list` reports `1 passed`.
- [x] 6.4 Run the conductor's remote calls from a scratch repo, and keep the run's first URL, per [D9](design.md#d9).
  Verify: `uv run pytest -q tests/test_conduct.py -k 'no_worker_pushes or rerun_pushes'` reports `2 passed`.
- [x] 6.5 Keep `origin`'s URLs in the home folder, and compare before any remote call, per [D9](design.md#d9), and record the
  exception to *The repo reaches nothing outside itself*.
  Verify: `grep -c 'def _keep_origin' skills/mf-ship/scripts/conduct.py` prints `1`, and
  `uv run pytest -q tests/test_conduct.py -k no_worker_pushes` reports `1 passed`.
- [x] 6.6 Halt `primary_of` on a repo git names past its folder, refuse a held key before the config comparison, per
  [D9](design.md#d9), and fold the kept URLs into the delta's *A halt stops only its version, and a re-run resumes*.
  Verify: `grep -c 'A halt stops only its version' openspec/changes/0052-security-hardening/specs/sdd/spec.md` prints `1`, and
  `uv run pytest -q tests/test_conduct.py -k 'no_worker_pushes or changed_git_config'` reports `2 passed`.
- [x] 6.7 Leave a first read to `Run`: `status`, `check` and `report` make no remote call for a repo no run kept, per
  [D9](design.md#d9).
  Verify: `grep -c 'def _read_url' skills/mf-ship/scripts/conduct.py` prints `1`, and
  `uv run pytest -q tests/test_conduct.py -k 'no_worker_pushes or rerun_pushes'` reports `2 passed`.
- [x] 6.8 Fetch no missing object in `_run`, print `run · unread` where a merged tag has no run's read, and keep the URLs in a run
  with no version, per [D9](design.md#d9).
  Verify: `grep -c 'GIT_NO_LAZY_FETCH' skills/mf-ship/scripts/conduct.py` prints `1`, `grep -c 'run · unread' skills/mf-ship/SKILL.md`
  prints `2`, and `uv run pytest -q tests/test_conduct.py -k 'no_worker_pushes or rerun_pushes'` reports `2 passed`.
