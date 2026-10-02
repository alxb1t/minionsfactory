# 0021-model-suggestion — design

**In one line:** `skills/mf-cut-change/SKILL.md` gains a `## Suggesting models` section, a sentence in Step 11
that runs it, and a line in `## Never`. Skill prose only. **Verdict: feasible** ([why](#verdict)).

Motivation is in [proposal.md → Why](proposal.md#why). This page holds the decisions and the text the skill gains.

## Context

- Step 11 reports the branch, the commit id and a clean tree, then names `/mf-build`
  (`skills/mf-cut-change/SKILL.md:115-118`).
- The sections after it run `## Input contract`, `## Prose rules`, `## Rules for the artifacts`, `## Never`
  (`skills/mf-cut-change/SKILL.md:120`, `:142`, `:172`, `:186`).
- `tests/test_skills.py` reads from this skill the labels of `## Input contract` and `## Prose rules`, and the
  paydown key `backlog:`. A new section between `## Rules for the artifacts` and `## Never` changes none of them.
- `mf-converge` dispatches its checkers as subagents of the session that conducts it.
- No skill names a model.

### Terms

| term | means |
|---|---|
| **the suggestion** | the lines the cut prints in chat: a model and an effort for the build, the check loop and the release |
| **a tier** | a class of model, not a name: **the mid tier** and **the strongest tier** |
| **the menu** | the models and efforts the human uses, when their `CLAUDE.md` names them |

## Goals / Non-Goals

**Goals**

- After a cut, the operator reads which model and effort to run each later station with, and why.
- The same change gets the same suggestion from any cut.

**Non-Goals**

- A suggestion per phase, a model named in the skill, or a file holding the suggestion.
- Any change to the stations that follow the cut.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | **The cut prints the suggestion in chat, in Step 11, after the commit.** It is written to no file | the cut has just read the whole scope; advice is not part of a change's record | a field in `proposal.md` · a separate skill |
| <a id="d2"></a>**D2** | **One suggestion per station, for the whole change:** build, converge, release. The highest row of the rubric any phase matches decides the build | the operator does not switch model mid-build | a suggestion per phase |
| <a id="d3"></a>**D3** | **The rubric speaks in tiers.** The agent chooses from the menu when the human's `CLAUDE.md` names one, and from the models the session offers when it does not | a model name in a skill is wrong at the next release, and another user has another menu | naming models in the skill · a menu file in the repo |
| <a id="d4"></a>**D4** | **Converge gets one line:** the model to start it in, or `skip, read by hand`. A skip is suggested only when every phase is prose, skill text or a scan over text; a new code path, a dependency or an anchored harm means run it. The line says which it found | the checkers inherit the conductor's model; a skip with no stated condition would be mood | a line per checker · never suggesting a skip |
| <a id="d5"></a>**D5** | **Release is the mid tier at medium**, at high when the change flags a hand-edit for the release | it follows a checklist and runs the gate | the strongest tier by default |
| <a id="d6"></a>**D6** | **No scan and no requirement hold the text.** The change declares `skip_specs` | it is advice; a wrong suggestion costs a model switch | a needle scan for the section's heading |

## The text the skill gains

### The section

Placed after `## Rules for the artifacts` and before `## Never`.

````markdown
## Suggesting models

After the commit, suggest in chat a model and an effort for the build, the check loop and the release. One
suggestion per station, for the whole change. Choose from the models the human uses: a menu in their `CLAUDE.md`
bounds the choice; with none, use the models this session offers.

| the change holds | build with |
|---|---|
| mechanical edits; a checklist to follow | the mid tier · medium |
| settled text to place; small tests | the mid tier · high |
| prose written fresh; moderate logic | the strongest tier · medium |
| new logic; a rule of a live skill or prompt written fresh; an irreversible phase; a `**HUMAN` phase | the strongest tier · high |

The highest row any phase matches decides.

- **Converge** — `skip, read by hand` only when every phase is prose, skill text or a scan over text. A new code
  path, a dependency, or an anchored harm means run it, in the build's model. Say which you found.
- **Release** — the mid tier · medium; high when the change flags a hand-edit for the release.

```
Suggested models
  build     <model · effort>                        <the reason, from the phases>
  converge  <model · effort | skip, read by hand>   <the reason>
  release   <model · effort>                        <the reason>
```

A suggestion, never an instruction: the human chooses.
````

### Step 11, before → after

```
before:  Report the branch, the commit id, and `git status --porcelain` printing nothing. Next: `/mf-build <change-id>`,
         in a fresh session. Then stop.

after:   Report the branch, the commit id, and `git status --porcelain` printing nothing. Then suggest models, as
         [Suggesting models](#suggesting-models) says. Next: `/mf-build <change-id>`, in a fresh session. Then stop.
```

### `## Never`, one line added

```
- Never write the model suggestion into the change, or into any file.
```

## Dependencies

None.

## Risks / Trade-offs

- **The cut suggests models for work it will not do.** → it is advice, printed after the commit, and the human
  chooses.
- **A suggested skip nudges toward releasing unchecked.** → [D4](#d4) states the one condition, and the line must
  say what it found.
- **A session may offer no model of a tier.** → the agent says so and names the nearest it has.

## Verdict

**Feasible.** One file changes, its new text is settled above, and no scan reads the places it touches.
