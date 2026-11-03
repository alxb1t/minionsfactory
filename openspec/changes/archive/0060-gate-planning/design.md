# Gate planning — design

How a cut's approval of a gate change becomes one the check reads, how a person approves a diff after the fact, and how the
build catches a bad quote at its phase. Verdict at the end: ready to build.

## Context

Read at `22c1af8` (v0.47.4).

- `skills/mf-converge/scripts/gate_check.py` (323 lines): `cut_commit` (`:83`) finds the one commit adding the change's
  `design.md`; `planning_tasks` (`:95`) keeps a sub-task naming `Makefile` and `` `gate` ``, its wrapped lines joined; `check`
  (`:238`) exports the base and `HEAD` with `git archive`, finds the gate makefiles and the dry runs, and halts when no planning
  task exists, naming only the file (`:277`), or on each changed line no planning task quotes (`:281-299`). `main` (`:302`) takes
  `--change` and `--base`.
- It runs at converge's precondition 6 (`skills/mf-converge/SKILL.md:215-220`) and the release's
  (`skills/mf-release/SKILL.md:124`); `skills/mf-cut-change/SKILL.md` and `skills/mf-build/SKILL.md` never name it. The input
  contract runs `I1`–`I17` in both (`skills/mf-build/SKILL.md:66`, `skills/mf-cut-change/SKILL.md:183`), and
  `tests/test_skills.py` fails when the two id sets differ. The cut's self-check is its Step 8
  (`skills/mf-cut-change/SKILL.md:113`); the build's commit is Step 2 item 6 (`skills/mf-build/SKILL.md:156`).
- `conduct.py` keeps per-primary state in `~/.mf-ship-origin/` (`KEPT_ORIGINS`, `:71`; `_kept_file` `:833`; `_digest` `:842`);
  its commands are `main`'s subparsers (`:2544-2570`), `grant` among them (`:2384`). `skills/mf-ship/SKILL.md:30-36` lists the
  forms the person types.
- Three trips: isekai `0088` (a `setup` target), gpunit `0017` (the gate's `pytest` deselects `e2e`), isekai `0093` (`LOOPBACK`
  and its `--deselect` go). Each task described the edit in prose; each recovery rewrote the cut commit.
- `0055·R3`: `skills/mf-build/SKILL.md:105`'s row "the tree is dirty, and `tasks.md` is tracked" also matches a ticked tree.
- `grill` as a station: `skills/mf-release/SKILL.md:286`, `README.md:13`, `docs/README.md:7`, `docs/decisions.md:11`.

## Goals / Non-Goals

**Goals:** a cut cannot write a gate task the check will not read; a bad quote halts at its phase; a person's approval of the exact
diff passes with no rewrite; a branch still cannot approve itself.

