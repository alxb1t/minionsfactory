# Small fixes — tasks

The phases follow [design](design.md): a phase and an id, the lock and the card, the prose, the cap's case, the port's case. Each task names its files and links the decision it follows.

## Progress

- [x] 1 — A phase and an id · moderate
- [x] 2 — The lock and the card · moderate
- [x] 3 — The prose · moderate
- [ ] 4 — The cap's case · moderate
- [ ] 5 — The port's case · hard

## 1 — A phase and an id

- [x] 1.1 In `tests/test_converge.py` add the setups `_no_progress` (commit a `tasks.md` with no `## Progress` list) and `_upper_tick` (`_TASKS` with `- [x] 1` as `- [X] 1`), and the cases `no progress` and `upper-case tick` to `_REFUSED`, each code 1 and reason `tasks.md has no ## Progress list` ([D1](design.md#d1)).
  Verify: `uv run pytest tests/test_converge.py --collect-only -q -k refuses_what_it_cannot_start` lists the cases `no progress` and `upper-case tick`.
- [x] 1.2 In `skills/mf-converge/scripts/converge.py` change `PROGRESS` to `^- \[([ x])\] (\d+) — `, and make `preconditions` raise `Halt("tasks.md has no ## Progress list")` when `PROGRESS.findall` finds nothing, before it reads a box ([D1](design.md#d1)).
  Verify: `uv run pytest tests/test_converge.py -q -k refuses_what_it_cannot_start` passes.
- [x] 1.3 In `tests/test_conduct.py` add `test_a_change_id_has_no_empty_word`: the conductor's `CHANGE_ID` fully matches `0001-a` and `0001-a-b`, and no `0001-a-`, `0001--a` or `0001-`. In `tests/test_integrate.py` add `test_next_names_no_version_whose_id_has_an_empty_word`: after `_version(root, "0001-a-")`, `_run(root, "next", "0001-a-")` returns code 1 and `next: 0001-a- · not open` ([D2](design.md#d2)).
  Verify: `uv run pytest tests/test_conduct.py tests/test_integrate.py --collect-only -q -k empty_word` lists both tests.
- [x] 1.4 In `skills/mf-ship/scripts/conduct.py` build `CHANGE_ID` from `SLUG`, so both groups stay: `re.compile(rf"(\d+)-({SLUG.pattern})")`, after `SLUG`. In `skills/mf-integrate/scripts/integrate.py` change `CHANGE_ID` to `(\d+)-([a-z0-9]+(?:-[a-z0-9]+)*)` ([D2](design.md#d2)).
  Verify: `uv run pytest tests/test_conduct.py tests/test_integrate.py -q -k empty_word` passes.

## 2 — The lock and the card

- [x] 2.1 **HALT CHECK** Converge's wait and its card rule are what the text will follow: `LOCK_WAIT` is 600 and `blockers` passes `accepted` ([D3](design.md#d3), [D4](design.md#d4)).
  Verify: `git grep -n -e "^LOCK_WAIT = 600" -e "\"verified\", \"accepted\"" -- skills/mf-converge/scripts/converge.py` prints both lines.
- [x] 2.2 In `skills/mf-release/SKILL.md`, Step 4's clearing of cards, change `for 2 minutes, then halt` to `for 10 minutes, then halt` ([D3](design.md#d3)).
  Verify: `git grep -n "for 10 minutes, then halt" -- skills/mf-release/SKILL.md` prints the line.
- [x] 2.3 In `skills/mf-release/SKILL.md`, preconditions 2 and 3, change `` `verified`, not merely `fixed` `` to `` `verified` or `accepted`, not merely `fixed` `` and `` `verified`. Else → halt `` to `` `verified` or `accepted`. Else → halt `` ([D4](design.md#d4)).
  Verify: `git grep -c "verified. or .accepted" -- skills/mf-release/SKILL.md` prints `skills/mf-release/SKILL.md:2`.

## 3 — The prose

- [x] 3.1 In the run directory's sentence of `skills/mf-build/SKILL.md`, `skills/mf-plan/SKILL.md`, `skills/mf-cut-change/SKILL.md`, `skills/mf-release/SKILL.md` and `skills/mf-integrate/SKILL.md`, replace `` `$(git rev-parse --path-format=absolute --git-common-dir)/../.minions` `` with `` `git rev-parse --path-format=absolute --git-common-dir`, then its parent's `.minions` ``; the words after it stay ([D5](design.md#d5)).
  Verify: `git grep -n -F "git-common-dir)/" -- skills` prints nothing.
- [x] 3.2 In `tests/test_skills.py` add `_SUBSTITUTION = re.compile(r"\$\((?!shell\b)[a-z]")` and `_substitution_problems(base)`, one line `skills/<name>/SKILL.md:<line>: a command substitution` for each line of each `SKILL.md` the pattern finds. Add `test_no_skill_names_a_command_substitution` (the repository: none) and `test_the_substitution_scan_reports_each_line`, which plants `` `$(git rev-parse HEAD)` `` and `` `$(shell …)` `` with `_plant` and expects the first alone ([D5](design.md#d5)).
  Verify: `uv run pytest tests/test_skills.py -q -k substitution` passes.
- [x] 3.3 In `skills/mf-converge/SKILL.md`, the sentence that begins `It loads` and names `stamp.py`: add `evidence.py` and `gate_integrity.py` to the scripts it loads from its folder, so the list ends `` `plan_check.py`, `evidence.py`, `gate_integrity.py` and `overlap.py` `` ([D6](design.md#d6)).
  Verify: `git grep -n -e evidence.py -e gate_integrity.py -- skills/mf-converge/SKILL.md` prints the line.
- [x] 3.4 In `tests/test_skills.py` add `_loads_problems(base)`: read the `names` cell of the `skills/mf-converge/scripts/converge.py` row of `docs/modules.md`, and for each name `skills/mf-converge/SKILL.md` does not hold print `skills/mf-converge/SKILL.md: <name>: not named`. Add `test_mf_converge_names_each_script_the_map_says_it_loads` (the repository: none) and a twin that writes `docs/modules.md` itself, the row `` | `skills/mf-converge/scripts/converge.py` | station | a.py, b.py | ``, plants a text naming `a.py`, and expects `b.py` alone ([D6](design.md#d6)).
  Verify: `uv run pytest tests/test_skills.py -q -k "names_each_script"` passes.

## 4 — The cap's case

- [ ] 4.1 In `tests/test_converge.py` add `test_a_resumed_counted_catch_up_halts_at_round_three`, shaped on the `catch-up at round three` branch of `_resumed`: plant a run, mark `catch-up`, whose first event is `round 2 · catch-up — … · counted` and whose newest event is a `verdicts` line at round 3, with the findings files at round 3 and a blocking card open; no `catch-up` or `start` event comes after it. `run(host)` returns 1 and the last event is `round 3 · halt — cap reached, R1 open · head <head>` ([D7](design.md#d7)).
  Verify: `uv run pytest tests/test_converge.py -q -k counted_catch_up` passes.
- [ ] 4.2 See 4.1's case red: in `skills/mf-converge/scripts/converge.py` change the `and` of `first.name == "catch-up" and first.detail` in `cap_of` to `or`, run the case, see it fail, and put `and` back. Quote the failing line in the commit body ([D7](design.md#d7)).
  Verify: `git grep -n -F "first.name == \"catch-up\" and first.detail" -- skills/mf-converge/scripts/converge.py` prints the line.

## 5 — The port's case

- [ ] 5.1 **HALT CHECK** The profile holds the signal rule the card asks for: the port's text names `(deny signal)` and `(allow signal (target same-sandbox))` ([D9](design.md#d9)).
  Verify: `git grep -n -e "(deny signal)" -e "(allow signal (target same-sandbox))" -- skills/mflib/platform.py` prints both lines.
- [ ] 5.2 In `tests/test_sandboxed.py` delete `test_the_cuts_hold_is_released_under_the_rule`, `_AWAKE`, and the `shlex` import its command alone used ([D8](design.md#d8)).
  Verify: `git grep -n -e test_the_cuts_hold_is_released_under_the_rule -e _AWAKE -- tests/test_sandboxed.py` prints nothing.
- [ ] 5.3 In `tests/test_sandboxed.py` add, under `real_sandbox`, `test_a_signal_between_siblings_is_delivered`: one sandboxed Python command runs two children in turn. The first starts `sleep 60` with `start_new_session=True` and prints its pid to the command's output; the second signals that pid with `SIGTERM`. The command exits 0; the test reads the pid from the output, sees the sleep gone within 10 s, and kills it in a `finally` ([D8](design.md#d8)).
  Verify: `uv run pytest tests/test_sandboxed.py -q -k signal_between_siblings` exits 0, passing under Seatbelt and skipping without it.
