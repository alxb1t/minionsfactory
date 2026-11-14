# Structure rules — tasks

The record, the module map with its rule, loads and cycles, names and OS commands, the recipes. No phase moves code.

## Progress

- [x] 1 — The record · moderate
- [x] 2 — The module map and its rule · hard
- [ ] 3 — Loads and cycles · hard
- [ ] 4 — Names and OS commands · hard
- [ ] 5 — The recipes · moderate

## 1 — The record

- [x] 1.1 Add `### D83 · The code is layered, with named seams, held by the gate` to `docs/decisions.md`, after `D52`, as [D7](design.md#d7) says.
  Verify: `git grep -n "^### D83 " docs/decisions.md` prints the heading.
- [x] 1.2 Add `D83` to the index line of *The shape* in `docs/decisions.md`, so the shape's ids read `D1…D4, D52, D83`.
  Verify: `git grep -n -F "D52, D83" docs/decisions.md` prints the index line.
- [x] 1.3 In `docs/decisions.md`, `D57`: drop "a shared helper module" from *Rejected*, and append to its *Accepts* bullet "· a script finds the change folder through its own `_change_dir` until the shared home holds the finder".
  Verify: `git grep -n "a shared helper module" docs/decisions.md` prints nothing.
- [x] 1.4 In `docs/decisions.md`, `D2`: add one sentence at the end of the bold statement, before its closing `**`, starting on a new line.
  The sentence: "Scripts may share code from one home under `skills/`, `skills/mflib/`, which the pin exports with the skills."
  Verify: `git grep -n "^Scripts may share code" docs/decisions.md` prints the line.
- [x] 1.5 In `docs/decisions.md`, `D79`: add a sentence at the end of the bold statement, before its closing `**`, starting on a new line ([D6](design.md#d6)).
  The sentence: "Where a change cannot clean every site, the rule carries a named list of the rest, which only shrinks: a listed site that is gone fails the rule, and a change that adds one to a list already in the tree is rejected in review."
  Verify: `git grep -n "^Where a change cannot clean every site" docs/decisions.md` prints the line.

## 2 — The module map and its rule

- [x] 2.1 Create `tests/test_structure.py` with `python_files(root)` and `edges(root)` per [D2](design.md#d2), and tests named `test_edges_…` that hold them: a name in a docstring, a self-name and a longer text are no edge; `mf-x/scripts/y.py` is one.
  Verify: `uv run pytest tests/test_structure.py -q -k edges` passes.
- [x] 2.2 Write `docs/modules.md`: a line saying what the page is for, then [D3](design.md#d3)'s table, a row for each Python file under the skills and scripts folders, its layer and the base names `edges` finds.
  Verify: `grep -n "scripts/conduct.py" docs/modules.md` prints its row.
- [x] 2.3 In `tests/test_structure.py`, add `check_map(root)` — rule 5 — with its real-tree test and planted twins, named `test_check_map_…`: a file with no row, a row with no file, a `names` cell that differs, a layer outside the list, a base name that more than one file holds.
  Verify: `uv run pytest tests/test_structure.py -q -k check_map` passes.
- [x] 2.4 In `docs/README.md`, add a row for `modules.md` to *The pages* table.
  Verify: `git grep -n "modules.md" docs/README.md` prints the row.

## 3 — Loads and cycles

- [ ] 3.1 In `tests/test_structure.py`, add `check_loads(root, listed=LOADS_OUTSIDE)` — rule 1 — and the literal `LOADS_OUTSIDE`, written from the rule's output ([D4](design.md#d4)).
  Its tests are named `test_check_loads_…`; twins: a station naming another station fails; the same folder, the home and a conductor naming a station pass; a listed pair the tree no longer holds fails.
  Verify: `uv run pytest tests/test_structure.py -q -k check_loads` passes.
- [ ] 3.2 In `tests/test_structure.py`, add `check_cycles(root, listed=CYCLE_FILES)` — rule 3 — and the literal `CYCLE_FILES`, written from the rule's output ([D4](design.md#d4)).
  Its tests are named `test_check_cycles_…`; twins: a planted cycle fails; a listed file the tree no longer holds in a cycle fails.
  Verify: `uv run pytest tests/test_structure.py -q -k check_cycles` passes.

## 4 — Names and OS commands

- [ ] 4.1 In `tests/test_structure.py`, add `check_names(root, listed=PRIVATE_REACH)` — rule 2 — and the literal `PRIVATE_REACH`, written from the rule's output ([D5](design.md#d5)).
  Its tests are named `test_check_names_…`; twins: a subscript, a `.get` and a `from … import` of a private name each fail; a public name passes; a listed pair the tree no longer holds fails.
  Verify: `uv run pytest tests/test_structure.py -q -k check_names` passes.
- [ ] 4.2 In `tests/test_structure.py`, add `check_os(root, listed=OS_NAMES)` — rule 4 — and the literal `OS_NAMES`, written from the rule's output ([D5](design.md#d5)).
  Its tests are named `test_check_os_…`; twins: `caffeinate` in an unlisted file fails; the same word in a docstring passes; a listed pair the tree no longer holds fails.
  Verify: `uv run pytest tests/test_structure.py -q -k check_os` passes.

## 5 — The recipes

- [ ] 5.1 Write `docs/recipes.md` per [D8](design.md#d8): the sections `## A station`, `## A state file`, `## An OS` and `## An executor`, each listing the files an extension edits today, its row in `docs/modules.md` and the rule that holds it.
  The station section adds that a script's base name must be held by one file.
  Verify: `grep -n "^## " docs/recipes.md` prints the station, state file, OS and executor headings.
- [ ] 5.2 In `docs/README.md`, add a row for `recipes.md` to *The pages* table.
  Verify: `git grep -n "recipes.md" docs/README.md` prints the row.
- [ ] 5.3 In `AGENTS.md`, extend the `docs/` bullet of *Layout* to name the module map and the recipes.
  Verify: `git grep -n "recipes" AGENTS.md` prints the bullet.
