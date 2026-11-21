# Models — design

A change's `models.toml` gets one home, `skills/mflib/modelsfile.py`, in steps: pin what its copies do, move them with no assert changed, then give each disagreement its side. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

Today the file has a writer in `brief_check.py`, a second writer in the conductor, a third in prose, and one parser in the conductor whose callers each read it their own way.

```
brief_check.py --models ──▶ text ──▶ conduct.py cut ──▶ models.toml ◀── the attended cut, by hand
                                       (remove, then create)              (prose)
conduct.py: one parser, the key readers, a hash, a station map with defaults
  link    : the parser follows, the hash refuses
  bad byte: halts the run at a take, reads as no skip at a status read
  token   : checked for the converge workers and [build.moderate] alone
```

The series moves one region a version: pin, move, fix, in that order, each fix in a phase of its own. Earlier versions did it for the status log, the findings, the debt, the run log and the claim. This one does the models file, and pays card 0111·S1 where its fix fires.

## Goals / Non-Goals

- **Goals:** one module that writes and parses the file; the conductor and `brief_check.py` go through it; the copies that disagree agree; `brief_check.py` writes the file for the attended cut; the record says so.
- **Non-Goals:** the models line's grammar; the conductor's station defaults; the prose that writes the file by hand; a gate rule for the file; a bound on any other worker file.

## Decisions

