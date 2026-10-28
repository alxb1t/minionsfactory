"""The bundled gate check: fresh exports, gate makefiles, planned changes, ignore marks.

Real git and make in a scratch repository: the routes are make's own behaviour.
Why: 0034-gate-recipe-hardening design D1…D4.
"""

import os
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO / "skills" / "mf-converge" / "scripts" / "gate_check.py"
_CHANGE = "0002-x"
_UNPLANNED = (
    "## Progress\n\n- [ ] 1 — One\n\n## 1 — One\n\n- [ ] 1.1 Edit `README.md`.\n"
)
_GATE = "gate:\n\techo a\n\techo b\n"


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=mf", "-c", "user.email=mf@example.invalid"]
        + ["-c", "commit.gpgsign=false", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _commit(root: Path, files: dict[str, str], message: str) -> None:
    for name, text in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(text)
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", message)


def _branch(
    root: Path, base: dict[str, str], tasks: str, branch: dict[str, str]
) -> str:
    """Commit `base`, then the cut with `tasks`, then `branch`; return the base."""
    root.mkdir(exist_ok=True)
    _git(root, "init", "-q")
    _commit(root, {".gitignore": ".minions/\n.env\n", **base}, "base")
    first = _git(root, "rev-parse", "HEAD")
    change = f"openspec/changes/{_CHANGE}"
    _commit(root, {f"{change}/design.md": "# X\n", f"{change}/tasks.md": tasks}, "cut")
    _commit(root, branch, "build")
    return first


def _check(
    root: Path, base: str, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), "--change", _CHANGE, "--base", base],
        cwd=root,
        env={**os.environ, **(env or {})},
        capture_output=True,
        text=True,
    )


def _planned(quote: str = "") -> str:
    return f"## 1 — One\n\n- [ ] 1.1 Change the `gate` recipe in `Makefile`.{quote}\n"


def test_an_unchanged_gate_passes(tmp_path: Path) -> None:
    base = _branch(tmp_path, {"Makefile": _GATE}, _UNPLANNED, {"README.md": "x\n"})
    # A calling make's `-q` would fail both dry runs unless the check clears it.
    result = _check(tmp_path, base, {"MAKEFLAGS": "q"})
    assert (result.returncode, result.stdout) == (0, "gate: no unplanned change\n")
    exports = tmp_path / ".minions" / "gate-check"
    assert not exports.exists() or not any(exports.iterdir())


