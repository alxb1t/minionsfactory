# 0019-inferred-change-id — design

**In one line:** the `## Parameter` section of `mf-build`, `mf-converge` and `mf-release` gets the same inference rule, branch check and
echo, held by one scan. Prose and a test. **Verdict: feasible** ([why](#verdict)).

Motivation is in [proposal.md → Why](proposal.md#why). This page holds the decisions and the text the section
becomes.

## Context

- `skills/mf-build/SKILL.md:15-17`, `skills/mf-converge/SKILL.md:19-21` and `skills/mf-release/SKILL.md:20-22`
  each say `change-id` is an explicit, required parameter, and "Never infer it — not from the highest-numbered
  directory …, not from "there is only one active change"". Each gives its reason: a wrong id reads, builds or
  releases against another change.
- No test in `tests/` and no requirement in `openspec/specs/` holds that rule.
- `mf-cut-change` Step 4 makes the branch `v<version>_<slug>`, the slug being the id without its number, hyphens to
  underscores. Its `I1` requires the change directory to be tracked.
- `mf-converge` writes `start` to its status log once Step 1 passes (`skills/mf-converge/SKILL.md:127`).

### Terms

| term | means |
|---|---|
| **an active change** | a directory under `openspec/changes/`, not `archive/`, with a file tracked by git |
| **the change's branch** | `v<proposal version>_<slug>` — what `mf-cut-change` Step 4 names it |

## Goals / Non-Goals

**Goals**

- `/mf-build`, `/mf-converge` and `/mf-release` start with no argument after a cut.
- A wrong change is never taken: ambiguity and a branch mismatch halt.

**Non-Goals**

- `mf-cut-change`, and the `mfa-*` line.
- Any change to what the skills do once they have the id.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | **An explicit `change-id` wins. With none, the candidates are the active changes** — `git ls-files openspec/changes/`, without `archive/`, reduced to directory names. One → use it · none → halt `no active change` · several → halt, listing them | an untracked, half-written cut never counts; ambiguity is a halt, never a pick | the highest-numbered directory; any directory on disk |
| <a id="d2"></a>**D2** | **The inferred id must agree with the branch.** The current branch equals `v<proposal version>_<slug>`; else halt, naming both | independent facts that agree catch the realistic miss: a branch carrying someone else's change | trusting the single candidate alone |
| <a id="d3"></a>**D3** | **Echo, then proceed.** The first line is `change-id: <id> (inferred: the one active change; branch <branch> agrees)`; `mf-converge` writes the same into its status log's `start` line. No wait | the operator wants the skill to simply start | a confirmation prompt |
| <a id="d4"></a>**D4** | **The same text in each.** Each `## Parameter` section says the rule in the same words, with the skill's own reason kept | one rule, one wording; the scan holds every one | a shared file the skills include — skills are self-contained |

### The `## Parameter` section, before → after

```
before:  ## Parameter — the change id, required
         `change-id` is an explicit, required parameter. Without it, halt and ask for it.
         Never infer it — not from the highest-numbered directory …, not from "there is only one active change".
         <the skill's reason a wrong id is dangerous>

after:   ## Parameter — the change id
         A given `change-id` is used as given. Without one, infer it — strictly:
         1. The candidates are the active changes: `git ls-files openspec/changes/`, without `archive/`.
            None → halt: `no active change`. Several → halt, listing them.
         2. The one candidate's branch is `v<its proposal version>_<its slug>`. The current branch differs →
            halt, naming both.
         3. Echo `change-id: <id> (inferred: the one active change; branch <branch> agrees)`, then proceed.
         <the skill's reason a wrong id is dangerous — kept: it is why inference is strict>
```

## Seams — what the tests hold

The skills are prose; the seam is the text scan in `tests/test_skills.py`, with a `tmp_path` twin that plants each
breach.

| key | the scan checks |
|---|---|
| `sdd:inferred-change-id:one-active-change` | each of `mf-build`, `mf-converge`, `mf-release` names `git ls-files openspec/changes/`, `no active change` and `(inferred:`, and none names `Never infer it` |

## Dependencies

None.

## Risks / Trade-offs

- **A wrong change taken.** → Only when exactly one is tracked and the branch agrees; either failing halts.
- **A skill run on `main` after a release.** → No active change there; it halts.

## Verdict

Feasible. Each skill's `## Parameter` section and one scan; one phase, because the scan holds them at once.
