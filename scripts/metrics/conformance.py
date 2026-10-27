# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Print a conformance count: `trailer`, `minions` or `amends`.

`trailer` — commits in base..head whose `Change` trailer is not the change id.
`minions` — files tracked under `.minions/`. `amends` — the cut's amend commits
in base..head. Why: 0030-change-impact design D7.
"""

import os
import subprocess
import sys
from pathlib import Path


def _git(root: Path, *args: str) -> str:
    """Return a git command's stdout; a failure raises."""
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True
    ).stdout


def count(root: Path, kind: str, change: str, base: str, head: str) -> int:
    """Return the `kind` count for the change's commits over `base..head`."""
    span = f"{base}..{head}"
    if kind == "minions":
        return len(_git(root, "ls-files", "--", ".minions").splitlines())
    if kind == "amends":
        subject = f"docs({change}): amend the change directory"
        return _git(root, "log", "--format=%s", span).splitlines().count(subject)
    form = "--format=%(trailers:key=Change,valueonly,separator=%x2C)%x1e"
    trailers = _git(root, "log", form, span).split("\x1e")[:-1]
    return sum(value.strip() != change for value in trailers)


if __name__ == "__main__":
    env = os.environ
    print(
        count(
            Path.cwd(),
            sys.argv[1],
            env["MF_METRICS_CHANGE"],
            env["MF_METRICS_BASE"],
            env["MF_METRICS_HEAD"],
        )
    )
