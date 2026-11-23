# Debt paydown 4 — design

The debt cards that need no decision: archived lines say what the code holds, live texts and one checker row are fixed, and the cards the versions since paid are shown paid. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

Read at `3395878b`, v0.118.0: each fact of the brief stands, and each line a card names is quoted in the tables below. This version edits no file `0148-run-fields` edits, so it builds beside it without a conflict.

The cards fall in kinds, one phase each:

| kind | cards | phase |
|---|---|---|
| a stale line of an archived change | `0118·R2`, `0119·R4`, `0119·R5`, `0121·R2`, `0134·R2`, `0136·R1` | 1 |
| a live text or the checker's row | `0146·R11` with `0146·S16`, `0146·S13`, `0146·S11` | 2 |
| paid by a later version | `0120·R6`, `0122·S1`, `0134·R1`, `0146·R5`, `0147·R1`, `0147·S4` | 3 |

`0146·R11` and `0146·S16` are one line of `CHANGELOG.md`.

## Goals / Non-Goals

**Goals:** every card of `debt:` leaves the debt at the release; each archived or live line reads as the code and the later decisions hold; the checker row has its test red first.

**Non-Goals:** the cards in *Not in this change*; an archived spec delta, a decision's choice or a test under an archived change; editing `.minions/debt.md`.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | a patch with no spec delta: each fix makes a text or a row meet a requirement already in force | root `AGENTS.md`: a patch fixes what the line already does, debt cards among it | a delta for the checker row, which the V8 scenario already states |
| [D2](#d2) | an archived change's text is edited only on the lines a card names, to say what the code and the later decisions hold; the choice of no decision changes | a paydown that rewrites history's decisions makes new debt | a wider rewrite of the archived record |
| [D3](#d3) | the `CHANGELOG.md` line of v0.117.0's third phase says the cut's `I14` reads each phase line of `tasks.md`, under `## Progress` or not | the code and D5 of `0146-cut-catches` read the whole file; that line settles both cards | separate edits |
| [D4](#d4) | `worker.md` and `verify.md` leave out a fix commit's files with the spec's words: such files stand on its cards | the spec delta states the qualifier the references drop | a new rule for fix files |
| [D5](#d5) | `V8` takes a directory operand's module names from each file it holds, and an operand spelled with `./` as the tree spells it; a sibling folder whose name starts with the folder's stays no keyword | the card's own Fix; decided by the cutter, `C1` of the brief | a prefix test on the folder name, which `folder` already holds as `folder/` |
| [D6](#d6) | a card a later version paid is shown paid by a check of the line its fact names, with no edit | the line is the proof; the release deletes the card | a no-op edit, a test added for a paid card |

### D1

The V8 scenario of the `sdd` spec says the row holds when the expression selects a test of the file the command names. A directory's module names are tests of its files, so the fix meets that wording and adds no requirement. No file of `openspec/specs/` changes, and the change has `skip_specs: true`.

### D2

Each row replaces the text in *before* with *after*, on the line the card names, in the file under `openspec/changes/archive/`. The first group is every fragment of `0118-debt-paydown-3a` that holds a count outside an evidence table: the card names the proposal's opening line and the design's introduction, its D1 and D2 rows and its risk bullet. The choice of each row stays; only the count goes.

| file | before | after |
|---|---|---|
| `0118-debt-paydown-3a/proposal.md` | The debt from 75 cards to about 15: | The debt cards no conductor code decides: |
| `0118-debt-paydown-3a/proposal.md` | in two versions split by file | in versions split by file |
| `0118-debt-paydown-3a/design.md` | and four small ideas of this line | and the small ideas of this line |
| `0118-debt-paydown-3a/design.md` | two versions split by file | versions split by file |
| `0118-debt-paydown-3a/design.md` | and takes four ideas: | and takes the ideas of this line: |
| `0118-debt-paydown-3a/design.md` | about 45 cards, lowest risk | the cards no conductor code decides, lowest risk |
| `0118-debt-paydown-3a/design.md` | The seven old findings files | The old findings files |
| `0099-stacked-builds/design.md` | per 0119-debt-paydown-3b design D9 | per [0119-debt-paydown-3b design D9](../0119-debt-paydown-3b/design.md#d9) |
| `0100-worker-diet/design.md` | per 0119-debt-paydown-3b design D11 | per [0119-debt-paydown-3b design D11](../0119-debt-paydown-3b/design.md#d11) |
| `0104-codex-limits/design.md` | per 0119-debt-paydown-3b design D12 | per [0119-debt-paydown-3b design D12](../0119-debt-paydown-3b/design.md#d12) |

The rest of the archived lines carry a link or backticks, so each is shown whole under a caption. The proposal of `0119-debt-paydown-3b` says no file outside `conduct.py`, `converge.py` and their tests is touched; its amend added the archived design lines of the `0099-stacked-builds`, `0100-worker-diet` and `0104-codex-limits` rows above, which its D17 names.

`0119-debt-paydown-3b/proposal.md`, the Impact line:

```diff
-`skills/mf-ship/scripts/conduct.py`, `skills/mf-converge/scripts/converge.py`, `tests/test_conduct.py` and `tests/test_converge.py`. No dependency, no skill prose, no spec.
+`skills/mf-ship/scripts/conduct.py`, `skills/mf-converge/scripts/converge.py`, `tests/test_conduct.py` and `tests/test_converge.py`, and the archived design lines [D17](design.md#d17) corrects, in `openspec/changes/archive/0099-stacked-builds/design.md`, `openspec/changes/archive/0100-worker-diet/design.md` and `openspec/changes/archive/0104-codex-limits/design.md`. No dependency, no skill prose, no spec.
```

`0119-debt-paydown-3b/proposal.md`, the last exclusion:

```diff
-- Any file outside `conduct.py`, `converge.py` and their tests: `0118-debt-paydown-3a` holds them.
+- Any other file: `0118-debt-paydown-3a` holds them, save the archived design lines [D17](design.md#d17) corrects.
```

The same for the archived designs of `0121-ui-prepare`, `0134-run-layout` and `0136-status-log`, each whole on its line. The code writes a user and a global scratch config file, takes an id of any width, and its test plan holds a slow run-level test.

`0121-ui-prepare/design.md`, step 4 of the fetch command:

```diff
-4. Each command takes `--ignore-scripts`, `--no-audit`, `--no-fund`, `--registry` set to npm's own, `--userconfig` and `--globalconfig` set to `/dev/null`, `--cache` set to `.minions/npm-cache`, and `--before` set to seven days ago. The environment is the conductor's with each `npm_config_*` and `NPM_*` name and each name of `TOKENS` removed, and `HOME` and `TMPDIR` naming the scratch folder.
+4. Each command takes `--ignore-scripts`, `--no-audit`, `--no-fund`, `--registry` set to npm's own, `--userconfig` set to `user.npmrc` and `--globalconfig` set to `global.npmrc`, each a file of the scratch folder that nothing writes, as npm refuses one path for both, `--cache` set to `.minions/npm-cache`, and `--before` set to seven days ago. The environment is the conductor's with each `npm_config_*` and `NPM_*` name and each name of `TOKENS` removed, and `HOME` and `TMPDIR` naming the scratch folder.
```

`0134-run-layout/design.md`, the risk bullet on the old-layout id:

```diff
-- **`OLD_ID` is four digits and a slug.** The conductor's table matches an id by that pattern, where the other copies format any id into each path. Every change id today is of that form, and the decisions page fixes it.
+- **`OLD_ID` is digits of any width and a slug.** The conductor's table matches an id by that pattern, where the other copies format any id into each path. A `1-x` or a `10000-x` id reads as an old entry, as [D5](#d5)'s fix note says.
```

`0136-status-log/design.md`, the Tests introduction:

```diff
-The change adds tests at the lowest layer: unit cases over a module or a script's function, with `tmp_path` files and a patched clock. It adds no end-to-end test (`T1`), and no test that boots a browser or a run. Nothing runs over five seconds.
+The change adds tests at the lowest layer: unit cases over a module or a script's function, with `tmp_path` files and a patched clock. It adds no end-to-end test (`T1`) and no test that boots a browser. One test starts a run, `test_a_refused_status_log_at_the_start_halts_its_version_alone` of `tests/test_conduct.py`: it runs over five seconds and carries the `slow` marker.
```

### D3

The line is the first bullet of the v0.117.0 entry that opens `A `**HUMAN` line of `## Progress``. Only its first clause changes; the clause on a brief's `## Phases` and the rest of the line stay.

```diff
-- A `**HUMAN` line of `## Progress` fails the cut's `I14`, and a `**HUMAN` line of a brief's `## Phases` halts the brief check:
+- A `**HUMAN` phase line of `tasks.md` fails the cut's `I14`, under `## Progress` or not, and a `**HUMAN` line of a brief's `## Phases` halts the brief check:
```

### D4

`worker.md` and `verify.md` insert `, whose files stand on its cards` after `as a fix's`, the words `openspec/specs/sdd/spec.md` holds for the same pass. A fix commit's file that no card names is then judged, as the spec says. The lines read:

```diff
-and a file changed only by a commit the status log names as a fix's, stands on an `Unplanned:` line of a commit in range
+and a file changed only by a commit the status log names as a fix's, whose files stand on its cards, stands on an `Unplanned:` line of a commit in range
```

```diff
-The unplanned-file pass leaves out a file changed only by a commit the status log names as a fix's: a fix's files stand on no task.
+The unplanned-file pass leaves out a file changed only by a commit the status log names as a fix's, whose files stand on its cards: a fix's files stand on no task.
```

### D5

The card's fact line says a sibling folder with a longer name counts. It does not at `HEAD`: `folder` is `file.rstrip("/") + "/"`, so `tests/unit_extra/a.py` never starts with `tests/unit/`. The card's Fix and Evidence name the real gaps, and this decision pays them.

- `_defined(file, tree)` returns pairs `(path, name)`, `path` the file or each `.py` file under the directory at `HEAD`, `name` each name that file defines and `""` once.
- `row_v8` reads each operand as `Path(word).as_posix()`, so `./tests/test_a.py` is `tests/test_a.py`, the spelling of the tree.
- Its names are those of the operand's parts with `""` and each planned name, as before, and each pair's own path parts with its name.

```
tests/unit  -k test_gadget       names: "tests unit test_gadget.py test_spin"   selects
./tests/test_a.py  -k spin       operand read as tests/test_a.py                selects
tests/unit  -k test_other        tests/unit_extra/test_other.py is no file of tests/unit   V8
```

### D6

A paid card needs no edit and no test: its fact names a line that already holds what the card asked for. Each sub-task of phase 3 checks that line with a command and carries `**HALT CHECK**`, which should hold: a failure means the card was not paid and the plan is wrong. The slow markers are checked by the marker's effect: `-m "not slow"` deselects the test and pytest exits 5.

## Tests

One new unit test, no end-to-end run, no test deleted or merged, so `I16` holds no table. The count is `git grep -c '^def test_' -- tests/test_cut_check.py`, which prints 37 before.

| test | layer | the step it carries |
|---|---|---|
| `test_kexpr_naming_a_module_of_a_directory_holds` (new, `tests/test_cut_check.py`) | unit | `-k test_gadget` over a directory holding `test_gadget.py`, and `-k spin` over an operand spelled with `./`, hold; `-k test_other` over a directory halts `V8` when that module sits in a sibling folder whose name starts with the directory's |

The test is red before the fix at its first steps; its last step is a guard that holds before and after (`T1`). Read by the phase 3 checks, never edited: `tests/test_integrate.py` and `tests/test_conduct.py`.

## Dependencies

None.

## Risks / Trade-offs

- An archived line edited in place changes no card: only a change that lists the card at its release deletes it.
- A paid card's check is as strong as the line it reads. A marker checked by `-m "not slow"` proves the test is out of `make check`, which is what the card asked; it does not time the test.
- The checks of phase 3 already hold at `HEAD`, so a red run before the build proves nothing. Each stays as a `**HALT CHECK**` for that reason.

## Verdict

Ready to build.
