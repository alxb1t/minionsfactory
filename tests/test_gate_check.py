"""The bundled gate check: fresh exports, gate makefiles, planned changes, ignore marks.

Real git and make in a scratch repository: the routes are make's own behaviour.
Why: 0034-gate-recipe-hardening design D1…D4.
"""

import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

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
    root: Path, base: str, env: dict[str, str] | None = None, *extra: str
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), "--change", _CHANGE, "--base", base, *extra],
        cwd=root,
        env={**os.environ, **(env or {})},
        capture_output=True,
        text=True,
    )


def _planned(quote: str = "") -> str:
    return f"## 1 — One\n\n- [ ] 1.1 Change the `gate` recipe in `Makefile`.{quote}\n"


_HALT = (
    "gate: halt — the branch changes the gate, and no cut task quotes these lines:\n"
)


def _halted(result: subprocess.CompletedProcess[str], *lines: str) -> list[str]:
    """Return what the halt lacks: its header, or a `  <line>` entry."""
    missing = [] if result.returncode == 1 else [f"exit {result.returncode}"]
    missing += [] if result.stdout.startswith(_HALT) else ["the header"]
    return missing + [line for line in lines if f"\n  {line}\n" not in result.stdout]


def test_an_unchanged_gate_passes(tmp_path: Path) -> None:
    base = _branch(tmp_path, {"Makefile": _GATE}, _UNPLANNED, {"README.md": "x\n"})
    # A calling make's `-q` would fail both dry runs unless the check clears it.
    result = _check(tmp_path, base, {"MAKEFLAGS": "q"})
    assert (result.returncode, result.stdout) == (0, "gate: no unplanned change\n")
    exports = tmp_path / ".minions" / "gate-check"
    assert not exports.exists() or not any(exports.iterdir())


