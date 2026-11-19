---
bump: minor
---

# Findings

One module, `skills/mflib/findings.py`, writes and parses a findings file, so the scripts that read a card read the same card.

Reading map: [design](design.md) holds the decisions, the pin cases and the table of copies that disagree, [tasks](tasks.md) its phases: the pin, the module, the stations, the fix, the rule and the record.

## Why

Converge, `conduct.py`, `integrate.py`, `open_cards.py`, `overlap.py` and `skip_stub.py` each parse a findings file with
a pattern of their own, and the copies disagree:

- A card whose Status reads `Open`, or whose grade is bold, is a blocker to converge and unseen by the conductor's automatic grant.
- A card titled `S-1` is halted on by converge and not found by the rescue's security bar.
- A frontmatter value that crosses a line break reads one way in converge and another in the conductor.

The status log's module, `skills/mflib/statuslog.py`, showed the way: one writer and parser, in the shared home.

## What Changes

- A new module, `skills/mflib/findings.py`, on `skills/mflib/statefile.py`: the card, its fields and words, the
  frontmatter, the read, a halt's card ids, the stub and the stamp.
- Converge, `conduct.py` and `integrate.py` read and write through it. `open_cards.py`, `overlap.py` and `skip_stub.py`
  become thin commands over it, with their arguments, output and exits as they are.
- `skills/mflib/layout.py` names the findings files.
- The copies that disagree are made to agree, in a phase of their own after the move: one extent for a card, one field
  line, one word, one rule for a security card, one frontmatter, one read that follows no link, and a stamp that never
  unlinks the findings file first.
- The structure rules' format kind refuses a card head spelled outside `skills/mflib/`, each exception listed.
- The record agrees: D57, D78 and D83 amended, the threat model, `mf-converge`'s `SKILL.md`, the recipe and the map.

Per requirement of the delta ([spec delta](specs/sdd/spec.md)):

- ADDED **One module writes and parses a findings file** — the card, the frontmatter, the read and the stamp.
- MODIFIED **The card is defined in converge alone** — the worker reference defines the card; the module parses it.
- MODIFIED **A run grants one round at a small cap, and halts a large one for a re-plan** — the open blockers are read
  through the module, so `Open` and a bold grade count.
- MODIFIED **A converge conductor stubs a skipped checker** — the stub is written and read through the module; a Status
  that is not `verified` is not cleared.
- MODIFIED **Converge's conductor is a script** — the findings readers read through the module; the debt's readers keep the
  title rule; what makes a file malformed gains the card id.
- MODIFIED **The gate holds the structure rules** — the format kind gains the card head.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd` — the findings file's one reader and writer, and the rules that hold it.

## Impact

- `skills/mflib/findings.py` is new; `skills/mflib/layout.py` gains names.
- `skills/mf-converge/scripts/converge.py`, `skills/mf-converge/scripts/open_cards.py`,
  `skills/mf-converge/scripts/overlap.py`, `skills/mf-converge/scripts/skip_stub.py`,
  `skills/mf-ship/scripts/conduct.py` and `skills/mf-integrate/scripts/integrate.py` lose their parsers.
- `tests/test_findings.py` is new; `tests/test_converge.py`, `tests/test_conduct.py`, `tests/test_integrate.py`,
  `tests/test_open_cards.py`, `tests/test_overlap.py`, `tests/test_skip_stub.py`, `tests/test_layout.py` and
  `tests/test_structure.py` gain cases; `tests/conduct_load.py` is the helper the conductor's cases reach it through.
- `docs/modules.md`, `docs/decisions.md`, `docs/recipes.md`, `THREAT_MODEL.md` and `skills/mf-converge/SKILL.md` follow.

## Not in this change

- The viewer, `review_metrics.py` and `scripts/metrics/run.py`: their parsers wait for the version that moves the readers.
  The conductor keeps `_frontmatter` for the viewer until then.
- `debt.md`, its cards and its lock: the debt's own module. `debt_match.py` and `cut_context.py` keep their title rule.
- The prose a worker writes a card by, and the worker reference's definition of the card.
- `tasks.md`'s Progress and the proposal's frontmatter: the brief's module.
- The tables of roles, executors and halt kinds, save the grades and sizes the card's own readers need.
- Any station's behaviour that is not a copy of the findings format.
