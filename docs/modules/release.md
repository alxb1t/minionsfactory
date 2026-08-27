---
module: orchestrator/release.py
summary: Verify the release gate over on-disk facts, then prepare the release locally and halt for the human.
entry_point: verify_release_gate
public_api: [verify_release_gate, prepare_release, deferred_work_text, ReleaseVerdict, ReleaseResult, ReleaseStatus, ReleaseGit]
depends_on: [gate, findings]
---

# `release`

Verify a branch is releasable, then prepare the release **locally** and hand off to the human — the run's last
deterministic stage.

## What it does

[`verify_release_gate`](#verify_release_gate) judges every release precondition (gate green · the three findings
`clean` · no deferred work outstanding · release tag free · CHANGELOG `[Unreleased]` non-empty · clean tree)
into a [`ReleaseVerdict`](#releaseverdict). On a green verdict, [`prepare_release`](#prepare_release) cuts the
CHANGELOG, bumps `pyproject`, and commits + annotated-tags locally — then returns the human merge+push handoff.
**No LLM**: the `release.md` role is now pure control flow over disk. The **durable release record is `git log`,
`CHANGELOG.md` and the annotated tag** — nothing is written outside `repo`.

## Boundaries

**The boundary never crosses.** `prepare_release` prepares *locally* and stops — push and merge are the human's
high-consequence, irreversible steps. This is **structural, not a runtime check**: the [`ReleaseGit`](#releasegit)
seam has no `push` or `merge`, so prepare *cannot* ship even by mistake.

[`verify_release_gate`](#verify_release_gate) is **pure** — it judges over facts the caller gathers (the
release-time analog of [`decide`](driver.md#decide)); it runs no gate and reads no files itself.

## Data flow

```mermaid
flowchart TD
    facts["caller gathers facts: gate result · 3 findings · deferred work · changelog · tags · tree"] --> verify["verify_release_gate(...) — first-non-None blocker scan"]
    verify --> verdict{"ok?"}
    verdict -- no --> refuse["prepare_release → REFUSED (repo untouched)"]
    verdict -- yes --> act["prepare_release → cut CHANGELOG · bump pyproject · commit + tag (local)"]
    act --> prepared([PREPARED + human handoff])
```

## How clients use it

```python
verdict = verify_release_gate(
    version="v0.2",
    gate_result=gate.run_gate(repo),
    findings=[read_findings_state(p) for p in findings_paths],
    backlog_text=deferred_work_text(repo, "v0.2"),
    changelog_text=(repo / "CHANGELOG.md").read_text(),
    existing_tags=git_tags(repo),
    tree_is_clean=tree_is_clean(repo),
)
result = prepare_release(
    verdict, repo, "v0.2", today, branch, SubprocessReleaseGit()
)  # `change_id=` stamps the commit's `Change:` trailer; the entry point passes it
if result.status is ReleaseStatus.PREPARED:
    print(result.handoff)  # git checkout main; merge; push — the human's turn
```

## Edge cases & invariants

- **The two file predicates point opposite ways, deliberately.** A missing/empty CHANGELOG `[Unreleased]`
  **blocks** — absence of evidence is not evidence of absence for work that shipped. The deferred-work file
  `.minions/<version>_backlog.md` is the reverse: **any list line in it blocks**, whatever its checkbox state,
  and a **missing file passes** — it is per-version and lives in ephemeral run-artifact space, so its absence
  means nothing was deferred. An *unreadable* one still blocks (see
  [`deferred_work_text`](#deferred_work_text)).
- **Refuse-on-red is a true no-op.** On a red verdict `prepare_release` writes nothing, commits nothing, tags
  nothing — the repo is byte-for-byte unchanged. verify gates prepare; the two never run concurrently.
- **The tag keeps the leading `v`** (`v0.2` → tag `v0.2.0`); the CHANGELOG heading + `pyproject` version drop it
  (`0.2.0`).
- **Cutting re-arms the interlock.** After `prepare_release`, the CHANGELOG `[Unreleased]` is empty again, so a
  *next* [`verify_release_gate`](#verify_release_gate) blocks until new entries land — you cannot cut twice.

## Reference

### `ReleaseVerdict`

```python
@dataclass(frozen=True)
class ReleaseVerdict:
    ok: bool
    reason: str  # "" when releasable; the first blocking reason otherwise
```

The release gate's verdict — releasable, or blocked with a readable reason.

- **Produced by** — [`verify_release_gate`](#verify_release_gate); consumed by [`prepare_release`](#prepare_release).

### `verify_release_gate`

```python
def verify_release_gate(
    version, gate_result, findings, backlog_text, changelog_text, existing_tags, tree_is_clean,
    specs_valid=True, change_folded=True, commits=(), known_change_ids=(),
) -> ReleaseVerdict
```

Verify every release precondition; return `ok`, or the first blocking reason. **Pure** — the release-time analog
of [`decide`](driver.md#decide): it judges over already-gathered facts, so the whole gate is one first-non-`None`
scan over `str | None` blocker predicates.

- **Params** — `version`: e.g. `"v0.2"` → tag `v0.2.0` · [`gate_result`](gate.md#gateresult): the gate verdict (run by the caller) · [`findings`](findings.md#findingsstate): the three role verdicts (all must be `clean` — see [`all_findings_clean`](findings.md#all_findings_clean)) · `backlog_text`: the deferred-work text the caller read via [`deferred_work_text`](#deferred_work_text) · `changelog_text`: the raw `CHANGELOG.md` · `existing_tags`: the repo's tags (tag must be free) · `tree_is_clean`: no uncommitted changes · `specs_valid`, `change_folded`, `commits`, `known_change_ids`: the spec-fold and commit-trailer facts. **The composition root does not supply these four**, so they sit at their permissive defaults and the checks they gate — `_trailer_blocker` among them — are inert in every release the entry point drives. Feeding them means the release stage gathering commit, spec and fold state; owned by v0.10.
- **Returns** — [`ReleaseVerdict`](#releaseverdict): `ok=True`, or `ok=False` with the first reason.
- **Edge cases** — a missing/empty `[Unreleased]` blocks release, and a missing findings file (`None`) counts as not clean; a **missing** deferred-work file passes, while **any** list line in it blocks.
- **Gotchas** — takes `gate_result` (data), **not** the [`gate`](gate.md#gate) seam — it never runs the gate itself, unlike [`converge`](converge.md#converge).
- **Called by** — [`prepare_release`](#prepare_release)'s caller; composed in [`__main__`](main.md) by `_make_release`.
- **Source** — [`release.py`](../../orchestrator/release.py) · **Tests** — [`test_release.py`](../../tests/test_release.py)

### `deferred_work_text`

```python
def deferred_work_text(repo: Path, version: str) -> str
```

Read `<repo>/.minions/<version>_backlog.md` as the text the deferred-work predicate judges — the effectful half
of that check, kept out of the pure [`verify_release_gate`](#verify_release_gate).

- **Asymmetry** — an **absent** file reads as `""` and passes (nothing was deferred). An **unreadable** one — a
  directory at the path, a broken symlink, any other `OSError`, or a file that is not valid UTF-8 — returns a
  single list line naming the problem, so it blocks with a named reason instead of raising or reading as absent.
- **Called by** — [`__main__`](main.md)'s `_make_release`, which passes the result as `backlog_text`.
- **Source** — [`release.py`](../../orchestrator/release.py) · **Tests** — [`test_release.py`](../../tests/test_release.py)

### `ReleaseStatus`

```python
class ReleaseStatus(Enum):   # PREPARED | REFUSED
```

How release-prep ended: `PREPARED` (local commit + tag, awaiting the human) or `REFUSED` (a red verdict). The
[`driver`](driver.md#run) halts the run on `REFUSED`, completes it on `PREPARED`.

### `ReleaseResult`

```python
@dataclass(frozen=True)
class ReleaseResult:
    status: ReleaseStatus
    reason: str  # "" when prepared; the blocking reason when refused
    handoff: str  # merge+push instructions when prepared; "" when refused
```

The outcome of [`prepare_release`](#prepare_release).

- **Returned to** — [`driver.run`](driver.md#run) via the injected `release` seam; the handoff is printed by
  [`__main__`](main.md), never by the driver.

### `ReleaseGit`

```python
class ReleaseGit(Protocol):
    def commit_all(self, repo: Path, message: str) -> None: ...
    def tag(self, repo: Path, name: str, message: str) -> None: ...
```

The git operations release-prep needs — **and only those**. It has **no `push` or `merge`**: the "prepare
locally, the human ships" boundary is encoded in the seam's shape, not enforced at runtime. Implemented by the
real `SubprocessReleaseGit` (`git add -A` + `commit` + annotated `tag`, no shell, no push) and the recording
`FakeReleaseGit` (records commit messages + tag names, runs no git).

### `prepare_release`

```python
def prepare_release(verdict, repo, version, today, branch, git, change_id=None) -> ReleaseResult
```

Prepare the release on a green verdict, then hand off to the human; refuse on red.

- **Params** — [`verdict`](#releaseverdict): the gate result (refuse if not `ok`) · `repo`: the target repo, and the only tree written · `version`, `today`, `branch`: the tag/date/branch woven into the CHANGELOG, tag, and handoff · [`git`](#releasegit): the commit + local-tag seam · `change_id`: stamped as the commit's `Change:` trailer. The composition root passes it (`change_id=change_dir.name`), pinned by a test that drives `_make_release` end to end; the `| None = None` default is vestigial and kept only so the signature stays compatible with the direct-call tests.
- **Returns** — [`ReleaseResult`](#releaseresult): `REFUSED` (repo untouched) or `PREPARED` (with the handoff).
- **Edge cases** — refuse-on-red is a **true no-op**: no file write, no commit, no tag. On green the order is cut/bump → commit → tag (the commit is the point of no return). Nothing is written outside `repo`: the durable record is `git log`, `CHANGELOG.md` and the annotated tag.
- **Gotchas** — never pushes or merges (the `git` seam can't); the tag keeps the leading `v` (`v0.2.0`) while the CHANGELOG/`pyproject` version drops it (`0.2.0`).
- **Called by** — [`driver.run`](driver.md#run) via the injected `release` seam (once, after `converge` converges); composed in [`__main__`](main.md) by `_make_release`.
- **Source** — [`release.py`](../../orchestrator/release.py) · **Tests** — [`test_release.py`](../../tests/test_release.py)