@pytest.mark.slow
def test_an_include_changed_on_the_branch_halts(tmp_path: Path) -> None:
    files = {
        "Makefile": "include gate.mk\ngate:\n\t$(CHECK)\n",
        "gate.mk": "CHECK = false\n",
    }
    base = _branch(tmp_path, files, _UNPLANNED, {"gate.mk": "CHECK = true\n"})
    result = _check(tmp_path, base)
    removed, added = "removed: gate.mk: CHECK = false", "added: gate.mk: CHECK = true"
    assert not _halted(result, removed, added), result.stdout

    # A makefile the base's wildcard picks up cannot drop itself from the list.
    wildcard = tmp_path / "wildcard"
    files = {"Makefile": "include $(wildcard mk/*.mk)\ngate:\n\tfalse\n"}
    files["mk/a.mk"] = "A = 1\n"
    hidden = ".IGNORE:\nMAKEFILE_LIST := Makefile mk/a.mk\n"
    hidden += "$(info make: Entering directory `/')\n"
    base = _branch(wildcard, files, _UNPLANNED, {"mk/z.mk": hidden})
    result = _check(wildcard, base)
    assert not _halted(result, "added: mk/z.mk: .IGNORE:"), result.stdout

    # A file make reads through `$(shell)` is no makefile, but its dry run differs.
    data = tmp_path / "data"
    files = {"Makefile": "CMD := $(shell cat gate.cmd)\ngate:\n\t$(CMD)\n"}
    base = _branch(
        data, {**files, "gate.cmd": "false\n"}, _UNPLANNED, {"gate.cmd": "true\n"}
    )
    result = _check(data, base)
    assert not _halted(result, "dropped: false"), result.stdout
    assert "\nThe dry run changed:\n" in result.stdout
    assert "\n-false\n+true" in result.stdout

    # With no plan, a dry run that only gains a line, no makefile edited, halts too.
    gained = tmp_path / "gained"
    files = {
        "Makefile": "EXTRA := $(shell cat extra.txt)\ngate:\n\techo a\n\t$(EXTRA)\n"
    }
    base = _branch(
        gained, {**files, "extra.txt": ""}, _UNPLANNED, {"extra.txt": "echo b\n"}
    )
    result = _check(gained, base)
    assert not _halted(result, "added to the dry run: echo b"), result.stdout
    assert "\n+echo b" in result.stdout

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
            "added: rules.mk: .IGNORE:",
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
            "added: gate.mk: -false",
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
            "added: rules/gate.mk: -false",
        ),
        (
            "quoted-name",
            {"Makefile": "include café.mk\ngate:\n\tfalse\n", "café.mk": "# strict\n"},
            None,
            "café.mk",
            "added: café.mk: .IGNORE:",
        ),
    ]
    failures = []
    for label, initial, link, changed, line in cases:
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
        if _halted(result, line):
            failures.append((label, result.returncode, result.stdout))
    # Every link followed while resolving an include can change its contents,
    # even when the direct include name and the dry run stay unchanged.
    topologies = [
        (
            "chain",
            "gate.mk",
            {"gate.mk": "alias.mk", "alias.mk": "strict/gate.mk"},
            "alias.mk",
            "ignored/gate.mk",
        ),
        ("directory", "rules/gate.mk", {"rules": "strict"}, "rules", "ignored"),
        (
            "directory-chain",
            "rules/gate.mk",
            {"rules": "alias", "alias": "strict"},
            "alias",
            "ignored",
        ),
        (
            "target-directory",
            "gate.mk",
            {"gate.mk": "rules/gate.mk", "rules": "strict"},
            "rules",
            "ignored",
        ),
        (
            "relative-chain",
            "links/gate.mk",
            {"links/gate.mk": "../alias/gate.mk", "alias": "strict"},
            "alias",
            "ignored",
        ),
        (
            "parent-after-link",
            "rules/../gate.mk",
            {"rules": "strict/deep"},
            "rules",
            "ignored/deep",
        ),
    ]
    for label, include, links, changed, target in topologies:
        for plan, tasks, expected in [
            ("unplanned", _UNPLANNED, 1),
            ("unquoted", _planned(), 1),
            ("quoted", _planned(" Quotes `false` and `-false`."), 0),
        ]:
            root = tmp_path / f"{label}-{plan}"
            root.mkdir()
            for name, destination in links.items():
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                (root / name).symlink_to(destination)
            initial = {
                "Makefile": f"include {include}\n",
                "strict/gate.mk": "gate:\n\tfalse\n",
                "ignored/gate.mk": "gate:\n\t-false\n",
                "strict/deep/keep": "",
                "ignored/deep/keep": "",
            }
            base = _branch(root, initial, tasks, {"README.md": "x\n"})
            (root / changed).unlink()
            (root / changed).symlink_to(target)
            _commit(root, {}, "retarget resolution dependency")
            result = _check(root, base)
            valid = result.returncode == expected
            if expected:
                valid &= result.stdout.startswith(_HALT)
                valid &= "removed:" in result.stdout and "added:" in result.stdout
                valid &= "false" in result.stdout and "-false" in result.stdout
            else:
                valid &= result.stdout.startswith("gate: planned")
            if not valid:
                failures.append((f"{label}-{plan}", result.returncode, result.stdout))
    assert not failures, "\n".join(map(str, failures))


def test_a_sub_make_weakened_on_the_branch_halts(tmp_path: Path) -> None:
    files = {"Makefile": "gate:\n\t$(MAKE) -C checks check\n"}
    files["checks/Makefile"] = "check:\n\tuv run pytest -q\n"
    weakened = {"checks/Makefile": "check:\n\tuv run pytest -q || true\n"}
    base = _branch(tmp_path, files, _UNPLANNED, weakened)
    result = _check(tmp_path, base)
    added = "added: checks/Makefile: uv run pytest -q || true"
    assert not _halted(result, added), result.stdout


def test_a_dash_prefix_halts(tmp_path: Path) -> None:
    files = {"Makefile": "gate:\n\tfalse\n"}
    base = _branch(tmp_path, files, _UNPLANNED, {"Makefile": "gate:\n\t-false\n"})
    result = _check(tmp_path, base)
    assert not _halted(result, "added: Makefile: -false"), result.stdout


def test_an_ignore_target_halts(tmp_path: Path) -> None:
    branch = {"Makefile": f".IGNORE:\n{_GATE}"}
    base = _branch(tmp_path, {"Makefile": _GATE}, _UNPLANNED, branch)
    result = _check(tmp_path, base)
    assert not _halted(result, "added: Makefile: .IGNORE:"), result.stdout


