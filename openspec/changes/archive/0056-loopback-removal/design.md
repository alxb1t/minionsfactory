# Loopback removal — design

What leaves with `Ship loopback:`, what stays, and how a repo that still declares it is told. Verdict at the end: ready to
build.

## Context

Read at `f33a6b3` (v0.47.0). `conduct.py` is `skills/mf-ship/scripts/conduct.py`.

- The line lives in `conduct.py`: `EVENTS`' `loopback` (`:56`), `NEEDS_CLAUDE` (`:68-70`), `ShipLines.loopback`
  (`:178-182`), `_agents_flag` (`:344`), `ship_lines` (`:1417-1435`), `_loopback_listeners` (`:1460-1467`), `worker_settings`
  (`:1502-1521`), `argv` (`:1549-1558`), `read_plan` (`:2075-2088`), `Run.ship`'s log (`:2205-2207`).
- Its tests: `tests/test_conduct.py:2188-2227` in `test_the_plan_is_read_once`, `:2774-2782` in
  `test_a_claude_worker_starts_in_the_sandbox`. The drill: `LOOPBACK_PROMPT` (`tests/escape_drill.py:84-103`), `_loopback`
  (`:423-440`), its use in `main` (`:490`); `tests/test_escape_drill.py:30` names the line.
- Its record: D51 (`docs/decisions.md:465`, `:474-475`), `THREAT_MODEL.md:19`, `:40`, `:52-57`, `skills/mf-ship/SKILL.md:95-96`.
- No repo declares it: isekai took its loopback tests out of its gate on 2026-11-02.

## Goals / Non-Goals

**Goals:** no worker binds loopback; a leftover line is seen; the record says so.

**Non-Goals:** the container; touching the `VIRTUAL_ENV` fix, `_codex_held`, the refused-bind row or D15.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | The reader, the setting, the Codex refusal, the listeners and the event go | nothing uses them, and `0054·S3` stays open while they exist | keeping the opt-in |
| [D2](#d2) | A declared line halts the run | a planted line is seen | ignoring it |
| [D3](#d3) | The drill's loopback row goes | it proves a setting that no longer exists | — |
| [D4](#d4) | The record says no loopback, and names the container | A7 | — |

### D1

`ShipLines` loses `loopback`; `worker_settings` loses its `loopback` parameter and `allowLocalBinding`; `argv` passes
neither. `NEEDS_CLAUDE`, `self.held` and its use in `take`, the `read_plan` refusal, `_loopback_listeners`, the log, and
`loopback` in `EVENTS` go. `_agents_flag` stays only if D2 uses it.

### D2

`ship_lines`: `AGENTS.md` holding `**Ship loopback:**` with any value → `Stop(1, "conduct: halt — AGENTS.md: Ship loopback:
was removed (change 0056-loopback-removal): delete the line")`. `conduct.py agent` reads it the same way.

### D3

`tests/escape_drill.py`: `LOOPBACK_PROMPT`, `_loopback` and its call and its term in `main` go. `ESCAPE`'s bind in the
primary, which declares no line, stays, held when refused. `tests/test_escape_drill.py`'s comment on the line is reworded:
the primary's bind is refused because no worker binds loopback.

### D4

- **D51**: its statement's ", save through a local service where a repo opts into loopback" goes. *Accepts*' item "in a repo
  whose `AGENTS.md` declares `Ship loopback: yes`, a Claude worker reaches every service on the Mac's loopback; on Linux the
  flag does nothing" goes. *Rejected* gains "· loopback per repo: on macOS it reaches every local service".
- **`THREAT_MODEL.md`**: *Trust boundaries*' "network on a short list and loopback only where a repo opts in" → "network on a
  short list and no loopback". *Entry points*' "`Ship tools:`, `Ship network:` and `Ship loopback:` lines" → "`Ship tools:` and
  `Ship network:` lines". *Out of scope*'s bullet **A loopback repo's local services** goes. *Known gaps* gains "A gate that
  serves on loopback cannot run under a worker; a Linux container, where loopback is private, is the way out."
- **`skills/mf-ship/SKILL.md`** Step 3: "In a repo that declares `Ship loopback: yes`, its Claude workers reach every service on
  the Mac's loopback, and the run's log names those the operator's own processes hold; a root daemon's goes unlogged." goes.

## Tests

Counted at `f33a6b3`: `uv run pytest --collect-only -q | tail -1` prints `101 tests collected`. All edits, none added; none
end-to-end.

| test | change | holds |
|---|---|---|
| `test_the_plan_is_read_once` | edited | the loopback steps go; D2: a repo that declares the line halts the run with D2's text |
| `test_a_claude_worker_starts_in_the_sandbox` | edited | the `allowLocalBinding` steps go; no settings carry `allowLocalBinding` |
| `tests/test_escape_drill.py` | edited | the comment only; `_codex_held`'s cases stay |

None is deleted or merged.

## Dependencies

None.

## Risks / Trade-offs

- **A repo that needs loopback cannot run `mf-ship`** until the container exists. None does today.

## Verdict

Ready to build.
