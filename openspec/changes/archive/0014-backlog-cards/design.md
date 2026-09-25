# 0014-backlog-cards — design

**In one line:** a finding is a card — an id and a plain title on one list line, labelled fields nested under it
— written by the stations, carried verbatim by `mf-converge`, kept whole by `mf-backlog-export`.
**Verdict: feasible** ([why](#verdict)).

Motivation is in [proposal.md → Why](proposal.md#why). This page holds the decisions, the card itself, the
before → after text, the test and the evidence.

## Context

- `mf-converge` Step 4 fixes a findings file's frontmatter, but not the shape of a finding. Step 5 carries each
  non-blocking finding into `.minions/<version>_backlog.md` "as a list line, whole: id · severity · source role ·
  repository-relative `path:line` · the defect · the suggested fix" (`skills/mf-converge/SKILL.md:145-148`).
- `mf-backlog-export` Step 3 carries each item with "all six of" those fields (`skills/mf-backlog-export/SKILL.md:54-67`).
  In the human's backlog they became table rows whose *defect* cell holds a paragraph.
- `mf-release` precondition 5 halts while `.minions/<version>_backlog.md` holds any list line
  (`skills/mf-release/SKILL.md:73-75`).

### Terms

| term | means |
|---|---|
| **card** | one finding: a top-level list line `- **<id> — <title>**`, with one nested bullet per field |
| **field** | a labelled line inside a card: `  - **Why it's a problem:** …` |
| **deferred card** | the card of a non-blocking finding — review `nit`, security `medium` or `low` |

## Goals / Non-Goals

**Goals**

- A person reading one card knows why it matters, when it bites, and what fixing it costs.
- Nothing the old list line held is lost ([D1](#d1)'s mapping).

**Non-Goals**

- Changing the review and security engines — the card is part of the contract the stations are given.
- Converting the human's existing backlog blocks.
- Changing `mf-release`.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | **The card** has the fields below, always all of them, in that order | the human asked for why · what · priority · when; the grilling added a title, where, the fix's size, a trigger, related ids and a still-true check | a free-form paragraph (today's defect cell) |
| <a id="d2"></a>**D2** | **The stations write the card.** `mf-converge` Step 3 gives each station the card; Step 4 makes every finding in a findings file a card | only the station that found it knows why it matters and when it bites | `mf-converge` rewriting findings — it judges nothing |
| <a id="d3"></a>**D3** | **`mf-converge` carries deferred cards verbatim** into the backlog file (Step 5). The fix pass and the verify pass write only the card's **Status** field (Steps 4, 6) | carrying verbatim keeps the conductor from judging; Status is where the existing `open → fixed → verified` already lives | a separate status list |
| <a id="d4"></a>**D4** | **`mf-backlog-export` carries each card whole** — every field, verbatim — and runs its **Still true?** check against `HEAD` when classifying moot. It reads a top-level list line as an item and its nested lines as that item's fields | the export's field list re-flattens the card; *Still true?* makes the moot check a command | keeping the field list |
| <a id="d5"></a>**D5** | **A card stays a list item** — one top-level `- ` line, fields as nested `  - ` bullets | `mf-release` blocks on any list line, and the export's empty-file grep counts nested lines too; a card as a heading would let a release ship with deferred work | headings per card |
| <a id="d6"></a>**D6** | **Writing limits live in the card section itself**: plain words, each field at most 2 sentences, no counts — name the things | `mf-converge` and `mf-backlog-export` carry no `P` list (v0.13), and a skill states what it needs | citing `P` from a skill that does not hold it |
| <a id="d7"></a>**D7** | **A scan holds the card's field labels equal** in both skills, with a twin; one phase | the pattern that already guards the input contract and the prose rules; split, one commit would carry cards the export flattens | a separate export phase |

### D1 — the card

`mf-converge` owns this table as `## The card`; `mf-backlog-export` carries the same rows. The first cell is the
label, in bold.

| field | holds |
|---|---|
| **Title** | the top line — `- **<id> — <what goes wrong, in plain words>**` |
| **Why it's a problem** | the harm, in one or two sentences |
| **When you'd hit it** | a concrete scenario: what you run, and what happens |
| **What it affects** | the section name, then `path:line` — a section name survives edits a line number does not |
| **Priority** | `<severity> · <role>` — and why that severity |
| **Fix** | the suggested fix, then its size: one line, a test, or a design change |
| **Trigger** | when it becomes real; a blocking finding says `blocks this release` |
| **Still true?** | a command, or the section to read, that shows the defect is still there |
| **Related** | the ids to fix together, or `none` |
| **Status** | `open`, `fixed`, `verified` or `wontfix`, with the one-line note the fix or verify pass adds |

Under the table, both skills state the writing limits ([D6](#d6)) and show this card:

```
- **R5 — A crashed converge can be released as "skipped"**
  - **Why it's a problem:** release reads "no findings files" as "converge never ran".
  - **When you'd hit it:** converge freezes the diff, then crashes before a station writes.
  - **What it affects:** `mf-release` Step 1, precondition 4 (`skills/mf-release/SKILL.md:65`).
  - **Priority:** medium · security — a converge that failed ships as if skipped.
  - **Fix:** also read the frozen diff file as "converge ran" · size: one line and a test.
  - **Trigger:** the first release that records a skipped converge.
  - **Still true?** `grep -n 'findings files' skills/mf-release/SKILL.md`
  - **Related:** R4 — fix together.
  - **Status:** open
```

Nothing the old list line held is lost:

| old list line | card field |
|---|---|
| id | **Title** (before the dash) |
| severity · source role | **Priority** |
| `path:line` | **What it affects** |
| the defect | **Why it's a problem** and **When you'd hit it** |
| the suggested fix | **Fix** |

### D2–D3 — `mf-converge`, before → after

| where | before | after |
|---|---|---|
| Step 3, what each station is given | range · patch path · findings path | the same, plus: every finding is written as a card, per `## The card` |
| Step 4 | frontmatter, severities, status, resolution log | adds one paragraph: the body is a list of cards; `open → fixed → verified` is the card's **Status** field |
| Step 5, the carry | "…as a list line, whole: id · severity · source role · repository-relative `path:line` · the defect · the suggested fix." | "…as its card, whole and verbatim — every field, in order." |
| Step 6, the fix station | "flips each addressed finding's status `open → fixed` and adds a one-line resolution note" | "sets each addressed card's **Status** to `fixed`, with a one-line note" |
| new `## The card` | — | [D1](#d1)'s table, the writing limits, the example card — placed before `## Never` |

### D4 — `mf-backlog-export`, before → after

| where | before | after |
|---|---|---|
| Step 1 | "Every **list line** … is an item" | "Every **top-level** list line is an item — a card; its nested lines are the card's fields." The checkbox sentence stays |
| Step 2, moot | "re-check the subject against `HEAD` rather than against memory" | the same, plus: run the card's **Still true?** check and quote its output |
| Step 3 | "Carry each surviving item whole" — the field list of id, severity, role, `path:line`, defect and fix | "Carry each surviving card whole" — every field, verbatim, in `## The card`'s order. The reason paragraph and the no-second-copy rule stay |
| new `## The card` | — | the same table as `mf-converge`, the writing limits and the example — placed before `## Never` |

## Seams — what the test holds

The seam is the skill text on disk. `tests/test_skills.py` reads numbered ids with `_section_ids`; a card's
fields are labels, not numbers, so a label reader sits beside it and returns the bold first cells of a named
section's table rows.

| scenario key | the scan | the twin plants |
|---|---|---|
| `sdd:backlog-cards:fields-agree` | the labels in the `## The card` sections of `skills/mf-converge/SKILL.md` and `skills/mf-backlog-export/SKILL.md` are equal and non-empty | a pair differing by one label; a skill with no `## The card` — both reported |

## Evidence

| id | observation | check |
|---|---|---|
| **E1** | the human could not read the exported backlog | vault field note, MinionsFactory, 2026-09-25 |
| **E2** | the carry names six fields in one list line | `sed -n '145,148p' skills/mf-converge/SKILL.md` |
| **E3** | the export carries "all six of" them | `grep -n 'all six of' skills/mf-backlog-export/SKILL.md` |
| **E4** | the release blocks on any list line, nested ones included | `grep -n 'no list line at all' skills/mf-release/SKILL.md`; the export's empty-file grep is `^\s*[-*+] ` |

## Dependencies

None.

## Risks / Trade-offs

- **Cards are longer than list lines.** → They are read by a person; the length is the point. Each field is capped
  at 2 sentences.
- **An engine ignores the card and writes its own shape.** → The station, not the engine, owns its findings file,
  and the card is in its instructions. A carried non-card still blocks the release — it is a list line.
- **Both copies of the table drift in wording while their labels agree.** → The scan guards labels only, as for
  the contract and the prose rules; `mf-converge`'s copy wins.

## Verdict

**feasible.** Both skills and the test module change; nothing else. No dependency. One phase, green alone.