def test_makeflags_ignore_halts(tmp_path: Path) -> None:
    branch = {"Makefile": f"MAKEFLAGS += -i\n{_GATE}"}
    base = _branch(tmp_path, {"Makefile": _GATE}, _UNPLANNED, branch)
    result = _check(tmp_path, base)
    assert not _halted(result, "added: Makefile: MAKEFLAGS += -i"), result.stdout


def test_a_halt_lists_every_unquoted_line(tmp_path: Path) -> None:
    gate = f".PHONY: gate browsers drift derive\n{_GATE}"
    branch = {"Makefile": f".PHONY: gate browsers drift derive setup\nsetup:\n{_GATE}"}
    base = _branch(tmp_path, {"Makefile": gate}, _UNPLANNED, branch)
    result = _check(tmp_path, base)
    removed = "removed: Makefile: .PHONY: gate browsers drift derive"
    added = "added: Makefile: .PHONY: gate browsers drift derive setup"
    assert not _halted(result, removed, added, "added: Makefile: setup:"), result.stdout
    design = f"openspec/changes/{_CHANGE}/design.md"
    cut = _git(tmp_path, "log", "--diff-filter=A", "--format=%h", "--", design)
    assert "\nThe dry run is unchanged. A planning task names `Makefile` and " in (
        result.stdout
    )
    assert f"each line, in the cut commit {cut}. " in result.stdout
    assert re.search(
        f"/mf-ship approve-gate {_CHANGE} [0-9a-f]{{64}}\\.\n$", result.stdout
    )

    # A planning task's quoted line leaves the list; the rest stays in the one halt.
    quoted = tmp_path / "quoted"
    base = _branch(quoted, {"Makefile": gate}, _planned(" Adds `setup:`."), branch)
    result = _check(quoted, base)
    assert not _halted(result, removed, added), result.stdout
    assert "\n  added: Makefile: setup:\n" not in result.stdout


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


def test_exports_go_under_the_primary_run_directory(tmp_path: Path) -> None:
    primary, worktree = tmp_path / "primary", tmp_path / "v0.2_x"
    log = tmp_path / "pwd.log"
    # make evaluates `$(shell)` while it parses, so each export logs where it is.
    gate = f"$(shell pwd >> {log})\n{_GATE}"
    base = _branch(primary, {"Makefile": gate}, _UNPLANNED, {"README.md": "x\n"})
    _git(primary, "worktree", "add", "-q", "-b", "v0.2_x", str(worktree))

    result = _check(worktree, base)
    assert (result.returncode, result.stdout) == (0, "gate: no unplanned change\n")
    exports = (primary / ".minions" / "gate-check" / _CHANGE).resolve()
    made = {Path(line) for line in log.read_text().splitlines()}
    assert made == {exports / "base", exports / "head"}
    assert not exports.exists() and not (worktree / ".minions").exists()


def test_a_staged_tree_is_checked(tmp_path: Path) -> None:
    tasks = _planned(" It adds `echo c`.")
    base = _branch(tmp_path, {"Makefile": _GATE}, tasks, {"README.md": "x\n"})

    def staged(gate: str) -> subprocess.CompletedProcess[str]:
        (tmp_path / "Makefile").write_text(gate)
        _git(tmp_path, "add", "Makefile")
        tree = _git(tmp_path, "write-tree")
        return _check(tmp_path, base, None, "--head", tree)

    # HEAD's gate is the base's: only the staged tree holds the edit.
    unquoted = staged(f"{_GATE}\techo d\n")
    assert not _halted(unquoted, "added: Makefile: echo d"), unquoted.stdout
    quoted = staged(f"{_GATE}\techo c\n")
    assert quoted.returncode == 0, quoted.stdout
    assert quoted.stdout.startswith("gate: planned — 1.1 ")
    assert "\n+echo c" in quoted.stdout


