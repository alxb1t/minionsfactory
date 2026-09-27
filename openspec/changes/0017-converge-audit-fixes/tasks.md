# 0017-converge-audit-fixes — tasks

**In one line:** the head check first, then the card's vocabulary, then the stations' new duties. The text is in
[design.md → Where each rule lands](design.md#where-each-rule-lands).

## Progress

- [x] 1 — No unreviewed commit ships
- [x] 2 — Anchors, drift and repeats
- [x] 3 — The stale-claim pass and the red run

## 1 — No unreviewed commit ships

The release check and the catch-up round that answers it land together ([D1](design.md#d1), [D2](design.md#d2)).

- [x] 1.1 **HALT CHECK** — `mf-release` compares no head today. Verify:
  `grep -c 'HEAD equals the head:' skills/mf-release/SKILL.md` prints `0`.
- [x] 1.2 Test first: in `tests/test_skills.py`, add the reviewed-head scan and its twin, bound to
  `sdd:converge-audit:reviewed-head`. Verify: `uv run pytest tests/test_skills.py -q` fails, naming
  `skills/mf-release/SKILL.md`.
- [x] 1.3 `skills/mf-release/SKILL.md` Step 1: add the D1 precondition. Verify:
  `grep -c 'HEAD equals the head:' skills/mf-release/SKILL.md` prints `1`.
- [x] 1.4 `skills/mf-converge/SKILL.md`: add `## Catch-up round` before Step 1, per the D1–D2 diagram. Verify:
  `grep -c '^## Catch-up round' skills/mf-converge/SKILL.md` prints `1`.
- [x] 1.5 The scans pass. Verify: `uv run pytest tests/test_skills.py -q` exits 0.

## 2 — Anchors, drift and repeats

The card's vocabulary, which phase 3's stale-claim pass writes into ([D3](design.md#d3)–[D6](design.md#d6)).

- [x] 2.1 Test first: in `tests/test_skills.py`, add the anchors-and-drift scan and the repeats scan, each with its
  twin, bound to `sdd:converge-audit:anchors-and-drift` and `sdd:converge-audit:repeats-escalate`. Verify:
  `uv run pytest tests/test_skills.py -q` fails, naming `skills/mf-converge/SKILL.md`.
- [x] 2.2 `skills/mf-converge/SKILL.md` Step 4 and the **Priority** row: the D3 and D4 rows. Verify:
  `grep -c 'blocking | drift | nit' skills/mf-converge/SKILL.md` prints `1` or more.
- [x] 2.3 `skills/mf-converge/SKILL.md` Step 5, Step 8 and `## Never`: the D4 rows. Verify:
  `grep -c 'every `drift` card' skills/mf-converge/SKILL.md` prints `1` or more.
- [x] 2.4 `skills/mf-converge/SKILL.md` Step 3: the D5 station input and repeat rule. Verify:
  `grep -c 'repeat of' skills/mf-converge/SKILL.md` prints `1` or more.
- [x] 2.5 `skills/mf-converge/SKILL.md` Step 9 and `## Never`: the D6 rows. Verify:
  `grep -c 'Never delete a card from the backlog.\*\*' skills/mf-converge/SKILL.md` prints `0`.
- [x] 2.6 `docs/sdd.md` *The findings contract*: the `docs/sdd.md` row, with the D9 sentence. Verify:
  `grep -c 'blocking | drift | nit' docs/sdd.md` prints `1`.
- [x] 2.7 The scans pass. Verify: `uv run pytest tests/test_skills.py -q` exits 0.

## 3 — The stale-claim pass and the red run

The stations' new duties ([D7](design.md#d7), [D8](design.md#d8)).

- [x] 3.1 Test first: in `tests/test_skills.py`, add the stale-claim scan and the red-run scan, each with its twin,
  bound to `sdd:converge-audit:stale-claim-pass` and `sdd:converge-audit:red-before-green`. Verify:
  `uv run pytest tests/test_skills.py -q` fails, naming `skills/mf-converge/SKILL.md`.
- [x] 3.2 `skills/mf-converge/SKILL.md` Step 3 and Step 5: the D7 rows. Verify:
  `grep -c 'stale-claim pass' skills/mf-converge/SKILL.md` prints `2` or more.
- [x] 3.3 `skills/mf-converge/SKILL.md` Step 6 and Step 7: the D8 rows. Verify:
  `grep -c 'failing run from before the fix' skills/mf-converge/SKILL.md` prints `1` or more.
- [x] 3.4 The scans pass. Verify: `uv run pytest tests/test_skills.py -q` exits 0.
