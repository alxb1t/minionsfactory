# Design — 0004-planning-skills

Technical decisions for the v0.4 planning line. Full rationale is in the vault PRD
(`prd/v0.4_planning_skills.md`) + `decisions.md`; this records the *how*, repo-side.

## 1. The line = two producer→checker pairs + a spike + a conductor

`Order → Gauge → Blueprint → Forge → Inspect → Run`. `mf-order`+`mf-gauge` (produce + gate the PRD) and
`mf-forge`+`mf-inspect` (produce + gate the change) are the two pairs; `mf-blueprint` is the feasibility/design
spike between them; `mf-line` conducts. This is the planning-side mirror of the execution loop (coder + fresh
reviewer).

## 2. Independence lives inside the check-skills

`mf-gauge` and `mf-inspect` **spawn a fresh subagent** given only the artifact + the rubric, blind to the producer
context. This preserves fresh-instance independence even when a stage runs in a warm session or under `mf-line` —
so independence is a property of the skill, not of the invocation. (The strongest form — a *different model* — is
backlogged as cross-model planning checks.)

## 3. Interactive stages run in the main session; only checks are delegated

A subagent cannot hold a back-and-forth with the human, so `mf-order` (interview) and the human go/no-go gates
(blueprint verdict, inspect findings) run in the **main session**; `mf-line` delegates only the **checks** to fresh
subagents and pauses at the human gates. `mf-line` is an **LLM conductor** for now — a soft version of the "no LLM
in orchestration" invariant, acceptable because planning is supervised. The deterministic `minions author` CLI is
the on-thesis successor (backlog).

## 4. Rubrics are the shared contract, split (M)/(J)

Each rubric enumerates criteria tagged **(M) machine-checkable** (grep/section/count/id-match — un-gameable) vs
**(J) judgment** (needs the fresh checker). The split *is* the enforcement design. `prd-readiness` is shared by
order (drives) + gauge (gates); `feasibility` by blueprint (produces) + inspect (re-checks); `conformance` by
inspect. They live in `skills/rubrics/` (not per-skill) so there is one definition of "done." Skills reference a
rubric by its installed path (`~/.claude/skills/rubrics/<name>.md`) with the source-repo path
(`skills/rubrics/<name>.md`) as fallback — so `make install-skills` also links the rubrics dir.

## 5. Artifact placement + the private/public split

- PRD → vault `prd/vX.Y_<name>.md`; design proposition → vault `prd/vX.Y_design.md` (private thinking).
- Change → repo `openspec/changes/<id>/` (the sanitized, execution-ready subset).
- `mf-forge` / `mf-inspect` run with cwd = the repo and read the vault PRD/design via `.env` → `VAULT_PROJECT_DIR`
  (the same resolution the execution role prompts already do).

## 6. Feasibility verdict gates before task-cutting

`mf-blueprint` emits `feasible | feasible-with-caveats | needs-precursor | infeasible-as-specified`. Only the first
two proceed to `mf-forge`; the others HALT for a human decision (rescope or spin a precursor version). This catches
"infeasible / needs-refactor / wrong-size" at planning time, not mid-execution.

## 7. Skills home vs runtime; doc-only tracking

Skills are authored + versioned in the repo `skills/` (the product artifact, alongside `prompts/`) and installed to
`~/.claude/skills/` via `make install-skills` (symlink, so repo edits are live everywhere incl. the vault) /
`make uninstall-skills`. v0.4 is a **doc-only change**: all four change artifacts are present, but `specs/` is an
**N-A delta** (prose, nothing test-backed to bind). The checker only parses `spec.md`, so an N-A `specs/README.md`
adds no scenarios and the gate stays green; there is nothing to fold at release.

## 8. Commit-trailer contiguity (the v0.3 lesson)

Every commit carries `Change: 0004-planning-skills` **contiguous** with `Co-Authored-By:` (no blank line between) —
git parses trailers as one block in the last paragraph; a blank line splits it (the v0.3 release finding). Until
the trailer-normalizing git hook lands (backlog), compose the message with the trailer block intact.