def test_an_approval_passes_until_the_diff_moves(tmp_path: Path) -> None:
    root, home = tmp_path / "repo", tmp_path / "home"
    branch = {"Makefile": f".IGNORE:\n{_GATE}"}
    base = _branch(root, {"Makefile": _GATE}, _UNPLANNED, branch)
    env = {"HOME": str(home)}
    hashed = _check(root, base, env, "--digest").stdout.strip()
    assert len(hashed) == 64, hashed
    digest = hashlib.sha256(str(root.resolve()).encode()).hexdigest()[:16]

    # An approval in the repository, its run directory or the tree approves nothing.
    for planted in (".mf-ship-origin", ".minions/.mf-ship-origin"):
        entry = root / planted / f"{digest}.gate" / _CHANGE
        entry.parent.mkdir(parents=True)
        entry.write_text(f"{hashed}\n")
    _commit(root, {f".mf-ship-origin/{digest}.gate/x": f"{hashed}\n"}, "claim")
    unapproved = _check(root, base, env)
    assert not _halted(unapproved, "added: Makefile: .IGNORE:"), unapproved.stdout
    # The halt names the hash it read, so the person approves what it showed.
    assert unapproved.stdout.endswith(f"approve-gate {_CHANGE} {hashed}.\n")

    entry = home / ".mf-ship-origin" / f"{digest}.gate" / _CHANGE
    entry.parent.mkdir(parents=True)
    entry.write_text(f"{hashed}\n")
    approved = _check(root, base, env)
    assert approved.returncode == 0, approved.stdout
    assert approved.stdout == f"gate: approved — {hashed}\n\n"

    _commit(root, {"Makefile": f".IGNORE:\n{_GATE}\techo c\n"}, "one more edit")
    moved = _check(root, base, env)
    assert not _halted(moved, "added: Makefile: echo c"), moved.stdout

    # A line the approval saw, moved where it drops `pipefail`, lapses the approval.
    shifted = tmp_path / "shifted"
    strict = f"SHELL := /bin/bash -o pipefail\n{_GATE}"
    branch = {"Makefile": f"SHELL := /bin/sh\n{strict}"}
    base = _branch(shifted, {"Makefile": strict}, _UNPLANNED, branch)
    hashed = _check(shifted, base, env, "--digest").stdout.strip()
    digest = hashlib.sha256(str(shifted.resolve()).encode()).hexdigest()[:16]
    entry = home / ".mf-ship-origin" / f"{digest}.gate" / _CHANGE
    entry.parent.mkdir(parents=True)
    entry.write_text(f"{hashed}\n")
    assert _check(shifted, base, env).stdout.startswith(f"gate: approved — {hashed}")
    weaker = f"SHELL := /bin/bash -o pipefail\nSHELL := /bin/sh\n{_GATE}"
    _commit(shifted, {"Makefile": weaker}, "move the line")
    lapsed = _check(shifted, base, env)
    assert not _halted(lapsed, "added: Makefile: SHELL := /bin/sh"), lapsed.stdout


