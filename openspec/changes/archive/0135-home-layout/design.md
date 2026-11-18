# Home layout — design

One module, `skills/mflib/layout.py`, names every home-folder and XDG path a script builds, and the gate refuses a new spelling. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The home half of the state layout is built by hand in these scripts:

```
conduct.py    ~/.mf-ship-origin/<digest>[.released|.default|.pushed|.queue|.gate], live/, repos, probe mark,
              scratch folders, ship.toml (XDG config), skills links, Codex home, Claude settings home
pin.py        the same folder's source, pending, hold, checkout, live/; XDG data; skills links
gate_check.py the digest again, and <digest>.gate
viewer.py     ui.toml (XDG config), the state root (XDG state), repos, the queue's cuts through conduct.py
review_metrics.py  review-metrics.toml (XDG config), repos, Codex home
```

[0134-run-layout](../archive/0134-run-layout/design.md) did the run directory. The structure rules hold it: the sixth rule lists the `.mf-ship-origin` sites as exceptions. The mutants of the home region left a case alive for each of the config fallback, the digest of a linked path, the ledger and offline-base names, the queue's sub-names, the scratch prefix, the metrics' fallbacks and the pin's data folder and checkout.

## Goals / Non-Goals

**Goals**

- Every path below the home folder and every XDG root is built in `skills/mflib/layout.py`, once.
- Every caller keeps its own guard, its error text and its read or write.
- The gate refuses a new spelling of `.mf-ship-origin` or of an XDG variable's name.

**Non-Goals**

