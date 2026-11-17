# Run layout — design

One module of the shared home names the run directory's paths and holds the old-layout table, every script takes them from it, and the gate's sixth rule keeps them there. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The shared home, `skills/mflib/`, has one tenant, `platform.py`, born in 0128. Each script that reads or writes `.minions/` finds it with a git call and a join of its own, and builds the change folder with a `_change_dir` of its own or inline. The copies agree on the arithmetic and disagree on guards, error texts and the old-layout table.

```
today                                   after
  conduct.py   ─ git + join + table        conduct.py ─┐
  gate_check.py ─ git + join + table       gate_check ─┤   each keeps its git call,
  integrate.py ─ git + join + table        integrate ──┼─▶ guard and error text;
  run.py       ─ git + join + table        run.py ─────┤   mflib/layout.py holds
  converge.py  ─ join + table              converge ───┘   the paths and the table
```

The region was measured at `e008023c`: every site that builds a path, the copies' differences, the old layout, the tests and the structure rules. Each of its mutants that the tests did not hold is a case of phase 1.

## Goals / Non-Goals

- **Goals:** one home for the run directory's paths a second script spells; one old-layout table every station halts on; a gate rule that stops a new copy; the record agreeing.
- **Non-Goals:** a shared finder that runs git; the home folder's paths (`home-layout`); a state file's content; the skills' prose paths. See [proposal](proposal.md).

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | The module is `skills/mflib/layout.py`, standard library only, taken as `import mflib.layout`; every path is computed when asked, none at import | the tests isolate by `HOME` and the XDG variables per test, and a home module is imported once a process | constants built at import; a package of several files |
| [D2](#d2) | The module's surface is the primary from git's answer, the run directory, the change folder, the generic entries a second script spells, and the old-layout table with its reader | one home for what is shared | an entry one script alone spells |
| [D3](#d3) | The module runs no git: each script keeps its git call, its guard and its error text | those are the git runner's, a later version's; a shared finder that runs git changes at least one error text | a finder that runs git |
| [D4](#d4) | The differences below stay: a repo as named, the finders' guards, `CLAUDE_CONFIG_DIR`, `~/.mf-ship-origin` outside XDG | each is a behaviour change, not a move | folding them in |
| [D5](#d5) | The old layout is one table, the conductor's, in the module; every station and `run.py` halts on it, naming the first of the sorted paths | the copies disagree on the entries the table of D5 shows, and the tests hold some of them; every recorded repo is already moved | a table per script |
| [D6](#d6) | A move phase changes no assert: only the line by which a test reaches a name | an unchanged assert over moved code is the proof the move changed nothing | rewriting tests in a move |
| [D7](#d7) | The seed in `scripts/` is the one statement the file's depth fixes, and the seed rule holds `scripts/` | `scripts/` is outside `parents[2]` of the skills' seed | a fourth seed text |
| [D8](#d8) | The sixth rule is `check_layout`, with a list of (file, name) pairs that only shrinks | what stops a new copy; D79 has a rule's sites cleaned in the change that adds it | a rule with no list |
| [D9](#d9) | Converge's read of an old `backlog.md` stays as it is, and the pin holds it | the reason of D4 | moving it |
| [D10](#d10) | The build edits no debt card | the debt file is written under `.minions/debt.lock` by converge and the release alone | a task that writes `debt.md` |
| [D11](#d11) | The pin comes first, on today's code, each case seen red under a named change | a function-level test written after a move is written twice | moving before pinning |
| [D12](#d12) | The record is edited where it lives: D57, D83, the recipe, the threat model, and the skills that list the old layout | a decision in force is edited where it lives | a new decision |

### D1

`layout.py` imports `os`, `pathlib` and `re` and nothing else. A script loads it after the seed, as `awake.py` loads the port: `sys.path.insert(0, str(Path(__file__).resolve().parents[2]))` then `import mflib.layout`. Its names are public, because the names rule refuses a private name taken from a file a script names.

### D2

The module's public names, each a function of a primary `Path` unless noted:

```
primary_of(common)            git's common directory, as text or a Path → the primary checkout
run_dir(primary)              <primary>/.minions
change_dir(primary, change)   <primary>/.minions/changes/<change>
CHANGES                       "changes", for a descriptor opened part by part
runs_dir(primary)             <primary>/.minions/runs
claim_file(primary)           <primary>/.minions/runs/active
debt_file(primary)            <primary>/.minions/debt.md
debt_lock(primary)            <primary>/.minions/debt.lock
backlog_file(primary)         <primary>/.minions/backlog.md       (the old name)
backlog_lock(primary)         <primary>/.minions/backlog.lock     (the old name)
gate_dir(primary)             <primary>/.minions/gate
cut_reservation(primary, id)  <primary>/.minions/cuts/<id>
metrics_page(primary, id)     <primary>/.minions/metrics/<id>.html
OLD_LAYOUT, OLD_ROLES, OLD_ID, OLD_STAMP, OLD_LOG    the old-layout table
old_files(primary)            each change's old-layout files, each with its path in the change's folder
old_layout(primary, change)   the first of the change's old paths, sorted, relative to the primary, or None
```

An entry that one script alone spells (`grants/`, `tmp/`, `uv-cache/`, `npm-cache/`, `runs/detached.log`, `replay/`, `awake/`, `corpus/`) stays in that script as `layout.run_dir(primary) / "grants"`. It joins no `.minions` constant, so the sixth rule does not list it.

### D3

`primary_of(common)` is `Path(common).parent`. A caller that resolved git's answer before keeps resolving it: the conductor's `_common_dir` and `pin.py` do, `gate_check.py` does not. Each script's error text for a failed git call is untouched.

### D4

The conductor's `_run_dir` still halts when `.minions` is a link or no folder. `primary_of`'s guard on a repo outside the cwd stays in the conductor. `review_metrics.py` still reads `<repo>/.minions/changes` with no git. The viewer's `projects` still tests `.minions` on a row's own path before `primary_of` maps it.

### D5

The table is the conductor's: `OLD_LAYOUT`, the dict of old pattern to new name; `OLD_ROLES`, a change folder's `review.md` and `security.md`; `OLD_ID`; `OLD_STAMP` and `OLD_LOG`, the old worker log under `runs/<stamp>/`. `old_layout(primary, change)` is the first of `old_files(primary)[change]`, sorted, so the conductor's `grant` still names `.minions/build/0001-todo.done`. Each script keeps its words (`is the old layout: /mf-ship moves it`, exit 2; converge's `is at an old path: /mf-ship's run moves it`, return 1; `run.py`'s `OldLayout`).

The fix, in its own phase after the moves:

| copy | before | after |
|---|---|---|
| conductor | the old paths, the role names, the old log | unchanged, read from the module |
| converge, `gate_check.py`, integrate | the old paths and the role names | gain the old worker log |
| `run.py` | the old paths and the old log | gains the role names |

A hand-run station on a repo no run has moved, with an old worker log, now halts. Every recorded repo is already moved.

### D6

The conductor's and the stations' phases are moves. A test that reaches a moved name changes the line that reaches it; no `assert` changes. The conformance check holds it on each phase's diff.

### D7

`check_seed` holds `scripts/` too. A file under `skills/` takes `SEED` as today.

A file under `scripts/` takes `sys.path.insert(0, str(Path(__file__).resolve().parents[N] / "skills"))`, `N` its depth below the repo root: `1` for `scripts/corpus.py`, `2` for `scripts/metrics/run.py`. The case that an unseeded import in `scripts/` passes turns over.

### D8

`check_layout(root, listed=LAYOUT_SITES)` reads each script's syntax tree outside `skills/mflib/layout.py`. It finds each string constant outside docstrings that equals `.minions` or `.mf-ship-origin`, or starts with `.minions/`.

A pair is `(base name, name)`, the name `.minions`, `.minions/` or `.mf-ship-origin`. The list takes the keyword form the other rules take, so a planted-breach twin passes its own list. A message that spells a longer path in the middle of a sentence is text, and the rule is blind to it.

The list starts with the sites no move reaches: `conformance.py`'s pathspec, `codebase.py`'s junit report, which is the checkout's that ran the gate and not the primary's, each `.mf-ship-origin` site of `home-layout`, and any other constant that joins no path. The build writes the list from the rule's own output in phase 6.

### D9

`converge.py` reads an old `backlog.md` for a freeze's debt cards when no `debt.md` stands, and takes no lock beside one. A case of the pin holds it. `debt_file` and `backlog_file` are the module's names for the two.

### D10

Cards `0109·S1` and `0119·S1` cite lines of `conduct.py` that move. Converge's checkers read the cards on the diff's files and re-point them when they write the debt file; this change edits none.

### D11

The pin changes no file under `skills/` or `scripts/`. Each new case is seen red under one named change to the code it holds, then green. The cases run through the move phases unchanged, and the fix phase turns the old-layout cases to the one table.

### D12

D57 gives the finder to the shared home and drops *each script finding it through its own `_change_dir`* and the accepts clause that waits for the home. D83 gains the sixth rule. [`docs/recipes.md`](../../../docs/recipes.md)'s state-file recipe, `THREAT_MODEL.md`'s surface sentence for the home, and the old-layout paragraphs of `mf-build`, `mf-integrate` and `mf-release` follow. D16 and D18 stand.

## Tests

The tests are by layer. Counts are what the commands print at the end of the build, not before.

| layer | adds | command |
|---|---|---|
| unit | `tests/test_layout.py`: each function of the module against a hand-spelled path; the table's reader; `tests/test_structure.py`: `check_layout`, its twins, the widened seed rule | `uv run pytest tests/test_layout.py tests/test_structure.py -q --collect-only` |
| unit | the pin: one case per old-layout entry per copy, converge's lone `backlog.md`, the viewer's fingerprint, a linked worktree's finder per script | `uv run pytest tests/test_conduct.py tests/test_converge.py tests/test_gate_check.py tests/test_integrate.py tests/test_metric_scripts.py tests/test_viewer.py tests/test_run_dir_finders.py -q --collect-only` |
| end-to-end | none | — |

No end-to-end test is added ([T1](../../../CODING_STANDARDS.md)): every case reaches a function or a command line of one script. The conductor's cases call `migrate_layout`, `status`, `report` and `grant` as `tests/test_conduct.py:7456` and `:7592` do, so none starts a run.

These cases turn over, and no assert elsewhere changes ([T5](../../../CODING_STANDARDS.md)):

| test removed or turned | carried by |
|---|---|
| the `outside-skills` case of `test_check_seed_passes_a_seeded_or_exempt_import` | `test_check_seed_fails_on_an_unseeded_import`, which gains the `scripts/` case (D7) |
| the pin's old-layout cases of each copy in `tests/test_converge.py`, `tests/test_gate_check.py`, `tests/test_integrate.py` and `tests/test_metric_scripts.py`, each on its own entries | the same cases over the one table, with the role names and the old log (D5) |

The files the tasks name:

- `tests/old_layout.py` holds the entries as literals; `tests/test_run_dir_finders.py` builds repos with `tests/fake_worker.py`.
- The pin adds cases to `tests/test_conduct.py`, `tests/test_converge.py`, `tests/test_gate_check.py`, `tests/test_integrate.py`, `tests/test_metric_scripts.py` and `tests/test_viewer.py`.

## Dependencies

None.

## Risks / Trade-offs

- **A hand-run station reads the whole table.** `old_layout` calls `old_files`, which lists each old folder and each `runs/<stamp>/`, where a copy tested one name per entry. A run directory with many stamps costs one listing per call; the conductor pays it at each start already.
- **`OLD_ID` is four digits and a slug.** The conductor's table matches an id by that pattern, where the other copies format any id into each path. Every change id today is of that form, and the decisions page fixes it.
- **A seed in `scripts/` loads `skills/mflib/`.** `scripts/` is outside the pin's export, which archives `skills` alone, so the seed reaches the checkout's own `skills/`, and a metric script runs only in a checkout.
- **The list may start longer than the sites D8 names.** A `.minions` constant that is no join stays, on the list, and each later version shortens it.
- **The conductor's `_change_dir(runs.parent, change)`** reads as a path of `runs`. It stays: renaming that parameter is no move.

## Verdict

Ready to build. The pin comes first, then the module and the widened seed rule, the conductor's and the stations' moves, the one table as the fix, and the sixth rule with the record last.