**Non-Goals:** a recording `SHELL` (`0034·R9`); the gate check's reach past makefiles and dry runs.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | One halt lists every unquoted line, the rule, the cut commit and the way out | the report: the first halt named a file and hid the second requirement | two halts in turn |
| [D2](#d2) | `I18`, and `gate_check.py --tasks` run by the cut | the approval is the person's, at the cut, in a form the check reads | a rule in prose alone |
| [D3](#d3) | The build runs the check on the staged tree before every phase's tick | a bad quote costs a phase, not the build; a halt leaves the box unticked | a check after the commit · after the tick · on `Makefile` and `*.mk` names alone |
| [D4](#d4) | `approve-gate`: the hash a halt names, in the home folder | no worker writes there; a later edit or a moved line changes the hash; the conductor runs no worker's makefile | an approval on the branch · a conductor that runs the check |
| [D5](#d5) | The record and the ride-alongs | `0055·R3`'s trigger fires; the release names a station that is gone | — |

### D1

`check` computes the edits and the dropped dry-run lines before it looks for a planning task, and one halt prints them all:

```
gate: halt — the branch changes the gate, and no cut task quotes these lines:
  added: Makefile: setup:
  removed: Makefile: .PHONY: gate browsers drift derive
The dry run is unchanged. A planning task names `Makefile` and `gate` in backticks and quotes each line, in the
cut commit <sha>. A person approves this diff with /mf-ship approve-gate <change-id> <hash>.
```

"The dry run is unchanged" becomes "The dry run changed" with the diff below it when it did. With a planning task, the same list
reads "no cut task quotes" for its unquoted lines. With none, the list also holds each line the head's dry run adds,
`added to the dry run: <line>`, then each touched makefile, `changed: <name>`, else `changed: the dry run`: a change with no
plan never passes as planned.

### D2

`I18` joins both input-contract tables, word for word: "name `` `gate` `` in a sub-task that names `Makefile`, or a gate
makefile ending `.mk`, and quote in a fenced `diff` block each line it adds or removes, no blank line inside the block". Its
check column: "`gate_check.py --tasks openspec/changes/<change-id>/tasks.md` exits 0".

`gate_check.py --tasks <path>` reads the file alone, no git: each sub-task, its wrapped lines joined as `planning_tasks` joins
them, that names `` `Makefile` `` or a `` `*.mk` `` file must name `` `gate` `` and hold a line `` ```diff `` and at least one line
starting `+ ` or `- `; else exit 1, naming the sub-task. The cut's Step 8 runs it. A wrapped line is a sub-task's only while it
is indented and not blank, so a blank line inside the block ends the task, as today.

### D3

`gate_check.py` gains `--head <tree-ish>`, `HEAD` by default; `read_side` exports it as it exports `HEAD`. `mf-build` Step 2
item 5, every phase, before it ticks the box: stage the phase's paths by name, run `git write-tree`, then
`uv run --script <mf-converge's package>/scripts/gate_check.py --change <change-id> --base <merge-base> --head <the tree>`.
Exit 1 → **halt**, ticking and committing nothing, copying the halt. Exit 2 → **halt**, naming the side. Every phase, since a gate
makefile is whatever make reads, a `GNUmakefile` or an included `rules.inc` among them; a phase that moves none prints
`gate: no unplanned change`. Before the tick, so a halt leaves the box unticked and the start table's dirty-tree row continues the
phase.

### D4

The hash of what the check reads is sha256 over each affected gate makefile's unified diff, its raw lines with their line
numbers, then the dry runs' diff: a line moved or re-indented after the approval changes it, where the stripped edits stay
equal. Each halt names it in its way out, `/mf-ship approve-gate <change-id> <hash>`, so the diff a person reads and the hash
come from one run; `gate_check.py --digest` prints it alone. `check` passes, "gate: approved — <hash>", when
`~/.mf-ship-origin/<digest>.gate/<change-id>` holds that hash, `<digest>` the primary's, computed as `conduct.py`'s `_digest`
does. A test holds the two computations equal.

`conduct.py approve-gate <change-id> --yes <hash>`: from the primary, refuses a `<hash>` that is not 64 hex digits, else writes
the file `0o600`, its folder `0o700`. It runs no make, and no check: it runs outside the sandbox, to write the home folder, and
`make -n` on a branch still runs the `$(shell …)` a worker wrote. The check runs where make already runs, in converge's and the
build's own workers, inside their sandbox; a hash no later check computes approves nothing, so a stale or mistyped one fails
closed. A build's halt on its staged tree names that tree's hash, which its commit keeps. Run under the sandbox, the write fails,
and the command says so. `skills/mf-ship/SKILL.md`'s parameters gain the row "`approve-gate <change-id> <hash>` | the person's
yes to the gate check's halt that named `<hash>` … `conduct.py approve-gate <change-id> --yes <hash>`". Converge's
precondition 6 and the release's text name the approval.

### D5

- `skills/mf-build/SKILL.md:105`'s row → "the tree is dirty, `tasks.md` is tracked, and a `## Progress` box is unticked"
  (`0055·R3`).
- `skills/mf-release/SKILL.md:286` → "The last line, after a merge: `Next: /mf-plan <the next version>.`, or
  `Next: cd <primary> && /mf-plan <the next version>.`".
- `grill` → `plan` in the station diagrams at `README.md:13`, `docs/README.md:7`, `docs/decisions.md:11`; "grill" as `mf-plan`'s
  verb stays.

## Tests

Counted at `22c1af8`: `uv run pytest --collect-only -q | tail -1` prints `102 tests collected`; `grep -c '^def test_'
tests/test_gate_check.py` prints `13`. All unit or integration; none end-to-end.

| test | change | holds |
|---|---|---|
| `test_a_halt_lists_every_unquoted_line` | added, `tests/test_gate_check.py` | D1: no planning task, a `setup` target and a `.PHONY` edit: one halt names both lines, the cut commit and `approve-gate` |
| `test_a_bare_makefile_task_fails_the_plan_check` | added, `tests/test_gate_check.py` | D2: `--tasks` exits 1 on gpunit `0017`'s original task 1.6, and 0 on the same task with its `diff` block |
| `test_a_staged_tree_is_checked` | added, `tests/test_gate_check.py` | D3: `--head <tree>` halts on an unquoted staged line, passes a quoted one |
| `test_an_approval_passes_until_the_diff_moves` | added, `tests/test_gate_check.py` | D4: an approval of the hash passes; the halt names the hash; one more edit halts; a line moved after the approval halts; an approval written in the repository approves nothing |
| `test_approve_gate_records_the_hash` | added, `tests/test_conduct.py` | D4: `approve-gate --yes <hash>` writes the hash the halt names and runs none of the branch's makefile; a malformed hash refuses; the digest equals `gate_check.py`'s; a staged tree's hash approves that tree |
| `test_an_include_changed_on_the_branch_halts` | extended, `tests/test_gate_check.py` | D1: with no planning task, a dry run that only gains a line halts, naming it |
| `tests/test_skills.py` | unchanged | `I18` in both contract tables keeps the id sets equal |

None is deleted or merged. Each guard's twin is in its own test, per `T6`.

## Dependencies

None.

## Risks / Trade-offs

- **A cut that mentions `Makefile` without changing it** fails `--tasks`; it rephrases, "the gate recipe stays".
- **The approval reads the home folder** from a converge worker's sandbox, which denies only `SECRETS`; a reading Codex worker
  sees it too, and can write none.
- **Two `_digest`s** in two scripts; the test holds them equal.
- **The person reads a halt a worker relayed.** The check that names the hash runs inside a worker's sandbox, and a hostile worker
  can report a benign diff beside another diff's hash, as a hostile makefile can already rewrite what the check reads. That is
  the threat model's accepted class, a worker steering through what it writes; D51's threat is a confused agent, and a hostile
  repo needs a container. In exchange, the unsandboxed conductor runs no worker's code.
- **A check before every phase** costs each phase two exports and two dry runs.

## Verdict

Ready to build.
