# Findings — tasks

Pin each copy of the findings format as it stands, build the module, move the stations onto it, make the copies agree, then hold it by the gate and the record.

## Progress

- [x] 1 — The pin · moderate
- [ ] 2 — The module · hard
- [ ] 3 — The stations · moderate
- [ ] 4 — The fix · hard
- [ ] 5 — The rule and the record · moderate

## 1 — The pin

Each case is green on the tree as it stands ([D2](design.md#d2)). The worker sees it red once under the change its row of [the cases](design.md#the-cases) names, and never commits that change.

- [x] 1.1 Add `test_pin_a_*`, `test_pin_b_*`, `test_pin_c_*` and `test_pin_d_*` to `tests/test_converge.py`: cases a to d of [the cases](design.md#the-cases), each asserting what converge holds now.
  Verify: `uv run pytest tests/test_converge.py -q -k "test_pin_a_ or test_pin_b_ or test_pin_c_ or test_pin_d_"` passes.
- [x] 1.2 Add `test_pin_f_*` and `test_pin_g_converge_*` to `tests/test_converge.py`: case f, and case g's rows for converge's `Card.small` and open-blocker count.
  Verify: `uv run pytest tests/test_converge.py -q -k "test_pin_f_ or test_pin_g_converge_"` passes.
- [x] 1.3 Add `test_pin_e_conduct_*`, `test_pin_g_conduct_*` and `test_pin_h_*` to `tests/test_conduct.py`, reaching the conductor through `tests/conduct_load.py`: case e's conductor row, case g's conductor rows, case h.
  Verify: `uv run pytest tests/test_conduct.py -q -k "test_pin_e_conduct_ or test_pin_g_conduct_ or test_pin_h_"` passes.
- [x] 1.4 Add `test_pin_i_*`, `test_pin_j_*` and `test_pin_o_*` to `tests/test_conduct.py`: cases i, j and o, each on a file written under `tmp_path`.
  Verify: `uv run pytest tests/test_conduct.py -q -k "test_pin_i_ or test_pin_j_ or test_pin_o_"` passes.
- [x] 1.5 Add `test_pin_e_integrate_*` and `test_pin_n_*` to `tests/test_integrate.py`: case e's integrate row, and case n.
  Verify: `uv run pytest tests/test_integrate.py -q -k "test_pin_e_integrate_ or test_pin_n_"` passes.
- [x] 1.6 Add `test_pin_k_*` to `tests/test_open_cards.py`, `test_pin_l_*` to `tests/test_overlap.py` and `test_pin_m_*` to `tests/test_skip_stub.py`: cases k, l and m.
  Verify: `uv run pytest tests/test_open_cards.py tests/test_overlap.py tests/test_skip_stub.py -q -k "test_pin_k_ or test_pin_l_ or test_pin_m_"` passes.
- [x] 1.7 Add `test_pin_link_*` for each reader, in its own test file: `read_findings`, `_unjudged`, `unready`, `open_page`, `overlap.line` and `skip_stub.write`, each given a findings file that is a link.
  Verify: `uv run pytest tests/test_converge.py tests/test_conduct.py tests/test_integrate.py tests/test_open_cards.py tests/test_overlap.py tests/test_skip_stub.py -q -k test_pin_link` passes.
- [x] 1.8 Add `test_pin_malformed_*` for each reader, in its own test file, each given a file the rewrite left malformed ([D10](design.md#d10)): converge reads the role clean, `_unjudged` and `unready` read the file's own `verdict:`, `open_cards.py`, `overlap.py` and `skip_stub.py` answer as they do.
  Verify: `uv run pytest tests/test_converge.py tests/test_conduct.py tests/test_integrate.py tests/test_open_cards.py tests/test_overlap.py tests/test_skip_stub.py -q -k test_pin_malformed` passes.
- [x] 1.9 Add `test_pin_extent_converge_*` to `tests/test_converge.py`: where a card ends in converge's `_cards` — at a blank line, at an unindented line, at the next title, and at a `## Refuted` heading — the row of case b that the cases table names.
  Verify: `uv run pytest tests/test_converge.py -q -k test_pin_extent_converge` passes.
- [x] 1.10 Add `test_pin_amend_*` to `tests/test_converge.py`: an amend card whose qualified id is already in the debt file is skipped alone and the next amend card's check still runs; `unlocked` halts naming the role when a file is not clean at `HEAD`.
  Verify: `uv run pytest tests/test_converge.py -q -k test_pin_amend` passes.

## 2 — The module

The module takes converge's form as the one form, and holds each other copy's form as a legacy function ([D2](design.md#d2)).

- [ ] 2.1 Add `findings_name(role)`, `shadow_name(role)`, `open_name(role)` and `findings_file(primary, change, role)` to `skills/mflib/layout.py` ([D1](design.md#d1)), and `test_layout_findings_*` cases for each to `tests/test_layout.py`.
  Verify: `uv run pytest tests/test_layout.py -q -k test_layout_findings` passes.
- [ ] 2.2 Create `skills/mflib/findings.py`, standard library and `mflib.statefile` alone, with its first part: `BLOCKS`, `NON_SECURITY`, `SMALL`, `SIZE`, `TITLE`, `FIELD`, `Card`, `cards(text, role)` and `strays(text)`, from converge, `conduct.py` and `open_cards.py`, and the legacy form of each of their rules that differs: the extent, the field line, the word, the severity, the category, the status and the security card. Create `tests/test_findings.py` with a `test_card_*` case for each.
  Verify: `uv run pytest tests/test_findings.py -q -k test_card` passes.
- [ ] 2.3 Add its second part: `FRONT`, `front`, `fault`, `listed`, `frontmatter`, `read`, `halt_ids`, `stub`, `uncleared` and `stamped`, from converge, `conduct.py`, `integrate.py` and `skip_stub.py`, with a `test_front_*`, `test_read_*`, `test_stub_*` or `test_stamped_*` case for each. Each rule of [the copies](design.md#the-copies) that differs from converge's form is held as one legacy function, named as [D2](design.md#d2) says.
  Verify: `uv run pytest tests/test_findings.py -q -k "test_front or test_read or test_stub or test_stamped"` passes.
- [ ] 2.4 Add to `tests/test_findings.py` `test_legacy_*`: a table that runs each legacy function on the inputs of the pin's cases and expects the output the copy it replaces gave.
  Verify: `uv run pytest tests/test_findings.py -q -k test_legacy` passes.
- [ ] 2.5 Add the row `skills/mflib/findings.py`, layer `home`, names `statefile.py`, to `docs/modules.md`, in path order.
  Verify: `uv run pytest tests/test_structure.py -q` passes.

## 3 — The stations

No assert changes in this phase: a test's line that reaches a moved name changes, its asserts do not.

- [ ] 3.1 In `skills/mf-converge/scripts/converge.py` add `import mflib.findings` after `import mflib.layout`; delete `FRONT`, `TITLE`, `FIELD`, `BLOCKS`, `SMALL`, `SIZE`, `Card`, `_cards`, `_fault` and `_listed`; `read_findings`, `ruled`, `spoiled` and `stubs` take the module's names.
  Verify: `git grep -n -e "^FRONT = " -e "^TITLE = " -e "^FIELD = " -e "^BLOCKS = " -e "^SMALL = " -e "^SIZE = " -e "^class Card" -e "^def _cards(" -e "^def _fault(" -e "^def _listed(" -- skills/mf-converge/scripts/converge.py` prints nothing.
- [ ] 3.2 Make `skills/mf-converge/scripts/open_cards.py` and `skills/mf-converge/scripts/skip_stub.py` commands over the module: drop their `TITLE`, `NAMED`, `STATUS` and `WORD_END` patterns and `_read`, keep the names of [D3](design.md#d3), call the legacy form where a rule differs.
  Verify: `git grep -n -e "^TITLE = " -e "^NAMED = " -e "^STATUS = " -e "^WORD_END = " -- skills/mf-converge/scripts/open_cards.py skills/mf-converge/scripts/skip_stub.py` prints nothing.
- [ ] 3.3 In `skills/mf-converge/scripts/overlap.py` add the seed line of `skills/mf-converge/scripts/open_cards.py` and `import mflib.findings`; drop `TITLE`, `AFFECTS`, `PRIORITY`, `ROUND`, `EXECUTOR` and `_read`, so no pattern spells the card head (`- \*\*`); keep the names of [D3](design.md#d3); call the legacy form where a rule differs.
  Verify: `git grep -n -F -e "- \*\*" -- skills/mf-converge/scripts/overlap.py` prints nothing.
- [ ] 3.4 In `skills/mf-ship/scripts/conduct.py` delete `CARD`, `BLOCKS`, `NON_SECURITY`, `_field`, `_cards_in`, `_severity`, `_category`, `_status` and `_stamped`; `_open_blockers`, `_security_blocks`, `_security_card`, `_security_held`, `_unjudged`, `_amendable`, `_answered` and `_stamp` call the module, the legacy form where a rule differs; `_frontmatter` is one line over the module's conductor legacy form ([D3](design.md#d3)).
  Verify: `git grep -n -e "^def _field(" -e "^def _cards_in(" -e "^def _severity(" -e "^def _category(" -e "^def _status(" -e "^def _stamped(" -e "^CARD = " -- skills/mf-ship/scripts/conduct.py` prints nothing.
- [ ] 3.5 In `skills/mf-integrate/scripts/integrate.py` delete `def _frontmatter`, add `import mflib.findings` after `import mflib.layout`, and have `unready` call the module, the legacy form where a rule differs.
  Verify: `git grep -n -e "def _frontmatter" -- skills/mf-integrate/scripts/integrate.py` prints nothing.
- [ ] 3.6 In `docs/modules.md` add `findings.py` to the `names` cell of the rows of `converge.py`, `conduct.py`, `integrate.py`, `open_cards.py`, `overlap.py` and `skip_stub.py`, in order.
  Verify: `uv run pytest tests/test_structure.py -q` passes.

## 4 — The fix

Each task moves the rows of [the cases](design.md#the-cases) marked `turns` that its rule touches to `test_fix_<rule>_*` cases in the same test file ([D2](design.md#d2)), and adds a `test_fix_<rule>_*` case to `tests/test_findings.py`; the rules are `extent`, `field`, `word`, `security`, `ids`, `frontmatter`, `read`, `first` and `stamp`. A task that deletes a legacy function drops its row from the `test_legacy_*` table. A case marked `stays` is not touched.

- [ ] 4.1 One extent and one field line ([D4](design.md#d4)): the module's `cards` and `FIELD` are the one form in every reader; delete the legacy functions of the extent and of the field line.
  Verify: `uv run pytest tests/test_findings.py tests/test_converge.py tests/test_conduct.py tests/test_open_cards.py tests/test_overlap.py tests/test_skip_stub.py -q -k "test_fix_extent or test_fix_field"` passes.
- [ ] 4.2 One word ([D5](design.md#d5), [D11](design.md#d11)): `Card.word` reads Status, grade and category in every reader; an unknown or empty Status is not cleared; `open_cards.py` keeps its stop; `skip_stub.py` clears on `verified` alone.
  Verify: `uv run pytest tests/test_findings.py tests/test_conduct.py tests/test_open_cards.py tests/test_skip_stub.py -q -k test_fix_word` passes.
- [ ] 4.3 One security rule ([D6](design.md#d6)): `Card.security` fails closed on an unread category, as `_security_card` does; the malformed file's answer to the security readers is task 4.4's.
  Verify: `uv run pytest tests/test_findings.py tests/test_converge.py tests/test_conduct.py -q -k test_fix_security` passes.
- [ ] 4.4 Ids and strays ([D7](design.md#d7)): add `malformed(text, role)` to the module, naming a card id outside `R<n>` and `S<n>` and a Status or Priority under no title, and have each reader of cards call it and answer as the table of [D7](design.md#d7) says; the title pattern is unchanged.
  Verify: `uv run pytest tests/test_findings.py tests/test_converge.py tests/test_conduct.py tests/test_open_cards.py tests/test_overlap.py tests/test_skip_stub.py -q -k test_fix_ids` passes.
- [ ] 4.5 One frontmatter ([D8](design.md#d8)): `front` is the one form in `_frontmatter`, `unready`, `overlap.executor` and `uncleared`; `ruled` edits a key of the block alone; a key is stripped.
  Verify: `uv run pytest tests/test_findings.py tests/test_converge.py tests/test_conduct.py tests/test_integrate.py tests/test_overlap.py tests/test_skip_stub.py -q -k test_fix_frontmatter` passes.
- [ ] 4.6 One read ([D9](design.md#d9)): `_unjudged`, `_amendable`, `_answered`, `_open_blockers`, `_security_blocks`, `_security_held`, `unready`, `open_page`, `overlap.line` and `skip_stub.uncleared` read through the module's `read`; a missing file keeps each caller's answer.
  Verify: `uv run pytest tests/test_findings.py tests/test_conduct.py tests/test_integrate.py tests/test_open_cards.py tests/test_overlap.py tests/test_skip_stub.py -q -k test_fix_read` passes.
- [ ] 4.7 A repeated field reads its first line ([D11](design.md#d11)): `skip_stub.py` reads a card's Status through the module, no longer each Status line of the file.
  Verify: `uv run pytest tests/test_findings.py tests/test_skip_stub.py -q -k test_fix_first` passes.
- [ ] 4.8 The stamp ([D12](design.md#d12)): add `stamp(folder, name, model, tokens)` to the module, writing through `mflib.statefile.write` with the folder descriptor and mode `0o600`, its folder from `mflib.statefile.folder`; `_stamp` calls it.
  Verify: `uv run pytest tests/test_findings.py tests/test_conduct.py -q -k test_fix_stamp` passes.
- [ ] 4.9 Delete `_place` from `skills/mf-ship/scripts/conduct.py`: `_stamp` no longer calls it, and no other file does.
  Verify: `git grep -n -w -e "_place" -- skills` prints nothing.
- [ ] 4.10 Delete every function of `skills/mflib/findings.py` whose name ends `_legacy` ([D2](design.md#d2)) and its table row in `tests/test_findings.py`.
  Verify: `git grep -n -e "_legacy" -- skills` prints nothing.

## 5 — The rule and the record

- [ ] 5.1 In `tests/test_structure.py` make `_format_name` return `- **` for a string that contains `- **` or `- \*\*`, list each remaining site in `FORMAT_SITES`, each with its kind in a comment, as the table of [D13](design.md#d13) names them, and add `test_check_formats_card_head_*`: a planted `- **` constant and a planted `- \*\*` constant fail, a listed site that is gone fails, `skills/mflib/findings.py` passes.
  Verify: `uv run pytest tests/test_structure.py -q -k "test_check_formats_card_head or test_check_formats_holds_on_the_tree"` passes.
- [ ] 5.2 Amend D57, D78 and D83 in `docs/decisions.md` as [D15](design.md#d15) says, each decision edited where it lives.
  Verify: `git grep -c -e "findings.py" -- docs/decisions.md` exits 0.
- [ ] 5.3 In `THREAT_MODEL.md` name `skills/mflib/findings.py` in the sentence on the conductor's stamp, the sentence on findings files, the surface of the shared home and the sentence on a security card, which now reads an unread category as security in converge too.
  Verify: `git grep -c -e "findings.py" -- THREAT_MODEL.md` exits 0.
- [ ] 5.4 In `skills/mf-converge/SKILL.md` add `../../mflib/findings.py` for its reads and writes of a findings file to the sentence that lists what converge loads.
  Verify: `git grep -c -e "mflib/findings.py" -- skills/mf-converge/SKILL.md` exits 0.
- [ ] 5.5 In `docs/recipes.md` add to the state-file recipe that the findings files are written and parsed through `skills/mflib/findings.py`, their paths `layout.findings_file(primary, change, role)`.
  Verify: `git grep -c -e "findings.py" -- docs/recipes.md` exits 0.
