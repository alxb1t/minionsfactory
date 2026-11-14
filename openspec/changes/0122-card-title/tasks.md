# Card title — tasks

The card title in every reader of cards, then the tick read in the build skill.

## Progress

- [ ] 1 — Card title · moderate
- [ ] 2 — Tick read · moderate

## 1 — Card title

- [ ] 1.1 In `skills/mf-converge/scripts/converge.py`, change `TITLE` and `DEBT_TITLE` per [D1](design.md#d1): `(\S+)` becomes `([^\s*]+)`.
  Verify: `git grep -c -F -e '[^\s*]+' -- skills/mf-converge/scripts/converge.py` prints `skills/mf-converge/scripts/converge.py:2`.
- [ ] 1.2 In `skills/mf-converge/scripts/open_cards.py`, `skills/mf-converge/scripts/debt_match.py` and `skills/mf-converge/scripts/overlap.py`, change `TITLE` the same way: `\S+` becomes `[^\s*]+`, the capture kept in `open_cards.py`.
  Verify: `git grep -c -F -e '[^\s*]+' -- skills/mf-converge/scripts/open_cards.py skills/mf-converge/scripts/debt_match.py skills/mf-converge/scripts/overlap.py` prints each file with `1`.
- [ ] 1.3 In `skills/mf-ship/scripts/conduct.py`, change `CARD` and the `re.match` in `_cards` the same way, `\S+` becoming `[^\s*]+` with the capture kept, per [D2](design.md#d2) and [D7](design.md#d7).
  Verify: `git grep -c -F -e '[^\s*]+' -- skills/mf-ship/scripts/conduct.py` prints `skills/mf-ship/scripts/conduct.py:2`.
- [ ] 1.4 In `skills/mf-cut-change/scripts/cut_context.py`, change `CARD_ID` the same way: `\S+` becomes `[^\s*]+`, the capture kept.
  Verify: `git grep -c -F -e '[^\s*]+' -- skills/mf-cut-change/scripts/cut_context.py` prints `skills/mf-cut-change/scripts/cut_context.py:1`.
- [ ] 1.5 Add `test_a_bold_bullet_is_no_card` to `tests/test_converge.py`, after `test_a_findings_file_is_read_by_its_fields`: a body of `## Passes`, `- **stale-claim** — ran.`, a `## Summary` with `- **Spec** — none.`, then `_card("R1 drift")`. Assert `malformed` is `None`, the ids of `cards` are `["R1"]`, and `DEBT_TITLE.findall` of the body is `["R1"]`.
  Verify: `uv run pytest -q tests/test_converge.py -k a_bold_bullet_is_no_card` exits 0.
- [ ] 1.6 Add `test_open_cards_leave_a_bold_bullet_out` to `tests/test_open_cards.py`: `_FRONT`, `## Passes`, `- **stale-claim** — ran.`, then `_OPEN`. Assert `main` exits 0 and writes `_OPEN` and no other card, as `test_open_cards_extract_what_a_verify_judges` asserts its output.
  Verify: `uv run pytest -q tests/test_open_cards.py -k leave_a_bold_bullet_out` exits 0.
- [ ] 1.7 Add this sentence to the paragraph of `skills/mf-converge/references/worker.md` that opens "The body is a list of cards", per [D3](design.md#d3): "No line outside a card starts with `- **`: write a pass or a Summary item as a plain bullet." Keep the words `No line outside a card starts with` on one line of the file.
  Verify: `git grep -c -F -e 'No line outside a card starts with' -- skills/mf-converge/references/worker.md` prints `skills/mf-converge/references/worker.md:1`.

## 2 — Tick read

- [ ] 2.1 In `skills/mf-build/SKILL.md` Step 2, add an item 7 `**Read the tick back.**` after the commit item, and renumber `Hand over to the next phase` to 8, per [D4](design.md#d4). It runs `git grep -n -e '^- \[.\] <N> — ' HEAD -- openspec/changes/<change-id>/tasks.md` and prints the output; a `[ ]` in it is ticked, staged by name and committed `docs(<change-id>): tick phase <N>` with the trailer block of item 6, and the command runs again. Change "then items 3–6," in the HUMAN paragraph to "then items 3–7,". Keep `Read the tick back` and `items 3–7` each on one line.
  Verify: `git grep -c -F -e 'Read the tick back' -e 'items 3–7' -- skills/mf-build/SKILL.md` prints `skills/mf-build/SKILL.md:2`.
- [ ] 2.2 In `skills/mf-build/SKILL.md` Step 4, add to "Your sentences" that the close-out quotes the `## Progress` line of each phase built, as item 7 printed it, the words `as item 7 printed it` on one line of the file.
  Verify: `git grep -c -F -e 'as item 7 printed it' -- skills/mf-build/SKILL.md` prints `skills/mf-build/SKILL.md:1`.
