# The debt file module — tasks

The phases: the pin on today's code, the module with no caller, the stations through it, the fix of each copy's right side, the record.

## Progress

- [x] 1 — The pin · moderate
- [x] 2 — The module · hard
- [x] 3 — The stations · moderate
- [x] 4 — The fix · hard
- [x] 5 — The rule and the record · moderate
- [x] 6 — The title's width · moderate

## 1 — The pin

Each case below is green on the code as it stands and seen red under the change it names, per [D1](design.md#d1). A test's name starts `test_debt_pin_` and the task's word, so its `-k` finds it.

- [x] 1.1 **HALT CHECK** The functions the pin reaches stand in converge as the design reads them.
  Verify: `git grep -n -e "^def still_true" -e "^def amends" -e "^def debted" -e "^def spoiled" -- skills/mf-converge/scripts/converge.py` prints a line for each.
- [x] 1.2 In `tests/test_converge.py` add `test_debt_pin_still_true`: `still_true` strips the value; the command is the first backticked span at its start, split by `shlex`; prose runs nothing; an unbalanced quote and a blank span read `None`.
  Verify: `uv run pytest tests/test_converge.py -q -k debt_pin_still_true` passes.
- [x] 1.3 In `tests/test_converge.py` add `test_debt_pin_lock`: `debt_lock` makes `.minions/debt.lock` by `mkdir` and holds it through the body; an error in the body releases it; a held lock gets waits of `LOCK_POLL` seconds up to `LOCK_WAIT`, then the halt, and stays; a dangling `backlog.md` halts; the release removes a lock another holder made, and raises when the lock was broken.
  Verify: `uv run pytest tests/test_converge.py -q -k debt_pin_lock` passes.
- [x] 1.4 In `tests/test_converge.py` add `test_debt_pin_read`: `_debt_text` reads no file as `""`, replaces a bad byte, and halts on a link, a folder and a pipe, each by its reason, the pipe case bounded by a thread joined in ten seconds; the title pattern counts any `- **<id> — ` line at column 0, an unqualified id too.
  Verify: `uv run pytest tests/test_converge.py -q -k debt_pin_read` passes.
- [x] 1.5 In `tests/test_converge.py` add `test_debt_pin_filed`: the section is `## <change>` exactly, so a heading with trailing blanks gets a second heading; a section ends at a `## ` line alone; cards go after its last non-blank line; `_unfiled` takes the title and its indented lines, the id whole, and an emptied section's heading too, and an unknown id raises. The rows 0138 changed are proved again here.
  Verify: `uv run pytest tests/test_converge.py -q -k debt_pin_filed` passes.
- [x] 1.6 In `tests/test_converge.py` add `test_debt_pin_write`: `debt` files each non-blocking card that is not `verified`; a held spoiled card is not filed twice; a `verified` card with `repeat of <id>` clears that card on exit 1 alone; the preamble's text, and the spoiled card's id and fields, are held.
  Verify: `uv run pytest tests/test_converge.py -q -k debt_pin_write` passes.
- [x] 1.7 In `tests/test_converge.py` add `test_debt_pin_debted`: `debted` splits parts at ` · ` and ids at `, `, reads `none` as nothing, and counts the file's titles; `statuslog.names_lock` is true for the debt lock and the old backlog lock alone.
  Verify: `uv run pytest tests/test_converge.py -q -k debt_pin_debted` passes.
- [x] 1.8 In `tests/test_debt_match.py` add `test_debt_pin_match`: the paths are both sides of each `diff --git` line; a card runs to the next title or `#` line; **What it affects** is indented; every span counts, a `:n` suffix dropped; a dangling link exits 2; a link to a file is followed.
  Verify: `uv run pytest tests/test_debt_match.py -q -k debt_pin_match` passes.
- [x] 1.9 In `tests/test_cut_context.py` add `test_debt_pin_section`: `debt_section` keeps a listed id with its backticks stripped, an unqualified id too; a dangling link reads `None.`; a bad byte exits 2.
  Verify: `uv run pytest tests/test_cut_context.py -q -k debt_pin_section` passes.
- [x] 1.10 In `tests/test_conduct.py` add `test_debt_pin_cards`: the conductor's `_cards` strips the heading, reads the section to the next `## `, takes a title at column 0 alone, reads no file and a folder as `[]`, follows a link, and raises on a bad byte.
  Verify: `uv run pytest tests/test_conduct.py -q -k debt_pin_cards` passes.
- [x] 1.11 In `tests/test_conduct.py` add `test_debt_pin_stale_lock`: `_clear_stale_lock` leaves a lock at `LOCK_STALE` seconds, removes it one second past and returns its age, and leaves a lock `rmdir` refuses.
  Verify: `uv run pytest tests/test_conduct.py -q -k debt_pin_stale_lock` passes.
- [x] 1.12 In `tests/test_conduct.py` add `test_debt_pin_migration`: `migrate_debt` reads a `backlog.md` that is no regular file as `None` and moves nothing; with both files and a held old lock, `both stand` wins; each halt is held, and so is the locked link-then-unlink.
  Verify: `uv run pytest tests/test_conduct.py -q -k debt_pin_migration` passes.
- [x] 1.13 In `tests/test_converge.py` add `test_debt_pin_empty_page`: with `.minions/debt.md` a dangling link, which `debt_match.py` cannot read, the freeze writes `None.` to `debt-cards.md` and halts nothing.
  Verify: `uv run pytest tests/test_converge.py -q -k debt_pin_empty_page` passes.
- [x] 1.14 In `tests/test_converge.py` add `test_debt_pin_backlog_no_file`: a `backlog.md` that is a dangling link halts converge's `debt_lock` naming the old file, as a regular one does.
  Verify: `uv run pytest tests/test_converge.py -q -k debt_pin_backlog_no_file` passes.

## 2 — The module

`skills/mflib/debtfile.py` is born with no caller, each function holding a copy as it stands, per [D2](design.md#d2) and [D3](design.md#d3). Its docstrings name `0139-debt design D2`.

- [x] 2.1 Create `skills/mflib/debtfile.py` on `statefile.py` and `findings.py` with `Unreadable`, `TITLE` (`^- \*\*([^\s*]+) — `, multiline), `PREAMBLE` (converge's `DEBT_PREAMBLE` text) and `read(path)`, as the [function table](design.md#d3) says; add `tests/test_debtfile.py` with `test_debtfile_read`.
  Verify: `uv run pytest tests/test_debtfile.py -q -k debtfile_read` passes.
- [x] 2.2 Add `ids(text, change=None)`, `blocks(text)`, `card_id(block)`, `paths(patch)`, `matched(block, changed)` and `page(found)`, each the body of the function it is today's copy of; add `test_debtfile_ids`, `test_debtfile_blocks` and `test_debtfile_match`, each case titling its cards with a qualified id.
  Verify: `uv run pytest tests/test_debtfile.py -q -k "debtfile_ids or debtfile_blocks or debtfile_match"` passes.
- [x] 2.3 Add `filed(text, change, cards)`, `unfiled(text, ident)` and `clear(text, ids)`, the bodies of converge's `_filed`, `_unfiled` and `_section_end` and `clear` per [D12](design.md#d12); add `test_debtfile_filed`, `test_debtfile_unfiled` and `test_debtfile_clear`.
  Verify: `uv run pytest tests/test_debtfile.py -q -k "debtfile_filed or debtfile_unfiled or debtfile_clear"` passes.
- [x] 2.4 Add `spoiled(number, index, role, why, round_, change, where)`, the text converge's `spoiled` builds for one role, `where` the path the caller passes, and `qualify(lines, ident, qualified)`, the title rewrite of converge's `debt()`; add `test_debtfile_spoiled` and `test_debtfile_qualify`.
  Verify: `uv run pytest tests/test_debtfile.py -q -k "debtfile_spoiled or debtfile_qualify"` passes.
- [x] 2.5 Add `Held`, `LOCK_POLL` and `lock(path, wait=0)`, which makes `path` by `mkdir`, polls every `LOCK_POLL` seconds up to `wait`, raises `Held`, and removes `path` by `rmdir` at the end, no token yet, per [D6](design.md#d6); add `test_debtfile_lock`.
  Verify: `uv run pytest tests/test_debtfile.py -q -k debtfile_lock` passes.
- [x] 2.6 Add `write(path, text, folder=None)`, the staged write of `statefile.write` with a link refused, `WriteFailed` let through; add `test_debtfile_write`.
  Verify: `uv run pytest tests/test_debtfile.py -q -k debtfile_write` passes.
- [x] 2.7 Add the row `skills/mflib/debtfile.py | home | findings.py, statefile.py` to `docs/modules.md`, in path order.
  Verify: `uv run pytest tests/test_structure.py -q` passes.

## 3 — The stations

Each station goes through the module with no assert changed; only the line by which a test reaches a name moves, per [D1](design.md#d1).

- [x] 3.1 **HALT CHECK** The module's functions are the ones the stations will call.
  Verify: `git grep -n -e "^def read" -e "^def ids" -e "^def blocks" -e "^def filed" -e "^def unfiled" -e "^def lock" -e "^def write" -- skills/mflib/debtfile.py` prints a line for each.
- [x] 3.2 In `skills/mf-converge/scripts/converge.py` delete `DEBT_TITLE`, `DEBT_PREAMBLE`, `LOCK_POLL`, `_filed`, `_section_end` and `_unfiled`, and make `_debt_text` a call of `debtfile.read`; call `debtfile.ids`, `debtfile.PREAMBLE`, `debtfile.filed` and `debtfile.unfiled` where they were called, and re-word each `Unreadable` into the halt `_debt_text` words today. `LOCK_WAIT` stays.
  Verify: `git grep -n -e "DEBT_TITLE" -e "DEBT_PREAMBLE" -e "^LOCK_POLL" -e "_filed" -e "_unfiled" -e "_section_end" -- skills/mf-converge/scripts/converge.py` prints nothing.
- [x] 3.3 In `converge.py` make `debt_lock` a wrapper: it keeps the check of an old `backlog.md`, calls `debtfile.lock(path, LOCK_WAIT)` and words `Held` as `.minions/debt.lock held for 10 minutes`; `spoiled` builds each card through `debtfile.spoiled`, and `debt()` re-titles each card through `debtfile.qualify`, so no `- **` stays in the file; a test that patches `sleep` for the lock's wait reaches it through `debtfile` now, and no assert changes.
  Verify: `git grep -n -e "debtfile.lock" -e "debtfile.spoiled" -e "debtfile.qualify" -- skills/mf-converge/scripts/converge.py` prints a line for each.
- [x] 3.4 In `converge.py` write the debt and the freeze's empty page through `debtfile.write` and `debtfile.page`, in place of `DEBT_MATCH["write"]` and `DEBT_MATCH["page"]`, with the same exit and the same halt text; `DEBT_MATCH["main"]` still runs `debt_match.py`.
  Verify: `git grep -n -e 'DEBT_MATCH\["write"\]' -e 'DEBT_MATCH\["page"\]' -e 'DEBT_MATCH\["Stop"\]' -- skills/mf-converge/scripts/converge.py` prints nothing.
- [x] 3.5 In `skills/mf-converge/scripts/debt_match.py` make `main` a command over the module: `HEADING`, `TITLE`, `DIFF`, `AFFECTS`, `SPAN`, `LINES` and the functions `paths`, `cards`, `matched` and `page` leave it for the module's `paths`, `blocks`, `matched` and `page`; its arguments, output and exits stay, and `Stop` and `write` stay for `tests/test_staged_writes.py`.
  Verify: `git grep -n -e "^HEADING" -e "^TITLE" -e "^DIFF" -e "^AFFECTS" -e "^SPAN" -e "^LINES" -e "^def cards" -e "^def matched" -e "^def paths" -e "^def page" -- skills/mf-converge/scripts/debt_match.py` prints nothing.
- [x] 3.6 In `skills/mf-cut-change/scripts/cut_context.py` import `mflib.debtfile`, delete `DEBT_MATCH`, `CARD_ID` and `_card_id`, and have `debt_section` call `debtfile.blocks`, `matched` and `card_id`; its `_read` stays.
  Verify: `git grep -n -e "DEBT_MATCH" -e "CARD_ID" -e "_card_id" -- skills/mf-cut-change/scripts/cut_context.py` prints nothing.
- [x] 3.7 In `skills/mf-ship/scripts/conduct.py` make `_cards` parse through `debtfile.ids(text, change)`, keeping its read, and make `migrate_debt` take its lock through `with debtfile.lock(lock):`, `Held` worded as the held-lock halt is today.
  Verify: `git grep -n -e "debtfile.ids" -e "debtfile.lock" -- skills/mf-ship/scripts/conduct.py` prints a line for each.
- [x] 3.8 In `skills/mf-converge/scripts/overlap.py` reword the comment that says `debt_match.py`'s `What it affects` spans are copied, to name `skills/mflib/debtfile.py`, where they now live; no code changes.
  Verify: `git grep -n -F "debtfile.py" -- skills/mf-converge/scripts/overlap.py` prints a line.
- [x] 3.9 In `tests/test_converge.py` point the reach of `converge["DEBT_TITLE"]` at `mflib.debtfile.TITLE`, and point each line of the pins and of the older tests that reaches a name phase 3 deleted — `_filed`, `_unfiled`, `DEBT_PREAMBLE`, `LOCK_POLL`, `debt_match`'s `cards`, `matched`, `paths` and `page`, `cut_context`'s `_card_id` — at the module's function; in `tests/test_staged_writes.py` keep `debt_match.write` as it is; change no assert.
  Verify: `git grep -n -F 'converge["DEBT_TITLE"]' -- tests` prints nothing.
- [x] 3.10 In `tests/test_structure.py` delete `("debt_match.py", "- **")` and `("converge.py", "- **")` from `FORMAT_SITES` and `("cut_context.py", "debt_match.py")` from `LOADS_OUTSIDE`, per [D11](design.md#d11).
  Verify: `git grep -n -e '("debt_match.py", "- \*\*")' -e '("converge.py", "- \*\*")' -e '("cut_context.py", "debt_match.py")' -- tests/test_structure.py` prints nothing.
- [x] 3.11 In `docs/modules.md` give the rows of `converge.py`, `debt_match.py`, `cut_context.py` and `conduct.py` the names each now holds, `debtfile.py` among them and `debt_match.py` out of `cut_context.py`'s row; in `skills/mf-converge/SKILL.md` name `../../mflib/debtfile.py` beside `../../mflib/findings.py`.
  Verify: `uv run pytest tests/test_structure.py tests/test_skills.py -q` passes.
- [x] 3.12 **HALT CHECK** The move held: the pins and the older tests of the moved scripts pass with no assert changed.
  Verify: `uv run pytest tests/test_converge.py tests/test_debt_match.py tests/test_cut_context.py tests/test_staged_writes.py -q` passes.

## 4 — The fix

Each task turns the rows of the pin it names to one side and leaves the others, per [D4](design.md#d4) to [D9](design.md#d9).

- [x] 4.1 **HALT CHECK** The stations went through the module in the last phase.
  Verify: `git grep -n -F "debtfile" -- skills/mf-converge/scripts/converge.py skills/mf-cut-change/scripts/cut_context.py skills/mf-ship/scripts/conduct.py` prints a line of each file.
- [x] 4.2 In `skills/mflib/debtfile.py` narrow `TITLE` to a qualified id, `<digits>·<id>`, and give `ids` and a new `count(text, change=None)` that one reading; turn the title rows of the pins `debt_pin_read`, `debt_pin_debted` and `debt_pin_cards` and the total of `debt_pin_write`; turn the assert of `test_a_bold_bullet_is_no_card` in `tests/test_converge.py` that reads the title on an unqualified card, so its card is titled with a qualified id and the assert reads that id, and it still proves a bold-led bullet is no title; write `test_debtfile_title`.
  Verify: `uv run pytest tests/test_debtfile.py tests/test_converge.py tests/test_conduct.py -q -k "debtfile_title or debtfile_ids or debt_pin_read or debt_pin_debted or debt_pin_cards or debt_pin_write or bold_bullet"` passes.
- [x] 4.3 In `debtfile.py` have `blocks` take a card's extent from `findings.cards`, a blank line not ending it, and return the cards of a qualified id alone; have `filed` find a heading as `read` does, trailing blanks forgiven, and end a section at a `## ` line alone; turn the extent rows of the pin `debt_pin_match`, the unqualified-id row of `debt_pin_section` and the heading row of `debt_pin_filed`.
  Verify: `uv run pytest tests/test_debtfile.py tests/test_debt_match.py tests/test_cut_context.py tests/test_converge.py -q -k "debtfile_blocks or debtfile_filed or debt_pin_match or debt_pin_section or debt_pin_filed"` passes.
- [x] 4.4 Have `debt_match.py` read the debt through `debtfile.read`: a link halts, exit 2, a bad byte is replaced and a link to a file is not followed; have `cut_context.py` read through it and stop on `Unreadable`; turn the link and bad-byte rows of the pins `debt_pin_match` and `debt_pin_section`.
  Verify: `uv run pytest tests/test_debt_match.py tests/test_cut_context.py -q -k "debt_pin_match or debt_pin_section"` passes.
- [x] 4.5 In `converge.py` halt the freeze on any non-zero exit of `debt_match.py`, naming it and its exit, in place of the empty `debt-cards.md`; turn the pin `debt_pin_empty_page` to a halt, and turn the last assert of `test_the_debt_is_written_once_under_its_lock`, which reads a debt that is a link, to the freeze's halt; re-word the docstring of the freeze that says `debt_match.py`'s exit 2.
  Verify: `uv run pytest tests/test_converge.py -q -k "debt_pin_empty_page or the_debt_is_written_once"` passes.
- [x] 4.6 In `debtfile.py` give `lock` its holder's token: write `owner` inside the lock folder, renew the lock's time through the handle `lock` yields, `renew()`, release only a lock that holds the token and treat a lock gone or another's as no error; add `break_stale(path, limit)` that removes `owner` and then the folder, and leaves a lock that holds any other entry; write `test_debtfile_token`.
  Verify: `uv run pytest tests/test_debtfile.py -q -k debtfile_token` passes.
- [x] 4.7 In `converge.py` have the `debt_lock` wrapper yield the handle, and call `renew()` after each `still_true` call in `debt()`, and in `conduct.py` have `_clear_stale_lock` call `debtfile.break_stale`; turn the release rows of the pin `debt_pin_lock`.
  Verify: `uv run pytest tests/test_converge.py tests/test_conduct.py -q -k "debt_pin_lock or debt_pin_stale_lock"` passes.
- [x] 4.8 In `converge.py` write the debt through `mflib.statefile.folder(primary, mflib.layout.MINIONS)` and `debtfile.write(..., folder=)`, per [D7](design.md#d7); write `test_debt_pin_folder` in `tests/test_converge.py`: a link at `.minions` is refused.
  Verify: `uv run pytest tests/test_converge.py -q -k debt_pin_folder` passes.
- [x] 4.9 In `conduct.py` halt `migrate_debt` on a `backlog.md` that is no regular file, naming it, and have `report` name a debt it may not read in that change's line and go on, per [D8](design.md#d8) and [D9](design.md#d9); turn the no-file row of the pin `debt_pin_migration` and the folder and bad-byte rows of `debt_pin_cards`.
  Verify: `uv run pytest tests/test_conduct.py -q -k "debt_pin_migration or debt_pin_cards"` passes.

## 5 — The rule and the record

The lists shrank with the move, in phase 3, per [D11](design.md#d11); this phase amends the record and edits no debt card, per [D13](design.md#d13).

- [x] 5.1 In `docs/decisions.md` amend D16 where it lives: `.minions/debt.md` is written and parsed by `skills/mflib/debtfile.py`, and its lock knows its holder.
  Verify: `git grep -n -F "skills/mflib/debtfile.py" -- docs/decisions.md` prints a line.
- [x] 5.2 In `docs/decisions.md` amend D66 so `debt_match.py` is a command over the module, and D57 so `debt.md` stays generic and is written and parsed by the module; in D83 name the module beside `findings.py` as a writer of the card head.
  Verify: `git grep -n -F "is a command over the module" -- docs/decisions.md` prints a line.
- [x] 5.3 In `docs/recipes.md`, in the state-file recipe, say the debt file is written and parsed through `skills/mflib/debtfile.py`, its lock through `lock`; in `docs/modules.md` hold the layer text as it is.
  Verify: `git grep -n -F "debtfile.py" -- docs/recipes.md` prints a line.
- [x] 5.4 In `THREAT_MODEL.md` add to the findings-files bullet that the debt write holds its folder and its lock's token, and that the start-of-run move of an old layout's files, `migrate_layout`, and of an old `backlog.md`, `migrate_debt`, follow no link; add the debt module's name to the sentence that lists the shared home's formats.
  Verify: `git grep -n -F "migrate_debt" -- THREAT_MODEL.md` prints a line.

## 6 — The title's width

Converge files a card under its change's number at whatever width it has, so the title reads a number at any width, per [D4](design.md#d4) and [D10](design.md#d10).

- [x] 6.1 In `skills/mflib/debtfile.py` widen `TITLE` to `^- \*\*([0-9]+·[^\s*]+) — `, multiline; in `tests/test_debtfile.py` update the pattern `test_debtfile_read_holds_the_title_and_the_preamble` pins, turn the `001·R3` and `00001·R5` rows of `test_debtfile_title` from refused to read, and add `test_debtfile_title_width`: a card `qualify()` titles `1·R1` and one it titles `10000·R1` each round-trip through `ids()` and `blocks()`.
  Verify: `uv run pytest tests/test_debtfile.py tests/test_converge.py tests/test_conduct.py -q -k "debtfile_title or debtfile_read or debtfile_ids or debtfile_blocks or debtfile_qualify or debt_pin_read or debt_pin_debted or debt_pin_cards or debt_pin_write"` passes.