def test_an_include_changed_on_the_branch_halts(tmp_path: Path) -> None:
    files = {
        "Makefile": "include gate.mk\ngate:\n\t$(CHECK)\n",
        "gate.mk": "CHECK = false\n",
    }
    base = _branch(tmp_path, files, _UNPLANNED, {"gate.mk": "CHECK = true\n"})
    result = _check(tmp_path, base)
    assert result.returncode == 1
    assert result.stdout.endswith("names `Makefile` and `gate`:\n  gate.mk\n")

    # A makefile the base's wildcard picks up cannot drop itself from the list.
    wildcard = tmp_path / "wildcard"
    files = {"Makefile": "include $(wildcard mk/*.mk)\ngate:\n\tfalse\n"}
    files["mk/a.mk"] = "A = 1\n"
    hidden = ".IGNORE:\nMAKEFILE_LIST := Makefile mk/a.mk\n"
    hidden += "$(info make: Entering directory `/')\n"
    base = _branch(wildcard, files, _UNPLANNED, {"mk/z.mk": hidden})
    result = _check(wildcard, base)
    assert result.returncode == 1, result.stdout
    assert result.stdout.endswith(":\n  mk/z.mk\n")

    # A file make reads through `$(shell)` is no makefile, but its dry run differs.
    data = tmp_path / "data"
    files = {"Makefile": "CMD := $(shell cat gate.cmd)\ngate:\n\t$(CMD)\n"}
    base = _branch(
        data, {**files, "gate.cmd": "false\n"}, _UNPLANNED, {"gate.cmd": "true\n"}
    )
    result = _check(data, base)
    assert result.returncode == 1, result.stdout
    assert "and no cut task names" in result.stdout
    assert "\n-false\n+true" in result.stdout

    # Preserve the names Git tracks when make follows an include symlink, including
    # a parent directory, or Git would quote the filename in line-based output.
    cases = [
        (
            "symlink",
            {
                "Makefile": "include rules.mk\ngate:\n\tfalse\n",
                "strict.mk": "# strict\n",
                "loose.mk": ".IGNORE:\n",
            },
            ("rules.mk", "strict.mk", "loose.mk"),
            "rules.mk",
        ),
        (
            "recipe-symlink",
            {
                "Makefile": "include gate.mk\n",
                "strict.mk": "gate:\n\tfalse\n",
                "ignored.mk": "gate:\n\t-false\n",
            },
            ("gate.mk", "strict.mk", "ignored.mk"),
            "gate.mk",
        ),
        (
            "parent-symlink",
            {
                "Makefile": "include rules/gate.mk\n",
                "strict/gate.mk": "gate:\n\tfalse\n",
                "ignored/gate.mk": "gate:\n\t-false\n",
            },
            ("rules", "strict", "ignored"),
            "rules",
        ),
        (
            "quoted-name",
            {"Makefile": "include café.mk\ngate:\n\tfalse\n", "café.mk": "# strict\n"},
            None,
            "café.mk",
        ),
    ]
    failures = []
    for label, initial, link, changed in cases:
        root = tmp_path / label
        root.mkdir()
        if link:
            (root / link[0]).symlink_to(link[1])
        edits = {"README.md": "x\n"} if link else {changed: ".IGNORE:\n"}
        base = _branch(root, initial, _UNPLANNED, edits)
        if link:
            (root / link[0]).unlink()
            (root / link[0]).symlink_to(link[2])
            _commit(root, {}, "retarget include")
        result = _check(root, base)
        if result.returncode != 1 or not result.stdout.endswith(f":\n  {changed}\n"):
            failures.append((label, result.returncode, result.stdout))
    assert not failures, failures


def test_a_sub_make_weakened_on_the_branch_halts(tmp_path: Path) -> None:
    files = {"Makefile": "gate:\n\t$(MAKE) -C checks check\n"}
    files["checks/Makefile"] = "check:\n\tuv run pytest -q\n"
    weakened = {"checks/Makefile": "check:\n\tuv run pytest -q || true\n"}
    base = _branch(tmp_path, files, _UNPLANNED, weakened)
    result = _check(tmp_path, base)
    assert result.returncode == 1
    assert result.stdout.endswith(":\n  checks/Makefile\n")


def test_a_dash_prefix_halts(tmp_path: Path) -> None:
    files = {"Makefile": "gate:\n\tfalse\n"}
    base = _branch(tmp_path, files, _UNPLANNED, {"Makefile": "gate:\n\t-false\n"})
    result = _check(tmp_path, base)
    assert result.returncode == 1
    assert result.stdout.endswith(":\n  Makefile\n")


def test_an_ignore_target_halts(tmp_path: Path) -> None:
    branch = {"Makefile": f".IGNORE:\n{_GATE}"}
    base = _branch(tmp_path, {"Makefile": _GATE}, _UNPLANNED, branch)
    result = _check(tmp_path, base)
    assert result.returncode == 1
    assert result.stdout.endswith(":\n  Makefile\n")


def test_makeflags_ignore_halts(tmp_path: Path) -> None:
    branch = {"Makefile": f"MAKEFLAGS += -i\n{_GATE}"}
    base = _branch(tmp_path, {"Makefile": _GATE}, _UNPLANNED, branch)
    result = _check(tmp_path, base)
    assert result.returncode == 1
    assert result.stdout.endswith(":\n  Makefile\n")


def test_a_planned_change_that_drops_a_line_halts(tmp_path: Path) -> None:
    branch = {"Makefile": "gate:\n\techo a\n"}
    base = _branch(tmp_path, {"Makefile": _GATE}, _planned(), branch)
    result = _check(tmp_path, base)
    assert result.returncode == 1
    assert "\n  dropped: echo b\n" in result.stdout
    assert "\n-echo b" in result.stdout


