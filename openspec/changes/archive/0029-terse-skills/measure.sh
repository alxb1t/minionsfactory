# Print words and bytes of each reading set. Usage, from the repository root: sh measure.sh
# A station reads the shared context, then its skill; a generic worker also loads converge as its owning contract.
set -eu
S="AGENTS.md docs/principles.md docs/decisions.md"
C=skills/mf-converge
m() { n=$1; shift; printf '%s ' "$n"; cat "$@" | wc -w -c | awk '{print $1, $2}'; }
m shared $S
m cut $S skills/mf-cut-change/SKILL.md
m build-native $S skills/mf-build/SKILL.md
m build-generic $S skills/mf-build/SKILL.md skills/mf-build/references/generic-simplify.md
m converge-conductor $S $C/SKILL.md
m review-worker-generic $S $C/SKILL.md $C/references/generic-review.md
m security-worker-generic $S $C/SKILL.md $C/references/generic-security.md
m release $S skills/mf-release/SKILL.md
m bootstrap skills/mf-bootstrap/SKILL.md
