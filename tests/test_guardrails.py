"""Guardrail scan: no tracked file holds a home path or a key."""

import re
import subprocess
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent

# Each needle is built from parts so this file never matches itself.
# Why: 0023-backlog-paydown design B6.
_SHAPES = {
    "home path": re.compile("/(" + "Users" + "|" + "home" + r")/[A-Za-z][\w.-]*"),
    "Anthropic key": re.compile("sk" + "-ant-"),
    "GitHub token": re.compile("gh" + "[pousr]_|github" + "_pat_"),
    "AWS key id": re.compile("A" + "[KS]IA" + "[0-9A-Z]{16}"),
    "private key": re.compile("-----" + "BEGIN [A-Z ]*" + "PRIVATE KEY" + "-----"),
}


def _hits(root: Path) -> list[str]:
    """Return one line per shape found in a file `git ls-files` lists under `root`.

    e.g. a home path on line 3 of `a.md` → "a.md:3: home path"
    """
    listed = subprocess.run(
        ["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True
    ).stdout.decode()
    hits: list[str] = []
    for name in filter(None, listed.split("\0")):
        path = root / name
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if not any(shape.search(text) for shape in _SHAPES.values()):
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            hits += [
                f"{name}:{number}: {kind}"
                for kind, shape in _SHAPES.items()
                if shape.search(line)
            ]
    return hits


def test_no_tracked_file_holds_a_home_path_or_a_key() -> None:
    assert _hits(_REPO) == []


def test_the_guardrail_scan_reports_a_planted_path_and_key(tmp_path: Path) -> None:
    # A staged file is listed before any commit; an untracked one is not.
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    planted = (
        ("See /" + "Users/someone/notes.", "home path"),
        ("Home: `/" + "home/someone`.", "home path"),
        ("Key: " + "sk" + "-ant-x", "Anthropic key"),
        *(("Token: " + "gh" + p + "_x", "GitHub token") for p in "pousr"),
        ("Token: " + "github" + "_pat_x", "GitHub token"),
        *(("Id: " + p + "IA" + "A" * 16, "AWS key id") for p in ("AK", "AS")),
        ("-----" + "BEGIN RSA " + "PRIVATE KEY" + "-----", "private key"),
    )
    text = "\n".join(("Read me.", *(line for line, _ in planted)))
    (tmp_path / "notes.md").write_text(text)
    (tmp_path / "loose.md").write_text(text)
    subprocess.run(["git", "add", "notes.md"], cwd=tmp_path, check=True)

    assert _hits(tmp_path) == [
        f"notes.md:{number}: {kind}"
        for number, (_, kind) in enumerate(planted, start=2)
    ]
