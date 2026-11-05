# Pinned release — design

`pin.py` makes the hand pinning of 2026-11-04 the install: one exported release per machine, both hosts linked to it, moved only
at a quiet moment. Verdict at the end: ready to build.

## Context

Read at `a3814cb` (v0.55.0). `conduct.py` is `skills/mf-ship/scripts/conduct.py`.

- **F1. The install** links each `skills/mf-*` into `$(SKILLS_DIR)`, default `~/.agents/skills`, refusing a non-link
  (`Makefile:29-59`); `uninstall-skills` removes links into this checkout (`:61-71`). No test runs either. README's relink step
  passes `SKILLS_DIR=$HOME/.claude/skills` (`README.md:103-104`); `AGENTS.md:36-39` names `make install-skills`.
- **F2. The hand pin** of 2026-11-04 and -05: `git archive <tag> skills | tar -x -C ~/.local/share/minionsfactory/<tag>/`, a `VERSION`
  file, every `mf-*` on both hosts re-linked — v0.51.0, v0.52.0, v0.54.0 and v0.55.0 stand there, the links on v0.55.0.
- **F3. The conductor:** `SKILLS` (`:74`), `KEPT_ORIGINS` (`:78`); `_kept_file`, `_digest`, `_kept_origin` (`:890-952`); `_scratch`
  (`:1115-1125`); `_outside` borrowing the primary's objects (`:1128-1152`); `_remote` (`:1223-1230`). `_unlinked` checks only that
  each link exists, message `… is not linked; make install-skills` (`:2026-2038`), called by `preconditions` (`:2068`) and the probe
  (`:2535`). `run()` writes the claim (`:2768-2775`) and removes it in `finally` (`:2786`). `ship()` builds the `start` line
  (`:2672-2688`) and returns at `:2693`, `:2700`, `:2707`, `:2735`, `:2738`; `run()`'s exception path skips them (`:2779-2781`).
- **F4. `mf_version`** runs `git ls-files` and `git describe` in its package, `unknown` outside a checkout
  (`skills/mf-build/scripts/metrics.py:248-270`).
- **F5. Tests:** `test_a_missing_skill_stops_a_run` links every `mf-*` into both `SKILLS` folders under a tmp `HOME`
  (`tests/test_conduct.py:3640-3683`); the autouse `isolated_home` puts `HOME` and `XDG_*` under `tmp_path`
  (`tests/conftest.py:11-27`).
- **F6. The record:** D52 the highest decision (`docs/decisions.md:54`); *The repo reaches nothing outside itself*'s exceptions
  (`docs/principles.md:136-151`); *Known gaps* (`THREAT_MODEL.md:61-99`). `0051·R10` still true at `:2037`.

## Goals / Non-Goals

**Goals:** a run never reads a skill its machine moved under it; MF's own runs on the pin too; the move automatic and quiet; the
hand pin's trees adopted as they stand.

