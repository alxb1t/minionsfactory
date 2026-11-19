# Findings — design

A findings file has one writer and one parser, `skills/mflib/findings.py`, and each script that reads a card reads it through that module. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

Converge, `conduct.py`, `integrate.py`, `open_cards.py`, `overlap.py` and `skip_stub.py` each parse a findings file with a pattern of their own. The viewer, `review_metrics.py` and `scripts/metrics/run.py` parse it too, and stay out of this change.

The shared home holds `skills/mflib/layout.py`, `skills/mflib/statefile.py` and `skills/mflib/statuslog.py`. This change adds the module for the findings files beside them, on the same staged write and the same read that follows no link.

```
conduct.py  converge.py  integrate.py        stations: read and write a findings file
open_cards.py  overlap.py  skip_stub.py      thin commands over the module
        \         |         /
         skills/mflib/findings.py            the card, the frontmatter, the read, the stub, the stamp
                  |
         skills/mflib/statefile.py           the staged write, the read that follows no link
         skills/mflib/layout.py              the findings files' names
```

## Goals / Non-Goals

- Goal: one parser for the card and the frontmatter, in the home, held by the gate.
- Goal: each disagreement between the copies made to agree in a phase of its own, after the move ([D2](#d2)).
- Non-goal: a station's behaviour that is not a copy of the findings format.
- Non-goal: the debt, the viewer, the metrics, the worker prose and the worker reference ([proposal](proposal.md)).

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | One module, `skills/mflib/findings.py`, standard library only, on `statefile` | the status log's module set the shape; a home module is imported once and computes nothing at import | a module per script; a class that holds a path |
| [D2](#d2) | Pin, move, fix, each a phase of its own; the move holds each copy's form as a `_legacy` variant and changes no assert; the fix deletes every variant | a checker can judge a pure move and not a move mixed with a fix | one phase that moves and fixes |
| [D3](#d3) | `open_cards.py`, `overlap.py` and `skip_stub.py` stay commands; the conductor keeps `_frontmatter` for the viewer | tests import `open_cards.py` and `skip_stub.py` for `write` and `Stop`; the metrics load `overlap.py` for `cards`, `overlap` and `ROLES`; the viewer takes the conductor's `_frontmatter` | deleting a name a reader still takes |
| [D4](#d4) | A card is its title and the indented lines after it; a blank line does not end it. A field line is converge's `FIELD`: the colon inside the bold, outside it, or absent | the worker reference and the release say so; it is the one form that reads what the template writes | the conductor's run to the next title |
| [D5](#d5) | A word is `Card.word` exactly: split at blanks, backticks and `*` dropped, a trailing `.,;:` stripped, case folded; it reads the category too. A word no reader knows, and an empty Status, read as not cleared | each reader normalises a word its own way; `**stability**` reads as security by accident | each reader's own split |
| [D6](#d6) | A security card is the conductor's fail-closed rule in converge too; a malformed findings file reaches the conductor's security readers as a blocking security card | an unread category must not open the bar | converge's exact `security` |
| [D7](#d7) | A card id outside `R<n>` and `S<n>`, and a Status or Priority under no title, make the file malformed, checked at the file's read | the contract's ids; a card titled `S-1` is halted on and not found by the rescue's bar | the check in the title's pattern: debt cards and the spoiled card share it |
| [D8](#d8) | The frontmatter is converge's `FRONT` and the whole stripped value, for every reader and writer; a key is stripped as its value is | the conductor's pattern crosses a line break; `ruled` rewrites the first `^key:` anywhere | the conductor's first `\S+` |
| [D9](#d9) | Every reader takes `statefile.read`: no link followed, a bad byte replaced; a missing file keeps each caller's answer, and a security reader fails closed | no read of the conductor's follows a link; a missing file has a different answer in each reader today | one answer for all |
| [D10](#d10) | A file still malformed after its rewrite stays as it is: converge reads the role clean and cards it; the conductor and integrate read the file's own verdict | converge's side is a shipped design and the conductor's is the fail-closed one | unifying them |
| [D11](#d11) | Which Status words a caller accepts stays the caller's: `skip_stub.py` clears on `verified` alone, converge on `verified` and `accepted`. A repeated field reads its first line. The small sizes and the Fix size's parse are held once, in the module, as they are; `overlap.py`'s Round parse stays its own | "may this file be overwritten" is the stub's question, and the stricter answer; both size copies agree today | one list of words |
| [D12](#d12) | The conductor's stamp writes through `statefile.write` with its folder descriptor and mode `0o600`, renamed over the target and never unlinked first; its folder comes from `statefile.folder` | `_place` deletes the target before it writes | keeping `_place` |
| [D13](#d13) | The structure rules' format kind refuses a string constant outside `skills/mflib/` that contains `- **` or `- \*\*`; its list holds each remaining site, named by kind | the patterns that spell the card head are in many scripts; the kind that holds the status log's names takes it | a rule per file |
| [D14](#d14) | No build task edits a debt card | `.minions/debt.md` is written under its lock by converge and the release alone; converge widens card `0136·S3` to name the stamp and re-points a card that cites a moved line, where it reads the diff | a task that writes the debt |
| [D15](#d15) | The record agrees in the last phase: D57, D78 and D83; the threat model's sentences on the stamp, the findings files, the home and the security card; the state-file recipe. The module map's rows and `mf-converge`'s `SKILL.md` sentence on what converge loads land in the phase whose `make check` holds them | a decision is edited where it lives | prose in `design.md` alone |

### D1

The module holds: the title and field patterns, `Card`, the cards of a text and its strays, the frontmatter and its fault, the read of a file, a halt's card ids, the stub's text, the test for an uncleared file, and the stamp. The layout names `findings_name(role)`, `shadow_name(role)` and `open_name(role)`, and `findings_file(primary, change, role)`, beside `status_log(primary, change)`.

The grades and sizes the card's readers need — `BLOCKS`, `NON_SECURITY`, `SMALL`, `SIZE` — live in the module, each copy deleted. No other table moves.

### D2

Phase 1 pins each copy as it stands. The build's worker sees each case red under the change its row names in the case table, then green; the red change is never committed.

Phase 2 builds the module with converge's form as the one form. A copy that differs is held as a function named `<function>_<script>_legacy`, `<script>` the script's name without `.py`. It takes and returns what the copy it holds took and returned, so a station changes only the name it calls and keeps its own behaviour through phase 3.

Example: `cards_conduct_legacy` is the conductor's extent of a card, returning the pairs `_cards_in` yielded.

Phase 4 deletes every `_legacy` function and turns each case marked `turns` to the one side. A row of a pin case that turns moves, as the one side's assert, to a `test_fix_<rule>_*` case in the same test file, so each task's `-k` reaches it. A case marked `stays` holds through both.

### D3

A thin command keeps its arguments, output and exits. The names kept:

| file | names kept |
|---|---|
| `open_cards.py` | `open_page`, `write`, `Stop`, `main` |
| `overlap.py` | `cards`, `overlap`, `ROLES`, `line`, `Unread`, `main` |
| `skip_stub.py` | `role_of`, `round_of`, `stub`, `uncleared`, `write`, `Stop`, `main` |
| `conduct.py` | `_frontmatter`, one line over the module |

### D4

Before, in `conduct.py`, a card runs from its title to the next title, through a blank line and a `## Refuted` heading; in converge it ends at a blank line. After, in the module, it ends at the first line that is neither indented nor blank-then-indented. `Card.lines` keep the blank lines between its indented lines and drop a blank line after the last, so a card copied into the debt keeps its bytes.

```
- **R1 — a title**
  - **Status:** open
                          <- a blank line: the card goes on
  - **Fix:** one line.
- **R2 — next**           <- the next title ends R1
```

### D5

Before, `**Open**` and a bold grade block to converge and not to the conductor. After, `Open` and `**open**` read `open` everywhere. `open_cards.py` keeps its stop on a word it does not know and on an empty Status.

### D6

Before, converge's `Card.security` is a card whose category is exactly `security`. After, a blocking adversarial card whose category is not one of those `NON_SECURITY` names is a security card, in converge as in `conduct.py`.

### D7

The check is the module's `malformed(text, role)`, which a reader of cards calls on the text `read` returned; `read` itself checks nothing, so a reader of the frontmatter alone never meets it. It is not in the title pattern. The title pattern keeps taking a debt card's `<4 digits>·<id>` and a spoiled card's `M<n>`, so `debt_match.py` and the debt write are not touched.

A reader that reads cards answers a malformed file as follows; a reader of the frontmatter alone is not touched.

| reader | a malformed file |
|---|---|
| converge `read_findings` | malformed: one rewrite worker, as now |
| `_open_blockers` | `None`, as an unread file |
| `_security_blocks`, `_security_held` | `True`, a blocking security card |
| `open_cards.py`, `skip_stub.py` | `Stop`, exit 2; the stub is not written over it |
| `overlap.py` | `Unread` |

### D8

A frontmatter is a block at the start of the file, ended by the first `---` line. `ruled`'s edit of `head`, `round`, `reviewed`, `mode` and `workers` takes a key of that block alone, never a line of the body.

### D9

| reader | missing file | bad byte |
|---|---|---|
| converge `read_findings` | `None`, as now | replaced |
| `_unjudged` | a named fault, as now | replaced; it raised |
| `_open_blockers` | `None`, as now | replaced |
| `_security_blocks`, `_security_held` | `True`, as now | replaced; a malformed file is `True` |
| `unready` | not ready, as now | replaced; it raised |
| `open_cards.py`, `overlap.py` | `Stop`, `Unread`, as now | replaced |
| `skip_stub.py` `uncleared` | no file: the stub is written, as now | replaced |

### D10

The disagreement stays and is pinned by the cases for each reader in [the pin](tasks.md#1--the-pin).

### D11

`skip_stub.py` reads a card's Status through the module, no longer every Status line of the file; a repeated field reads the first line in every reader.

### D12

The mode stays `0o600`, so case o stays whole. The staged name becomes the module's `<name>.tmp`, and the target is no longer unlinked first.

### D13

The format name for the card head is `- **`. A string constant that contains `- **` or `- \*\*` outside `skills/mflib/` is a breach unless the pair of file and name is listed. The list holds each remaining site, with the kind in a comment:

| file | kind | leaves the list when |
|---|---|---|
| `review_metrics.py`, `run.py` | the card's reader | the viewer and the metrics read through the module |
| `converge.py`, `debt_match.py`, `cut_context.py`, `debt.py` | the debt's | the debt has its module |
| `conduct.py` | the debt's, the integrate note, the probe's `- **WHEN**` | the debt has its module and the tables move |
| `brief_check.py` | the Acceptance pattern, no card | the brief has its module |
| `cut_context.py` | the spec template, no card | the brief has its module |

`open_cards.py`, `overlap.py` and `skip_stub.py` hold no card head once phase 3 is done, so none is listed.

### D14

A task that writes `.minions/debt.md` would break its lock rule. Converge re-points a card that cites a moved line, and widens `0136·S3`, where it reads the diff.

### D15

Each amended decision keeps its words and gains the module's name: D57 names `skills/mflib/findings.py` the writer and parser of the findings files, D78 says converge reads its findings through it, D83 counts the card head among the format names the gate holds.

## The cases

Phase 1 adds these cases, each green on the code as it stands. A letter names a case in the tasks.

| | asserts, as the code stands | test file | fix phase |
|---|---|---|---|
| a | `Card.word`: backticks and `*` dropped, the first word, a trailing `.,;:` stripped, case folded, `""` for an empty field; an Amend of `` `Yes`. `` is yes | `tests/test_converge.py` | stays |
| b | converge reads `**Name**:`, `**Name:**` and a bare `**Still true?**`; a tab or four blanks indent; values stripped; the first of a repeated field wins. A nested title line, a spaced id, an en dash, a hyphen and no dash are no title; `A6` is | `tests/test_converge.py` | stays; the `A6` row turns, and the blank-line end of a card, which phase 1 adds here as `test_pin_extent_converge_*`, turns |
| c | converge's frontmatter: a block at the start alone, ended by the first `---` line; keys and values stripped; a bare key ignored; a value keeps its colons; only `mode: skipped` is a stub; each missing key and each wrong integer, list or verdict has its own message; a key's fault is named before an Amend's | `tests/test_converge.py` | stays |
| d | `Card.security` is an adversarial card whose category is exactly `security`: `Security`, no category and a conformance card are not | `tests/test_converge.py` | turns |
| e | one table over the conductor's and integrate's `_frontmatter`: an empty value reads the next line's word; a trailing `# note` is cut; an unclosed block is read; a key after the block and no opening `---` read `None` | `tests/test_conduct.py`, `tests/test_integrate.py` | turns |
| f | `rewrite` keeps a good file's cards and reads a still-malformed file clean at `HEAD`; the spoiled card is open with `Amend: no`, for dispatched roles alone; `ruled` leaves a body's `round:` line, refuses a link, keeps `## By rule` above the log; `stubs` halts on a link | `tests/test_converge.py` | stays |
| g | the Fix size in both copies: the last `size:` with no colon after it, backticks and the dot stripped; `one line and a test` is small; no size is `a design change` to the conductor. An open blocker: `open`, `` `open` — x `` and `open, then …` count; `opened`, `Open`, `**open**` and `fixed — was open` do not | `tests/test_conduct.py`, `tests/test_converge.py` | the `Open` and `**open**` rows turn |
| h | the conductor's card runs from a title to the next title, through blank lines and `## Refuted`; `_field` needs an indented `**Name:**`; `_severity` gives `**high**` raw; `_category` is the third part, backticks stripped and lowered; `_status` keeps case and `*` | `tests/test_conduct.py` | turns |
| i | `_security_card` fails closed on an unknown or missing category, not on the named ones or a medium card; `_security_blocks` takes `R`/`S` ids after `amend needed — ` and fails closed on an unread file; `_security_held` holds on a named card or a Status that starts `open` | `tests/test_conduct.py` | stays; the `A1` rows turn |
| j | `_unjudged` names a missing verdict and a head that is not `HEAD`, and raises on a bad byte; `_amendable` needs both files present and clean; `_answered` is `False` on a missing head or file | `tests/test_conduct.py` | the bad-byte row turns |
| k | `open_cards.py`: a card runs to the next title or `#` line; `A4` is a title; the Status word after `` `*_ `` to the first non-word character, case folded; the first Status decides; `_wontfix_`, empty, `**Status**:` and an unindented Status each stop; a bad byte stops | `tests/test_open_cards.py` | turns |
| l | `overlap.py`: the same extent; Affects and Priority as indented `**Name:**` alone; a grade read raw; no Round is round 1; `executor:` alone on its line; a bad byte raises | `tests/test_overlap.py` | turns |
| m | `uncleared` reads the keys before the first `\n---` with no opening needed; it sees no `` `open` ``, `**open**` or `**Status**:` card; only `verified` clears; a stub is never uncleared; `role_of` refuses a wrong suffix, a wrong grandparent, a linked file or folder | `tests/test_skip_stub.py` | turns; `verified` alone stays |
| n | `unready`: a patch with no findings files is not ready; a missing verdict is not clean; a bad byte raises | `tests/test_integrate.py` | the bad-byte row turns |
| o | `_stamped` replaces `model:` in place with `tokens:` after it, in the first block at the start alone; `_stamp` replaces a bad byte, leaves the file at mode 0600 and leaves a linked file or folder alone | `tests/test_conduct.py` | stays: the stamp keeps its mode ([D12](#d12)) |

Beside the letters, phase 1 adds a case for each difference the mutants do not reach: a findings file that is a link, in each reader, and a file still malformed after its rewrite, in each reader ([D10](#d10)).

## The copies

What each rule is today, and the one side phase 4 gives it.

| rule | the copies today | the one side |
|---|---|---|
| a card's end | the conductor's runs to the next title; converge's stops at the first unindented line, a blank included; `open_cards.py`'s and `overlap.py`'s at the next title or `#` line | the title and the indented lines after it ([D4](#d4)) |
| a field line | converge's `FIELD`; the conductor, `open_cards.py`, `skip_stub.py` and `overlap.py` take `**Name:**` alone | `FIELD` ([D4](#d4)) |
| a field's word | converge's `Card.word`; the conductor strips backticks and blanks and lowers the grade, not the Status; `open_cards.py` and `skip_stub.py` split their own way; `overlap.py` reads a grade raw | `Card.word` ([D5](#d5)) |
| a security card | converge's exact `security`; the conductor's fail-closed rule | the fail-closed rule ([D6](#d6)) |
| a card id | converge's title takes any id; the conductor finds a halt's ids by `\b[RS]\d+\b` | `R<n>` and `S<n>`, malformed otherwise ([D7](#d7)) |
| a bold line that is no card | `open_cards.py` stops on a Status under no title; the rest pass it by | malformed in every reader ([D7](#d7)) |
| a frontmatter value | the conductor's and integrate's first `\S+`; converge's whole stripped value; `overlap.py` needs `executor:` alone | the whole stripped value ([D8](#d8)) |
| a frontmatter's extent | `skip_stub.py` and `overlap.py` split at the first `\n---`; `ruled` edits the first `^key:` anywhere | the block at the start alone ([D8](#d8)) |
| a read | `read_text()` in the conductor, integrate, `open_cards.py` and `overlap.py`; `statefile.read` in converge | `statefile.read` ([D9](#d9)) |
| an overwrite | the stamp unlinks the target, stages `.<name>` at `0600`; the rest stage `<name>.tmp` at `0644` | `statefile.write` with a folder and mode ([D12](#d12)) |
| a repeated field | most readers take the first; `skip_stub.py` reads every Status line | the first ([D11](#d11)) |

## Tests

This change adds unit cases and no end-to-end test (`T1`): every case reaches a function, none starts a worker or a run. The pin's cases reach the conductor through `tests/conduct_load.py`, which compiles the script once, so none is `slow`.

| layer | what is added | where | the count, by |
|---|---|---|---|
| unit | the pin's cases a to o and the per-reader cases | `tests/test_converge.py`, `tests/test_conduct.py`, `tests/test_integrate.py`, `tests/test_open_cards.py`, `tests/test_overlap.py`, `tests/test_skip_stub.py` | `uv run pytest tests/test_converge.py tests/test_conduct.py tests/test_integrate.py tests/test_open_cards.py tests/test_overlap.py tests/test_skip_stub.py --collect-only -q` |
| unit | the module's cases, each variant equal to the copy it replaces | `tests/test_findings.py` | `uv run pytest tests/test_findings.py --collect-only -q` |
| unit | the layout's names | `tests/test_layout.py` | `uv run pytest tests/test_layout.py --collect-only -q` |
| unit | the format kind's card head: a planted breach, a listed site that is gone | `tests/test_structure.py` | `uv run pytest tests/test_structure.py --collect-only -q` |

End-to-end runs added: none.

Tests removed or merged: none. A row of a case marked `turns` in [the cases](#the-cases) moves to a `test_fix_*` case of the same file and takes the one side, so the I16 table is empty.

## Dependencies

None.

## Risks / Trade-offs

- The pin is large. A case that fails on the clean tree is a wrong case, not a wrong tree: fix the case.
- A `_legacy` variant is a copy that lives one phase. The gate does not hold its removal; phase 4's last task does, by a search for `_legacy`.
- The conductor's `_frontmatter` stays beside the module until the viewer reads through it, so one parser of the old form is left, one line long.
- A malformed file now reaches the security readers as a blocking security card ([D6](#d6)): a version whose adversarial file is spoiled is barred from the rescue and supervisor, as an unreadable one is today.

## Verdict

Ready to build, in the phases of [tasks](tasks.md).
