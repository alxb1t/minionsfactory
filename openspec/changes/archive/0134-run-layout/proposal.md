---
bump: minor
version: 0.106
beside: [0133-host-free-tests]
---

# Run layout

One module, `skills/mflib/layout.py`, knows the run directory's paths that a second script spells, and the old-layout table is one.

Reading map: [design](design.md) holds the module's surface, the one old-layout table and the sixth structure rule, [tasks](tasks.md) holds its phases: pin, module, conductor, stations, old layout, rule and record.

## Why

Each script that reads `.minions/` finds the primary checkout with a git call of its own and joins `.minions` in a finder of its own. Several define `_change_dir`, and several hold an old-layout table. The tables disagree: a change folder's old `review.md` and `security.md`, and an old worker log, halt some stations and not others.

A new state path is one more copy, and no gate stops it. This version puts the paths in the shared home, `skills/mflib/`, that [0128-platform-port](../archive/0128-platform-port/proposal.md) created. A sixth structure rule then holds them there.

## What Changes

- `skills/mflib/layout.py` is born: the primary from git's answer, the run directory, the change folder, the generic entries a second script spells, and the old-layout table with its reader.
- The conductor, each station, the readers and the metric scripts take the path from the module. Each keeps its git call, its guard and its error text. No assert of a test changes in a move phase.
- The old layout is one table. Each station and `scripts/metrics/run.py` halts on it, naming the same file. This is the one behaviour change: a change folder's old role names and an old worker log halt the stations that did not read them.
- A sixth structure rule: no string constant equal to `.minions` or `.mf-ship-origin`, or starting `.minions/`, outside `layout.py`, save the sites a list names. The seed rule also holds `scripts/`.
- The record agrees: D57 and D83 amended, the state-file recipe, the threat model's surface sentence, the old-layout lists of the skills, and the requirements below.

Requirements the delta touches, one line each:

- MODIFIED *Every worktree shares the primary's run directory*: the finder is the home's `change_dir`, and the old layout is one table.
- MODIFIED *A run moves the old findings files to the checkers' names*: `run.py` halts on the old names, as every station does.
- MODIFIED *The gate holds the structure rules*: a sixth rule, and the seed's second form for `scripts/`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`: the run directory's finder and old-layout halts, the old findings names, and the structure rules.

## Impact

- New: `skills/mflib/layout.py`, `tests/test_layout.py`, `tests/old_layout.py`, `tests/test_run_dir_finders.py`.
- Edited: the scripts named in [tasks](tasks.md), among them `scripts/corpus.py`, `scripts/metrics/run.py` and `scripts/metrics/debt.py`, which gain the seed.
- Edited, tests: `tests/test_structure.py`, `tests/test_conduct.py`, `tests/test_converge.py`, `tests/test_gate_check.py`, `tests/test_integrate.py`, `tests/test_metric_scripts.py` and `tests/test_viewer.py`; `tests/fake_worker.py` is read, not edited.
- Edited, record: `docs/modules.md`, `docs/decisions.md`, `docs/recipes.md`, `THREAT_MODEL.md`, and the old-layout paragraphs of `skills/mf-build/SKILL.md`, `skills/mf-integrate/SKILL.md` and `skills/mf-release/SKILL.md`.
- No dependency, no station, no parameter. The pin carries the new file with the rest of `skills/`.

## Not in this change

- A shared finder that runs git: the git runner's version.
- The skills' prose paths and the content of a state file (the status log, the queue entry, the claim): later versions of the series.
- `~/.mf-ship-origin` and the home folder's paths: `home-layout`, the next version.
- The differences [D4](design.md#d4) names stay as they are: the metrics page and the viewer take a repo as named, with no git; the finders' different guards; `CLAUDE_CONFIG_DIR` moves the settings and not the skills links; `~/.mf-ship-origin` stays outside XDG.
- G2, G3, G4 — the viewer's own structure: `ui · scaffold`.
- The Linux runner, E2's probes, the cloud facts' behaviour: Linux ready.
- H4's shipped run-data model: the metrics timeline.
- A third executor, Linear + Forgejo, and any second git host.
- H5, the bootstrap template's `Worktrees:` line: a bootstrap question of its own.
- Converge's read of an old `backlog.md` stays as it is, and is pinned.
- Debt cards `0109·S1` and `0119·S1`: converge re-points them where it reads the diff; this change edits no card.
