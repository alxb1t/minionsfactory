# Rescue — tasks

Build the settled [design](design.md), one phase at a time.

## Progress

- [x] 1 — The halt file
- [x] 2 — The skill
- [ ] 3 — The conductor
- [ ] 4 — The record

## 1 — The halt file

- [x] 1.1 Write `.minions/build/<id>.halt` on every halt in `skills/mf-build/SKILL.md`, and read it into the build check's halt line
  in `skills/mf-ship/scripts/conduct.py`, with a `halt-<id>` mode in `tests/fake_worker.py` and its step in
  `test_run_halts_when_a_worker_claims_what_disk_does_not_show`, per [D1](design.md#d1).
  Verify: `uv run pytest -q tests/test_conduct.py -k claims_what_disk_does_not_show` reports `1 passed`, and `grep -n '\.halt' skills/mf-build/SKILL.md` prints a line.

## 2 — The skill

- [x] 2.1 Write `skills/mf-rescue/SKILL.md`, per [D2](design.md#d2).
  Verify: `uv run pytest -q tests/test_skills.py` reports no failure, and `grep -n 'Rescue:' skills/mf-rescue/SKILL.md` prints a line.

## 3 — The conductor

- [ ] 3.1 Add `Run.rescue`, `PROMPTS["rescue"]`, `RESCUES`, `self.rescues`, the path check and `rescue` in `EVENTS`, called where
  [D3](design.md#d3) names; add the `rescue-fix`, `rescue-diagnose` and `rescue-wild` modes to `tests/fake_worker.py` and
  `test_a_rescue_fixes_a_plan_halt_in_its_run`, `test_a_rescue_diagnoses_a_decision_halt`, `test_a_rescue_outside_the_plan_halts`
  and `test_a_sub_task_is_rescued_once`, per [D3](design.md#d3) and [D4](design.md#d4).
  Verify: `uv run pytest -q tests/test_conduct.py -k rescue` reports `4 passed`.
- [ ] 3.2 Read `[rescue]` with the build's table as its fallback and `skip = true`, in `_table`, `_models` and `read_plan`; add
  `test_rescue_skip_runs_none`, per [D5](design.md#d5).
  Verify: `uv run pytest -q tests/test_conduct.py -k rescue_skip_runs_none` reports `1 passed`.
- [ ] 3.3 Read and empty the rejoin and grants folders by directory descriptor; add `test_a_linked_rejoin_folder_deletes_nothing`,
  per [D7](design.md#d7).
  Verify: `uv run pytest -q tests/test_conduct.py -k linked_rejoin_folder_deletes_nothing` reports `1 passed`.

## 4 — The record

- [ ] 4.1 Add the rescue lines to `report`; `mf-rescue` to `AGENTS.md`'s skills list and `skills/mf-ship/SKILL.md`'s halt table;
  amend D47 and add D53 in `docs/decisions.md`; name the class in `THREAT_MODEL.md`, per [D6](design.md#d6).
  Verify: `grep -n 'D53' docs/decisions.md` prints a line, and `grep -n 'mf-rescue' AGENTS.md` prints a line.
