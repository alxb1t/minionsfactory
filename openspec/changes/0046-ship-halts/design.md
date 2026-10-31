# Ship halts — design

How a halt stays with its version, and how a catch-up keeps a count of its own. Verdict at the end: ready to build.

## Context

- `advance` loops on `while not self.halts`, a list every version shares (`skills/mf-ship/scripts/conduct.py:819`,
  `:766`).
- `ship()` logs each halt only at the end of the run (`conduct.py:898`). `0045` stopped at 08:04, and its halt reads
  08:08.
- `verify_log` needs the last event to be `halt` or `done` (`conduct.py:505`), and `report` prints the log's last line
  after its per-version lines (`conduct.py:1049`), so of several halts it shows one.
- Cut order is enforced twice: `mf-release` precondition 10 and `mf-integrate`'s "never skip ahead".
- `mf-converge`'s catch-up counts against the cap of three (`skills/mf-converge/SKILL.md:139`), and its pickup takes a
  round while one remains. A version clean at round 2 can reach integrate with none left.
- D47 says "the first failed check halts the run" (`docs/decisions.md:442`).

The deny glob behind the first of those halts was fixed on the default branch in `23fdf6d`, off the line. Phase 1's
CHANGELOG entry names that commit.

## Goals / Non-Goals

**Goals:** one version's halt costs no other version its build and converge; a merge cannot run a version out of
rounds; a run names what it released, what halted and what waits.