**Non-Goals:** a pin per project; packaging; pruning; marks for stations run by hand.

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | `pin.py install [<tag>\|live]` — export, `VERSION`, both hosts, the hold, the source | Q3–Q6, Q12, Q13, Q18, Q21 | a Python package; `SKILLS_DIR` |
| [D2](#d2) | Live marks; an install under a live run writes `pending` | Q8, Q9, Q14 | a waiter process |
| [D3](#d3) | The quiet move at the last run's end and at an install with no run live, a tag `origin` holds, from a scratch clone | Q14 as amended at the cut, Q16, Q17, Q20, Q21 | a move at a run's start; an `After release:` command |
| [D4](#d4) | The `start` line names the release; `mf_version` reads `VERSION` | Q10 | — |
| [D5](#d5) | `_unlinked` checks one tree on both hosts; its remedy a bare install | Q6, Q11 | — |
| [D6](#d6) | The record: a new decision, the principle's exceptions, the threat model, README, `AGENTS.md`, `mf-ship` | Q7, Q15 | — |

### D1

`skills/mf-ship/scripts/pin.py`, a stdlib `uv run --script`, run from the checkout by `make install-skills` (`TAG ?=`); `install` takes
the checkout and its primary from the cwd's `git rev-parse --show-toplevel` and `--git-common-dir`, `move` from `source`. Tests and the
conductor load it with `runpy`, as the conductor loads `integrate.py`, so its lines are covered and no `uv` start is needed:

- the **data folder** is `$XDG_DATA_HOME/minionsfactory`, else `~/.local/share/minionsfactory`; a release is `<folder>/<tag>/skills/`
  with `<folder>/<tag>/VERSION` naming the tag; a tree that stands is kept, never rewritten.
- **bare:** the newest `v*` tag the kept `origin` lists — with no kept URL, `pin: cannot install — no run kept origin's URLs: run /mf-ship once, or make install-skills TAG=<tag>` — (`~/.mf-ship-origin/<digest>`, read as `_kept_origin` reads it), exported from
  a fresh scratch clone of that URL at that tag (`git clone --depth 1 --branch <tag>` into a temp folder, then its `skills/`); the hold
  `~/.mf-ship-origin/hold` cleared.
- **`<tag>`:** `git archive <tag> skills` from the checkout; the hold written with the tag. **`live`:** each link to the checkout's
  `skills/mf-*`; the hold written `live`, and `~/.mf-ship-origin/checkout` the checkout's path, which a pending `live` links.
- **the links:** every `mf-*` the tree holds, on `~/.claude/skills` and `~/.agents/skills`, by `os.symlink` to a temp name then
  `os.replace`; a destination that exists and is no link refused, untouched; a link whose skill the tree lacks removed.
- **the source:** `~/.mf-ship-origin/source` holds the checkout's primary path.
- **remote calls** run with `GIT_DIR` an empty bare repo in the conductor's `_scratch()`, as `_outside` does.
- `pin.py uninstall` removes each `mf-*` link on both hosts that points into the data folder or the checkout.

### D2

`run()` writes `~/.mf-ship-origin/live/<digest>` holding its pid first, from `primary_of(cwd)`, before `preconditions` — the detached
parent and its child each — and removes it in `finally`; a mark whose pid is
not alive is stale. `pin.py install` with a live mark standing exports the tree, writes `~/.mf-ship-origin/pending` naming it, moves
no link, and prints `pin: pending <tag> — a run is live`; `TAG=live` writes `pending: live`.

### D3

`pin.move()` runs at two quiet moments, and nowhere else: **at a run's end**, in `run()`'s claimed `try`'s `finally` (`:2773-2786`),
before its live mark and claim go, when no other live mark stands; and **at `pin.py install`**, when no live mark stands. It
re-reads the live marks just before it links, and moves nothing if one appeared. The person, 2026-11-05: no move at a run's start —
a conductor already loaded would read new skills with old code. A pending tag always moves, `live` among them; a hold stops only
the automatic check for a newer tag — the newest `v*` tag the source's kept `origin` lists when newer than the linked one —
exported from a scratch clone as in D1, then the links moved and `pending` removed. The source's newest local tag, when `origin`
does not hold it, is skipped and named. An `origin` that cannot be read moves nothing. Its remote calls take `GIT_TIMEOUT` and the
conductor's ssh options. It needs `source`; without it — every test's isolated `HOME` — nothing. After a reboot or a killed run, a
pending release waits for the next run's end or the person's next install.

### D4

`ship()`'s `start` line ends `· mf <tag>` from the linked tree's `VERSION`, `· mf live <describe>` when the links point at a checkout,
`· pending <tag>` while `pending` stands, and `· skipped <tag>: not on origin` for a tag the move skipped. `mf_version` reads
`Path(package).parents[2] / "VERSION"` — the tree's root, `<tag>/VERSION` — on its existing not-in-a-checkout path
(`metrics.py:260-261`, `:268-270`).

### D5

`_unlinked(executor)` also resolves every `mf-*` link on both hosts and stops when they name more than one tree, or a tree other
than the one beside its own `__file__`:
`run: cannot run — the mf-* links point into more than one tree: <names>; make install-skills`. Its existing message names a bare
`make install-skills`, which links both hosts (`0051·R10`).

### D6

A new decision — *One pinned MF release per machine* — D55 at the cut, renumbered by `integrate.py` if another lands first: the
tree, the hold, the quiet move, the scratch clone, Q15's gap. *The repo reaches nothing outside itself* lists the data folder and
`source`, `hold`, `pending`, `checkout`, `live/`. `THREAT_MODEL.md` *Known gaps*: a station by hand leaves no live mark; a `TAG=<tag>` install
trusts the checkout. README's install section — its "the `Makefile` records why a symlink" line (`README.md:38`) among it — and relink step, `AGENTS.md`'s
line and `skills/mf-ship/SKILL.md`'s preconditions name `make install-skills` as the pin.

## Tests

`git grep -c '^def test_' main -- tests/` totals the suite at the cut. Added, integration on a scratch `HOME`, an MF clone and a bare
`origin` (`T1`, `slow` above 5 s): `tests/test_pin.py` — a bare install from `origin`, `TAG=<tag>` and `live` holds, a refused
non-link, a pending write under a live mark, a stale mark ignored, a planted replace ref not reaching the export,
a repo planted above the scratch supplying no config, uninstall. In
`tests/test_conduct.py`: `test_a_run_marks_itself_live`, `test_the_last_run_moves_the_links`, a step in
`test_a_missing_skill_stops_a_run` for a mixed install. In `tests/test_metrics.py`: `mf_version` from `VERSION`. None deleted.

## Dependencies

None.

## Risks / Trade-offs

- **A hand session** leaves no live mark; the links can move under it — Q15's gap, stated in the decision.
- **The first bare install** needs `origin` reachable; offline it names the remedy, `TAG=<tag>`.
- **Every tree is kept:** about 400 KB a release.

## Verdict

Ready to build.
