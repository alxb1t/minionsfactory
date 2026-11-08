# Cut and converge diet — tasks

Build the settled [design](design.md), one phase at a time; each test step goes red before its code.

## Progress

- [ ] 1 — Plan reviews
- [ ] 2 — Helpers and notes
- [ ] 3 — The pickup check
- [ ] 4 — The bundle
- [ ] 5 — The release and the record

## 1 — Plan reviews

- [ ] 1.1 **HALT CHECK** The base stands, `0100-worker-diet` merged: this `Verify:` alone; the
  [Context](design.md#context)'s line numbers are `ed7298f`'s.
  Verify: `test -d openspec/changes/archive/0100-worker-diet` exits 0; `grep -n '^### D70 · A worker starts lean$' docs/decisions.md` prints a line; `grep -n -e '^## Step 8.5 — Plan review$' -e '^\*\*Helpers\.\*\* Where the host starts fresh workers' skills/mf-cut-change/SKILL.md` prints a line for each.
- [ ] 1.2 Edit `## Step 8.5 — Plan review` of `skills/mf-cut-change/SKILL.md`: the packet, the budget, the review tree,
  the table's second row and the sentence on each review, per [D1](design.md#d1), each new phrase on one line.
  Verify: `grep -n -e 'the \*\*review packet\*\*' -e 'budget reached' -e 'git write-tree' -e 'judging the diff since the first' -e 'only at a path or .path:line.' skills/mf-cut-change/SKILL.md` prints a line for each.

## 2 — Helpers and notes

- [ ] 2.1 Edit *Helpers* and *The source is evidence*, and add *The notes*, in Step 2 of `skills/mf-cut-change/SKILL.md`,
  per [D2](design.md#d2), each new phrase on one line.
  Verify: `grep -n -e 'on Sonnet 5.5 · medium where the host offers it' -e '^\*\*The notes\.\*\*' -e 'a helper.s answer or the notes' skills/mf-cut-change/SKILL.md` prints a line for each.

## 3 — The pickup check

- [ ] 3.1 Add `## The pickup check`, the opening line's clause and the closing rule's clause to
  `skills/mf-converge/references/verify.md`; edit the frontmatter's `round:` and the Status diagram in `worker.md`; per
  [D3](design.md#d3).
  Verify: `grep -n -e '^## The pickup check$' -e 'a pickup check is no round' -e 'save a \[pickup check\]' -e 'in a pickup check, both findings files' skills/mf-converge/references/verify.md` prints a line for each; `grep -n -e 'never by a pickup check' -e 'the checker or a pickup check:' skills/mf-converge/references/worker.md` prints a line for each.
- [ ] 3.2 Edit the diagram, the `pickup` row of the events table, *Resuming a run*, Steps 6, 7 and 8 and *Never* of
  `skills/mf-converge/SKILL.md`, per [D3](design.md#d3), each new phrase on one line.
  Verify: `grep -n -e 'the pickup round counts' -e 'in the pickup round' skills/mf-converge/SKILL.md` prints nothing; `grep -n -e 'the pickup check is no round' -e 'verify round <N> · pickup' -e 'A pickup check is due' -e '8 pickup: 6 fix, one check' -e 'Step 8 item 6' -e 'writing no .verdicts. line' -e 'A role it needs is a mailbox role' -e 'every way to Step 7' -e 'and a pickup check, own their files' skills/mf-converge/SKILL.md` prints a line for each.

## 4 — The bundle

- [ ] 4.1 Edit `test_a_bundle_holds_what_the_change_cites` in `tests/test_bundle.py`, its verbatim-block asserts replaced by
  the diff's; then `diffed`, `bundle`, the section heading, `REPLACES` and the docstring in
  `skills/mf-converge/scripts/bundle.py`, per [D4](design.md#d4).
  Verify: `uv run pytest -q tests/test_bundle.py` reports `3 passed`; `grep -n -e '^def diffed(' -e 'difflib.unified_diff' -e 'Requirements the delta modifies or removes, as diffs' skills/mf-converge/scripts/bundle.py` prints a line for each.
- [ ] 4.2 Edit `test_debt_match_bundles_the_cards_on_the_diffs_files` and `test_debt_match_refuses_what_it_cannot_read` in
  `tests/test_debt_match.py`, then `skills/mf-converge/scripts/debt_match.py`, per [D4](design.md#d4).
  Verify: `uv run pytest -q tests/test_debt_match.py` reports `2 passed`; `grep -n -e '^HEADING = "# Debt cards on the diff.s files"$' -e '^def page(' skills/mf-converge/scripts/debt_match.py` prints a line for each; `grep -n '^def section(' skills/mf-converge/scripts/debt_match.py` prints nothing.
- [ ] 4.3 Edit `test_the_packets_hold_what_each_role_reads` in `tests/test_skills.py`, then the packet tables of
  `generic-conformance.md` and `generic-adversarial.md` and the `diff.patch` row of `verify.md`, per [D4](design.md#d4).
  Verify: `uv run pytest -q tests/test_skills.py` reports `21 passed`; `grep -n 'never a slice again' skills/mf-converge/references/generic-conformance.md skills/mf-converge/references/generic-adversarial.md skills/mf-converge/references/verify.md` prints a line for each file.
- [ ] 4.4 Edit *Spec* and the repeats line of `generic-conformance.md`, the repeat rule and *Scoping* of `worker.md`
  (`0095·R3`), and Step 2 item 4 of `skills/mf-converge/SKILL.md`, per [D4](design.md#d4), each new phrase on one line.
  Verify: `grep -n 'debt-cards.md' skills/mf-converge/SKILL.md skills/mf-converge/references/worker.md` prints a line for each file; `grep -n -e 'the bundle.s requirement diffs' -e 'check repeats against .debt-cards.md.' skills/mf-converge/references/generic-conformance.md` prints a line for each; `grep -n 'An \*\*amend round\*\* judges its whole range with the full plan' skills/mf-converge/references/worker.md` prints nothing; `grep -n 'In an \*\*amend round\*\*, conformance judges its whole range' skills/mf-converge/references/worker.md` prints a line.

## 5 — The release and the record

- [ ] 5.1 Edit Step 1 and the close-out of `skills/mf-release/SKILL.md`, per [D5](design.md#d5), each new phrase on one line.
  Verify: `grep -n -e 'in two reads, never whole' -e 'grep..s .inconclusive. lines' -e 'sed -n 1,20p' skills/mf-release/SKILL.md` prints a line for each.
- [ ] 5.2 Add D71 after D68's block in `docs/decisions.md`, and `D71` after `D68` on the map's check-loop line, per
  [D6](design.md#d6).
  Verify: `grep -n '^### D71 · The cut and converge read what changed$' docs/decisions.md` prints a line; `grep -n 'D66, D68, D71' docs/decisions.md` prints a line.
- [ ] 5.3 Amend D16, D40, D57, D64 and D66 in `docs/decisions.md`, per [D6](design.md#d6), each new phrase on one line.
  Verify: `grep -n -e 'in one more round' -e 'bundles the debt cards on the diff' docs/decisions.md` prints nothing; `grep -n -e 'checked by one verify pass that is no round' -e 'the cut writes their answers to its notes' -e 'bundle.md., .debt-cards.md., .models.toml' -e 'cut.halt. and .cut-notes.md' -e 'as a diff from the living spec' -e 'writes the debt cards on' docs/decisions.md` prints a line for each.
- [ ] 5.4 Edit *Checker*, *`fixed` is a claim* and *Every edit opens a round* in `docs/principles.md`, and `## Surfaces` in
  `THREAT_MODEL.md` (`0095·S5`), per [D6](design.md#d6), each new phrase on one line.
  Verify: `grep -n -e 'a pickup.s by one pass outside the cap' -e 'A pickup check is one checker for both files' -e 'or a pickup check, promotes it' docs/principles.md` prints a line for each; `grep -n -e 'references/verify.md. — how a checker promotes' -e 'A pickup.s fix is checked by one worker' THREAT_MODEL.md` prints a line for each.