**Non-Goals:** merging in ready order; version numbers at the merge; declared dependencies; retries.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | A halt stops its version; only a failed probe or a crash stops the run | one version's trouble is that version's | stopping every version at the first failed check |
| [D2](#d2) | Cut order holds at the merge: a halt holds every version behind it | the release and integrate rules stay as they are until the order changes | skipping ahead now: tags would land out of order |
| [D3](#d3) | Each halt is logged when it happens, and the run closes on one line | the log is what the person watches | collecting halts for the end of the run |
| [D4](#d4) | `report` prints every `halt` line and marks a held version | it would otherwise show the last halt alone | a `hold` event: the order changes later, and the closing line already names the held |
| [D5](#d5) | A catch-up over merges only has its own count | a merge is not a fix: *Every edit opens a round* asks for a count and a cap, not this cap | reserving a round: a real three-round fix loop still reaches integrate with none left |
| [D6](#d6) | D47 and the principle are edited where they live | A7 | a new decision: this amends D47's halting rule |

### D1

`Run` gains `stopped`, and `advance` asks it instead of reading the shared list. `who` is `run` for a failed probe, and
for a crash, which `advance` catches as `conduct.py failed: <error>`.

```python
def stopped(self, change: str) -> bool:
    """Return whether a halt names `change` or the run."""
    with self.guard:
        return any(who in ("run", change) for who, _ in self.halts)
```

`advance` opens `while not self.stopped(version.change):`. A `Stop` inside a version's thread stays that version's
halt, as today. `Run.halt`'s docstring says the version starts no new worker. `ship`'s branch on `if not self.halts`
before the threads stays: at that point only the probe or every version at a halt stage can have halted.

### D2

Stage B moves to `Run.deliver`, which returns the versions held behind a halt. A version halted in stage A enters
`advance` and returns at once, so the loop stops at it.

```python
def deliver(self, versions: list[Version]) -> list[str]:
    """Run stage B in change-id order; return the versions held behind a halt."""
    for index, version in enumerate(versions):
        self.advance(version, ())
        if self.stopped(version.change):
            behind = versions[index + 1 :]
            return [later.change for later in behind if not self.stopped(later.change)]
    return []
```

### D3

`Run.halt` appends under the guard, then writes the `halt` event outside it. `ship` no longer loops over the halts at
its end. A run with a halt writes one closing event and returns 1:

```python
def closing(self, held: list[str]) -> str:
    """Return the closing line's detail: what halted, what is held, what released."""
    halted = " ".join(dict.fromkeys(who for who, _ in self.halts))
    waiting = " ".join(held) or "none"
    return f"halted {halted} · held {waiting} · released {' '.join(self.released) or 'none'}"
```

```
10:00:09 · 0002-marks · halt — build check fail — phase 1 unticked
10:04:31 · run · halt — halted 0002-marks · held none · released v0.1.0
```

`verify_log` needs no edit: the closing event is a `halt`, and a `halt` before it is an event like any other.

### D4

`report` reads the closing line, the log's last event. Before it, `report` prints every other `halt` line. A version
in the closing line's `held` list joins `touched`, so one that ran no worker still has its line, and that line ends
` · held behind <id>`, `<id>` being the lowest-id version the log's `halt` events name.

```python
held = re.search(r" · held (.+?) · released ", closing)
```

`none` in the `held` list is no version.

### D5

`skills/mf-converge/SKILL.md`, `## Catch-up round`. The diagram, before → after:

```
  round < 3 ? ── no ─▶ halt: revert the late commits, or re-converge from round 1
```
```
  the selection merges only? ── yes ─▶ its own count ─▶ freeze
               │ no
               ▼
  round < 3 ? ── no ─▶ halt: revert the late commits, or re-converge from round 1
```

Item 2, the whole item, after:

> 2. **Cap** — enumerate the selection as [Catch-up scope](#catch-up-scope) does, once, at the run's start. **Merges
>    only** → the run has **its own count**: one judge round and at most one fix round, and `round:` carries on past
>    three. Any other selection counts against the cap of three: the files' `round:` is the last judged round, and at
>    the cap → halt as drawn.

Item 4, the last sentence, before → after: "Otherwise Step 7's rules apply, under the same cap." → "Otherwise Step 7's
rules apply, under the run's count. A blocking finding open at the end of its own count is a `halt — cap reached`, as
at the cap."

Step 7, after "**The cap is three rounds, and the pickup round counts.**", add: "A catch-up over merges only has
[its own count](#catch-up-round)."

`cap reached` stays the words, so `mf-review-metrics` keeps counting the halt.

### D6

`docs/decisions.md`, D47's bold paragraph, before → after: "the first failed check halts the run, and a re-run resumes
from disk." → "a failed check halts its version, a halt holds every version behind it at the merge, a failed probe
halts the run, and a re-run resumes from disk."

`docs/principles.md`, *Every edit opens a round*, a bullet after **Why**:

> - **A merge:** a catch-up over merges only counts its own rounds: one judge round, at most one fix round.

`skills/mf-ship/SKILL.md`, the diagram's stage lines, after:

```
  A · each version at build or converge, in parallel: spawn ─▶ wait ─▶ check, until integrate or release
      a halt stops only its version
                    │  every thread joined
  B · each open version, in change-id order: integrate ─▶ converge (catch-up) ─▶ release, by its stage
      a halt, here or in A, holds every version behind it
```

Its Step 4, before "The last line:", add: "A run with a halt closes on `halted <ids> · held <ids> · released <tags>`:
what it released stays released, and a re-run resumes the rest."

## Tests

Fake-worker tests in `tests/test_conduct.py` (`T1`: the fake worker is the lowest layer that reaches a run). A proof of
the catch-up's count is the spec scenario and converge's review: v0.28 retired prose guards.

| layer | at cut | added | removed | proof |
|---|---:|---:|---:|---|
| Unit test functions | 74 | 2 | 1 | `uv run pytest --collect-only -q \| tail -1` prints `74 tests collected` at the cut, `75 tests collected` after |
| Integration tests | 0 | 0 | 0 | — |
| End-to-end runs | 0 | 0 | 0 | — |

`T2`: the new tests below reach a state no test reaches: one version halted while another runs on.
`test_run_halts_on_a_human_phase` holds two versions, but its halt is recorded in `deliver`, after the threads join, so
no version runs on behind a halt.

| test | holds |
|---|---|
| `test_a_later_version_halts_and_the_earlier_ships` | with `liar-0002-marks`: exit 1; `0001-todo` released and `v0.1.0` tagged; no `release 0002-marks` call; the `0002-marks` `halt` line before `0001-todo`'s `spawn — release`; the last line `… · run · halt — halted 0002-marks · held none · released v0.1.0`; `log --verify` exits 0; `report` prints the `halt` line and the closing line |
| `test_an_earlier_version_halts_and_the_later_is_held` | with `liar-0001-todo`: exit 1; `converge 0002-marks` called, no `integrate` or `release` call; the last line `… · run · halt — halted 0001-todo · held 0002-marks · released none`; `report`'s `0002-marks` line ends ` · held behind 0001-todo` |

Tests edited:

| test | edit |
|---|---|
| `test_run_halts_on_a_human_phase` | the `halt` line found with `any(…)`, and the last line `… · run · halt — halted 0001-todo · held 0002-marks · released none` |
| `test_run_halts_on_a_timeout` | the `halt` line found with `any(…)`, and the last line `… · run · halt — halted 0001-todo · held none · released none` |
| `test_run_halts_when_a_worker_claims_what_disk_does_not_show` | run under `fake("deny", "liar")`; the `halt` line names the denial; then the steps of `test_a_rerun_resumes_from_disk`; then a step with `liar-probe`: `_calls` is `["probe"]`, the last line `… · run · halt — halted run · held none · released none`; then a step with two versions and a models file that is not UTF-8: no `converge 0002-marks` call, a `conduct.py failed` halt, the same last line |
| `test_log_verify_finds_an_unpaired_spawn_and_an_open_end` | takes the `RunLog` and `last_log` steps |
| `test_a_worker_carries_the_allowlist_and_a_denial_is_named` | loses its `fake("deny", "liar")` block |

`_fake` gains one mode: `liar-<name>`, `<name>` a change id or `probe`. The worker for that name writes nothing, as
`liar` does for a build.

The `I16` table, per `0040·R6`:

| test removed | carried by |
|---|---|
| `test_a_rerun_resumes_from_disk` | `test_run_halts_when_a_worker_claims_what_disk_does_not_show` holds its re-run steps, and `test_log_verify_finds_an_unpaired_spawn_and_an_open_end` its `RunLog` and `last_log` steps |

## Dependencies

None.

## Risks / Trade-offs

- **Versions keep running behind a halted one** → they spend build and converge, then wait. That is the point, and a
  re-run does not repeat them.
- **`held behind` is derived from the log** → the lowest-id halted version is the one stage B stopped at, since stage B
  stops at the first in change-id order.
- **The catch-up's count is prose** → a worker could misread it. The spec scenarios and converge's review hold it, and
  the status log shows the rounds.
- **`converge-reading-set` is past its watch** → [D5](#d5) adds a few lines to `mf-converge`, and adds no section.

## Migration Plan

```
1 per-version halts ─▶ 2 the catch-up's count ─▶ release
```

Each phase ends on a green gate. Nothing is irreversible.

## Verdict

Ready to build. Acceptance: a later version's halt leaves the earlier to ship; an earlier version's halt leaves the
later converged and held; the closing line and `report` name both; a failed probe stops the run; the catch-up's count
and D47 are edited where they live.
