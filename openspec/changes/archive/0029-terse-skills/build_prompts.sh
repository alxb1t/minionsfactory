# Write one reader prompt per skill and side to .minions/0029-reader/, run from the repository root.
# old is the text at v0.28.0; new is the text at HEAD. Usage: sh build_prompts.sh
set -eu
Q=openspec/changes/0029-terse-skills/questions
mkdir -p .minions/0029-reader
for side in old new; do
  if [ "$side" = old ]; then ref=a926ca1; else ref=$(git rev-parse --short HEAD); fi
  for skill in mf-cut-change mf-build mf-converge mf-release mf-bootstrap; do
    files=$(git ls-tree -r --name-only "$ref" "skills/$skill" | grep -v '/templates/')
    [ -n "$files" ] || { echo "no files for $skill at $ref" >&2; exit 1; }
    if [ "$skill" != mf-bootstrap ]; then files="AGENTS.md docs/principles.md docs/decisions.md $files"; fi
    {
      cat "$Q/preamble.md"
      for f in $files; do printf '\n=== %s\n\n' "$f"; git show "$ref:$f"; done
      printf '\n=== the questions\n\n'
      cat "$Q/$skill.md"
    } > ".minions/0029-reader/${skill}_$side.prompt.md"
  done
done
ls .minions/0029-reader
