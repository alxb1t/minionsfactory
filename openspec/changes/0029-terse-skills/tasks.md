# Terse skills — tasks

Build the settled [design](design.md), one phase at a time. `C` below is `openspec/changes/0029-terse-skills`.
Every rewrite follows [D2](design.md#d2) and its Step 5 example, keeps [D3](design.md#d3)'s interfaces, and adds
its file's section to `C/rule_map.md` as [D4](design.md#d4) shapes it.

## Progress

- [x] 1 — Rewrite converge and its generic review and security
- [x] 2 — Rewrite build and its generic simplify
- [ ] 3 — Rewrite the cut
- [ ] 4 — Rewrite the release
- [ ] 5 — Rewrite the bootstrap
- [ ] 6 — Rewrite the shared context
- [ ] 7 — Measure the reading sets and build the reader prompts
- [ ] 8 — Run the fresh-reader check **HUMAN · METERED**

## 1 — Rewrite converge and its generic review and security

- [x] 1.1 Rewrite `skills/mf-converge/SKILL.md`; create `openspec/changes/0029-terse-skills/rule_map.md` with its section.
  Verify: `[ "$(wc -w < skills/mf-converge/SKILL.md)" -lt 5900 ]` exits 0, and
  `sh openspec/changes/0029-terse-skills/kept.sh skills/mf-converge/SKILL.md 158 165` prints `kept`.
- [x] 1.2 Keep converge's headings, status-log events and card fields, per [D3](design.md#d3).
  Verify: `test "$(git show a926ca1:skills/mf-converge/SKILL.md | grep '^## ')" = "$(grep '^## ' skills/mf-converge/SKILL.md)"` exits 0, and
  ``for e in start freeze fan-out verdicts fix verify pickup catch-up backlog halt done; do grep -q "^| \`$e\` |" skills/mf-converge/SKILL.md || echo "$e"; done`` prints nothing.
- [x] 1.3 Rewrite `skills/mf-converge/references/generic-review.md` and `skills/mf-converge/references/generic-security.md`; add their sections.
  Verify: `grep -cE '^## skills/mf-converge/(SKILL|references/generic-(review|security))\.md$' openspec/changes/0029-terse-skills/rule_map.md` prints `3`, and
  `uv run pytest -q tests/test_skills.py` exits 0.

## 2 — Rewrite build and its generic simplify

- [x] 2.1 Rewrite `skills/mf-build/SKILL.md` and `skills/mf-build/references/generic-simplify.md`; add their sections.
  Verify: `[ "$(wc -w < skills/mf-build/SKILL.md)" -lt 4208 ]` exits 0, and
  `grep -cE '^## skills/mf-build/(SKILL|references/generic-simplify)\.md$' openspec/changes/0029-terse-skills/rule_map.md` prints `2`.
- [x] 2.2 Keep build's headings and its `I`, `P` and `T` rows, per [D3](design.md#d3).
  Verify: `test "$(git show a926ca1:skills/mf-build/SKILL.md | grep -E '^## |^\| \*\*[IPT][0-9]+\*\* \|')" = "$(grep -E '^## |^\| \*\*[IPT][0-9]+\*\* \|' skills/mf-build/SKILL.md)"` exits 0.

## 3 — Rewrite the cut

- [ ] 3.1 Rewrite `skills/mf-cut-change/SKILL.md`; add its section.
  Verify: `[ "$(wc -w < skills/mf-cut-change/SKILL.md)" -lt 3244 ]` exits 0, and
  `grep -c '^## skills/mf-cut-change/SKILL\.md$' openspec/changes/0029-terse-skills/rule_map.md` prints `1`.
- [ ] 3.2 Keep the cut's headings and its `I`, `P` and `T` rows, per [D3](design.md#d3).
  Verify: `test "$(git show a926ca1:skills/mf-cut-change/SKILL.md | grep -E '^## |^\| \*\*[IPT][0-9]+\*\* \|')" = "$(grep -E '^## |^\| \*\*[IPT][0-9]+\*\* \|' skills/mf-cut-change/SKILL.md)"` exits 0.

## 4 — Rewrite the release

- [ ] 4.1 Rewrite `skills/mf-release/SKILL.md`; add its section.
  Verify: `[ "$(wc -w < skills/mf-release/SKILL.md)" -lt 2788 ]` exits 0, and
  `grep -c '^## skills/mf-release/SKILL\.md$' openspec/changes/0029-terse-skills/rule_map.md` prints `1`.
- [ ] 4.2 Keep the release's headings and precondition 8, per [D3](design.md#d3).
  Verify: `test "$(git show a926ca1:skills/mf-release/SKILL.md | grep '^## ')" = "$(grep '^## ' skills/mf-release/SKILL.md)"` exits 0, and
  `sh openspec/changes/0029-terse-skills/kept.sh skills/mf-release/SKILL.md 93 100` prints `kept`.

## 5 — Rewrite the bootstrap

- [ ] 5.1 Rewrite `skills/mf-bootstrap/SKILL.md`, keeping its headings; add its section.
  Verify: `[ "$(wc -w < skills/mf-bootstrap/SKILL.md)" -lt 732 ]` exits 0,
  `test "$(git show a926ca1:skills/mf-bootstrap/SKILL.md | grep '^## ')" = "$(grep '^## ' skills/mf-bootstrap/SKILL.md)"` exits 0, and
  `grep -c '^## skills/mf-bootstrap/SKILL\.md$' openspec/changes/0029-terse-skills/rule_map.md` prints `1`.

## 6 — Rewrite the shared context

- [ ] 6.1 Rewrite `AGENTS.md`, `docs/principles.md` and `docs/decisions.md`; add their sections. Fix a link in `README.md` or `docs/README.md` only where its target moved.
  Verify: `grep -cE '^## (AGENTS|docs/principles|docs/decisions)\.md$' openspec/changes/0029-terse-skills/rule_map.md` prints `3`, and
  `uv run pytest -q tests/test_principles.py tests/test_skills.py` exits 0.
- [ ] 6.2 Keep every decision and principle heading, per [D3](design.md#d3).
  Verify: `test "$(git show a926ca1:docs/decisions.md | grep '^### ')" = "$(grep '^### ' docs/decisions.md)"` exits 0, and
  `test "$(git show a926ca1:docs/principles.md | grep '^### ')" = "$(grep '^### ' docs/principles.md)"` exits 0.

## 7 — Measure the reading sets and build the reader prompts

- [ ] 7.1 Run `sh openspec/changes/0029-terse-skills/measure.sh`; its output is the after table, in this phase's commit body beside [D5](design.md#d5)'s before table.
  Verify: `sh openspec/changes/0029-terse-skills/measure.sh | awk 'BEGIN { split("4947 8191 9155 9399 10847 11232 11202 7735 732", b) } $2 >= b[NR] { bad = 1 } END { exit bad }'` exits 0.
- [ ] 7.2 Build the reader prompts, per [D6](design.md#d6): `sh openspec/changes/0029-terse-skills/build_prompts.sh`.
  Verify: `ls .minions/0029-reader/*.prompt.md | wc -l` prints `10`.
- [ ] 7.3 **HALT CHECK** The installed executors are the versions [D6](design.md#d6)'s recipes were written for.
  Verify: `codex --version | grep -c '^codex-cli 0\.163\.'` prints `1`, and `claude --version | grep -c '^2\.1\.[0-9]* (Claude Code)$'` prints `1`.

## 8 — Run the fresh-reader check **HUMAN · METERED**

- [ ] 8.1 Run Codex over every prompt, from an empty directory:
  ```sh
  R=$(git rev-parse --show-toplevel); E="$R/openspec/changes/0029-terse-skills/evidence"
  mkdir -p "$E/codex" && cd "$(mktemp -d)"
  for p in "$R"/.minions/0029-reader/*.prompt.md; do n=$(basename "$p" .prompt.md)
    codex exec -m gpt-6.1-sol -s read-only --ephemeral --skip-git-repo-check --json -o "$n.txt" - < "$p" > "$E/codex/$n.events.jsonl"
    { echo "executor: $(codex --version) · model: gpt-6.1-sol"; echo; cat "$n.txt"; } > "$E/codex/$n.md"; done
  cd "$R"
  ```
  Verify: `ls openspec/changes/0029-terse-skills/evidence/codex/*.md | wc -l` prints `10`, and
  `grep -hoE '"type":"(command_execution|file_change|mcp_tool_call|web_search|collab_tool_call)"' openspec/changes/0029-terse-skills/evidence/codex/*.events.jsonl` prints nothing.
- [ ] 8.2 Run Claude Code over every prompt, from an empty directory:
  ```sh
  R=$(git rev-parse --show-toplevel); E="$R/openspec/changes/0029-terse-skills/evidence"
  mkdir -p "$E/claude" && cd "$(mktemp -d)"
  for p in "$R"/.minions/0029-reader/*.prompt.md; do n=$(basename "$p" .prompt.md)
    { echo "executor: $(claude --version) · model: claude-opus-5-5"; echo
      claude -p --model claude-opus-5-5 --tools "" --no-session-persistence --output-format text < "$p"; } > "$E/claude/$n.md"; done
  cd "$R"
  ```
  Verify: `ls openspec/changes/0029-terse-skills/evidence/claude/*.md | wc -l` prints `10`.
- [ ] 8.3 Judge every answer against [D6](design.md#d6)'s expected answers in `openspec/changes/0029-terse-skills/evidence/verdicts.md`, under the header `| executor | skill | n | old | new | verdict |`, one row per executor × question.
  Verify: `grep -cE '^\| (codex|claude) \|' openspec/changes/0029-terse-skills/evidence/verdicts.md` prints `72`, and
  `grep -c '| off |$' openspec/changes/0029-terse-skills/evidence/verdicts.md` prints `0`.
