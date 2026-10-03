---
version: v0.22
backlog: [0020·N1, 0020·N3, 0021·N1]
---

# 0022-runner-retires — proposal

**In one line:** the deprecated deterministic runner is deleted — `orchestrator/`, `prompts/`, their tests, specs
and pages — and with it the spec↔test binding and the tests that assert an absence.

| read | for |
|---|---|
| this page | why, and what changes |
| [design.md](design.md) | the decisions (`R1`…`R11`), the measurements, every text before → after, the release's hand-edits |
| [tasks.md](tasks.md) | the build: the binding stops, the absence tests go, the text follows, the runner goes |
| [specs/](specs/) | the delta: the runner's capabilities removed; `sdd` loses its runner-held and absence requirements, and its keys |

## Why

The runner is deprecated and not extended: the `mf-*` skills are the one line (D3). It still holds most of the
repository's code, a capability of the living spec per module, and one live part — the spec↔test binding the gate runs.
That binding makes every spec carry keys only it reads, and no target repo can run it. The retired-word scans in
`tests/test_conventions.py` test a history, not the system.

## What Changes

```
Makefile                    the gate's binding line          DELETED   phase 1
tests/ markers              @pytest.mark.spec, spec_exempt   DELETED   phases 1, 4
docs/decisions.md           D36, D37                         NEW       phases 1, 2
tests/test_conventions.py   the absence scans                DELETED   phase 2
docs/principles.md          a Held by line, a principle      REWRITTEN phase 2
CLAUDE.md · README.md · docs/README.md · config.yaml · skill examples
                            the runner's mentions            DELETED   phase 3
orchestrator/ · prompts/ · docs/architecture.md · docs/modules/ · the runner's tests
                            the runner                       DELETED   phase 4, last
.env.example                the runner's scaffolding         DELETED   phase 4
pyproject.toml · uv.lock    pydantic, the marker registration DELETED  phase 4
```

- **The binding stops.** The gate drops `specs check`; the surviving tests drop their markers. See [R1](design.md#r1).
- **No test asserts an absence.** `tests/test_conventions.py` is deleted; *A retired word is retired everywhere*
  is held by the retiring change's acceptance and by review. See [R4](design.md#r4).
- **D36 and D37** enter `docs/decisions.md`. See [R5](design.md#r5).
- **The front door** stops naming the runner. Nothing is added in its place. See [R8](design.md#r8).
- **The runner is deleted**, last. See [R11](design.md#r11).
- **Pays down** `0020·N1`, `0020·N3` and `0021·N1`. See [R10](design.md#r10).
- **BREAKING:** `python -m orchestrator` no longer exists.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `build-loop`, `cli`, `converge`, `diff`, `fanout`, `gate`, `provider`, `release`, `status`: every requirement
  REMOVED. The emptied capability files are deleted by hand at the release ([R2](design.md#r2)).
- `sdd`: the requirements below.

| requirement | what changes |
|---|---|
| Enforced binding | REMOVED — the binding is deleted (D36) |
| Full backfill traceability | REMOVED — the markers are deleted (D36) |
| Reviewer conformance | REMOVED — `mf-converge` review holds it |
| Release fold | REMOVED — `mf-release` holds it |
| Change structure | REMOVED — the input contract `I1`…`I15` holds it |
| Repository is the source of truth for change progress | REMOVED — `mf-build` holds it; its scans go (D37) |
| Commit-to-change traceability | REMOVED — D21 keeps the trailer; nothing checks it |
| The retired gate config is named nowhere | REMOVED — no test asserts an absence (D37) |
| The backlog export is named nowhere | REMOVED — no test asserts an absence (D37) |
| The skills run the repository's `make gate` | MODIFIED — `Key:` and `Layers:` leave its scenario |
| The cut and the build share one input contract | MODIFIED — the same |
| A release may skip the check loop, and says so | MODIFIED — the same |
| The build and the cut share one list of prose rules | MODIFIED — the same |
| Converge keeps deferred work in one repository backlog | MODIFIED — the same |
| The release does not read the backlog | MODIFIED — the same |
| The card is defined in converge alone | MODIFIED — the same |
| The release ships only a reviewed head | MODIFIED — the same |
| Anchored harms block, and drift has its own tier | MODIFIED — the same |
| A repeated finding escalates | MODIFIED — the same |
| Review searches for stale claims | MODIFIED — the same |
| A fix's test fails without the fix | MODIFIED — the same |
| Converge keeps a status log | MODIFIED — the same |
| A skill infers the one active change | MODIFIED — the same |

## Impact

| area | files |
|---|---|
| the runner | `orchestrator/` · `prompts/` · `docs/architecture.md` · `docs/modules/` · the runner's tests, listed in [design.md](design.md#the-runners-tests) |
| tests | `tests/test_conventions.py` · `tests/test_skills.py` · `tests/test_principles.py` |
| docs | `docs/decisions.md` · `docs/principles.md` · `docs/README.md` |
| front door | `CLAUDE.md` · `README.md` · `Makefile` · `openspec/config.yaml` · `.env.example` |
| skills | `skills/mf-build/SKILL.md` · `skills/mf-cut-change/SKILL.md` |
| dependencies | `pydantic` removed; `uv.lock` re-locked |
| target repos | none |

## Not in this change

- **A trailer check in `mf-release`.** D21 stays a convention `mf-build` writes ([R3](design.md#r3)).
- **Any new scan**, for the runner's names or any other ([R4](design.md#r4)).
- **The `test_skills.py` needles** that guard a live rule against its opposite — they stay.
- **A README rewrite.** Only its runner section is deleted.
- **Renaming `sdd`**, or editing its Purpose in a phase — the Purpose is a release hand-edit ([R7](design.md#r7)).
- **`mf-converge`, `mf-release`**, `CHANGELOG.md`'s history and `openspec/changes/archive/`.
- **Card `0020·N2`** — this change does not open `skills/mf-converge/SKILL.md`.
