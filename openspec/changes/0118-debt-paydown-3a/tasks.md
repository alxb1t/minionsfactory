# Debt paydown 3a — tasks

Premise checks for the cards that close without code, the prose and archive fixes, the corpus and metrics fixes, then the new `cut_check.py` row. Decisions: [design](design.md).

## Progress

- [x] 1 — the cards closed without code, each Still true? recorded · moderate
- [x] 2 — the prose and archive cards; C4 under the threat model's Out of scope · moderate
- [x] 3 — corpus.py skips old findings and follows no linked case; review_metrics $NAME and per-repo marks; 0100·S4, 0101·R7, 0114·R7 · hard
- [ ] 4 — cut_check.py's row for a Verify: needle a later task removes · hard

## 1 — the cards closed without code, each Still true? recorded

Each sub-task checks one premise of the context table in [design](design.md), per [D8](design.md#d8). No file changes in this phase.

- [x] 1.1 **HALT CHECK** 0097·R1: `skills/mf-ship/scripts/conduct.py` no longer defines the checker mailbox, so D51's "alone" holds.
  Verify: `git grep -n 'def _open_mailbox' -- skills/mf-ship/scripts/conduct.py` prints nothing.
- [x] 1.2 **HALT CHECK** 0097·R5: the mailbox reply write is gone from `skills/mf-ship/scripts/conduct.py`.
  Verify: `git grep -n '_place(fd, f"{role}.answer"' -- skills/mf-ship/scripts/conduct.py` prints nothing.
- [x] 1.3 **HALT CHECK** 0097·R6: the mailbox folder creation is gone from `skills/mf-ship/scripts/conduct.py`.
  Verify: `git grep -n 'mailbox.parent.mkdir' -- skills/mf-ship/scripts/conduct.py` prints nothing.
- [x] 1.4 **HALT CHECK** 0097·S4: no served checker request reaches a spawn in `skills/mf-ship/scripts/conduct.py`.
  Verify: `git grep -n 'serve_requests' -- skills/mf-ship/scripts/conduct.py` prints nothing.
- [x] 1.5 **HALT CHECK** 0097·S5: the halt that called a mailbox a link is gone from `skills/mf-ship/scripts/conduct.py`.
  Verify: `git grep -n 'the checker mailbox' -- skills/mf-ship/scripts/conduct.py` prints nothing.
- [x] 1.6 **HALT CHECK** 0101·S8: `skills/mf-converge/SKILL.md` holds no resume table; `converge.py` resumes.
  Verify: `git grep -n 'Resuming a run' -- skills/mf-converge/SKILL.md` prints nothing.
- [x] 1.7 **HALT CHECK** 0100·R2: `skills/mf-converge/SKILL.md` dispatches no worker by description.
  Verify: `git grep -n 'round <N>' -- skills/mf-converge/SKILL.md` prints nothing.
- [x] 1.8 **HALT CHECK** 0094·S7 and 0094·S8: the script that matched surfaces is retired.
  Verify: `git ls-files skills/mf-converge/scripts/surfaces.py` prints nothing.
- [x] 1.9 **HALT CHECK** 0114·R3: the comment is gone from `tests/test_plan_check.py`.
  Verify: `git grep -n -F '# A selection or another option is no quiet flag' -- tests/test_plan_check.py` prints nothing.
- [x] 1.10 **HALT CHECK** 0114·R5: the comment is gone from `skills/mf-converge/scripts/plan_check.py`.
  Verify: `git grep -n -F 'A node id line, a per-file count line' -- skills/mf-converge/scripts/plan_check.py` prints nothing.
- [x] 1.11 **HALT CHECK** 0114·R4: the archived design of 0114 no longer promises the directory shortcut.
  Verify: `git grep -n 'an operand whose file or folder exists' -- openspec/changes/archive` prints nothing.
- [x] 1.12 **HALT CHECK** 0114·R6: the archived design of 0114 no longer counts the recurrence.
  Verify: `git grep -n 'came back three times' -- openspec/changes/archive` prints nothing.
- [x] 1.13 **HALT CHECK** 0100·R1 stays wontfix by the class of 0098·R1: the count stands in `docs/decisions.md`.
  Verify: `git grep -c -h '28.6k' -- docs/decisions.md` prints `1`.
- [x] 1.14 **HALT CHECK** 0117·R1 stays wontfix by the same class: the figure stands in the archived proposal of 0117.
  Verify: `git grep -c -h -F '9.87 over' -- openspec/changes/archive/0117-codex-converge/proposal.md` prints `1`.
- [x] 1.15 **HALT CHECK** 0089·R4 stays accepted: its test stands in `tests/test_conduct.py`.
  Verify: `git grep -c -h 'fake("halt-0002-marks", "rescue-diagnose", "supervise-delta")' -- tests/test_conduct.py` prints `1`.
- [x] 1.16 **HALT CHECK** 0102·R2 stays accepted: its test stands in `tests/test_conduct.py`.
  Verify: `git grep -c -h 'def test_a_halt_in_a_phase_resumes_there' -- tests/test_conduct.py` prints `1`.
- [x] 1.17 **HALT CHECK** 0105·R6 stays accepted: its test stands in `tests/test_conduct.py`.
  Verify: `git grep -c -h 'def test_a_version_with_adversarial_skipped_ships_on_a_stub' -- tests/test_conduct.py` prints `1`.
- [x] 1.18 **HALT CHECK** 0108·R10 stays accepted: its test stands in `tests/test_conduct.py`.
  Verify: `git grep -c -h 'def test_a_version_converges_with_no_conducting_worker' -- tests/test_conduct.py` prints `1`.
- [x] 1.19 **HALT CHECK** 0098·R1: the suite total it counted is gone from the archived design of 0098.
  Verify: `git grep -n 'sums to 278' -- openspec/changes/archive` prints nothing.
- [x] 1.20 **HALT CHECK** 0113·R1 stays wontfix: the range stands in the archived design of 0113.
  Verify: `git grep -c -h 'context of 100–275k tokens' -- openspec/changes/archive/0113-plan-review-diet/design.md` prints `1`.
- [x] 1.21 **HALT CHECK** 0114·R2: the timing is gone from the archived design of 0114.
  Verify: `git grep -n 'about 330 s' -- openspec/changes/archive` prints nothing.
- [x] 1.22 **HALT CHECK** 0116·R1 stays wontfix: the requirement stands in `openspec/specs/sdd/spec.md`.
  Verify: `git grep -c -h 'SHALL write three files' -- openspec/specs/sdd/spec.md` prints `1`.

## 2 — the prose and archive cards; C4 under the threat model's Out of scope

Each sub-task edits one file as the card's Fix says, before → after, and its `Verify:` finds the new text or the lack of the old. A quoted before-text may span a line break of its file: join the lines when replacing, and keep each new needle on one line.

- [x] 2.1 0086·R3. In `openspec/changes/archive/0086-ship-fixes-3/design.md`, `D3`'s "its halt names `left or first`, else …" sentence becomes "its halt names `left or first`; a clean merge whose `decisions` rule halts names that halt and `git -C <tree> merge --no-ff --no-commit <default>`", and the `## Tests` bullet for `test_a_merge_in_renumbers_a_planned_decision` gains that halt as a step.
  Verify: `git grep -c -h 'a clean merge whose .decisions. rule halts names that halt' -- openspec/changes/archive/0086-ship-fixes-3/design.md` prints `1`.
- [x] 2.2 0086·R3. In `openspec/changes/archive/0086-ship-fixes-3/proposal.md`, add to *Modified Capabilities* the line "MODIFIED *The ship station takes cut versions to the default branch*: a clean merge whose `decisions` rule halts names the hand merge",
  and add `skills/mf-ship/SKILL.md` to its *Impact*.
  Verify: `git grep -c -h 'MODIFIED \*The ship station takes cut versions to the default branch\*' -- openspec/changes/archive/0086-ship-fixes-3/proposal.md` prints `1`.
- [x] 2.3 0089·R5. In `skills/mf-release/SKILL.md`, the gate-check step's "the person's `docs(<change-id>): amend the change directory` commit does" gains ", or under the version's switch its supervisor's ([D61](../../docs/decisions.md#d61--a-supervisor-answers-what-rescue-diagnoses))".
  Verify: `git grep -c -h "or under the version's switch its supervisor's" -- skills/mf-release/SKILL.md` prints `1`.
- [x] 2.4 0089·R6. In `CHANGELOG.md`, the `0089-supervisor` phase 2 line "no supervisor runs over a blocking security card" becomes "no supervisor runs over a blocking security card at a converge halt".
  Verify: `git grep -c -h 'blocking security card at a converge halt' -- CHANGELOG.md` prints `1`.
- [x] 2.5 0091·R2. In `openspec/changes/archive/0091-cut-halts/proposal.md`, the frontmatter line becomes `debt: [0082·S5, 0083·S3, 0088·S9, 0088·S10]`.
  Verify: `git grep -c -h -F 'debt: [0082·S5, 0083·S3, 0088·S9, 0088·S10]' -- openspec/changes/archive/0091-cut-halts/proposal.md` prints `1`.
- [x] 2.6 0096·R2. In `openspec/changes/archive/0096-codex-ready/design.md`, `D7`'s clause "so a forged worktree entry under `/tmp` names no folder a Codex worker could make" becomes "so a Claude worker's own temp folder can still hold the folder a forged worktree entry under `/tmp` names, as *Known gaps* says".
  Verify: `git grep -n 'names no folder a Codex worker could make' -- openspec/changes/archive` prints nothing.
- [x] 2.7 0099·R2. In `docs/decisions.md`, D45's bold sentence "`integrate.py delta` on the open merge, commits when that passes, and else leaves the merge open with its note" becomes "`integrate.py delta` on the open default-branch merge, commits when that passes, and else leaves the merge open with its note; the conductor's own `chore(stack)` merge runs no delta check".
  Verify: `git grep -c -h 'merge runs no delta check' -- docs/decisions.md` prints `1`.
- [x] 2.8 0099·R6. In `openspec/changes/archive/0099-stacked-builds/proposal.md`, "it stacks again on the dependency's next build." becomes "it stacks again on the dependency's next build while that dependency is unreleased; once it has released, the dependent builds on the default branch."
  Verify: `git grep -c -h 'once it has released, the dependent builds on the default branch' -- openspec/changes/archive/0099-stacked-builds/proposal.md` prints `1`.
- [x] 2.9 0104·R5. In `openspec/changes/archive/0104-codex-limits/design.md`, `D6`'s "The real check" bullet ends "then `codex sandbox -P mf -c <profile> -C <the worktree> -- git write-tree` exits 0, `<profile>` a `permissions.mf` profile extending `:workspace` that makes those roots writable and `:slash_tmp` and `:tmpdir` read-only"; delete its `Fix note (2026-11-09, R1)` paragraph.
  Verify: `git grep -n 'Fix note (2026-11-09, R1)' -- openspec/changes/archive/0104-codex-limits/design.md` prints nothing.
- [x] 2.10 0111·R5. In `openspec/changes/archive/0111-sandbox-tmp/design.md`, the *Risks / Trade-offs* cell's first clause "phase 1 alone makes its gate green" becomes "phase 1 leaves its gate red until phase 4's repair ([D9](#d9))", the rest of the cell kept.
  Verify: `git grep -n 'phase 1 alone makes its gate green' -- openspec/changes/archive` prints nothing.
- [x] 2.11 0113·R2. In `openspec/changes/archive/0113-plan-review-diet/design.md`, `D4`'s `monkeypatch` row reads "a line holding the name in quotes or after a dot, inside a `setattr` or `patch` call that may span lines", and its `import reader` row reads "a line `import <stem>`, `from <pkg> import <stem>` or `from . import <stem>`, `<stem>` the file's name without its suffix".
  Verify: `git grep -c -h 'inside a .setattr. or .patch. call that may span lines' -- openspec/changes/archive/0113-plan-review-diet/design.md` prints `1`.
- [x] 2.12 0115·R4. In `openspec/changes/archive/0115-plan-metrics/design.md`, `D6`'s "The first repo that holds both gives the row's `repo`" becomes "The one repo that holds both gives the row's `repo`; two such repos are ambiguous, and the row binds to none".
  Verify: `git grep -n 'first repo that holds both' -- openspec/changes/archive` prints nothing.
- [x] 2.13 0100·R3. In `skills/mf-build/SKILL.md`, make the `bundle.py --decisions` command end `tasks.md openspec/changes/<change-id>/specs/*/spec.md`, the delta's files after the tasks file.
  Verify: `git grep -c -h -F 'tasks.md openspec/changes/<change-id>/specs/*/spec.md' -- skills/mf-build/SKILL.md` prints `1`.
- [x] 2.14 0100·S6. In `THREAT_MODEL.md`, add to *Known gaps* the bullet "A plugin enabled outside the user settings file, managed settings among them, still starts in a Claude worker (`0100·S6`)."
  Verify: `git grep -c -h 'enabled outside the user settings file' -- THREAT_MODEL.md` prints `1`.
- [x] 2.15 0100·S7. In `AGENTS.md`, "when a task names the file" becomes "when a task names the file or a path `## Surfaces` of the threat model matches".
  Verify: `git grep -c -h 'or a path .## Surfaces. of the threat model matches' -- AGENTS.md` prints `1`.
- [x] 2.16 0100·S7. In `skills/mf-build/SKILL.md`, "when a task names the file" becomes "when a task names the file or a path `## Surfaces` of the threat model matches".
  Verify: `git grep -c -h 'or a path .## Surfaces. of the threat model matches' -- skills/mf-build/SKILL.md` prints `1`.
- [x] 2.17 0100·S7. In `skills/mf-cut-change/SKILL.md`, the reading line's "when the source's phases name the file" becomes "when the source's phases name the file or a path `## Surfaces` of the threat model matches".
  Verify: `git grep -c -h 'name the file or a path .## Surfaces. of the threat model matches' -- skills/mf-cut-change/SKILL.md` prints `1`.
- [x] 2.18 0095·S3 per [D3](design.md#d3). In `THREAT_MODEL.md`, add to *Out of scope*, before the bullet "A planted skip.", the bullet "**A security card is the category its checker writes.** C4 of `0095-converge-roles`, confirmed by the person on 2026-11-11: the rescue and the supervisor are barred from a card whose Priority's category is `security`, so a security harm graded under another category reaches them under the version's switch ([D60](docs/decisions.md#d60--a-run-heals-its-own-halts), [D61](docs/decisions.md#d61--a-supervisor-answers-what-rescue-diagnoses))."
  Verify: `git grep -c -h 'C4' -- THREAT_MODEL.md` prints `1`.

## 3 — corpus.py skips old findings and follows no linked case; review_metrics $NAME and per-repo marks; 0100·S4, 0101·R7, 0114·R7

Each code sub-task writes its test first, runs it red, then makes the fix, and its `Verify:` runs after the fix ([D8](design.md#d8)).

- [x] 3.1 **CORPUS** `open-cards` In `tests/test_corpus.py` add `test_a_case_skips_an_input_its_shape_does_not_match`, and in `scripts/corpus.py` let a case hold an optional `shape` ([D9](design.md#d9)). The test: `shape = "^ok"` over one file that opens `ok` and one that does not prints `corpus: <name> · 1 runs · 1 skipped · pass`, and a case whose every input is skipped prints `corpus: <name> · no input`. The code: `broken` returns `<name>: shape is not a regex` for a `shape` that is no string or does not compile; `run_case` keeps an input only when `re.search` of its text, read with `errors="replace"` and `re.MULTILINE`, finds it; its last line reads `· <n> runs · <k> skipped · pass`, `<n>` the inputs run and the skipped part present only when `k` is above zero.
  Verify: `uv run pytest tests/test_corpus.py -q -k shape_does_not_match` exits 0.
- [x] 3.2 **CORPUS** `open-cards` In `scripts/corpus.toml`, give the `open-cards` case `shape = '^[ \t]+- \*\*Status:\*\*'`, a findings file with no card Status being older than the card shape ([D9](design.md#d9)).
  Verify: `git grep -n "shape = " -- scripts/corpus.toml` prints a line.
- [x] 3.3 **CORPUS** `open-cards` In `tests/test_corpus.py` add `test_a_linked_case_directory_is_refused`, and in `scripts/corpus.py`'s `run_case` raise `Stop(f"corpus/{name} is a link")` before the `rmtree` when `minions / "corpus" / name` is a link (0103·S2). The test: `corpus/<name>` a link to a folder holding `1/keep.txt`; `corpus.main` returns 2 printing `corpus: cannot run — corpus/<name> is a link`, and `keep.txt` stands.
  Verify: `uv run pytest tests/test_corpus.py -q -k linked_case_directory` exits 0.
- [x] 3.4 **CORPUS** `review-metrics` In `tests/test_review_metrics.py` extend `test_a_span_is_bound_to_the_ids_a_cut_queued`, and in `skills/mf-review-metrics/scripts/review_metrics.py` let `_token` replace a value `$NAME` or `${NAME}` ([D10](design.md#d10)). The test: a `conduct.py cut` call reading `B=<brief>; … brief=$B`, and another with `brief="${B}"`, each bind the span to the id; an unassigned `brief=$C` stays as written and binds none. The code: the value comes from an earlier `NAME=<value>` word of the same command, its trailing `;`, `&` and `|` dropped from the value; a name no word assigns stays as written.
  Verify: `uv run pytest tests/test_review_metrics.py -q -k bound_to_the_ids` exits 0.
- [x] 3.5 **CORPUS** `review-metrics` In `tests/test_review_metrics.py` extend `test_operator_work_is_booked_to_the_nearest_mark`, and in `skills/mf-review-metrics/scripts/review_metrics.py` give `_operator` an optional fourth parameter `repos: Sequence[Path] = ()`, which `booked` passes ([D10](design.md#d10)). The test: two repos each hold a mark, a session record with `"cwd"` of the second repo books its operator messages to the second repo's mark though the first's is nearer, and a session with no `cwd`, or a call with no `repos`, books as before. The code: `_events` emits one `{"event": "cwd", "cwd": <text>}` event for the first row holding a string `cwd`, none when no row does, `_sessions` copies its text into the session record as `"cwd"`, and `_operator` keeps only the marks whose `repo` equals the `name` of the repo `cwd` is, holds, or names by `gitdir:` in its `.git` file as `<repo>/.git/worktrees/<name>`.
  Verify: `uv run pytest tests/test_review_metrics.py -q -k nearest_mark` exits 0.
- [x] 3.6 **CORPUS** `review-metrics` In `tests/test_review_metrics.py` extend `test_review_metrics_books_a_worker_by_its_log_name`, and in `skills/mf-review-metrics/scripts/review_metrics.py`'s `_log_workers` skip a `task_started` whose `task_type` is a string other than `local_agent` (0100·S4). The test: a converge log whose `task_started` events are one `local_agent` and one `local_bash` named like a worker has the agent as its only worker.
  Verify: `uv run pytest tests/test_review_metrics.py -q -k books_a_worker_by_its_log_name` exits 0.
- [x] 3.7 0101·R7. In `tests/test_bundle.py`, the first docstring line "the decisions and living requirements a change cites." becomes `"""Converge's bundle: the decisions it cites and the requirements its delta changes.`, no longer holding `living requirements a change cites`.
  Verify: `git grep -n 'living requirements a change cites' -- tests/test_bundle.py` prints nothing.
- [x] 3.8 0114·R7. In `tests/test_plan_check.py`, delete the comment "A new commit on the same tree runs every command again: `HEAD` keys them all." above the empty commit in `test_a_result_is_kept_by_tree_and_reused`, keeping the commit and its assertions.
  Verify: `git grep -n -F 'A new commit on the same tree runs every command again' -- tests/test_plan_check.py` prints nothing.

## 4 — cut_check.py's row for a Verify: needle a later task removes

- [ ] 4.1 In `tests/test_cut_check.py` add the defect `_needle_removed_by_a_later_task` as row `V6` of `test_each_mechanical_row_fails_by_name` and `test_a_needle_a_later_task_adds_back_passes_v6`, and in `skills/mf-cut-change/scripts/cut_check.py` add `row_v6(change, plan)` after `row_v1` ([D11](design.md#d11)). The tests: the first sub-task's `Verify:` greps `x` in `a.py`, and a later sub-task naming `a.py` holds a fenced `diff` block, before its `Verify:` line, with the removed line `-x` (the row fails) or the removed line `-x` and the added line `+x` (the row is silent). The code: read the raw `change.tasks`, not `plan["subtasks"]`, which joins lines; return `<task>: <needle> is removed in <later>` for a needle a later sub-task naming the search's file quotes in a removed line; add `"V6"` to `ROWS` after `"V5"` and `("V6", row_v6(change, plan))` after `V5` in `check`.
  Verify: `uv run pytest tests/test_cut_check.py -q -k "V6 or adds_back"` exits 0.
- [ ] 4.2 In `skills/mf-cut-change/SKILL.md`, change both `V1`–`V5` to `V1`–`V6`, and in Step 8's second bullet add "a needle a later task removes" to what the rows settle.
  Verify: `git grep -n 'V6' -- skills/mf-cut-change/SKILL.md` prints a line.