def test_an_edited_verify_halts(tmp_path: Path) -> None:
    check = "Verify: `grep -n x README.md` prints a line."
    tasks = (
        "## Progress\n\n- [ ] 1 — One\n\n## 1 — One\n\n"
        f"- [ ] 1.1 Edit `README.md` before the first `Verify:`.\n  {check}\n"
        "- [ ] 1.2 List it.\n  Verify: `ls` prints `README.md`.\n"
    )
    base = _branch(tmp_path, {"Makefile": _GATE}, tasks, {"README.md": "x\n"})
    path = tmp_path / "openspec" / "changes" / _CHANGE / "tasks.md"
    design = f"openspec/changes/{_CHANGE}/design.md"
    cut = _git(tmp_path, "log", "--diff-filter=A", "--format=%h", "--", design)

    def verify(*extra: str) -> subprocess.CompletedProcess[str]:
        argv = [sys.executable, str(_SCRIPT), "--verify", "--change", _CHANGE, *extra]
        return subprocess.run(argv, cwd=tmp_path, capture_output=True, text=True)

    # A ticked box is the build's: its check is still the plan's.
    path.write_text(tasks.replace("- [ ] 1.1", "- [x] 1.1"))
    passed = verify()
    assert passed.returncode == 0, passed.stdout
    assert passed.stdout == f"verify: every `Verify:` is the plan's at {cut}\n"

    narrowed = "Verify: `grep -n x README.md` prints nothing."
    path.write_text(tasks.replace(check, narrowed))
    edit = f"  1.1 · uncommitted\n  - {check}\n  + {narrowed}\n"
    halted = verify()
    assert halted.returncode == 1, halted.stdout
    assert halted.stdout.startswith(
        f"verify: halt — a `Verify:` differs from the plan at {cut}"
    )
    assert halted.stdout.endswith(f":\n{edit}"), halted.stdout
    # `--change` compares them too, after its gate check.
    gated = _check(tmp_path, base)
    assert gated.returncode == 1, gated.stdout
    assert gated.stdout.startswith("gate: no unplanned change\nverify: halt — ")

    # A phase commit's edit halts, committed.
    _commit(tmp_path, {}, "build: narrow the check")
    committed = verify()
    assert committed.returncode == 1, committed.stdout
    assert committed.stdout.endswith(f"\n  1.1\n  - {check}\n  + {narrowed}\n")

    # The person's amend is the plan from there on.
    amended = tasks.replace(check, narrowed)
    _commit(
        tmp_path,
        {
            str(path.relative_to(tmp_path)): amended
            + "- [ ] 1.3 More.\n  Verify: `ls`.\n"
        },
        f"docs({_CHANGE}): amend the change directory",
    )
    amend = _git(tmp_path, "rev-parse", "--short", "HEAD")
    assert verify().stdout == f"verify: every `Verify:` is the plan's at {amend}\n"
    # A check dropped from the plan halts, as one added would.
    path.write_text(amended)
    dropped = verify()
    assert dropped.returncode == 1, dropped.stdout
    assert dropped.stdout.endswith(
        "\n  1.3 · uncommitted\n  - Verify: `ls`.\n  + (no Verify:)\n"
    )

    path.unlink()
    missing = verify()
    assert missing.returncode == 2, missing.stdout
    assert missing.stdout.startswith(
        f"gate: cannot check — openspec/changes/{_CHANGE}/tasks.md: "
    )
    assert verify("--base", base).returncode == 2


def test_a_bare_makefile_task_fails_the_plan_check(tmp_path: Path) -> None:
    prose = (
        '- [ ] 1.6 In `Makefile`, the `gate`\'s `pytest` line takes `-m "not e2e"`.\n'
        "  Verify: `make -n gate` prints `not e2e`.\n"
    )
    quoted = (
        '- [ ] 1.6 In `Makefile`, the `gate`\'s `pytest` line takes `-m "not e2e"`:\n'
        "  ```diff\n"
        "  - \tuv run pytest -q\n"
        '  + \tuv run pytest -q -m "not e2e"\n'
        "  ```\n"
        "  Verify: `make -n gate` prints `not e2e`.\n"
    )
    # A blank line inside the block ends the sub-task before its quoted lines.
    gapped = quoted.replace("```diff\n", "```diff\n\n")
    cases = {
        "prose": (prose, 1),
        "quoted": (quoted, 0),
        "gapped": (gapped, 1),
        "mk": ("- [ ] 2.1 Add `setup` to `mk/tools.mk`.\n", 1),
        "none": ("- [ ] 1.1 Edit `README.md`.\n", 0),
    }
    outcomes = {}
    for label, (task, _) in cases.items():
        tasks = tmp_path / f"{label}.md"
        tasks.write_text(f"## Progress\n\n- [ ] 1 — One\n\n## 1 — One\n\n{task}")
        result = subprocess.run(
            [sys.executable, str(_SCRIPT), "--tasks", str(tasks)],
            capture_output=True,
            text=True,
        )
        outcomes[label] = (result.returncode, result.stdout)
    codes = {label: code for label, (code, _) in outcomes.items()}
    assert codes == {label: code for label, (_, code) in cases.items()}, outcomes
    halt = outcomes["prose"][1]
    assert halt.startswith("gate: halt — I18: "), halt
    assert "\n  1.6: no ```diff line · no line starting `+ ` or `- `\n" in halt
    assert "\n  2.1: no `gate` · no ```diff line" in outcomes["mk"][1]
