# Station guards — design

Each guard of the gate, `Verify:`, the cut, converge, integrate and the viewer gets the case it lacks, seen red under the break that removes the guard. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

A scratch clone removed each guard below and the suite stayed green: no case reaches it, or the case that does cannot tell it from its neighbour. The version line that follows moves this code, so each guard is held first.

The change edits tests, and one line group of `skills/mf-ui/scripts/viewer.py`. No station behaves differently ([D10](../../../docs/decisions.md): a change with no behaviour change says so, here as `skip_specs: true`).

```
tests/test_gate_check.py  test_gate_run.py  test_plan_check.py      phase 1  gate
tests/test_verify_check.py                                         phase 2  Verify:
tests/test_cut_check.py                                            phase 3  cut
tests/test_converge.py                                             phase 4  converge
tests/test_integrate.py                                            phase 5  integrate
tests/test_viewer.py   skills/mf-ui/scripts/viewer.py              phase 6  viewer
```

## Goals / Non-Goals

- **Goals:** one case for each guard in [the guards](#the-guards); each case fails only when its own guard is broken.
- **Non-goals:** the *Also* items of each finding, which ride with the region's version; a mutation tool in the repo; any change to what a station does.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | A case is the lowest layer that can fail for its guard, and joins an existing test or table before a new test is added | `T1`, `T2`: setup is most of a test's cost | a new end-to-end test per guard |
| [D2](#d2) | The build sees each new case red under the break named in [the guards](#the-guards), then restores the line; no broken line is committed | a case never seen red may hold nothing | a mutation tool in the repo: a feature of its own |
| [D3](#d3) | A guard in a loop over a set is held by many inside names | a set's order is the hash seed's, so one outside name breaks some seeds only | one outside name beside one inside name |
| [D4](#d4) | A guard that is a conjunction has one case per conjunct | `W5`: each conjunct can fail alone | one case for the whole condition |
| [D5](#d5) | Debt card `0120·R3` is closed by its premise: its tests already carry `slow` at the base | the card's lines moved and its marks were added since; the release deletes the card, so the claim must hold | marking them again |
| [D6](#d6) | The viewer's bind address is a constant read by a server factory | the address is then a value a test reads from the server the factory builds, with no socket opened, and `serve` stays a loop that needs no cover | a test that starts `serve`; a test that binds a real socket, which a sandbox that refuses local binding fails at the bind |

### D1

A new test is added only where no test reaches the state: a direct call to `gate_makefiles`, a gate that rewrites the tree, a table of `merge3` merges, a git that fails after the worktree is read, and the viewer's bind. The rest are cases in the tests and tables named in [the guards](#the-guards).

### D2

For each row of [the guards](#the-guards): add the case, run it, break the line as the row says, see the case fail for that reason, restore the line, see it pass. Each phase but the last holds its sources unchanged, so each ends with `git diff --quiet HEAD -- skills` exiting 0. The last phase edits `viewer.py` alone.

### D3

`gate_makefiles` walks `names`, a `set`. With `continue` turned `break`, a name outside the tree hides the names after it, and which come after is the hash seed's. A case with many inside names and one outside name fails on almost every seed.

### D4

`gate_run.gate` rewrites its verdict when `tree is None or settled_tree() != tree or dry_run() != dry`. The dirty-tree case holds the first conjunct. The second needs a gate that edits a tracked file, the third a gate that changes `make -n gate`'s output with the tree unchanged.

### D5

At the base each of `test_workers_are_the_unfinished_spawns`, `test_the_projector_gives_each_state_its_why` and `test_liveness_is_active_then_quiet` has `@pytest.mark.slow` on the line above it. The card names `tests/test_viewer.py:211`, `:275` and `:434`, lines from before. This is the cutter's decision, recorded in the brief; the proposal still lists the card, and a premise check in the last phase holds the marks.

### D6

`viewer.py` gains `HOST = "127.0.0.1"` beside `PORT`, and `server(port)`, which returns `ThreadingHTTPServer((HOST, port), Handler)`. `serve` calls `server(port).serve_forever()`. The behaviour is the same; the loopback literals of the printed URLs and the `Host` check stay as they are.

The case binds nothing. It sets `ThreadingHTTPServer` in `server.__globals__` to a recorder that keeps the address it is given, as the file's tests reach `read_part.__globals__`, and calls `server(0)`. It turns red when `HOST` is not loopback and when `server` stops reading `HOST`, in any sandbox. The module docstring's `no socket is opened` stays true and stays.

## The guards

One row per guard. **Break** is the edit that must turn the case red. **Case** is the input the case adds and what it asserts.

| id | guard | break | case |
|---|---|---|---|
| G1 | `plan_problems` in `skills/mf-converge/scripts/gate_check.py` | the `continue` after `if not GATE_MAKEFILE.search(text):` becomes `break` | in `test_a_bare_makefile_task_fails_the_plan_check`, a case of two sub-tasks: 1.1 edits `README.md`, 1.2 is the bare `Makefile` task of case `prose`; exit 1 and `1.2: no ```diff line` |
| G2 | `gate_makefiles` in the same file | the `continue` after `if not lexical.is_relative_to(top) or not target.is_relative_to(top):` becomes `break` | a new test calls `gate_makefiles` through `runpy`, with a trace whose `MAKEFILE_LIST :=` line names `../outside.mk` and many files that exist in the tree; each inside file is in the result |
| G3 | `gate` in `skills/mf-converge/scripts/gate_run.py`, conjunct `settled_tree() != tree` | remove `settled_tree() != tree or` from the `if tree is None or …` line | a new test with a gate recipe that rewrites `README.md`; stdout holds `gate: green — unrecorded, the worktree is not settled` and no record exists for the tree |
| G4 | the same line, conjunct `dry_run() != dry` | remove `or dry_run() != dry` | in the same new test, a gate whose Makefile prints `$(shell cat .minions/mode 2>/dev/null)` in a recipe line and whose recipe writes the ignored `.minions/mode`; the tree stays settled, the output differs, stdout holds `unrecorded` and no record exists |
| G5 | `passed` in `skills/mf-converge/scripts/plan_check.py` | remove `search and` from the last `return` | in `test_a_plan_check_finds_what_the_plan_left`, after the search that finds nothing, a sub-task whose `Verify:` is `false` followed by `prints nothing`; the check is `(1, ["plan: 1.1 — `false` exited 1"])` |
| G6 | `search` in `skills/mf-cut-change/scripts/verify_check.py`, short options | in the pattern `-(?:[A-Za-df-z]+e?\|e)` widen `[A-Za-df-z]` to `[A-Za-z]` | in `test_a_check_out_of_shape_breaks_and_is_not_run`, `grep -eo` over a file outside the repository is refused |
| G7 | the same, option list | add `f` to `SHORT` | `grep -n -f` over a file outside the repository, then `a.md`, is refused |
| G8 | the same, file operands | in `paths = (operands + tail[1:])[0 if pattern else 1 :]` make the slice `[1:]` | `grep -n -e x` over a file outside the repository, then `a.md`, is refused |
| G9 | `breaks` in the same file | remove the `set(shell[i - 1]) <= OPERATOR` clause from `starts` | `grep -n x a.md; cd /` is refused for `cd` |
| G10 | `breaks`, words after `then` | remove the `shell[i - 1] in ("do", "then")` clause | `if grep -n x a.md; then cd /; fi` is refused for `cd` |
| G11 | the passing twin | none: the case passes when the guards hold | `grep -n cd` over `app/states.py` is one plain command and prints nothing |
| G12 | `row_i4` in `skills/mf-cut-change/scripts/cut_check.py`, a phase listed twice | delete the whole `problems.extend(…)` statement that holds `listed twice` | in `test_i4_names_each_defect_of_the_tasks_shape`, a `## Progress` line repeated; `phase 1 is listed twice in `## Progress`` is in the halt |
| G13 | `row_i4`, no phase listed | delete the `if not phases:` block | every `## Progress` phase line removed; ``## Progress` lists no phase` is in the halt |
| G14 | `row_i4`, a sub-task outside its section | delete the closing `for` loop over `prose_lines` | a listed phase's sub-task placed under another phase's `## N —` heading; `sub-task 1.1 sits outside its `## … —` section` is in the halt. The assert `sub-task 2.1 sits in section 1` not in the halt checks a message the code never prints: it goes |
| G15 | `_unfiled` in `skills/mf-converge/scripts/converge.py` | `and` becomes `or` in `if tops and not …` | in `test_a_fixed_repeats_old_card_is_cleared`, a second card under the heading of the card the verified repeat clears; the heading and the second card stay, byte for byte |
| G16 | `pickup` in the same file | remove `context.round >= context.cap or` | a run at round three with an open small card sends no pickup: its log has no `pickup` event |
| G17 | `catch_up` | `context.round >= CAP` becomes `context.round > CAP` | a counted late commit after a run that ended at round three halts with `the files judged round 3, the cap` |
| G18 | `cap_of` | in the `its own count` branch return `CAP` | a resume planted by a new branch of `_resumed`: a `catch-up` event at round three ending ` · its own count`, with an open blocking card in the checkers' answers; the run fixes at round four, as a cap of five lets it, and does not halt `cap reached` |
| G19 | `blockers` | remove `"accepted"` from `("verified", "accepted")` | a conformance card of Status `accepted` leaves the run converged |
| G20 | `BLOCKS` | remove `"critical"` from the adversarial tuple | an open `critical` adversarial card blocks the run |
| G21 | `merge3` in `skills/mf-integrate/scripts/integrate.py` | delete the `start == groups[-1][0]` clause of the group test | a new test of a table of `merge3(base, ours, theirs)` rows, among them `("a\n", "", "b\na\n")`, which halts with `both sides changed` |
| G22 | `_git` in the same file | replace its `raise Stop(2, …)` with `pass` | a new test with a `git` stub that runs the real git for `rev-parse` and fails any other call: the exit is 2 and the line is `integrate: cannot run — git <command> failed: <the stub's line>` |
| G23 | `Handler` and `serve` in `skills/mf-ui/scripts/viewer.py` | `HOST` becomes `"0.0.0.0"` | a new test puts a recorder for `ThreadingHTTPServer` in `server.__globals__`, calls `server(0)`, and asserts the address it was given is `("127.0.0.1", 0)` and its handler is `Handler`, per [D6](#d6); no socket is opened |

## Tests

Tests added by layer, and the end-to-end runs: none. Every case is a unit test or a function-level call (`T1`), and each joins an existing test where one reaches the state (`T2`).

| file | tests at the base | tests added | command |
|---|---|---|---|
| `tests/test_gate_check.py` | 19 | 1: G2 | `git grep -c "^def test_" -- tests/test_gate_check.py` |
| `tests/test_gate_run.py` | 11 | 1: G3, G4 | `git grep -c "^def test_" -- tests/test_gate_run.py` |
| `tests/test_converge.py` | 33 | 2: G16 and G17; G19 and G20 | `git grep -c "^def test_" -- tests/test_converge.py` |
| `tests/test_integrate.py` | 10 | 2: G21, G22 | `git grep -c "^def test_" -- tests/test_integrate.py` |
| `tests/test_viewer.py` | 25 | 1: G23 | `git grep -c "^def test_" -- tests/test_viewer.py` |
| `tests/test_plan_check.py` | 18 | none: G5 is a case | `git grep -c "^def test_" -- tests/test_plan_check.py` |
| `tests/test_verify_check.py` | 5 | none: G6 to G11 are cases | `git grep -c "^def test_" -- tests/test_verify_check.py` |
| `tests/test_cut_check.py` | 26 | none: G12 to G14 are cases | `git grep -c "^def test_" -- tests/test_cut_check.py` |

Cases added to a test that stands: G1, G5, G6 to G15, and G18 as a row of `_RESUMED`. No test is deleted or merged, so there is no `I16` table. The one assert that goes is G14's, which holds an absence ([D37](../../../docs/decisions.md)).

## Dependencies

None.

## Risks / Trade-offs

- G23's case reads the address `server` hands its server class and opens no socket: the build's sandbox refuses a local bind, so a real bind fails at the bind, not at the assert, and a case that skips there is never seen red per [D2](#d2). The real bind is the standard library's, and `serve` stays uncovered.
- G16 to G18 need a status log at round three. `_plant` and a new branch of `_resumed` in `tests/test_converge.py` do it; a case that needs a new fixture beyond them is a doubt for the person.
- A case asserts what the script prints today. A message that changes in a later move changes the case, by the move rule of the series.

## Verdict

Ready to build, in the phases of [tasks](tasks.md): the gate, `Verify:`, the cut, converge, integrate, and the viewer with its premise check.