- No path changes. `HOME` and each XDG variable are read when a path is asked for, as today.
- No finder for git's answer, no change of a script's own git call: that is the git runner's.
- No change to what `~/.mf-ship-origin` holds, or to `CLAUDE_CONFIG_DIR`'s reach.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | The home half goes into `skills/mflib/layout.py`, beside the run directory's | one file names every path a script builds from where it runs; a file per half doubles the map and the seed | a second module `home.py` |
| [D2](#d2) | The module's surface is the table of D2, each name public | a name that crosses a file must not start with `_` ([D83](../../../docs/decisions.md#d83--the-code-is-layered-with-named-seams-held-by-the-gate)) | a function per file name, none per folder |
| [D3](#d3) | No script defines a finder or a join for a home path; each caller takes the module's name | a wrapper is a second spelling, and the rule cannot see it | keeping the removed `_queue`, `_digest` and `KEPT` constants as aliases |
| [D4](#d4) | Phase 1 pins the survivors on today's code, each case seen red under its named change | a move with no test of the name is a rename no test sees | pinning after the move |
| [D5](#d5) | A listed pair leaves `LAYOUT_SITES` or `PRIVATE_REACH` in the phase that moves its site; the conductor's `_queue` stays one line over `queue_dir` until the viewer stops reaching it | the rule fails on a listed pair the tree no longer holds, and the gate is green at every phase | removing `_queue` in phase 3 and the viewer's pair with it |
| [D6](#d6) | Pin's `_kept_origin` and `_scratch` stay borrowed from the conductor; `_scratch` keeps the making and takes the folder and the prefix from the module | each is behaviour, a read and a parse or a making with a fallback, not a path | moving them into the module |
| [D7](#d7) | The sixth rule refuses, outside the module, a constant that contains `.mf-ship-origin` or equals an XDG variable's name, and no list excuses it | after the move nothing else stops a new `"~/.mf-ship-origin/x"`; equality alone passes it | listing the sites as `.minions`'s are |
| [D8](#d8) | The principles' closed list names what the code reaches below the home folder | the list is the record of what the repo reaches outside itself, and the module now holds each name once | leaving the list as it is |
| [D9](#d9) | The record lines that say the run directory alone gain the home half, the module's docstring in the phase that adds the functions | a docstring that says the run directory alone is false once the module holds the home | editing the docstring in the last phase |
| [D10](#d10) | No task edits `.minions/debt.md`; converge re-points the cards that cite a moved line | the debt file is written under its lock by converge and the release alone | a build task that writes the file |

### D1

The module imports `hashlib`, `os`, `re` and `pathlib`, runs no git and computes each path when asked, none at import. It reads `HOME` through `Path.home()` and the variables `XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_STATE_HOME`, `CODEX_HOME` and `CLAUDE_CONFIG_DIR` at the call, an empty one as unset, as each copy does today. Each function keeps the `Why:` line of the def it replaces.

### D2

Each name below is a function unless it is in capitals. A primary is the path `primary_of` gives.

| name | gives | replaces |
|---|---|---|
| `KEPT_ORIGINS` | `".mf-ship-origin"` | the conductor's `KEPT_ORIGINS`, `KEPT` of `pin.py` and of `gate_check.py`, the inline copies |
| `kept_dir()` | `Path.home() / KEPT_ORIGINS` | each `Path.home() / KEPT_ORIGINS` |
| `digest(primary)` | the first 16 hex digits of the sha256 of `primary.resolve()` | `_digest`, removed, and the inline copy in `gate_check.py`'s `approval` |
| `kept_file(primary)` | `kept_dir() / digest(primary)` | `_kept_file`, removed |
| `released_dir(primary)` | `<digest>.released` under `kept_dir()` | `_ledger`, removed |
| `default_file(primary)` | `<digest>.default` | `_default_file`, removed |
| `pushed_file(primary)` | `<digest>.pushed` | `_pushed_file`, removed |
| `queue_dir(primary)` | `<digest>.queue` | `_queue` |
| `queue_lock`, `queue_cuts`, `queue_rejoin`, `queue_briefs`, `queue_supervised` `(primary)` | `lock`, `cuts`, `rejoin`, `briefs`, `supervised` under `queue_dir(primary)` | the joins off `_queue` |
| `gate_approval(primary, change)` | `<digest>.gate/<change>` under `kept_dir()` | `approve_gate`'s folder and `gate_check.py`'s entry |
| `live_dir()`, `live_mark(primary)` | `live`, and `live/<digest>` | `_mark_live`, and pin's `_kept("live")` |
| `repos_file()` | `repos` under `kept_dir()` | `_record_repo` and the two `recorded` |
| `probe_mark(executor, pid)` | `probe-<executor>-<pid>` under `kept_dir()` | the probe's mark |
| `SCRATCH_PREFIX`, `scratch_parent()` | `".mf-ship-remote-"`, and `Path.home()` | `_scratch`'s literals |
| `pin_source()`, `pin_pending()`, `pin_hold()`, `pin_checkout()` | `source`, `pending`, `hold`, `checkout` under `kept_dir()` | pin's `_kept(name)` |
| `config_dir()` | `minionsfactory` under `XDG_CONFIG_HOME`, else `~/.config` | each hand-built config root |
| `ship_file()`, `review_metrics_file()`, `ui_file()` | `ship.toml`, `review-metrics.toml`, `ui.toml` under `config_dir()` | `_ship_file`'s path, and the removed `config_path` of `review_metrics.py` and of `viewer.py` |
| `data_dir()` | `minionsfactory` under `XDG_DATA_HOME`, else `~/.local/share` | pin's `data` |
| `state_dir()` | `minionsfactory` under `XDG_STATE_HOME`, else `~/.local/state` | the viewer's `state_folder`, removed |
| `SKILLS`, `skills_dir(executor)` | `{"claude": ".claude/skills", "codex": ".agents/skills"}`, and `Path.home()` joined to one | the conductor's `SKILLS`, pin's `HOSTS` |
| `codex_home()` | `CODEX_HOME`, else `~/.codex` | `_codex_home`, removed, and the copy in `review_metrics.py` |
| `claude_home()` | `CLAUDE_CONFIG_DIR`, else `~/.claude` | the line in `_plugins_off` |

The probe's entry is a file. The module names no path of the run directory here: those are 0134's.

### D3

- Removed from the conductor: `KEPT_ORIGINS`, `SKILLS`, `_digest`, `_kept_file`, `_ledger`, `_default_file`, `_pushed_file` and `_codex_home`, and in phase 4 `_queue`.
- Removed from pin: `KEPT`, `HOSTS`, `data` and `_kept`; from `gate_check.py`: `KEPT`.
- Removed from the viewer: `config_path`, `state_folder` and `recorded`; from `review_metrics.py`: `config_path` and `recorded`.

A test that reached one takes the module's name on the same line: the move changes no assert.

### D4

Phase 1 holds today's code. Each case is run once under the change its task names, and seen red, then reverted and seen green. Each home name is spelled by hand in the test, so a rename in the module later turns it red.

### D5

The conductor's pairs and pin's leave `LAYOUT_SITES` in phase 3. The viewer's, `gate_check.py`'s and `review_metrics.py`'s leave in phase 4, with the viewer's `_queue` pair of `PRIVATE_REACH`. Phase 3 leaves `_queue` as `return mflib.layout.queue_dir(primary)`, which the viewer and the tests still reach.

### D6

Pin's `_conduct()["_kept_origin"]` and `["_scratch"]` are the pairs of `PRIVATE_REACH` that stay. Only the conductor's `_scratch` changes: `tempfile.TemporaryDirectory(dir=scratch_parent(), prefix=SCRATCH_PREFIX)`, and its temp-folder fallback stays.

### D7

`check_layout` keeps `.minions` and `.minions/` on `LAYOUT_SITES`. A string constant outside the module that contains `.mf-ship-origin`, or equals `XDG_CONFIG_HOME`, `XDG_DATA_HOME` or `XDG_STATE_HOME`, is a breach whatever the list holds, worded `x.py spells <name>: a home-folder name outside layout.py`; a test holds that `LAYOUT_SITES` names none. The rule lands in the last phase, after the phases that clean the sites ([D79](../../../docs/decisions.md#d79--a-tool-finds-a-checker-judges)).

### D8

`docs/principles.md`'s list under *The repo reaches nothing outside itself* gains `<digest>.released`, `<digest>.default`, the probe's mark, the scratch folders `.mf-ship-remote-*` in the home folder, `settings.json` under `~/.claude` or `CLAUDE_CONFIG_DIR`, the Codex sessions the conductor reads, and the queue's `briefs/` and `supervised/`. [D55](../../../docs/decisions.md#d55--one-pinned-mf-release-per-machine) holds the pin's own files.

### D9

These lines name the run directory alone: the module's docstring, the threat model's surface sentence for `skills/mflib/*`, the map's line for the layer `home`, and the state-file recipe's rule line. Each gains the home half. The executor recipe's rows that name the conductor's `SKILLS` and pin's `HOSTS` point at the module's `SKILLS`.

### D10

Cards 0060·S6 and 0062·S1 cite lines this version moves: `approve_gate`'s path and the ledger's. Converge re-points them where it reads the diff, as it did for [0134-run-layout](../archive/0134-run-layout/design.md).

## Tests

The change adds unit tests and no end-to-end test: each case is a function of a path, or of one script's finder, under the autouse `isolated_home` ([T1](../../../CODING_STANDARDS.md)). Every extension is in a file that exists; no new file holds a test. One case moves, and no test is deleted:

| removed | carried by |
|---|---|
| the `.mf-ship-origin` case of `test_check_layout_fails_on_a_planted_constant`, which asserts the old message `not listed in LAYOUT_SITES` | `test_check_layout_fails_on_a_home_folder_name`, whose message is the rule's new one ([D7](#d7)) |

| layer | adds | where |
|---|---|---|
| unit, the module | each name of D2 against its hand-spelled path; `HOME` and each XDG variable changed between calls change the answer; a linked path gives the primary's digest | `tests/test_layout.py` |
| unit, the pin of phase 1 | the survivors of the region's mutants, a case each | `tests/test_conduct.py`, `tests/test_viewer.py`, `tests/test_review_metrics.py`, `tests/test_pin.py` |
| unit, the rule | a planted home name, a planted name for each XDG variable, a list holding none | `tests/test_structure.py` |

Baselines, each by `git grep -c -e "^def test_" -- <file>` at the base: `tests/test_layout.py` 12, `tests/test_structure.py` 55, `tests/test_pin.py` 11, `tests/test_conduct.py` 220, `tests/test_viewer.py` 29, `tests/test_review_metrics.py` 34. The end-to-end runs added: none; the command `git grep -c -e "^def test_" -- tests/test_sandboxed.py` is untouched.

## Dependencies

None.

## Risks / Trade-offs

- A path that moves by one character is a sandbox or a home-folder bug no gate sees. Phase 1 spells each name by hand, so the move cannot pass red.
- The conductor's `_queue` lives one phase past its use ([D5](#d5)): the price of a green gate at each phase.
- The test lines that reach a moved name change their reach. They change no assert, and the conformance check holds that on each phase's diff.
- `gate_check.py`'s copy of the digest resolved the primary its own finder did not. `digest` resolves, as both copies do, so no answer changes.

## Verdict

Ready to build in the phases of [tasks](tasks.md): the pin, the module, the conductor and the pin, the readers, the rule and the record. It changes the structure-rules requirement and adds no decision.