def test_a_planned_dash_the_task_does_not_quote_halts(tmp_path: Path) -> None:
    branch = {"Makefile": "gate:\n\techo a\n\t-echo b\n"}
    base = _branch(tmp_path, {"Makefile": _GATE}, _planned(), branch)
    result = _check(tmp_path, base)
    assert result.returncode == 1
    assert "\n  added: Makefile: -echo b\n" in result.stdout
    assert "dropped" not in result.stdout

    # A pattern list misses forms: a `-` after a rule's `;` or from a variable,
    # `.ONESHELL`, a continued rule line, `define`, a computed name, `$(eval)`, a
    # `$(shell)` value. Every added line the task does not quote halts.
    unlisted = tmp_path / "unlisted"
    lines = [
        "SHELL := /bin/sh",
        "I := -",
        ".ONESHELL:",
        "side: ; -echo d",
        "\t$(I)echo b",
        "S := SHELL",
        "$(S) := /bin/sh",
        "define SHELL",
        "/bin/sh",
        "endef",
        "$(eval MAKEFLAGS += -i)",
        "MF := MAKEFLAGS",
        "$(MF) += -i",
        "MAKEFLAGS += $(shell echo ki)",
        "gate: \\",
        " ; -false",
    ]
    branch = {"Makefile": "\n".join(lines) + "\n"}
    base = _branch(unlisted, {"Makefile": "gate:\n\tfalse\n"}, _planned(), branch)
    result = _check(unlisted, base)
    assert result.returncode == 1, result.stdout
    for line in lines:
        assert f"\n  added: Makefile: {line.strip()}\n" in result.stdout


def test_a_planned_change_that_removes_an_unquoted_line_halts(tmp_path: Path) -> None:
    # The dry run never prints `SHELL`, so only the diff's removed line shows it.
    gate = f"SHELL := /bin/bash -o pipefail\n{_GATE}"
    base = _branch(tmp_path, {"Makefile": gate}, _planned(), {"Makefile": _GATE})
    result = _check(tmp_path, base)
    assert result.returncode == 1, result.stdout
    assert "\n  removed: Makefile: SHELL := /bin/bash -o pipefail\n" in result.stdout


def test_a_planned_change_the_task_quotes_passes(tmp_path: Path) -> None:
    branch = {"Makefile": "gate:\n\techo a\n\t-echo c\n"}
    tasks = _planned("\n  It drops `echo b` and adds `-echo c`.")
    base = _branch(tmp_path, {"Makefile": _GATE}, tasks, branch)
    result = _check(tmp_path, base)
    assert result.returncode == 0, result.stdout
    assert result.stdout.startswith("gate: planned — 1.1 Change the `gate` recipe")
    assert "\n-echo b\n+echo c\n" in result.stdout


def test_a_dry_run_failing_in_an_export_exits_2(tmp_path: Path) -> None:
    files = {"Makefile": f"include .env\n{_GATE}", ".env": "KEY = x\n"}
    base = _branch(tmp_path, files, _UNPLANNED, {"README.md": "x\n"})
    result = _check(tmp_path, base)
    assert result.returncode == 2
    assert result.stdout.startswith("gate: cannot check — the base's make database")
    assert ".env" in result.stdout
    assert not (tmp_path / ".minions" / "gate-check" / _CHANGE).exists()

    # A path the branch marks `export-ignore` is missing from its export.
    ignored = tmp_path / "ignored"
    branch = {
        "GNUmakefile": "gate:\n\ttrue\n",
        ".gitattributes": "GNUmakefile export-ignore\n",
    }
    base = _branch(ignored, {"Makefile": "gate:\n\tfalse\n"}, _UNPLANNED, branch)
    result = _check(ignored, base)
    assert result.returncode == 2, result.stdout
    assert result.stdout == "gate: cannot check — the head's export lacks GNUmakefile\n"


def test_no_single_cut_commit_halts(tmp_path: Path) -> None:
    base = _branch(tmp_path, {"Makefile": _GATE}, _UNPLANNED, {"README.md": "x\n"})
    design = f"openspec/changes/{_CHANGE}/design.md"
    _git(tmp_path, "rm", "-q", design)
    _git(tmp_path, "commit", "-q", "-m", "drop")
    _commit(tmp_path, {design: "# X\n"}, "again")
    result = _check(tmp_path, base)
    assert result.returncode == 1
    assert result.stdout.startswith("gate: halt — no single cut commit")
