# Gate-recipe hardening — design

One bundled check reads both sides' gates from fresh exports, halts on any unplanned change to a file the gate's
make reads, and halts on a planned change that drops a command or adds an ignore mark. Verdict: ready to build.
Scope is [the proposal](proposal.md); behaviour is [the delta](specs/sdd/spec.md).

## Context

Premises were re-checked on `main` at `8d7383e` (v0.31.1) before the cut.

| evidence at the cut | implication |
|---|---|
| Converge precondition 6 (`skills/mf-converge/SKILL.md:157-164`) and release precondition 8 (`skills/mf-release/SKILL.md:97-104`) run `git show <base>:Makefile \| make -n -f - gate` in the branch's tree; they differ in the station word, how `<base>` is defined, and converge's status-log clause | both become one call ([D5](#d5)) |
| *Never weaken the gate to pass* names the preconditions for the recipe (`docs/principles.md:100-102`) | its *Held by:* names the script ([D5](#d5)) |
| `_METRICS_SCRIPTS` (`tests/test_skills.py:404-407`) maps one script per station | it becomes a list of pairs, so `mf-release` names both bundled scripts ([Tests](#tests)) |
| No station uses `git archive` or `git worktree`; MF's gate (`Makefile:9-14`) has no include, sub-make, `-` prefix, `.IGNORE` or `MAKEFLAGS` | the check is new; MF's own gate passes it unchanged |
| GNU Make 3.81 here, 4.x on CI (`ubuntu-24.04`); `make -n` hides a `-` prefix, `.IGNORE` and `MAKEFLAGS += -i`; `make -pn -r gate` prints `MAKEFILE_LIST :=` per database; an export reads the base's includes and sub-makes and leaves no repository state; `$(shell)`, `+` and `$(MAKE)` lines run under `-n` | [D1](#d1)–[D3](#d3): the scratch-repo experiments of the planning |
| `uv run pytest --collect-only -q \| tail -1` prints `38 tests collected` | [Tests](#tests) |

## Goals / Non-Goals

**Goal:** no change to the files a gate's make reads ships unless its cut planned it, and no planned change hides a
failing command.

**Non-goals:** see [the exclusions](proposal.md#not-in-this-change).

## Decisions

The grilling settled these choices (the brief's Q2–Q11); the build does not reopen them.

### D1

| id | decision | because | rejected |
|---|---|---|---|
| D1 | Both sides' make runs in fresh exports — `git archive <base>` and `git archive HEAD` — under `.minions/gate-check/<change-id>/{base,head}/`, with `MAKEFLAGS`, `MFLAGS` and `MAKELEVEL` removed from the environment; the exports are removed when the check ends, pass or halt | The base's includes and sub-makes are its own (`0023·S1`); both sides lack the same ignored files and build outputs; the branch's `$(shell)` runs outside the checkout | A worktree, which leaves `.git/worktrees/` until removed; the working tree |

### D2

| id | decision | because | rejected |
|---|---|---|---|
| D2 | A **gate makefile** is any file in a `MAKEFILE_LIST :=` line of `make -pn -r gate` on either export, as a path inside the export. **Unplanned** — no planning task (D3) — a branch whose `git diff --name-only <base> HEAD` names a gate makefile halts | One rule closes the include, sub-make, `-`, `.IGNORE` and `MAKEFLAGS` routes (`0023·S1`, `S5`, `R8`); it reads one line of make's database, the same on 3.81 and 4.x | Parsing make's database for prefixes; comparing output alone |

### D3

| id | decision | because | rejected |
|---|---|---|---|
| D3 | A **planning task** is a `- [ ] N.M` or `- [x] N.M` line in `tasks.md` at the cut commit naming both `Makefile` and `` `gate` ``. **Planned**: compare both exports' `make -n gate`, and halt on a line the base prints and the branch does not; scan the gate makefiles' diff, and halt on an added line that starts a recipe with `-` (a tab, then `-`), names `.IGNORE`, or sets `MAKEFLAGS` with an `i` flag — each unless a planning task holds the line's text | A planned recipe change must still not hide a failure; the exact text in the task is a decision a person read | `-k` as a mark — it hides nothing, the run still exits 2; a task that only names the recipe excusing every line |

`<cut>` is the one commit `git log --diff-filter=A --format=%h -- openspec/changes/<change-id>/design.md` prints;
none or more than one halts.

### D4

| id | decision | because | rejected |
|---|---|---|---|
| D4 | One script, `skills/mf-converge/scripts/gate_check.py`, standard library only, its PEP 723 header pinning `>=3.12`, run as `uv run --script … --change <change-id> --base <base>` from the repository root | D2 allows a bundled standard-library script; one implementation for both stations | The rule as prose in both preconditions; a script per station |

| exit | means | prints |
|---|---|---|
| 0 | the gate is the base's, or the plan covers its change | `gate: the base's` or `gate: planned — <the planning task>` |
| 1 | halt: an unplanned gate makefile change, a dropped line, an ignore mark, or no single cut commit | the reason, the files or lines, and for a planned change the two dry runs' diff |
| 2 | cannot check: a dry run failed on a side, or git or make is missing | the side and the first line of make's error |

### D5

| id | decision | because | rejected |
|---|---|---|---|
| D5 | Both preconditions call the script and halt on its verdict; the principle names it | One rule in two stations, word for word apart from the station | Keeping the differing prose |

Converge's precondition 6, after:

```markdown
6. **The gate is the base's, or the cut planned its change.** Run
   `uv run --script <this package>/scripts/gate_check.py --change <change-id> --base <base>`, `<base>` being
   Step 2's merge-base. Exit 0 → pass. Exit 1 → **halt**, copying what it prints to the report and the status log.
   Exit 2, or `uv` missing → **halt**: the gate cannot be read, and it names the side. A branch does not certify its
   own weakened gate.
```

The release's precondition 8: the same, with `../mf-converge/scripts/gate_check.py` resolved from this skill's
package, `<base>` being `git merge-base <default-branch> HEAD`, the copy to the report only, and *release* for
*certify*.

The principle's *Held by:* ends: *`mf-converge` precondition 6 and `mf-release` precondition 8, through
`skills/mf-converge/scripts/gate_check.py`, for the recipe.*

### D6

| id | decision | because | rejected |
|---|---|---|---|
| D6 | Converge runs | Security cards; a new script that runs make on branch-controlled makefiles | A hand read |

## Tests

The tests run real `git` and `make` in `tmp_path` repositories — the lowest layer that can fail for the check
(`T1`): the routes are make's own behaviour. They stay offline.

| layer | at cut | added | removed | proof |
|---|---:|---:|---:|---|
| Unit test functions | 38 | 11 | 0 | `uv run pytest --collect-only -q \| tail -1` prints `38 tests collected` at the cut, `49 tests collected` after |
| Integration tests | 0 | 0 | 0 | — |
| End-to-end runs | 0 | 0 | 0 | — |

| test, added | file | holds |
|---|---|---|
| `test_an_unchanged_gate_passes` | `tests/test_gate_check.py` | exit 0; nothing left under `.minions/gate-check/` |
| `test_an_include_changed_on_the_branch_halts` | the same | `0023·S1`: the base side reads the base's include; unplanned → exit 1 |
| `test_a_sub_make_weakened_on_the_branch_halts` | the same | `0023·S1`: `$(MAKE) check` with `\|\| true` added |
| `test_a_dash_prefix_halts` | the same | `0023·S5`: `-false`, unplanned |
| `test_an_ignore_target_halts` | the same | `0023·R8`: `.IGNORE` |
| `test_makeflags_ignore_halts` | the same | `MAKEFLAGS += -i` |
| `test_a_planned_change_that_drops_a_line_halts` | the same | planned; a base line gone, not quoted |
| `test_a_planned_dash_the_task_does_not_quote_halts` | the same | planned; an added `-` prefix |
| `test_a_planned_change_the_task_quotes_passes` | the same | planned; every line quoted → exit 0 |
| `test_a_dry_run_failing_in_an_export_exits_2` | the same | a hard `include .env`, ignored → exit 2 naming the side |
| `test_no_single_cut_commit_halts` | the same | `design.md` added twice → exit 1 |

| test, extended | file | gains |
|---|---|---|
| `test_the_stations_run_the_bundled_metrics_script` · `test_the_metrics_script_scan_reports_a_missing_script` | `tests/test_skills.py` | `_METRICS_SCRIPTS` becomes a list of pairs holding `mf-converge` → `scripts/gate_check.py` and `mf-release` → `../mf-converge/scripts/gate_check.py`; the twin plants a missing `gate_check.py` |

Planned addition count: ``grep -cE '^\| `test_[a-z0-9_]+` \| `?(tests/test_gate|the same)' openspec/changes/0034-gate-recipe-hardening/design.md`` prints `11`.

## Dependencies

None.

## Risks / Trade-offs

- **The check halts on any unplanned makefile edit, even a harmless one** → by design: the cut names the recipe
  when a change means to touch it.
- **The branch's makefile code runs under `-n`** → in an export under `.minions/`, never in the checkout; the
  stations already ran `make -n` on the branch's tree.
- **A gate that needs an ignored file to parse cannot be checked** → exit 2, the person decides.
- **A weakening through a program the recipe calls** → out of scope; review reads the diff.

## Migration Plan

```
1 the check + its tests ─▶ 2 the stations call it ─▶ simplify ─▶ converge ─▶ release
```

Each phase ends on a green gate. Nothing is irreversible.

## Verdict

Ready to build. Acceptance: every route in [Tests](#tests) tested, both preconditions calling the script, the principle naming
it, and the release tagging `v0.31.2`.
