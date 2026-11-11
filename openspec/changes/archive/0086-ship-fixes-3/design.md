# Ship fixes 3 — design

A planned decision id renumbered when the default branch takes it, an insert-only delta kept, and git's own error named.
Verdict at the end: ready to build.

## Context

Read at `5650ab1` (v0.70.0), the brief's own `At` commit: every fact it cites stands. `I` is
`skills/mf-integrate/scripts/integrate.py`, `G` is `skills/mf-converge/scripts/gate_check.py`, `C` is
`skills/mf-ship/scripts/conduct.py`. See [the proposal](proposal.md#why) for what the runs hit.

- **F1. The decision rule.** `decisions` (`I:525-549`) counts as new only the `### D<n> ` headings (`DECISION`, `I:35`) the
  branch added (`I:533`), renumbers them past the default branch's highest when the lowest collides (`I:535-536`), and recites
  every path of `base..HEAD` (`I:544-546`). `G`'s `renumbered` (`G:242-260`) copies the rule for `check_verify` (`G:279`).
- **F2. Where the rule runs.** `mf-integrate` Step 3.2 runs it on every merge (`skills/mf-integrate/SKILL.md:104-111`). `C`'s
  `merge_in` (`C:3472-3500`) calls `settle` (`C:3502-3528`) only when git's merge fails, and `settle` runs a rule only on a
  path git left in conflict (`C:3515-3516`). `replay` does the same (`I:644-647`): `0064·R6`.
- **F3. The 0085 case.** `0085-self-healing-ship`'s plan cited `**D59 · A run heals its own halts**` and
  `grep -n '^### D59 · A run heals its own halts'` with no heading on the branch; `0083-plan-queues` built
  `### D59 · A hard plan closes on a checked brief, …`. `C`'s merge was clean in `docs/decisions.md`: no rule ran.
- **F4. The delta rule.** `delta` (`I:576-600`) flags each MODIFIED or REMOVED title whose living block differs between the base
  and `MERGE_HEAD` (`I:594`); it never reads the delta's own block. `TOKEN` (`I:39`) and `_changes` (`I:380`) exist. `replay`
  (`I:648-655`) and `C`'s `_delta` (`C:957-968`) read it.
- **F5. Git's error.** `primary_of` (`C:340-357`) reads `_common_dir` (`C:334-337`), which drops git's stderr through `_maybe`,
  and stops with "not in a git repository" on any failure (`C:348`); `awake.py`'s `_record`
  (`skills/mf-cut-change/scripts/awake.py:46`) and `I`'s `_tree` (`I:291-297`) do the same. Under an Intel Python, `/usr/bin/git`
  exits 1 with `missing compatible architecture (have 'arm64,arm64e', need 'x86_64')`.

## Goals / Non-Goals

**Goals:** a version whose planned id the default branch took builds with no person; a delta already holding the default branch's
change merges with no note; a git that cannot run says why.

**Non-Goals:** a rescue row for a taken id (`skills/mf-rescue/SKILL.md`) — the merge settles it; the `changelog` rule on a clean
merge — a clean `CHANGELOG.md` needs no renumber; `0034·R9` ([D5](#d5)).

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | A **planned decision** is an id the plan cites with its title, above the base's highest, headed nowhere on the branch; a heading on the default branch carrying that title is a dependency's | Q2 | an id cited with no title; reserving the id at the cut |
| [D2](#d2) | `G`'s `renumbered` copies D1's rule, read from the merge's first parent | Q2 | importing `I` into `G` |
| [D3](#d3) | `C` and `replay` run `decisions` on every merge, conflicted or clean | Q2, `0064·R6`, C4 | the rule on a conflict only |
| [D4](#d4) | A MODIFIED delta whose block only inserts into the default branch's current block, and keeps nothing the default branch removed, is kept | Q3, C3 | a three-way token merge of the blocks; insertions measured against the default branch's block alone |
| [D5](#d5) | `0034·R9` stays carded | C2 | its card's fix, a design change, in this patch |
| [D6](#d6) | Git's own first stderr line, and `uv run --script`, on any failure but "not a git repository" | Q4 | a check of the interpreter's architecture |
| [D7](#d7) | D45 amended; `mf-integrate`'s rule rows | Q2, Q3 | — |

### D1

In `I`, beside `DECISION`:

- `TITLED = re.compile(r"^### D(\d+) · (.+)$", re.MULTILINE)` — a decision heading with its title.
- ``PLANNED = re.compile(r"\bD(\d+) · ([^*`'\"|\n]+)")`` — a citation with its title, which runs to the first `*`, backtick,
  quote, `|` or line end.
- `_planned(plan: list[str], base: str, ours: str, theirs: str) -> set[int]` — the planned ids: each `PLANNED` match in `plan`,
  its title cut by `.strip(" .,;:")` at both ends, an empty title dropped; kept when its id is above `max(_ids(base), default=0)`,
  not in `_ids(ours)`, and no title of it **matches** the `TITLED` title of that id in `theirs`, cut the same way. A title matches
  another when one starts with the other: a grep needle cuts a title short.

```
  plan cites "D59 · Branch rule"   base top D58   branch heads no D59
      │
      ├── theirs heads "D59 · Branch rule…" ──▶ a dependency's: stays
      └── theirs heads "D59 · Main rule" ─────▶ planned: new = [59] ≤ top 59 ──▶ D59 → D60
```

`decisions` reads `plan` from each path `git diff --name-only <base> HEAD -- openspec/changes` prints outside
`openspec/changes/archive/`, by `_show(tree, "HEAD", path)`, a path `HEAD` lacks skipped, and sets
`new = sorted((_ids(ours) - _ids(base_text)) | planned)`. When git merged `docs/decisions.md` with no conflict and no id moves,
`decisions` returns `decisions: no id collides` before it writes, so git's clean result stands. The renumbering, `_recite` and
`_renumber_changelog` are unchanged: the plan's files are in `base..HEAD`, so `_recite` moves every citation of a moved id there.

### D2

`G` gains `_ids`, `TITLED`, `PLANNED` and `_planned` under its "`integrate.py`'s" comment (`G:46`), copied as they stand in `I`.
`renumbered(merge)` reads `plan` from each path `_git("diff", "--name-only", base, ours, "--", "openspec/changes")` prints outside
`openspec/changes/archive/`, by `_show(ours, path)`, and takes `new` as [D1](#d1) does. Its docstring example gains the planned
case: base D58, ours plans `D59 · x`, theirs heads `D59 · y` → `{59: 60}`.

### D3

- **`C`.** `merge_in` calls `settle` on each merge it opens itself, failed or clean:
  `if not opened and (_maybe(tree, *merge) is None or _merge_open(tree))`. `settle` runs the `CHANGELOG.md` rule on a conflicted
  `CHANGELOG.md` and the `docs/decisions.md` rule on every merge, in `self.rules`' order; its halt names `left or first`; a clean merge whose `decisions` rule halts names that halt and `git -C <tree> merge --no-ff --no-commit <default>`. Its docstring says so. A merge already open stays unsettled, as today.
- **C4, decided by the cutter.** A merge a dead run left open is not settled again: `_renumber_changelog` reads its own earlier
  output, so a second `decisions` chains a move (`{59: 61, 61: 62}`) twice in `CHANGELOG.md`. A planned id missed there halts the
  build's own `Verify:`, as today.
- **`replay`.** It reads `_unmerged(scratch)` once, after git's merge and before any rule. It runs `changelog` when that set holds
  `CHANGELOG.md`, then `decisions` on every merge. Its line names `CHANGELOG.md` when the set holds it, and `docs/decisions.md`
  when the set holds it or `decisions` printed `decisions: renumbered`. This closes `0064·R6`.

### D4

`I` gains `_inserts_only(base: str, main: str, side: str | None) -> bool`, over each text's non-whitespace `TOKEN`s. It is true
when `side` is not None, every edit of `_changes(main, side)` is an insertion (`start == end`), and every base token an edit of
`_changes(base, main)` covers is covered by an edit of `_changes(base, side)` too: the delta keeps nothing the default branch
removed. `delta` keeps its loop over `_requirements(spec, EDITED)`, and skips a title whose living block changed when the title is
under `## MODIFIED Requirements` alone, the default branch still holds it, and
`_inserts_only(<the base's block, or "">, <the default branch's block>, _requirement(<the delta>, title))`. Every other changed
title is reported as today. `replay` and `C`'s `merge_in` read `delta`, so they follow with no edit.

```
  base: "It SHALL hold."           default branch: "It SHALL hold. It SHALL log."
  delta: "It SHALL hold, always. It SHALL log."   ──▶ insertions only: kept
  delta: "It SHALL hold, always."                 ──▶ drops "It SHALL log.": reported

  base: "It SHALL hold. It SHALL log."   default branch: "It SHALL hold."
  delta: "It SHALL hold, always. It SHALL log."   ──▶ keeps what the default branch removed: reported
```

C3, decided by the cutter: Q3's rule measured insertions against the default branch's block alone. The plan review showed such a
delta can restore a sentence the default branch deleted, silently, at the archive. The base-token guard reports it.

### D5

C2, decided by the cutter: Q6 lists `0034·R9` in `debt:`, but no phase or acceptance line of the brief builds it, and its card's
fix — the gate run in each export under a recording `SHELL` — is a design change no decision settles. A patch building an unsettled
design breaks the principle *Decisions are made before the cut*. The card stays open in `.minions/debt.md`, and `THREAT_MODEL.md`
keeps it among the known gaps.

### D6

- **`C`.** `primary_of` runs `_run(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir")` itself. A failure whose stderr
  holds `not a git repository` stops as today; any other stops with exit 2 and
  `conduct: cannot run — git rev-parse failed: <git's first non-blank stderr line>; run it as uv run --script <path>`, `<path>`
  being `Path(__file__)`. `_common_dir` stays for its other callers.
- **`awake.py`.** `_record` reads the same: `not a git repository` keeps its line; any other failure prints
  `awake: cannot run — git rev-parse failed: <line>; run it as uv run --script <path>`.
- **`I`.** `_tree` runs `_run(tree, "rev-parse", "--show-toplevel")`. A failure whose stderr holds `not a git repository` stops
  with `is not a worktree root`, as today; any other with `integrate: cannot run — git rev-parse failed: <line>; run it as uv run
  --script <path>`.

A stderr with no non-blank line names `exit <code>`, as each script's `_git` does.

### D7

- **`docs/decisions.md` D45** — "applies fixed rules to the CHANGELOG, decision ids and spec delta" → "applies fixed rules to the
  CHANGELOG, decision ids — the plan's planned ones too — and spec delta"; "It settles a conflict in `CHANGELOG.md` or
  `docs/decisions.md` by `integrate.py`'s rules and halts on any other, runs" → "It settles a conflict in `CHANGELOG.md` or
  `docs/decisions.md` by `integrate.py`'s rules, runs the `decisions` rule on every merge, halts on any other conflict, runs".
- **`skills/mf-integrate/SKILL.md`** — the `decisions` row (`:110`) gains "; a decision the plan cites as `D<n> · <title>`, above
  the base's highest and headed nowhere on the branch, counts as new, unless the default branch's heading of that id carries the
  title"; the `delta` row (`:111`) gains ", save a MODIFIED one whose delta only inserts into the default branch's block and keeps nothing
  it removed".

## Tests

`git grep -c '^def test_' -- tests/` totals 235 at the cut. Added: 5, each an integration test on real git in a scratch repository,
none `slow`. No end-to-end test.

- `test_decisions_renumbers_a_planned_id_the_default_branch_took` (`tests/test_integrate.py`, new) — base `### D58 · Base`; the
  versions `0002-b`, `0003-c` and `0004-d` cut from it — `0002-b`, whose `design.md` cites `**D59 · Branch rule**` and `per D59`, and whose `tasks.md` cites
  `grep -n '^### D59 · Branch rule' docs/decisions.md`; `0003-c`, citing `D59 · Main rule`; `0004-d`, citing `per D59` alone. Main
  then heads `### D59 · Main rule`. Each merge of `main` is clean. `decisions` on `0002-b` prints
  `decisions: renumbered D59 → D60, citations with them` and both files cite `D60` alone; committed, `replay HEAD` prints
  `replay: by rule — docs/decisions.md`, and `G`'s `renumbered` of the merge, loaded with `runpy`, returns `{59: 60}`. `decisions`
  on `0003-c` and on `0004-d` prints `decisions: no id collides`, their files unchanged.
- `test_delta_keeps_a_delta_that_only_inserts` (`tests/test_integrate.py`, new) — main changes requirement `First`; a delta whose
  `First` block is main's with a sentence added and a line rewrapped exits 0; one rewriting a word of main's block exits 1 naming
  `sdd: First`; a REMOVED `First` exits 1 naming it. Then main drops a sentence of `Second` that the base held: a delta keeping it
  and adding a clause exits 1 naming `sdd: Second`.
- `test_a_git_failure_names_its_line` (`tests/test_integrate.py`, new) — a fake `git` first on `PATH`, printing the architecture
  error of F5 to stderr and exiting 1: `delta <tree>` exits 2 with `integrate: cannot run — git rev-parse failed: <that line>; run it
  as uv run --script <the script>`; with the real `git`, a folder outside any repository still prints `is not a worktree root`.
- `test_a_merge_in_renumbers_a_planned_decision` (`tests/test_conduct.py`, new) — `Run.merge_in`, called as
  `test_a_merge_in_refuses_a_planted_hook` calls it, on a cut-only `0002-marks` whose plan cites `D59 · Marks rule` while main heads
  `### D59 · Main rule`: the merge commits as `chore(integrate): merge main into 0002-marks`, and the plan cites `D60`. A further step:
  the `decisions` rule halting on a clean merge, the halt naming `git -C <tree> merge --no-ff --no-commit <default>`.
- `test_a_git_failure_names_its_line_and_uv` (`tests/test_conduct.py`, new) — the fake `git`: `status` exits 2 with
  `conduct: cannot run — git rev-parse failed: <that line>; run it as uv run --script <the script>`; the real `git` outside any
  repository, `GIT_CEILING_DIRECTORIES` set, still prints `conduct: cannot run — not in a git repository`.

Extended or edited:

- `test_stop_kills_only_a_recorded_caffeinate` (`tests/test_awake.py:187`) — a last step, after its subprocess step
  (`tests/test_awake.py:223-230`): the fake `git` first on `PATH`, `stop` exits 2 with
  `awake: cannot run — git rev-parse failed: <that line>; run it as uv run --script <the script>`.
- `test_a_crashed_integrate_script_halts_and_a_rerun_merges` (`tests/test_conduct.py:908`) — its `crash.py` keeps `delta` and
  `changelog` crashing and defines `decisions` returning `decisions: none`: [D3](#d3) runs `decisions` on its clean merge, and the
  test holds a crashed `delta`.

No test is deleted or merged.

## Dependencies

None.

## Risks / Trade-offs

- A dependency's id cited with a title that differs from its heading's is renumbered → the build's own `Verify:` on that heading
  halts, as today's miss does; the plan names a dependency's decision by its heading.
- `decisions` on a clean merge whose ids move rewrites `docs/decisions.md` with `merge3`, whose diff is not git's → it can halt
  `both sides changed`, or a `_recite` can halt on ambiguous ownership, where git merged cleanly; either halts for the person, as
  on a conflict. A clean merge with no move writes nothing ([D1](#d1)).
- An Intel Python still cannot run git → the line names the fix; the scripts do not pick an interpreter.

## Verdict

Ready to build.
