# Capability: `diff` (frozen-diff supply)

Compute the target repo's diff for a commit range — list-argv git, never a shell — and supply it to a
read-only role by writing it to a patch file the role reads (the role has no shell of its own). This
spec captures the behavior shipped in `orchestrator/diff.py`; each scenario declares `Layers: unit`
and is bound to its proving test.

## Requirements

### Requirement: Compute the range diff

`compute_diff` SHALL compute the diff for `base..head` via a list-argv git invocation (no shell) and
return its output.

#### Scenario: The range argv is built and the output returned
- **Key:** `diff:compute:builds-range-argv`
- **Layers:** unit
- **WHEN** `compute_diff` runs for a base and head
- **THEN** it invokes `git diff base..head` as a list argv and returns the diff text

### Requirement: Supply the diff to a read-only role

`run_role_with_diff` SHALL write the diff to the patch file the read-only role reads, then run the
role — so the role reviews a frozen artifact rather than re-deriving the diff itself.

#### Scenario: The diff is written before the role runs
- **Key:** `diff:supply:writes-file-then-runs-role`
- **Layers:** unit
- **WHEN** `run_role_with_diff` runs
- **THEN** the diff is written to the patch file and then the role is run over it
