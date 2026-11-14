---
bump: minor
beside: [0123-linux-ci-green]
---

# Structure rules

The gate holds the shape of the scripts — what each loads, which names cross, where an OS command lives — and the record states the shape.

Reading map: [design](design.md) holds the rules, the module map and the decisions, [tasks](tasks.md) holds the phases: the record, the module map, loads and cycles, names and OS commands, the recipes.

## Why

Every later version of the refactoring series moves code. Today nothing stops a feature from adding a load of another station, a borrowed private name, a cycle or a new OS command, and the record rejects shared code. The rules land first, each with a list of today's breaches that only shrinks; this change moves no code.

## What Changes

- `docs/decisions.md`: a new decision, `D83`, names the layers and the seams; `D57` and `D2` allow one shared home; `D79` gains the clause that a gate rule's list of today's sites only shrinks.
- `docs/modules.md`: a row for each Python file under `skills/` and `scripts/`, with its layer and the files it names.
- `tests/test_structure.py`: the structure rules over the scripts' syntax trees — loads, private names, cycles, OS commands, the map — each with a list of today's exceptions and a planted-breach twin.
- `docs/recipes.md`: a recipe for each kind of extension — a station, a state file, an OS, an executor.
- Requirement ADDED to `sdd`: **The gate holds the structure rules**.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`: one requirement added, **The gate holds the structure rules**. No existing requirement is modified: no station's behaviour changes.

## Impact

- `docs/decisions.md`
- `docs/modules.md`
- `docs/recipes.md`
- `docs/README.md`
- `AGENTS.md`
- `tests/test_structure.py`

## Not in this change

- Moving code: the home `skills/mflib/`, the port, the tables and the state modules are later versions.
- `D50`'s chart and `D78`'s load of `converge.py`: `D50` is edited when the chart moves into the home; `D78` stays as the one allowed edge.
- G2, G3, G4, H4, the Linux runner and a third executor: other versions, per the brief.
- A mutation tool in the repo, and any edit to `THREAT_MODEL.md` surfaces: the version that creates the home adds its glob.
