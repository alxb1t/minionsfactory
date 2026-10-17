# 0025-improvements — tasks

**In one line:** the close-outs; the cut commits without waiting; the release merges and pushes on a yes; the
HUMAN checklist. The text is in [design.md](design.md). A wrapped line is checked joined:
`tr -s '\n ' ' ' < <file>` turns the file into one line.

## Progress

- [ ] 1 — The close-outs
- [ ] 2 — The cut commits without waiting
- [ ] 3 — The release merges and pushes
- [ ] 4 — The HUMAN checklist

## 1 — The close-outs

[The close-out line](design.md#the-close-out-line) and [the report steps](design.md#the-report-steps) in
`mf-bootstrap`, `mf-cut-change`, `mf-build`, `mf-converge` and `mf-release` ([B1](design.md#b1)–[B3](design.md#b3)), then the scan.

- [ ] 1.1 **HALT CHECK** — the report steps read as design quotes them. Verify:
  `grep -c '^Report five things:$' skills/mf-converge/SKILL.md` and
  `grep -c '^Report the phases built, the gate' skills/mf-build/SKILL.md` each print `1`.
- [ ] 1.2 `skills/mf-bootstrap/SKILL.md`: Step 5, and the `.gitignore` row ([B14](design.md#b14), `0024·N2`).
  Verify: `grep -c '^\*\*Close-out:\*\* at most three sentences' skills/mf-bootstrap/SKILL.md` and
  `grep -c 'starting on a new line' skills/mf-bootstrap/SKILL.md` each print `1`.
- [ ] 1.3 `skills/mf-cut-change/SKILL.md`: Step 11. Verify:
  `grep -c '^\*\*Close-out:\*\* at most three sentences' skills/mf-cut-change/SKILL.md` and
  `grep -c 'Next: /mf-build <change-id>, in a fresh session.' skills/mf-cut-change/SKILL.md` each print `1`.
- [ ] 1.4 `skills/mf-build/SKILL.md`: Step 4, and Step 2 item 2. Verify:
  `grep -c '^\*\*Close-out:\*\* at most three sentences' skills/mf-build/SKILL.md`,
  `grep -c 'Show the command.s real output as it runs' skills/mf-build/SKILL.md` and
  `grep -c 'Next: /mf-converge, in a fresh session.' skills/mf-build/SKILL.md` each print `1`.
- [ ] 1.5 `skills/mf-converge/SKILL.md`: Step 10. Verify:
  `grep -c '^\*\*Close-out:\*\* at most three sentences' skills/mf-converge/SKILL.md` and
  `grep -c 'Next: /mf-release, in a fresh session.' skills/mf-converge/SKILL.md` each print `1`, and
  `grep -c '^Report five things:$' skills/mf-converge/SKILL.md` prints `0`.
- [ ] 1.6 `skills/mf-release/SKILL.md`: Step 5, the phase-1 text. Verify:
  `grep -c '^\*\*Close-out:\*\* at most three sentences' skills/mf-release/SKILL.md` and
  `grep -c 'Next: merge and push' skills/mf-release/SKILL.md` each print `1`.
- [ ] 1.7 `tests/test_skills.py`: `_close_out_problems`, its test and its planted twin, both named with
  `close_out`, per [the scans](design.md#the-scans). Verify:
  `uv run pytest tests/test_skills.py -q -k close_out | tail -1 | grep -c '^2 passed'` prints `1`.

## 2 — The cut commits without waiting

[The cut commits](design.md#the-cut-commits), word for word ([B4](design.md#b4)–[B6](design.md#b6)).

- [ ] 2.1 **HALT CHECK** — the wait reads as design quotes it. Verify:
  `grep -c 'Then \*\*wait for their OK\*\*' skills/mf-cut-change/SKILL.md` and
  `grep -c "The person's OK precedes the commit" docs/decisions.md` each print `1`.
- [ ] 2.2 `skills/mf-cut-change/SKILL.md`: the description, the role line, Step 8, Step 9 and *Never*. Verify:
  `grep -c '^## Step 9 — Show, then commit$' skills/mf-cut-change/SKILL.md` prints `1`,
  `grep -c 'wait for their OK' skills/mf-cut-change/SKILL.md` prints `0`, and
  `tr -s '\n ' ' ' < skills/mf-cut-change/SKILL.md | grep -o 'once the human starts it' | wc -l | tr -d ' '`
  prints `2`.
- [ ] 2.3 `docs/decisions.md`: D7's bold paragraph, D38 after D10, and the map's Planning ids. Verify:
  `grep -c '^### D38 · The cut commits without waiting$' docs/decisions.md` and
  `grep -c 'D5…D10, D38' docs/decisions.md` each print `1`, and
  `grep -c "The person's OK precedes the commit" docs/decisions.md` prints `0`.
- [ ] 2.4 `docs/principles.md`: the accepted exception. Verify:
  `tr -s '\n ' ' ' < docs/principles.md | grep -c "The person's read of the committed change and"` prints `1`.
- [ ] 2.5 `tests/test_skills.py`: `_cut_commits_problems`, its test and its planted twin, both named with
  `cut_commits`, and the comment above `_SELF_CHECK`. Verify: `uv run pytest tests/test_skills.py -q -k cut_commits | tail -1 | grep -c '^2 passed'`
  and `grep -c 'the build runs them once the human starts it' tests/test_skills.py` each print `1`.

## 3 — The release merges and pushes

[The release merges and pushes](design.md#the-release-merges-and-pushes), word for word
([B7](design.md#b7)–[B10](design.md#b10), [B14](design.md#b14)).

- [ ] 3.1 **HALT CHECK** — the release and D17 read as design quotes them. Verify:
  `grep -c 'Never merge, never push, never check out the default branch' skills/mf-release/SKILL.md` and
  `grep -c '^### D17 · The release verifies, folds, archives, tags, and stops$' docs/decisions.md` each print `1`.
- [ ] 3.2 `skills/mf-release/SKILL.md`: the description, the title, the role block, the new Step 5, Step 6 and
  *Never*. Verify: `grep -c "^## Step 5 — Merge and push, on the person's yes$" skills/mf-release/SKILL.md`,
  `grep -c '^## Step 6 — Close: report, and stop$' skills/mf-release/SKILL.md` and
  `grep -c 'Next: grill the next version.' skills/mf-release/SKILL.md` each print `1`, and
  `grep -c 'Squash caveat' skills/mf-release/SKILL.md` prints `0`.
- [ ] 3.3 `docs/decisions.md`: D17 whole, and D8's title (`0024·N1`). Verify:
  `grep -c "^### D17 · The release verifies, folds, archives, tags, and on the person's yes merges and pushes$" docs/decisions.md`
  and `grep -c "stays out of this repo's gate$" docs/decisions.md` each print `1`, and
  `grep -c 'stays out of the gate$' docs/decisions.md` prints `0`.
- [ ] 3.4 `README.md`: lines 10 and 29. Verify:
  `grep -c 'One change goes from an idea to a tag on the default branch.' README.md` and
  `grep -c 'then, on a yes, merge and push' README.md` each print `1`.
- [ ] 3.5 `tests/test_skills.py`: `_merge_problems`, its test `test_the_release_merges_and_pushes_on_a_yes` and
  its planted twin `test_the_merge_scan_reports_every_needle`. Verify:
  `uv run pytest tests/test_skills.py -q -k 'merges_and_pushes or merge_scan' | tail -1 | grep -c '^2 passed'`
  prints `1`.

## 4 — The HUMAN checklist

[The HUMAN checklist](design.md#the-human-checklist), word for word ([B11](design.md#b11), [B12](design.md#b12)).

- [ ] 4.1 **HALT CHECK** — the HUMAN paragraph reads as design quotes it. Verify:
  `grep -c 'print its sub-tasks as the person' skills/mf-build/SKILL.md` prints `1`.
- [ ] 4.2 `I14` in `skills/mf-build/SKILL.md` and `skills/mf-cut-change/SKILL.md`. Verify:
  `grep -c 'exact commands with real values' skills/mf-build/SKILL.md skills/mf-cut-change/SKILL.md` prints
  `skills/mf-build/SKILL.md:1` and `skills/mf-cut-change/SKILL.md:1`, and
  `uv run pytest tests/test_skills.py -q -k contract | tail -1 | grep -c '^2 passed'` prints `1`.
- [ ] 4.3 `skills/mf-build/SKILL.md`: the HUMAN paragraph in Step 2. Verify:
  `grep -c '<N> — <Title> · HUMAN' skills/mf-build/SKILL.md` and `grep -c '^Next: /mf-build$' skills/mf-build/SKILL.md`
  each print `1`, and `grep -c 'print its sub-tasks as the person' skills/mf-build/SKILL.md` prints `0`.
- [ ] 4.4 `tests/test_skills.py`: `_human_checklist_problems`, its test and its planted twin, named with
  `human_checklist`. Verify:
  `uv run pytest tests/test_skills.py -q -k human_checklist | tail -1 | grep -c '^2 passed'` prints `1`.
