# minions_factory — shared context for Claude Code

MinionsFactory is a **CLI + orchestrator for autonomous Python feature development with Claude Code**. Pointed
at a target repo, it drives an **in-repo change** to completion: a **coder** builds the change's `tasks.md`
phase by phase (the orchestrator **runs the quality gate itself** and detects the advance); at plan end it fans
out **review ‖ security ‖ simplify** as fresh read-only instances, runs a **converge loop** over their blocking
findings, and hands a **release** step the gated, tagged result — which **folds the change's spec delta into the
living `openspec/specs/`** and archives the change. Every role is a **fresh, single-role Claude Code instance**; the
driver **advances or halts** on machine-checkable disk state. The project dogfoods its own conventions —
spec-driven changes, a strict quality gate, all state on disk.

Hard constraints that shape the code: **no LLM sits in the orchestration layer** (the driver is deterministic,
unit-testable control flow); **the orchestrator runs the objective checks itself** (the gate + git state — so
the agent it drives can't game them); **all state lives on disk** (a run resumes from the change's `tasks.md`
progress + git, never from memory); and **roles are fresh instances behind a provider seam** (harness-agnostic —
Claude Code is the default adapter, with no dependency on a harness's internals).

> **This file is shared, role-independent context — what is *true* about this repo. It is not a script.**
> What you should *do* comes from the **prompt/task you were given** (author a change, build a phase, review the
> branch diff, run a security pass, apply fixes). If your prompt conflicts with this file, **the prompt wins.**
> Read this for the facts; follow your prompt for the actions — don't infer a workflow from this file alone.

---

## Where the work is defined — spec-driven changes (in-repo)

This repo follows **spec-driven development** (OpenSpec-style). Two in-repo trees under **`openspec/`** carry the
truth:

- **`openspec/specs/<capability>/spec.md`** — the **living, test-backed behavioral spec**: what the system does
  *now*. Each requirement carries WHEN/THEN **scenarios**, and every scenario is bound to a proving test
  (`@pytest.mark.spec("<key>")`) — enforced by the **spec-binding check** (`specs check`; see the gate below).
- **`openspec/changes/<change-id>/`** — the **active change** you build: `proposal.md` (scope/approach),
  `design.md` (technical decisions), `tasks.md` (the ordered phases + progress checkboxes), and `specs/` (the
  **delta** — `## ADDED / MODIFIED / REMOVED Requirements` for this change). Read the change **in-tree**; record
  progress in `tasks.md`. On release the delta **folds** into the living `openspec/specs/` and the change moves to
  `openspec/changes/archive/<change-id>/`.

**Progress lives in `tasks.md` + git** — read the active change (`openspec/changes/<id>/`), its `tasks.md`, and
the recent `git log` (every commit carries its `Change:` trailer) to see where the work stands. Don't re-derive
decisions already settled in the change; if something there conflicts with reality, raise it with the human
rather than silently diverging.

**Everything a run reads or writes is inside the repository.** The orchestrator resolves **no path outside the
target repo**: findings, the coder's HALT report and the release's deferred-work backlog all land under
**`.minions/`**, whose run artefacts are gitignored — `minions.toml`, the gate command list, is the one tracked
file in it (see *The findings contract* below). Product intent lives *upstream* of the code, in a private
Obsidian vault the human keeps — the planning docs, research, the narrative record — and **no role the
orchestrator spawns reaches into it**. The **PM-side skills** run from there, out of band: they take the
vault project dir as cwd and resolve the target repo from its `overview.md` → `repo:`. The vault reaches the
repo; the repo never reaches the vault. `.env` is gitignored local
scaffolding declaring nothing the orchestrator needs, and the committed `CLAUDE.md` / `.env.example` stay
path-free.

**Commits carry a `Change: <change-id>` git trailer** so history reads back to intent
(`git log --grep "Change: <id>"` → the commits → `openspec/changes/archive/<id>/` → proposal/design/tasks/delta).

---

## The quality gate (a phase is done only when all are green)

The gate **leads with a locked lock-sync step** — `uv sync --locked`, which asserts `uv.lock` is up to date and
fails rather than silently re-resolving — so the gate certifies what the lock pins rather than whatever `.venv`
happens to hold. It is environment setup rather than a quality *axis*, so it is listed here as the step it is and
the four axes follow:

- `pytest` — all tests pass. **Test-first (red → green)** for every unit of logic we control. The suite doubles
  as executable documentation — name tests as behavioural sentences.
- `ruff format --check` + `ruff check` — format + lint clean (`D` docstrings + `ANN` annotations enabled).
- `ty check` — strict type-check clean.
- **`specs check`** — the spec binding holds: every scenario is test-backed and every `spec` marker resolves
  (a structural check; the reviewer judges whether a test *genuinely* exercises its scenario). This repo runs
  **from source**: invoke it like the existing `run` command —
  `uv run python -m orchestrator specs check --strict`. There is **no installed `minions` binary yet**;
  `minions specs check` is only the future installed alias.

Six steps in all — the sync, format, lint, typecheck, test, and the spec checker last. `.minions/minions.toml`'s
`gate` array is the source of truth (the orchestrator runs *it*); `Makefile`'s `gate` target, `README.md` and CI
mirror it command-for-command.

External effects are **faked** in tests behind their seams — the **provider** (`claude -p`) behind the
`Provider` Protocol (`FakeProvider`) and the **gate subprocess** behind the gate seam (`FakeGate`) — so **no
unit test spawns a real Claude Code instance or hits the network**; real `claude -p` is exercised only in an
end-to-end dogfood run. CI (`.github/workflows/ci.yml`) runs the gate on every push. The gate **command list is
read from the target repo** (`.minions/minions.toml`), not hardcoded, so a non-Python target needs no code change.

The repo keeps a **`CHANGELOG.md`** in [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format, aligned
to the version line (change `vX.Y` = CHANGELOG release = `pyproject` version = git tag `vX.Y.0`): each phase
appends under `## [Unreleased]`; the release step cuts `## [X.Y.0]`. Keeping it current is part of the phase
ritual — the change's `tasks.md` carries it phase by phase, and `CHANGELOG.md`'s own `## [Unreleased]`
section is the shape to follow.

---

## Engineering conventions

The change's **`design.md`** is authoritative, with this file behind it — read it. (The human keeps a longer
decision record upstream in the vault; it is the *human's*, not an input any role reads.) In brief, the
load-bearing seams are:

- a **`Provider` Protocol** — a real `ClaudeCodeProvider` (`claude -p`, `--output-format json`) + a
  `FakeProvider`; the driver depends on the **seam**, never the CLI directly (harness-agnostic + unit-testable).
- **the orchestrator runs the gate itself** via a `run_gate(repo)` seam (real subprocess + `FakeGate`); the gate
  command list is **read from the target repo** (`.minions/minions.toml`), not hardcoded.
- **the active change is read from disk** — the coder resolves `openspec/changes/<change-id>/` in-tree and builds its
  `tasks.md` phase by phase; findings + spec state are read from disk, never trusted from a role's claim.
- **the driver is deterministic control flow** — no LLM; **advance is *detected*** (a new commit landed **and**
  the phase checkbox moved), not trusted; a halt writes a disk contract the next run resumes from.
- roles are defined by a **prompt + a disk I/O contract** — each role prompt (`prompts/`) is the first-class
  authority for what that instance does.

---

## The findings contract

The three read-only roles — **review ‖ security ‖ simplify** — each write exactly **one** findings file and
nothing else, and the fan-out, the converge loop and the release stage all read them back from disk. The shape is
a contract, not a convention: an execution line downstream parses it.

**Path.** One resolution site — `findings_path()` in `orchestrator/findings.py` — yields
**`<repo>/.minions/findings/<change-id>_<role>.md`**. Rooted in the **repository being built** (findings are run
artefacts of that repo, and `.minions/`'s artefacts are gitignored), and keyed on the **change id** — the same
identifier as the change directory and the `Change:` commit trailer, not the release version. Because all three
stages resolve through the one function, they cannot drift.

**Frontmatter.** Each file opens with a YAML block the orchestrator parses — the boundary where a role's
declared verdict enters the driver, though what the parse enforces is **shape only**. Four keys are
shape-validated (`FindingsState`, frozen): **`verdict`** (`clean | changes-requested`), **`open_blocking`**
(int), **`round`** (int, bumped by each verify pass) and **`head`** (an unconstrained string — the SHA that round
judged, off which the next verify pass scopes its diff; nothing checks that it looks like a commit id).
**Convergence turns on `verdict` alone**: `all_findings_clean` reads that one field, and `open_blocking` is
parsed but consulted by no decision anywhere in the orchestrator. The prompts write five more for the human —
`type` (`review | security | simplify`), `plan`, `project`, `branch`, `reviewed`. A missing file is **not**
clean: `all_findings_clean` counts an absent file as unconverged, so a role that never ran can't let the loop
or the release gate pass falsely.

**Two severity vocabularies — which one applies is the role's.** Security grades
`critical | high | medium | low` and **blocks on `critical` + `high`**; review and simplify grade
`blocking | nit` and **block on `blocking`** (simplify's blocking tier is deliberately narrow — dual paths and
misleading surface only). Either way `open_blocking` counts *that role's* blocking tier, and a role
declaring `verdict: clean` is obliged to leave it at zero — a **role obligation**, not a machine check: the
orchestrator never cross-checks the counter against the body. A non-blocking finding never stalls the converge
loop; it is carried into the release's deferred-work file, `<repo>/.minions/<version>_backlog.md`, where **any**
remaining list line holds the release until it is fixed and removed, or exported by the human.

**Status: `open → fixed → verified`, with a producer/checker asymmetry that is the whole point.** A finding is
born `open`. The **fixer — the producer — writes `fixed`** and touches nothing else: per-finding status and note
only, counters and `verdict` left alone. `fixed` is a claim, not a resolution. **Only the checker promotes to
`verified`** — the same read-only role on its verify pass (`round ≥ 2`), which re-judges each finding against the
scoped fix diff and either promotes it or **reopens** it to `open` with a one-line reason; a regression the fix
introduced becomes a new finding at `open`. A finding the fixer believes is wrong is marked `wontfix` with a
justification — also the checker's to accept or reopen. No role verifies its own fix, and the producer never
converges the loop. The same asymmetry governs the compliance rubric's gap report
(`skills/rubrics/compliance.md`): the side that applies the fixes writes `fixed`, and only a fresh teardown
measurement promotes to `verified`.

**The resolution log is append-only.** The verify pass rewrites the frontmatter counters in place, but records
each transition as a dated line **appended** to a `## Resolution log` at the foot of the file. Past rounds are
never rewritten — the counters say where the loop stands now, the log says how it got there.

---

## Guardrails (invariants — hold for every role)

- **Never commit a secret, or a *real* absolute path from the machine the run is on** — `.env` itself, an API
  key; the **operator's home or vault path** (a PM-side skill runs from the vault and writes into this repo's
  *tracked* `openspec/` tree, so that path is one careless paste away from history), or **this repository's own
  root** transcribed out of a `.minions/` artefact into tracked prose. Paths a fixture or a worked example
  *constructs* — a fictional home, a `tmp_path` expression in a test — are not the target of this rule; a rendered
  one, carrying a real username, is. `.env` is gitignored; the committed `CLAUDE.md` / `.env.example` stay
  path-free.
- **Deps minimal + human-gated.** Any new dependency (`uv add`) — argue for it and **wait for approval** before
  installing. Test/lint/type tools stay dev-only; keep the runtime lean.
- **No LLM in the orchestration layer; the orchestrator owns the objective checks.** The driver stays
  deterministic and testable; the gate + git state are run by the orchestrator (not the agent it drives) so they
  can't be gamed.
- **State lives on disk.** Reconstruct "where are we" from the active change's `tasks.md` + git (+ the folded
  `openspec/specs/`) — never from memory. Resume is therefore free.
- **Findings stay under `.minions/`; progress + specs stay in git.** The read-only roles write only their one
  findings file (gitignored run artefact); the coder writes code + `tasks.md` + the change's spec delta, keeps
  `CHANGELOG.md` current, and puts a `Change:` trailer on every commit. The durable record of a release is the
  repository's own — `git log`, `CHANGELOG.md` and the tag; no role writes one anywhere else.
