# 0018-converge-status-log — tasks

**In one line:** one phase — the status-log section and the event line in each step. The text is in
[design.md](design.md).

## Progress

- [x] 1 — Converge keeps a status log

## 1 — Converge keeps a status log

The section fixes the file and its shape; each step names the event it writes ([D1](design.md#d1)–[D5](design.md#d5)).

- [x] 1.1 **HALT CHECK** — no skill names a status log yet. Verify:
  `grep -rc '_status_log.md' skills/ | grep -v ':0$'` prints nothing.
- [x] 1.2 Test first: in `tests/test_skills.py`, add the status-log scan and its twin, bound to
  `sdd:converge-status:log`. Verify: `uv run pytest tests/test_skills.py -q` fails, naming `skills/mf-converge/SKILL.md`.
- [x] 1.3 `skills/mf-converge/SKILL.md`: add `## The status log` before `## Catch-up round` — path, line form, order,
  runs, event list and ending rule, with [the log's shape](design.md#the-logs-shape). Verify:
  `grep -c '^## The status log' skills/mf-converge/SKILL.md` prints `1`.
- [x] 1.4 `skills/mf-converge/SKILL.md`: each step writes its event, per
  [where each event is written](design.md#where-each-event-is-written). Verify:
  `grep -c 'status log' skills/mf-converge/SKILL.md` prints `8` or more.
- [x] 1.5 `skills/mf-converge/SKILL.md` `## Never`: never edit or delete a status-log line. Verify:
  `grep -c 'status-log line' skills/mf-converge/SKILL.md` prints `1`.
- [x] 1.6 The scans pass. Verify: `uv run pytest tests/test_skills.py -q` exits 0.
