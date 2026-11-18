---
bump: minor
---

# Home layout

One module names every path under the operator's home folder and the XDG roots, and the gate stops a script spelling one.

Reading map: [design](design.md) holds the module's surface, the moves and the rule, [tasks](tasks.md) holds the phases: the pin, the module, the conductor and the pin, the readers, the rule and the record.

## Why

The first half of the state layout, [0134-run-layout](../archive/0134-run-layout/proposal.md), gave `.minions` one module. The home half is still spelled by hand: `~/.mf-ship-origin` in the conductor, the pin and the readers, its digest in the conductor and in `gate_check.py`, the config, data and state roots wherever a file lives there, the Codex home and the list of repos in the conductor and a reader each. A copy that drifts is a path no test sees: the mutants of the home region left a case alive for each.

This version is the second of two on the state layout. It moves no behaviour: every path is the one a script computes today.

## What Changes

- `skills/mflib/layout.py` gains the home half: the kept folder and its digest, each name under it, the queue's sub-names, the gate approval, the live marks, `repos`, the probe's mark, the scratch folders' parent and prefix, the pin's files, the config files, the data and state roots, the skills links, the Codex home and the Claude settings home.
- `conduct.py`, `pin.py`, `gate_check.py`, `viewer.py` and `review_metrics.py` take each of those from the module. No script keeps a finder or a join for one.
- The sixth structure rule refuses, outside the module, a string constant that contains `.mf-ship-origin` or equals an XDG variable's name. Its list holds no such site.
- The principles' closed list names what the code reaches, and the record lines that say the run directory alone gain the home half.
- Requirement *The gate holds the structure rules*: its state-path rule gains the home folder's name and the XDG names; its scenarios gain one for each.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`: *The gate holds the structure rules*.

## Impact

- Code: `skills/mflib/layout.py`, `skills/mf-ship/scripts/conduct.py`, `skills/mf-ship/scripts/pin.py`, `skills/mf-converge/scripts/gate_check.py`, `skills/mf-ui/scripts/viewer.py`, `skills/mf-review-metrics/scripts/review_metrics.py`.
- Tests: `tests/test_layout.py`, `tests/test_structure.py`, `tests/test_conduct.py`, `tests/test_pin.py`, `tests/test_viewer.py`, `tests/test_review_metrics.py`. Existing tests change only the line by which they reach a name.
- Record: `docs/principles.md`, `docs/modules.md`, `docs/recipes.md`, `THREAT_MODEL.md`.
- No dependency, no new script, no new station, no decision overturned.

## Not in this change

- G2, G3, G4: the viewer's own structure, `ui · scaffold`.
- The Linux runner, E2's probes, the cloud facts' behaviour: Linux ready.
- H4's shipped run-data model: the metrics timeline.
- A third executor.
- Linear + Forgejo, and any second git host.
- The export of a version's portable record.
- H5, the bootstrap template's `Worktrees:` line: a bootstrap question of its own.
- C3's rows K–O: the brief module, the state formats, the tables, the metrics timeline.
- A shared finder that runs git: the git runner.
- The skills' prose: the release and preamble scripts.
- The content of a state file — the status log, the queue entry, the claim: the state formats.
- `~/.mf-ship-origin` under XDG, and the reach of `CLAUDE_CONFIG_DIR`: each is a behaviour change, not a move.
