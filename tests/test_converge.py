"""`converge.py`, the converge conductor, driven over a fake host.

A real repository under `tmp_path`, its version in a worktree; the host fakes the
sandbox, the checkers and the fixer, so no worker process runs.
Why: 0108-converge-script design D1, its `## Tests` table.
"""

import runpy
import subprocess
import time
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, NamedTuple, Protocol, TextIO

import pytest

_SCRIPTS = Path(__file__).resolve().parent.parent / "skills" / "mf-converge" / "scripts"
_CHANGE = "0001-a"
_TASKS = "# Tasks\n\n## Progress\n\n- [x] 1 — One · moderate\n\n## 1 — One\n"
_WORKERS = {
    "conformance": ("claude", "claude-opus-5-5", "high"),
    "adversarial": ("claude", None, None),
    "fix": ("claude", "claude-sonnet-5-5", "medium"),
}


def _converge() -> dict[str, Any]:
    return runpy.run_path(str(_SCRIPTS / "converge.py"))


def _git(cwd: Path, *args: str) -> str:
    identity = ["-c", "user.name=mf", "-c", "user.email=mf@example.invalid"]
    return subprocess.run(
        ["git", *identity, "-c", "commit.gpgsign=false", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _commit(cwd: Path, files: dict[str, str], message: str) -> str:
    for name, text in files.items():
        path = cwd / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    _git(cwd, "add", *files)
    _git(cwd, "commit", "-q", "-m", message)
    return _git(cwd, "rev-parse", "HEAD")


class Checked(NamedTuple):
    code: int
    killed: bool
    models: tuple[str, str | None, str | None]
    limit: str
    fallback: bool
    tokens: int | None


class NoSandbox(Exception):
    code = 2


class Read(Protocol):
    """The fields of `converge.py`'s `Verdict` a test reads."""

    verdict: str
    head: str
    round: int
    open_blocking: int
    stub: bool
    inconclusive: tuple[str, ...]
    cards: tuple[Any, ...]
    malformed: str | None
    unclean: str | None


def findings(role: str, head: str, **keys: object) -> str:
    """Return a findings file of `role` at `head`, clean; `keys` change or drop keys.

    A key given None is dropped; `body` is the text below the frontmatter.
    """
    front: dict[str, object] = {
        "type": role,
        "plan": _CHANGE,
        "project": "primary",
        "branch": _CHANGE,
        "head": head,
        "reviewed": "2026-11-09",
        "round": 1,
        "open_blocking": 0,
        "verdict": "clean",
        "mode": "parallel",
        "workers": 1,
        "files": 1,
        "commits": 1,
        "passes": "[stale-claim, test-cost, no-removed-test]",
        "inconclusive": "[]",
        "model": "claude-opus-5-5",
        "executor": "claude",
        "packet": "diff.patch",
    }
    if role != "conformance":
        del front["passes"]
    body = str(keys.pop("body", "## Summary\n\nClean.\n"))
    front.update(keys)
    lines = "".join(f"{k}: {v}\n" for k, v in front.items() if v is not None)
    return f"---\n{lines}---\n\n{body}\n## Resolution log\n"


class Host:
    """A fake of the run `converge` is handed: its sandbox and its workers."""

    def __init__(self, primary: Path, tree: Path) -> None:
        self.primary = primary
        self.tree = tree
        self.plan: dict[tuple[str, str], tuple[str, str | None, str | None]] = {}
        self.exits: dict[str, int] = {}
        self.printed = {"make": "uv run ruff check .\n"}
        self.ran: list[list[str]] = []
        self.checks: list[tuple[str, str, str | None, str]] = []
        self.sandbox = True
        self.judge: Callable[[str, str], str] = self.clean

    def folder(self) -> Path:
        return self.primary / ".minions" / "changes" / _CHANGE

    def clean(self, role: str, head: str) -> str:
        return findings(role, head)

    def trees(self) -> list[Path]:
        return [self.primary, self.tree]

    def sandboxed(
        self, argv: list[str], cwd: Path, trees: list[Path], out: TextIO | None = None
    ) -> int:
        if not self.sandbox:
            raise NoSandbox("conduct: cannot run — no OS sandbox")
        assert cwd == self.tree
        assert trees == self.trees()
        self.ran.append(argv)
        name = Path(argv[3]).name if argv[0] == "uv" else argv[0]
        print(self.printed.get(name, ""), end="", file=out)
        return self.exits.get(name, 0)

    def checker(
        self,
        change: str,
        station: str,
        table: str,
        cwd: Path,
        prompt: str,
        deadline: float,
        effort: str | None = None,
    ) -> Checked:
        assert (change, cwd) == (_CHANGE, self.tree)
        assert deadline > time.monotonic()
        self.checks.append((station, table, effort, prompt))
        head = _git(self.tree, "rev-parse", "HEAD")
        self.folder().mkdir(parents=True, exist_ok=True)
        (self.folder() / f"{table}.md").write_text(self.judge(table, head))
        return Checked(0, False, _WORKERS[table], "", False, 1200)


@pytest.fixture
def host(tmp_path: Path) -> Host:
    """Return a fake host over a primary checkout and its version's worktree.

    `main` holds the change directory; the version adds one commit on it.
    """
    primary = tmp_path / "primary"
    primary.mkdir()
    _git(primary, "init", "-q", "-b", "main")
    folder = f"openspec/changes/{_CHANGE}"
    _commit(
        primary,
        {
            ".gitignore": ".minions/\n",
            "Makefile": "gate:\n\ttrue\n",
            "docs/decisions.md": "# Decisions\n\n### D1 · One rule\n\nIt holds.\n",
            f"{folder}/proposal.md": "---\nbump: minor\n---\n\n# A\n",
            f"{folder}/design.md": "# A — design\n\nPer D1 · One rule.\n",
            f"{folder}/tasks.md": _TASKS,
        },
        "base",
    )
    tree = tmp_path / _CHANGE
    _git(primary, "worktree", "add", "-q", "-b", _CHANGE, str(tree))
    _commit(tree, {"src/a.py": "A = 1\n"}, "feat(0001-a): one")
    return Host(primary.resolve(), tree.resolve())


def run(host: Host, workers: Mapping[str, object] | None = None) -> int:
    """Return `converge`'s exit over the fake host, on `_WORKERS` unless given."""
    deadline = time.monotonic() + 3600
    return _converge()["converge"](
        host, _CHANGE, host.tree, workers=workers or _WORKERS, deadline=deadline
    )


def events(host: Host) -> list[str]:
    """Return the newest run's events, oldest first, each without its time."""
    log = (host.folder() / "status_log.md").read_text().splitlines()
    heading = next(i for i, line in enumerate(log) if line.startswith("## Run"))
    run_lines = []
    for line in log[heading + 1 :]:
        if not line.strip() or line.startswith("## Run"):
            break
        run_lines.append(line.split(" · ", 1)[1])
    return run_lines[::-1]


def _dirty(host: Host) -> None:
    (host.tree / "stray.txt").write_text("x\n")


def _unticked(host: Host) -> None:
    tasks = _TASKS.replace("- [x] 1", "- [x] 1 — One\n- [ ] 2")
    _commit(host.tree, {f"openspec/changes/{_CHANGE}/tasks.md": tasks}, "a phase")


def _empty(host: Host) -> None:
    _git(host.tree, "reset", "-q", "--hard", "main")


def _no_gate(host: Host) -> None:
    host.printed["make"] = "make: Nothing to be done for `gate'.\n"


def _red(host: Host) -> None:
    host.exits["gate_run.py"] = 2


def _changed(host: Host) -> None:
    host.exits["gate_check.py"] = 1
    host.printed["gate_check.py"] = "gate: halt — the gate changed\n  approve abc123\n"


def _verify(host: Host) -> None:
    host.exits["gate_check.py"] = 1
    host.printed["gate_check.py"] = (
        "verify: halt — a `Verify:` differs from the plan at 1a2b3c4; the build never"
        " amends one:\n  1.2\n  - a\n  + b\n  2.1 · uncommitted\n  - c\n  + d\n"
    )


def _old(host: Host) -> None:
    old = host.primary / ".minions" / "findings" / f"{_CHANGE}_review.md"
    old.parent.mkdir(parents=True)
    old.write_text("old\n")


def _no_sandbox(host: Host) -> None:
    host.sandbox = False


_REFUSED: dict[str, tuple[Callable[[Host], None], int, str | None]] = {
    "dirty": (_dirty, 1, "the tree is dirty: stray.txt"),
    "unticked": (_unticked, 1, "phase 2 of tasks.md is unticked: mf-build owns it"),
    "empty": (_empty, 1, "the range is empty: base is HEAD"),
    "no gate": (_no_gate, 1, "the root Makefile's gate runs no command"),
    "red": (_red, 1, "the gate is red before round 1: gate_run.py exit 2"),
    "changed": (
        _changed,
        1,
        "gate check: gate: halt — the gate changed · approve abc123",
    ),
    "verify": (_verify, 1, "verify: halt — 1.2, 2.1"),
    "old layout": (_old, 1, None),
    "no sandbox": (_no_sandbox, 2, None),
}


@pytest.mark.parametrize("case", list(_REFUSED))
def test_a_converge_refuses_what_it_cannot_start(
    host: Host, case: str, capsys: pytest.CaptureFixture[str]
) -> None:
    setup, code, reason = _REFUSED[case]
    setup(host)
    head = _git(host.tree, "rev-parse", "HEAD")

    assert run(host) == code

    assert host.checks == []
    printed = capsys.readouterr().out
    log = host.folder() / "status_log.md"
    if case == "old layout":
        assert not log.exists()
        assert f".minions/findings/{_CHANGE}_review.md" in printed
        assert "/mf-ship" in printed
        return
    written = events(host)
    assert not any(line.startswith("round 1 · start") for line in written)
    if case == "no sandbox":
        assert "no OS sandbox" in printed
        reason = "conduct: cannot run — no OS sandbox"
    assert written[-1] == f"round 1 · halt — {reason} · head {head}"


def test_the_freeze_writes_the_patch_the_bundle_and_the_debt_cards(host: Host) -> None:
    converge = _converge()
    debt = host.primary / ".minions" / "debt.md"
    debt.parent.mkdir(parents=True)
    debt.write_text(
        "# Debt\n\n## 0000-z\n\n- **0000·R1 — A stays one**\n"
        "  - **What it affects:** `src/a.py:1`\n- **0000·R2 — B**\n"
        "  - **What it affects:** `src/b.py`\n"
    )
    _commit(host.tree, {"src/b.txt": "b\n"}, "feat(0001-a): two")
    base = _git(host.tree, "merge-base", "main", "HEAD")
    head = _git(host.tree, "rev-parse", "HEAD")
    context = converge["Context"](host, _CHANGE, host.tree, _WORKERS, 1e12)
    converge["open_run"](context)

    frozen = converge["freeze"](context, base, head)

    folder = host.folder()
    assert (frozen.base, frozen.head, frozen.commits, frozen.files) == (
        base,
        head,
        2,
        2,
    )
    patch = (folder / "diff.patch").read_text()
    assert patch == _git(host.tree, "diff", "--binary", base, head) + "\n"
    bundle = (folder / "bundle.md").read_text()
    assert bundle.startswith(f"# {_CHANGE} — bundle")
    assert "### D1 · One rule" in bundle
    cards = (folder / "debt-cards.md").read_text()
    assert "0000·R1" in cards
    assert "0000·R2" not in cards
    assert events(host)[-1] == (
        f"round 1 · freeze — {base[:7]}..{head[:7]} · 2 commits · 2 files"
    )

    debt.unlink()
    debt.mkdir()
    converge["freeze"](context, base, head)

    assert (folder / "debt-cards.md").read_text() == (
        "# Debt cards on the diff's files\n\nNone.\n"
    )


_REFERENCES = (
    "generic-conformance.md",
    "generic-adversarial.md",
    "verify.md",
    "fix.md",
)


def test_each_worker_prompt_is_filled_from_its_reference() -> None:
    converge = _converge()
    names = converge["PLACEHOLDERS"]
    values = {name: f"<{name} value>" for name in names}

    for reference in _REFERENCES:
        filled = converge["prompt"](reference, **values)

        template = (_SCRIPTS.parent / "references" / reference).read_text()
        assert filled.startswith("role: <role value>\nchange: <change value>\n")
        assert "{" not in filled
        for name in names:
            assert (f"<{name} value>" in filled) is (f"{{{name}}}" in template)

    with pytest.raises(ValueError, match="unknown placeholder: colour"):
        converge["prompt"]("verify.md", colour="red", **values)
    del values["findings"]
    with pytest.raises(ValueError, match="verify.md: findings is not filled"):
        converge["prompt"]("verify.md", **values)


def _card(card: str, *, amend: str | None = "no", status: str = "open") -> str:
    """Return a card `<id> <severity>`, e.g. "R1 blocking", with its fields."""
    ident, severity = card.split()
    role = "conformance" if ident.startswith("R") else "adversarial"
    fields = [
        ("Why it's a problem:", "it breaks."),
        ("What it affects:", "`src/a.py:1`."),
        ("Priority:", f"{severity} · {role} · functional correctness — it breaks."),
        ("Round:", "1"),
        ("Fix:", "fix it · size: one line."),
        ("Amend:", amend),
        ("Still true?", "`grep -n A src/a.py`"),
        ("Related:", "none."),
        ("Status:", status),
    ]
    lines = [f"  - **{name}** {value}" for name, value in fields if value is not None]
    return "\n".join([f"- **{ident} — It breaks**", *lines]) + "\n"


def test_a_findings_file_is_read_by_its_fields(host: Host) -> None:
    converge = _converge()
    head = _git(host.tree, "rev-parse", "HEAD")
    frozen = converge["Freeze"]("b" * 40, head, 2, 3)
    folder = host.folder()
    folder.mkdir(parents=True)

    def read(role: str, **keys: object) -> Read:
        (folder / f"{role}.md").write_text(findings(role, head, **keys))
        return converge["read_findings"](folder / f"{role}.md", role, frozen)

    clean = read("conformance", files=3, commits=2, inconclusive="[design.md]")
    assert (clean.verdict, clean.head, clean.round, clean.open_blocking) == (
        "clean",
        head,
        1,
        0,
    )
    assert clean.inconclusive == ("design.md",)
    assert (clean.malformed, clean.unclean, clean.stub) == (None, None, False)
    cards = _card("S1 high") + _card("S2 medium", amend="yes", status="wontfix")
    blocked = read(
        "adversarial", files=3, commits=2, verdict="changes-requested", body=cards
    )
    assert [(c.id, c.blocking, c.status, c.amend) for c in blocked.cards] == [
        ("S1", True, "open", False),
        ("S2", False, "wontfix", True),
    ]
    assert blocked.cards[1].fields["Still true?"] == "`grep -n A src/a.py`"
    passes = "[stale-claim, test-cost, coverage-trace]"
    assert read("conformance", files=3, commits=2, passes=passes).unclean is None

    for keys, why in (
        ({"files": 2, "commits": 2}, "scope resolved 2 files and 2 commits"),
        ({"files": 3, "commits": 1}, "scope resolved 3 files and 1 commit"),
        ({"passes": "[stale-claim, no-removed-test]"}, "lacks test-cost"),
        ({"passes": "[stale-claim, test-cost]"}, "lacks coverage-trace"),
    ):
        unclean = read("conformance", **{"files": 3, "commits": 2, **keys}).unclean
        assert unclean is not None
        assert why in unclean

    for keys, why in (
        ({"files": None}, "files is missing"),
        ({"commits": "many"}, "commits is not an integer"),
        ({"passes": "stale-claim"}, "passes is not a list"),
        ({"verdict": "fine"}, "verdict is neither clean nor changes-requested"),
        ({"body": _card("R1 drift", amend=None)}, "card R1 has no Amend line"),
        ({"body": _card("R1 drift", amend="maybe")}, "card R1 has no Amend line"),
    ):
        assert read("conformance", **{"files": 3, "commits": 2, **keys}).malformed == (
            f"conformance.md is malformed: {why}"
        )

    stub = read(
        "adversarial",
        mode="skipped",
        files=None,
        commits=None,
        inconclusive=None,
        workers=0,
    )
    assert (stub.stub, stub.malformed, stub.unclean, stub.verdict) == (
        True,
        None,
        None,
        "clean",
    )
    assert converge["read_findings"](folder / "gone.md", "conformance", frozen) is None
    (folder / "linked.md").symlink_to(folder / "conformance.md")
    linked = converge["read_findings"](folder / "linked.md", "conformance", frozen)
    assert linked.malformed == "linked.md is malformed: it is a link"

    frozen = converge["Freeze"]("b" * 40, head, 1, 1)
    context = converge["Context"](host, _CHANGE, host.tree, _WORKERS, 1e12)
    converge["open_run"](context)
    for role in ("conformance", "adversarial"):
        (folder / f"{role}.md").write_text(findings(role, head))
    checked = {
        "conformance": Checked(0, False, _WORKERS["conformance"], "", False, 97960),
        "adversarial": Checked(0, False, ("claude", None, None), "", True, None),
    }

    read = converge["read_verdicts"](context, frozen, checked)

    assert set(read) == {"conformance", "adversarial"}
    assert events(host) == [
        "round 1 · verdicts — conformance clean · open_blocking 0 · executor claude"
        " · model claude-opus-5-5 · effort high · tokens 97960",
        "round 1 · verdicts — adversarial clean · open_blocking 0 · executor claude"
        " · model default · effort default · tokens unavailable"
        " · fallback: codex usage limit",
    ]


def _verdicts(role: str) -> str:
    executor, model, effort = _WORKERS[role]
    return (
        f"round 1 · verdicts — {role} clean · open_blocking 0 · executor {executor}"
        f" · model {model or 'default'} · effort {effort or 'default'} · tokens 1200"
    )


def test_a_clean_round_converges_with_no_fix(host: Host) -> None:
    base = _git(host.tree, "merge-base", "main", "HEAD")
    head = _git(host.tree, "rev-parse", "HEAD")
    span = f"{base[:7]}..{head[:7]}"

    assert run(host) == 0

    assert events(host) == [
        f"round 1 · start — base {base[:7]} · head {head[:7]} · 1 commit · 1 file",
        f"round 1 · freeze — {span} · 1 commit · 1 file",
        f"round 1 · fan-out — conformance and adversarial dispatched · {span}"
        " · 2 workers",
        _verdicts("conformance"),
        _verdicts("adversarial"),
        "round 1 · done — converged in 1 round · 0 cards to debt",
    ]
    assert [(station, table, effort) for station, table, effort, _ in host.checks] == [
        ("converge-conformance-r1", "conformance", None),
        ("converge-adversarial-r1", "adversarial", None),
    ]
    for _, role, _, text in host.checks:
        assert text.startswith(f"role: {role}\nchange: {_CHANGE}\nround: 1\n")
        assert f"`head: {head}` and `mode: parallel`" in text
        assert str(host.folder() / f"{role}.md") in text
    assert [
        Path(argv[3]).name if argv[0] == "uv" else argv[0] for argv in host.ran
    ] == [
        "make",
        "gate_run.py",
        "gate_check.py",
    ]


def test_a_skipped_checker_is_a_stub(host: Host) -> None:
    head = _git(host.tree, "rev-parse", "HEAD")
    skips = {**_WORKERS, "adversarial": "skip"}

    assert run(host, workers=skips) == 0

    stub = (host.folder() / "adversarial.md").read_text()
    assert f"head: {head}\n" in stub
    assert "mode: skipped\n" in stub
    assert [station for station, *_ in host.checks] == ["converge-conformance-r1"]
    written = events(host)
    assert written[2].startswith("round 1 · fan-out — conformance dispatched · ")
    assert written[2].endswith(" · 1 worker")
    assert written[3:] == [
        _verdicts("conformance"),
        "round 1 · done — converged in 1 round · 0 cards to debt",
    ]

    (host.folder() / "adversarial.md").write_text(
        findings(
            "adversarial", head, verdict="changes-requested", body=_card("S1 high")
        )
    )
    assert run(host, workers=skips) == 1
    assert events(host)[-1].startswith(
        "round 1 · halt — skip_stub: cannot stub — "
        f"{host.folder() / 'adversarial.md'} holds a checker's round not cleared"
    )

    both = {**skips, "conformance": "skip"}
    assert run(host, workers=both) == 1
    assert events(host) == [
        "round 1 · halt — both checkers are skipped: a plan that skips both runs no"
        f" converge · head {head}"
    ]
