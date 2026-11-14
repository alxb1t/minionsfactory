# Structure rules — design

Rules the gate holds over the scripts' shape, a map of the files they hold against, and the record that states both; no code moves. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

Every later version of the refactoring series moves code, one region at a time. The gate holds none of the shape those moves aim at: a script may load another station, take a private name from another file, close a cycle or name an OS command anywhere. `D57` rejects a shared helper module, and `D2` allows no shared code.

This change puts the rules in the gate first, each with a list of today's breaches that only shrinks, so each move shortens a list and no feature lengthens one. It writes the map the rules read, the decision that names the layers, and the recipes for an extension. It moves no code and changes no station's behaviour.

```
  docs/modules.md ──┐
  skills/**/*.py ───┼─▶ tests/test_structure.py ──▶ make gate / make check
  scripts/**/*.py ──┘     loads · names · cycles · OS commands · the map
```

## Goals / Non-Goals

- **Goals:** the rules run in `make gate` and `make check`, each with a planted-breach twin and a stale-exception twin; the map has a row for each Python file under `skills/` and `scripts/`; the record states the layers, the seams, the shared home and the clause that a list only shrinks; a recipe for each kind of extension.
- **Non-Goals:** moving any code; creating `skills/mflib/`; editing `D50` or `D78`; editing `THREAT_MODEL.md`; a rule for tables, state formats or the git runner, which land with the version that moves each.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | One test file, `tests/test_structure.py`, holds every rule; each rule is a function of a root folder and its exception list that returns its breach lines | a planted twin runs the same function on a tree under `tmp_path` with its own list; the gate runs it with the rest of the suite | a rule per file · a new gate step · a script under `skills/` |
| [D2](#d2) | An edge is a **name**: a string constant outside docstrings whose last `/` segment is the base name of another tracked script | a load, a run and a path built from parts all show as a literal; a syntax tree reads it with no judgment | resolving `runpy` arguments · resolving a path built through names |
| [D3](#d3) | `docs/modules.md` holds one row for each script: path, layer and the files it names; the test holds it to the tree and to the names found | the map is the declared shape; a script that drifts from it fails | a map in the test · a map no test reads |
| [D4](#d4) | Rule 1 allows a name of the same folder, of the home, or — from the conductor — of a station; rule 3 allows no cycle | the end state: a call goes down only, the conductor alone loads a station | a layer table beyond the layers of [D3](#d3) |
| [D5](#d5) | Rule 2 forbids a private name taken from a file the script names; rule 4 names `sandbox-exec`, `caffeinate`, `sysctl` and `ps` only in listed files | a private name is an interface nobody declared; an OS command is the platform seam | a ban on every `_` name · a rule for each OS tool |
| [D6](#d6) | Each rule carries a list of today's breaches as a literal in the test; a listed breach that is gone fails the test | the list only shrinks, and each version that moves a region deletes its lines | an allowlist that may stay · a count in the test |
| [D7](#d7) | The record: `D83` is new in *The shape*; `D57` and `D2` allow one shared home; `D79` gains the clause of [D6](#d6); `D50` and `D78` stay as they read | the decisions say what holds; this design says how it came about | editing `D50` before its chart moves · a decision per rule |
| [D8](#d8) | The recipes are `docs/recipes.md`, one section for each kind of extension, written from the tree as it stands | the map says what exists; a recipe says what an extension edits | recipes inside `D83` · a recipe for a module that does not exist |
| [D9](#d9) | One requirement is ADDED to `sdd`; none is MODIFIED | no station's behaviour changes; the requirements a move falsifies are the moves' | a requirement per rule |

### D1

The rules are plain functions: `check_loads(root, listed=LOADS_OUTSIDE)`, `check_names(root, listed=PRIVATE_REACH)`, `check_cycles(root, listed=CYCLE_FILES)`, `check_os(root, listed=OS_NAMES)` and `check_map(root)`. Each takes the root of a tree holding `skills/`, `scripts/` and `docs/modules.md`, and returns a list of breach lines, empty when it holds. `listed` is the rule's list of [D6](#d6), defaulting to the module constant.

The real-tree test of each rule calls it on the repository root with the default list and asserts the result is empty. A planted twin builds a small tree under `tmp_path` and passes its own `listed`: empty for a breach that must fail, the planted entry for one that must pass, and an entry the tree lacks for the stale twin. The tests run on every core in the gate's `-n auto`, and `make check` keeps them: each parses a file once, so none is `slow`.

### D2

`python_files(root)` returns the repo-relative paths, as strings with `/`, of each `*.py` under `skills/` and `scripts/`, sorted. `edges(root)` returns a dict from each such path to the sorted list of paths it names, `[]` for none.

The edge from file F to file G holds when F's syntax tree has a string constant, outside a module, class or function docstring, whose text after its last `/` equals G's base name, G not F. A constant that only contains the name inside longer text is no edge: `"run conduct.py"` is none, `"mf-ship/scripts/conduct.py"` is one.

```
HERE.parents[1] / "mf-integrate/scripts/integrate.py"   edge: converge.py → integrate.py
runpy.run_path(str(HERE / "stamp.py"))                  edge: converge.py → stamp.py
os.path.basename(word) == "conduct.py"                  edge: review_metrics.py → conduct.py
```

An edge is a name, not proof of a load: a script that only names another is held to the same rules. The base names under `skills/` and `scripts/` must be unique, since an edge finds its file by base name; `check_map` fails on a base name that more than one file holds.

### D3

The map is a table in `docs/modules.md`, one row for each Python file under `skills/` and `scripts/`:

| column | holds |
|---|---|
| path | the repo-relative path, in backticks |
| layer | `conductor`, `station`, `reader`, `gate` or `home` |
| names | the base names of the files it names ([D2](#d2)), comma-separated, `—` for none |

Today's layers: `conduct.py` and `pin.py` are the `conductor`; each script of `mf-plan`, `mf-cut-change`, `mf-build`, `mf-converge`, `mf-integrate` and `mf-release` is a `station`; `viewer.py`, `review_metrics.py` and the scripts under `scripts/metrics/` are `reader`; `scripts/corpus.py` and `scripts/docstrings.py` are `gate`. `home` is for a file under `skills/mflib/`, which no row uses until that folder exists.

Rule 5, the map: `check_map` fails on a file with no row, a row with no file, a layer outside the list, a `names` cell that differs from the edges found, and a base name that more than one file holds. The `names` cell makes a new load a visible diff of the map.

### D4

Rule 1, loads. The edge F → G is allowed when F and G share a folder, when G's layer is `home`, or when F's layer is `conductor` and G's is `station`. Any other edge fails unless the pair is in `LOADS_OUTSIDE`.

Rule 3, cycles. The edges make a graph; each strongly connected set of more than one file is a cycle. `CYCLE_FILES` lists the files that sit in a cycle today, and the files found must equal the list: a file found and not listed fails, a file listed and not found fails.

What the cut read on the base tree, for the build to confirm by running the rules:

| list | today's entries |
|---|---|
| `LOADS_OUTSIDE` | `brief_check.py` → `conduct.py`, `verify_check.py` · `converge.py` → `integrate.py` · `cut_check.py` → `gate_check.py`, `plan_check.py` · `cut_context.py` → `brief_check.py`, `bundle.py`, `debt_match.py` · `facts.py` → `brief_check.py` · `viewer.py` → `conduct.py`, `converge.py` · `review_metrics.py` → `conduct.py`, `overlap.py`, `metrics.py` |
| `CYCLE_FILES` | `conduct.py`, `pin.py`, `brief_check.py` — `conduct.py` and `pin.py` load each other, and `conduct.py` runs `brief_check.py`, which loads `conduct.py` |

The build writes each list from what the rule prints. A difference from this table is a line in `build-notes.md`, never a halt: the rule's output is the list.

### D5

Rule 2, private names. A **private reach** in F holds when F has a string constant that is the key of a subscript, or the argument of `.get` or `getattr`, or an attribute of a name other than `self` and `cls`, or the alias of a `from … import`, written `_name` with one leading underscore, and `_name` is defined at the top level of a file G that F names. `PRIVATE_REACH` lists each `(F, name)` today.

Today's reaches are the conductor's helpers read from `brief_check.py`, `pin.py` and `viewer.py` through the dict `runpy` hands back: `_rows` and `_plain_row`; `_scratch` and `_kept_origin`; `_claim`, `_cuts`, `_progress`, `_rating`, `_frontmatter`, `_build_halt`, `_maybe` and `_queue`. `review_metrics.py` also reads `_STYLE` of `metrics.py` as an attribute of the module it loads.

Rule 4, OS commands. A string constant outside a docstring that holds `sandbox-exec`, `caffeinate`, `sysctl` or `ps` as a whole word names it. `OS_NAMES` lists each `(file, command)` today, written from the rule's output; the cut found `conduct.py`, `awake.py` and `viewer.py`.

### D6

The lists are literals at the top of `tests/test_structure.py`: `LOADS_OUTSIDE`, `PRIVATE_REACH`, `CYCLE_FILES` and `OS_NAMES`. A rule's real-tree test fails on a breach not listed and on a listed entry the tree no longer holds. Each rule has a stale twin: a planted tree with the breach gone and the entry kept fails.

Growth is held by review: `D79` says a change that adds an entry to a list already in the tree is rejected; this change writes each list first. The test holds the other direction, so a version that moves a region cannot leave its entries behind.

### D7

The record is edited where it lives:

| page | edit |
|---|---|
| `docs/decisions.md` | `D83 · The code is layered, with named seams, held by the gate`, in *The shape*, and its id in the index; it names the layers (prose, scripts, shared home, ports), the rule that a call goes down only, the conductor as the one script that loads a station, and the seams (platform, executor, host, tooling) |
| `D57` | the shared helper module leaves *Rejected*; its *Accepts* says a script finds the change folder through its own `_change_dir` until the shared home holds the finder |
| `D2` | scripts may share code from one home under `skills/`, `skills/mflib/`, which the pin exports with the skills |
| `D79` | the clause of [D6](#d6), worded as the case where a change cannot clean every site |

`D83` carries `D78`'s edge: the conductor loads stations in process, and no station loads another or the conductor. `D50` is edited when its chart moves into the home, not before.

### D8

`docs/recipes.md` has one section each for a station, a state file, an OS and an executor. Each lists the files an extension edits today, read from the tree, the row it adds to `docs/modules.md` and the structure rule that holds it; the station section adds that a base name must be held by one file. A section that depends on a module the series has not built says what the extension edits until that module exists, and names the trigger — "when the home holds the module" — never a version.

### D9

The requirement is **The gate holds the structure rules**. It states the rules, the lists and the stale-exception failure, with a scenario each. No existing requirement is MODIFIED: the requirements that a move falsifies — those naming `_change_dir`, the load of `integrate.py`, the in-process load of `converge.py` and `conduct.py`'s `SLUG` — stay true while no code moves, and each is amended by the version that moves it.

## Tests

The change adds unit tests in one file, `tests/test_structure.py`, and removes none. Each rule has its real-tree test, a planted-breach twin and a stale twin. No integration or end-to-end test is added: no browser, no engine, no process is started.

| layer | adds | reason | command |
|---|---|---|---|
| unit | the tests of `tests/test_structure.py` | the rules read syntax trees and one table; the lowest layer that can fail, per `T1` | `uv run pytest tests/test_structure.py -q --collect-only` |
| integration | none | — | — |
| end-to-end | none | — | — |

No test is deleted or merged, so the removal table of `I16` is empty. Each file is parsed once; no test runs over 5 s, so none carries `slow`.

## Dependencies

None.

## Risks / Trade-offs

- **A name that is no load** — `review_metrics.py` holds `"conduct.py"` as data it matches in a command. The rule reads it as an edge and the exception list holds it; the cost is one listed pair.
- **A new script costs a row** — each version that adds a script edits `docs/modules.md`, which the recipes say. That is the map doing its work.
- **Lists as literals** — a list edited to add an entry passes the test; only review stops it. `D79` says so, and the stale twin holds the other direction.
- **Rule 2 by name** — a private name found by its text can match a local attribute of the same spelling. Such a pair is listed like any other.

## Verdict

Ready to build in the phases of [tasks](tasks.md): the record, the map and its rule, loads and cycles, names and OS commands, the recipes. Each list is what its rule prints on the base tree; none of the phases moves code.