Each settles a plan decision: D1 Q179 and Q209, D3 Q26, D4 Q180, D5 Q182, D6 Q183 and Q213, D7 Q213, D8 Q184, D9 Q185 and Q210, D10 Q183, D11 Q181, D12 Q186, D13 Q212, D14 Q214, D16 Q176. D2 is Q209's; D15 is the record's.

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `skills/mflib/modelsfile.py` is the module, on `statefile.py` and `layout.py`. | the writer's map is in one script and the reader's in another | a module beside `brief_check.py`; one more map in the conductor |
| [D2](#d2) | The conductor keeps each station's models: the station map, the defaults, the executor fallbacks and the child run of `brief_check.py`. | they are what a run does with a table, not the file's form | moving the defaults into the module |
| [D3](#d3) | Phases: pin, module, stations, fix, record. The move changes no assert. | a checker can judge a pure move, and a move with a fix mixed in it cannot be judged | a fix in the move phase |
| [D4](#d4) | One map. `[rescue]`, `[supervise]` and `auto_grant` are the person's keys, read and never written; `[converge.review]` and `[converge.security]` are read no more; a key the map does not name is ignored. | the writer's map holds no person's key, and no cut has written the old tables since they were renamed | reading the old tables for ever |
| [D5](#d5) | Every `model` and `effort` of every table is checked against one token rule at the read; a table that fails halts its version. | the writer checks every word, the reader only some tables; card 0111·S1 is a `[build]` model that reaches a worker's argv | a check per station |
| [D6](#d6) | One read: no link, no block, a regular file, 65,536 bytes, decoded strictly. A missing file is no file; every other failure is a broken file. | the plan's readers read a broken file as nothing planned, and the version is the scope of failure | each reader its own rule |
| [D7](#d7) | The hash is taken over the bytes of the one read; the cut's check fails on a broken file, naming it. | the hash blocks on a pipe and raises on a folder | a second read for the hash |
| [D8](#d8) | The write is `statefile.write` under the change folder's descriptor, refusing a link. | one mechanism, renamed over the target | remove, then create |
| [D9](#d9) | `brief_check.py --models <brief> <slug> --write <change-id>` parses as `--models` does and writes through the module. | the attended cut writes by hand what `--models` prints, and nothing checks it | a new script |
| [D10](#d10) | `conduct.py status` appends the broken file's halt to the version's line and goes on; the viewer reads no skip from it. | a status read must not halt, and the person has to be told | a halt line of the run |
| [D11](#d11) | The models line's `cut` part stays out of the file. | no table names it, and the cutter runs before the file is read | a `[cut]` table |
| [D12](#d12) | No format kind in the gate's rule; a round-trip case holds the one map. | the table names are common words | a kind that fails every `build` |
| [D13](#d13) | `statefile.open_folder` opens a folder and makes nothing; the claim's own open moves onto it. | `statefile.folder` makes each part it opens, which a read must not | a second private open |
| [D14](#d14) | The pin phase carries one rider: the test of the halt a build's spawn removes reaches the spawn through the `run` command. | it fails on Linux, and a patch of its own is a whole version for one test | a patch |
| [D15](#d15) | The record: D57, D77 and D41, the threat model, the module map and the recipe, edited where they live. | a decision in force is edited where it lives, on its page | a new decision |
| [D16](#d16) | This change names by identifier only what stands after its diff; a helper it removes is named by what it did. | the plan check halted earlier cuts on a removed helper's name | naming the base's helpers |

### D1

The module is `skills/mflib/modelsfile.py`, standard library only. It finds the file through `layout.models_file(primary, change)`, and its functions take `primary` and `change`, as `layout.status_log` does. Each docstring cites this design.

| name | does | phase |
|---|---|---|
| `TABLES` | the writer's map: a models-line part to its table, `build`, `build-moderate` to `build.moderate`, `converge`, `conformance`, `adversarial`, `fix`, `release` | 2 |
| `TOKEN` | the token pattern `[A-Za-z0-9._-]+` | 2 |
| `PERSON` | the person's tables, `rescue` and `supervise`, which no tool writes | 4 |
| `BOUND` | the most bytes the read takes, `65536` | 4 |
| `OLD_WORKERS` | the old checker tables by the worker each stands for | 2, gone in 4 |
| `Broken` | a `ValueError`: the file's problem, as a phrase | 2 |
| `text(decided, named, shadowed)` | the text `--models` prints: `named` maps a part to its words, `["skip"]` or `[<host/>model, effort]` | 2 |
| `read(primary, change)` | the file parsed; `{}` with no file | 2 |
| `table(data, name)` | a table, a dotted name walking in; `None` for none | 2 |
| `decides(data)`, `shadows(data)`, `rescue_skips(data)`, `auto_grants(data)` | the keys' readers | 2 |
| `skipping(data, names)` | the tables of `names` that say `skip = true` | 2 |
| `digest(primary, change)` | the sha256 of the file; `None` when missing | 2 |
| `write(primary, change, text)` | the file written | 2 |
| `load(primary, change)` | the one read's bytes | 4 |

In phase 2 each function does what the copy it replaces does, a function or an argument for each copy where the copies disagree; phase 4 keeps a side. `read` imports `layout`, `digest` and `write` go through `statefile.folder`, so the module's map row names `layout.py` and `statefile.py`. The module's `write` removes the file in its own `_remove(primary, change)`, the step a test patches, then creates the file `O_EXCL`.

### D2

`_models`, `_skips`, `_shadow`, `_models_text`, `STATIONS`, `PLANNED`, `SUPERVISOR` and `CHECKER_DEFAULT` stay in `conduct.py`. Its `_table`, `_decides`, `_shadows`, `_skips_rescue` and `_auto_grants` stay as one-line readers over the module's: each reads the file through `_models_data(runs, change)`, which words the module's `Broken` as the `Stop` its copy raised, `conduct: halt — changes/<id>/models.toml: <why>`. `_unwritten(change, error)` returns the `Stop`, code 2, that words a failed write as `cut: cannot run — changes/<id>/models.toml cannot be written: <why>`; in phase 3 it takes the `OSError` the module's write raises, in phase 4 the `statefile.WriteFailed`, whose `error` holds the `OSError`.

### D3

Phase 1 pins the code as it stands, each case seen red under the change its row of [the cases](#the-cases) names, then green. Phase 3 moves with no assert changed: a test reaches a moved name by a new line and nothing else. Phase 4 turns the cases of [the turned cases](#the-turned-cases).

### D4

The map names `[rescue]`, `[supervise]` and `auto_grant` as the person's keys: no tool writes them, and every reader of them goes through the module. `read` no longer falls back to an old table, so a cut that wrote `[converge.review]` before the rename runs on the checkers' defaults. The requirement that kept the old tables read goes with them.

### D5

The check is in the module's `read`: each `model` and `effort` of each table of the map, the values of `TABLES` and `PERSON`, that is a string must fully match `TOKEN`, else `Broken("<table> '<word>' is not a model or effort")`. A value that is no string reads as none, as today, and the conductor's per-station check in `_models` goes. This pays card 0111·S1: a `[build]` model `TMPDIR=/tmp/mf-codex-x` is refused at the read.

### D6

`load` opens the file under the change folder's descriptor from `statefile.open_folder`, through `statefile.read_bytes` with a limit of `BOUND` plus one, and decodes it strictly. Its phrases:

| the file | `Broken` says |
|---|---|
| missing, its folder missing | no file: `read` gives `{}`, `load` and `digest` give `None` |
| a link, a dangling link | `it is a link` |
| a pipe, a folder | `it is not a regular file` |
| over the bound | `it is over 65536 bytes` |
| a byte that is not UTF-8 | `it is not UTF-8` |
| text that is not TOML | the TOML error, as today |

A broken file halts its version alone wherever the run plans or takes it: `take` re-reads every planned station, so a bad byte no longer halts the run. `_skips` lets the `Stop` rise; `stage_of` and `_unjudged`, which read it for a status or the viewer, read no skip then.

### D7

`digest` is the sha256 of `load`'s bytes: `None` for a missing file, `Broken` raised for a broken one. `_check_cut` reads it in place of the stand test and the hash, before it looks at the entry's text, so a broken file fails the cut even when the entry holds none: a missing file fails `no .minions/changes/<id>/models.toml`, a broken one `changes/<id>/models.toml: <why>`, a differing one `changes/<id>/models.toml changed since the cut was queued`.

### D8

`write` calls `statefile.write(Path("models.toml"), text, refuse_link=True, folder=fd)`, `fd` from `statefile.folder` of the run directory, `changes` and the change. A link at the file is refused, and the target of a hard link keeps its bytes while the name is replaced. A `WriteFailed` ends the cut with exit 2 through `_unwritten`.

### D9

`--write <change-id>` is valid beside `--models` alone. It runs the same parse and halts, finds the primary through `git rev-parse --path-format=absolute --git-common-dir`, run with a timeout, and `layout.primary_of`, writes through `modelsfile.write`, and prints `brief: wrote .minions/changes/<change-id>/models.toml`. Its exits are `--models`': 0 done, 1 halts printed, 2 no item; a failed write, and a git that fails or finds no repository, print `brief: cannot write — <why>` and exit 2.

The parse moves into `models_of(opened, item)`, which returns `decided`, `named` and `shadowed`; `text` is the module's. The flag makes `brief_check.py` import `mflib.layout`, so its map row gains `layout.py`.

### D10

`status` appends ` — <the Stop's text without its "conduct: halt — ">` to a version's line when `_models_data` stops for it, e.g. `0001-todo · build — changes/0001-todo/models.toml: it is not UTF-8`, and goes on. The status table of `skills/mf-ship/SKILL.md` says so. This is the cut's reading of "a status read names the file and goes on".

### D11

`TABLES` has no `cut` entry and the spec says why: the cut's model goes on `conduct.py cut`'s own arguments.

### D12

`check_formats` gains no kind. `tests/test_modelsfile.py` holds a round-trip case: every table and key `text` writes is read back by `read`.

### D13

`open_folder(root, *parts)` opens `root`, followed, then each part with `O_NOFOLLOW | O_DIRECTORY`, and makes nothing. A missing part raises `FileNotFoundError`, a link `OSError` `ELOOP`, a file `NotADirectoryError`. The claim's `_open` calls it for the claim folder, and its callers see what they saw. `docs/recipes.md`'s rule line is brought up to the format kinds that stand.

### D14

The rider is `test_a_build_spawn_removes_the_halt_the_last_build_left`. It keeps its assertions: the build's spawn, the halt file gone, `rescue.md` kept.

### D15

| page | edit |
|---|---|
| `docs/decisions.md` D57 | `models.toml` is written and parsed by `skills/mflib/modelsfile.py` |
| `docs/decisions.md` D77 | `brief_check.py --models --write` writes it for the attended cut; the queue writes it through the module |
| `docs/decisions.md` D41 | a cut by hand writes what `brief_check.py --models` prints, by `--write` |
| `THREAT_MODEL.md` | the models file's read and write follow no link; the surface list names `modelsfile.py` |
| `docs/modules.md` | a `home` row, and the names of the conductor's and `brief_check.py`'s rows |
| `docs/recipes.md` | the models file's line; the rule line names the kinds that stand |

Card 0111·S1 is closed by its premise: no task edits `.minions/debt.md`; the release deletes the card. Cards 0140·S1 and 0140·S3 stay open: neither trigger is a models site.

### D16

`tasks.md` names the conductor's `_models_data`, `_unwritten`, `_table`, `_decides`, `_shadows`, `_skips`, `_skips_rescue`, `_auto_grants` and `_models`, and the module's names of [D1](#d1). It names what the diff removes — the conductor's models-file parser, hash and writer, its token pattern, its old-name map, and `brief_check.py`'s text writer and tables — by what they did. A `Verify:` that proves one gone is a search for its definition line.

## Tests

The change adds unit tests of the module and of the helpers it adds to the home, in `tests/test_modelsfile.py`, `tests/test_statefile.py` and `tests/test_layout.py`, and run-level cases that start no worker, in `tests/test_modelsfile.py` with the conductor loaded by `conduct_load`. It adds no end-to-end test: the repository has no browser layer, and no case needs more than a repository in `tmp_path`. Each case sits at the lowest layer that can fail for the behaviour ([T1](../../../CODING_STANDARDS.md)).

A case that would block on a pipe runs the read in a child process and kills it after 10 s. The counts are `uv run pytest tests/test_modelsfile.py tests/test_statefile.py tests/test_layout.py --collect-only -q` before and after the change. `tests/test_conduct.py` is re-pointed in phase 3 and turned in phase 4, and gains the rider of [D14](#d14); `tests/test_claim.py` keeps every assert when the claim's open moves; `tests/test_brief_check.py` gains the `--write` cases.

No test is deleted or merged. The tests of [the turned cases](#the-turned-cases) change an assertion in phase 4, each carrying its scenario to the new rule; none is removed.

### The cases

Each case is green on the code as it stands and red when the code changes as the last column says; the build worker sees both.

| case | asserts | red when |
|---|---|---|
| a | the token pattern takes `_`, upper case and `.`, and refuses an empty string, a space, `;`, `/` and a non-ASCII letter; `[build.moderate]` takes `[build]`'s executor and is checked | the pattern or the moderate lines change |
| b | the hash leaks no file descriptor | its descriptor is not closed |
| c | a folder at `models.toml` fails the cut's check as no models file | the check tests anything but a file |
| d | a folder reads as `{}`; text that is not TOML is a `Stop` with code 1 naming the file; a bad byte raises `UnicodeDecodeError`, no `Stop` | the parser's catch or its stand test changes |
| e | a string where a table belongs reads as no table | the table walk takes a non-table |
| f | only a top-level `decide = "recommended"` decides | the key's value or place changes |
| g | integrate reads `[release]` alone; the rescue `[rescue]`, else `[build]`, an empty `[rescue]` counting; a worker table before its old name; the token check on the converge workers and `build.moderate`, model and effort; `build.moderate` refusing an executor; a checker with no executor taking `[converge]`'s and the fixer `claude`; a model or effort that is no string reading as none; the supervisor's defaults filling each missing part; a `claude` model on the run's Codex refused | the station map, a default or a check changes |
| h | only the boolean `true` shadows | the test of the value changes |
| i | the fixer is never skipped; a bad byte reads as no skip | the skipped names or the catch change |
| j | only a boolean `[rescue] skip` skips the rescue | the test of the value changes |
| k | only `[converge] auto_grant = false` refuses a grant | the default or the test changes |
| l | a station whose models moved after the plan is a `Stop` with code 1 | the comparison changes |
| m | every planned station is read again before a take's first step: a refused worker or moderate table, or text that is not TOML, halts the version | a station leaves the re-read |
| n | the plan's read keeps `planned`, `grants_auto`, `skips`, `decides` and `shadowed`; text that is not TOML plans nothing and raises nothing; the Codex note reads the checkers alone | a field leaves the read |
| o | a worker table that moved after the plan keeps the version out at a rejoin | the take-back's comparison changes |
| q | the models text: a timeout is a `Stop` with code 2; a failure names stdout's first non-blank line, else stderr's; a bad byte in the child's output is replaced | the child's handling changes |
| r | `brief_check.py --models` prints each optional part in `TABLES` order, byte for byte; an item's heading with trailing blanks still decides | the order or the heading test changes |

### The pins

Each pin is green on the code as it stands and holds what no changed line reaches.

| pin | holds today |
|---|---|
| a bad byte | every parser but the skip reader raises `UnicodeDecodeError`; the skip reader reads no skip; the plan's model read returns none; the hash hashes the bytes; the plan reads nothing and keeps no flag; a take halts the whole run |
| text that is not TOML | every parser raises a `Stop` with code 1, caught by the skip reader and the plan's model read; a take halts the version alone |
| a link | the parser follows it and the hash returns none, so the cut's check fails as changed since queued, and passes when the entry holds no text; a dangling link reads as `{}`; the writer removes a link that stands, and one planted after the removal is a `Stop` with code 2, its target untouched |
| a hard link | the writer unlinks the name and the other name keeps its bytes |
| a pipe | the parser reads it as no file and plans the defaults; the hash blocks; the writer replaces it |
| a folder | the parser reads `{}`; the cut's check says no models file; the writer stops with code 2; the hash raises `IsADirectoryError`, shielded only by the check's earlier test |
| a word that is no token, `TMPDIR=/tmp/x` and `a b` | taken for build, rescue, release, integrate, supervise and converge; refused for the converge workers and `build.moderate` |
| keys no writer writes | `[rescue]`, `[supervise]` and `auto_grant` are read; the old tables stand in for missing new ones, their `skip` ignored |
| the `cut` part | never reaches the file |
| where `skip` and `shadow` count | `skip` under `[converge]`, the checker tables and `[rescue]` alone; a skipped table's station still reads its models; `shadow` under `[converge]` alone |
| wrong types | `skip = "yes"`, `skip = 1`, `shadow = 1` and `decide = true` read as false; `auto_grant = "false"` and `0` still grant; a model or effort that is a number, a list or a table reads as none; `build = "x"` is no table; an executor of `3`, `"Claude"` or a list is unknown |
| the queued text against the file | any byte changed after the cut fails the check; an entry with no text passes any file |
| `--models` | an item with every optional part, the switch and the shadow prints byte for byte; the conductor's text and its written file are the same bytes |

### The turned cases

These change in phase 4, and only there.

| test or case | turns to |
|---|---|
| `test_a_checker_on_another_host_is_planned_and_probed`, its old-table lines | the old tables are read no more: both stations read their defaults |
| the same test's skip row for `[converge` | the skip reader raises the version's `Stop` |
| the third run of `test_run_halts_when_a_worker_claims_what_disk_does_not_show` | a bad byte halts version `0001-todo`; the other version goes on |
| `test_a_link_planted_after_the_removal_truncates_no_models_file` | a hard link planted before the write: the name is replaced, the other name keeps its content; a link at the file is refused |
| cases d, m, n | a folder, a bad byte and a broken file in the take and the plan read as the one read says |
| case c | a folder at the file fails the cut's check naming it: `it is not a regular file` |
| the module's `test_module_…` cases of `read`, `digest` and `write` | each turns in the phase that fixes its function: the read in 4, the digest in 4, the write in 4 |
| case g's rows for the token's reach and for a worker table before its old name | every table is token-checked; the old name is ignored |
| case i's row for a bad byte | the skip reader raises the version's `Stop` |
| the pins of a link, a pipe, a folder, a bad byte and the scopes of failure | a broken file, each halting its version, and the cut's check naming it |
| the pin of a word that is no token | refused for every table, `[build]`, `[rescue]`, `[release]` and `[supervise]` among them |
| the pin of keys no writer writes | the old tables are read no more; `[rescue]`, `[supervise]` and `auto_grant` are still read |
| the pin of the queued text against the file | a broken file fails the check even with no queued text |

## Dependencies

None.

## Risks / Trade-offs

- **The pin is wide.** A case seen red under a change that is no longer one line is read, not run: the worker names the line it changed in the commit's body.
- **A cut's old tables go dark.** A models file an older run wrote with `[converge.review]` runs its checkers on the defaults. No cut has written it since the rename; a person who planted one sees the version's defaults in its first converge prompt.
- **A link at the file is refused where it was replaced.** A rejoin that writes the entry's text back stops the cut with exit 2 on a planted link, naming it, where it used to remove the link. The person removes it.
- **`status` grows a clause.** The table in `skills/mf-ship/SKILL.md` is the one place a reader learns it.

## Verdict

Ready to build, in the phases of [tasks](tasks.md): the pin, the module, the stations, the fix, the record.
