# Print `kept` when lines FROM–TO of PATH at v0.28.0 appear in PATH now, line breaks and indents aside.
# Usage, from the repository root: sh kept.sh PATH FROM TO. A failed read exits non-zero, never `kept`.
set -eu
old=$(git show "a926ca1:$1" | sed -n "$2,$3p" | tr -s ' \n' ' ')
[ -n "${old# }" ] || { echo "no text at a926ca1:$1 lines $2-$3" >&2; exit 1; }
new=$(tr -s ' \n' ' ' < "$1")
case "$new" in *"${old% }"*) echo kept ;; *) echo changed ;; esac
