# Paydown — design

Twelve small cards fixed where they stand, four settled ones closed. Verdict at the end: ready to build.

## Context

Read at `1df4e7a` (v0.59.0). `conduct.py` is `skills/mf-ship/scripts/conduct.py`; `0071-ship-fixes` builds beside this, in other
functions of the same file, so the build re-reads lines by symbol.

- **F1. The probe:** `check_probe` returns `None` on `.gated` before it reads `.arch`, and reads `.arch` with `read_text()`, through a
  link, whole, and logs it (`conduct.py:1549-1570`).
- **F2. `remove_tree`:** compares `tree.resolve()` with `(self.worktrees / change).resolve()`, so a link at the cut's path passes, and
  runs git with no config refusal first (`conduct.py:2698-2725`). `_refuse_config_commands(cwd)` raises `Stop` (`:910`);
  `_config_changed(primary, state)` returns one (`:676`), against `self.git_state` (`:2340`). Its test steps sit in
  `test_a_ready_version_ships_past_a_slow_one` (`tests/test_conduct.py:555`, the `0004-listed` step `:631-654`).
- **F3. The stop order:** `stop_run` kills the conductor, `_clear`s the groups and the claim, then writes the line
  (`conduct.py` `stop_run`, `0051-reliability-paydown` design D5); the spec says the claim goes last
  (`openspec/specs/sdd/spec.md:1594`).
- **F4. The gate record:** `write_record` refuses a linked `.minions/gate` and a linked staged record
  (`skills/mf-converge/scripts/gate_run.py:97-99`); the spec says "no record SHALL be written through a link"
  (`openspec/specs/sdd/spec.md:15`).
- **F5. Docs:** `docs/principles.md:159` "`CI none`" only; `THREAT_MODEL.md:114-115` names a bare install, not a run's end, which
  `pin.py`'s `move()` also does.
- **F6. Integrate's wording:** Step 3 item 3's **additive** (`skills/mf-integrate/SKILL.md:102-104`) and item 4's cases (`:110`);
  the note-halt line (`:138`); the close-out's cut-only clause (`:182`); `next_version`'s docstring
  (`skills/mf-integrate/scripts/integrate.py` `next_version`).
- **F7. Settled cards:** `0063·R13` — the `run · live` row names the models-file exception; `0063·S5` — `_entries` opens with
  `O_NOFOLLOW` and `dir_fd`; `0064·S3` wontfix; `0060·R8` edits an archived proposal, past its trigger. `THREAT_MODEL.md`'s Known
  gaps (`:74`, `:79`, `:80`, `:99`) names `0049·S7`, `0049·R15`, `0050·R11` and `0052·S15` by id as carded and accepted: they stay
  while the threat model cites them.

## Goals / Non-Goals

**Goals:** the twelve cards fixed; the four closed; the backlog near its line.

**Non-Goals:** any card that needs a decision or a design.

## Decisions

| id | decision | cards | rejected |
|---|---|---|---|
| [D1](#d1) | `.arch` read right after the mark check, never through a link, 64 bytes at most, named only when it reads as an architecture | `0057·R6`, `0057·S1` | — |
| [D2](#d2) | `remove_tree` refuses a changed config and a link at the cut's path before git | `0057·S2`, `0057·S3`, `0057·R7` | — |
| [D3](#d3) | The spec says what the code does: the stop order, a linked record | `0051·R9`, `0064·R8` | splitting `_clear`; refusing a linked `.minions` |
| [D4](#d4) | The principles and the threat model say what the code does | `0057·R5`, `0068·S4` | — |
| [D5](#d5) | Integrate's wording: additive, the note-halt line, cut-only | `0061·R5`, `0061·R7`, `0063·R12` | — |
| [D6](#d6) | The settled cards close in `backlog:` with no code | F7's | — |

### D1

In `check_probe`, after the mark check: `arch = scratch / ".arch"`; when `arch.is_file()` and not `arch.is_symlink()`, open it with
`O_NOFOLLOW`, read its first 64 bytes, decoded with `errors="replace"` and stripped; the shell differs from `_native()` → fail `"<executor>'s shell runs as <shell> on a <native> host"` when the text matches
`[A-Za-z0-9_]{1,16}` and the file has one link (`st_nlink == 1`), else `"<executor>'s shell runs an unreadable .arch on a <native> host"`; a `.arch` that is a link fails as
unreadable. Then `probe.txt`, then `.gated`, as now. The test calls `conduct["check_probe"]` on a scratch folder holding `.gated`
and `.arch`, with no git: `.arch` is read before `probe.txt`.

### D2

At the top of `remove_tree`, after `tree is None`: `_refuse_config_commands(tree)` raising `Stop`, or `_config_changed(self.primary,
self.git_state)` returning one, → log `kept — <tree>: <the stop's text>` and return; `(self.worktrees / change).is_symlink()` →
`kept — <tree>: a link at the cut's path`; the path check compares `tree` with `self.worktrees.resolve() / change`, resolving no
last part. The delta's *A released worktree* scenario names both kept cases.

### D3

The delta: *A person can stop a run* reads "the conductor, then each worker group in the claim and the claim, then a `halt —
stopped by the person` line"; *The skills run the repository's `make gate`* reads "no record SHALL be written through a linked
`.minions/gate` or staged record".

### D4

`docs/principles.md:159` reads "…the line says `CI none`; under `mf-ship`, `CI not read under mf-ship`." `THREAT_MODEL.md:114-115`
reads "…and a later bare install or a run's end that moves to that tag links it as it stands; …".

### D5

Item 3's definition ends "…and changes nothing else, and is none of item 4's cases." The note-halt line reads "`Next: resolve or
accept the note in <worktree>, git add the paths; a union you change: edit or drop its ### <path> in
.minions/integrate/<change-id>.resolved, then /mf-integrate <change-id>`". The close-out reads "a cut-only branch merged before
its build, or a started one behind a gate change, ends `Next: /mf-ship, in the primary.`", its lead "A version with an unticked
phase," kept; `next_version`'s docstring reads "…a cut-only branch's — a dependent's, or one the default branch passed before its
first worker — before its build, or a started one's behind a gate change, opens with its note."

### D6

`proposal.md`'s `backlog:` lists the four with the twelve; `mf-release` deletes them.

## Tests

`git grep -c '^def test_' 1df4e7a -- tests/test_conduct.py` counts the file at the cut. Extended, under `T2`:

| test | gains |
|---|---|
| `test_a_probe_halts_on_a_write_out` | a direct `check_probe` call: a `.gated` beside a mismatched `.arch` fails; a `.arch` that is a link fails as unreadable |
| `test_a_ready_version_ships_past_a_slow_one` | `remove_tree` keeps a tree behind a link at the cut's path, keeps one when the config refuses, and keeps one git refuses to remove, its untracked file kept |

None added or deleted.

## Dependencies

None.

## Risks / Trade-offs

- **A link at the cut's path kept:** the person removes it by hand; the branch is released already.

## Verdict

Ready to build.
