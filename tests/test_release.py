"""The release script's subcommands and git helper, over a scratch repo.

Why: 0152-release-script design D1…D11 and D14.
"""

import contextlib
import importlib.util
import io
import json
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from types import ModuleType

import pytest

_REPO = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO / "skills" / "mf-release" / "scripts" / "release.py"
CHANGE = "0001-todo"
FOLDER = f"openspec/changes/{CHANGE}"
CHANGELOG = (
    "# Changelog\n\n## [Unreleased]\n\n{entries}\n## [0.1.0] - 2026-01-01\n\n- first\n"
)
GREEN = 'print("gate: green — abc · 41s")\n'
RED = 'print("boom")\nprint("gate: red — exit 2 · 3s")\nraise SystemExit(2)\n'
PLANNED = 'print("gate: no unplanned change")\n'
CARD = "- **{id} — a card**\n  - **Priority:** {priority}\n  - **Status:** {status}\n"


def _findings_text(
    role: str, head: str, verdict: str = "clean", mode: str = "sequential"
) -> str:
    keys = f"type: {role}\nhead: {head}\nround: 1\nverdict: {verdict}\nmode: {mode}\n"
    return f"---\n{keys}---\n\nbody\n"


@dataclass
class Repo:
    """A project on `main` with a version branch, clean findings and fake gates."""

    root: Path
    ns: ModuleType
    fakes: Path

    def git(self, *args: str) -> str:
        done = subprocess.run(
            ["git", "-c", "user.name=mf", "-c", "user.email=mf@example.invalid"]
            + ["-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false", *args],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        )
        return done.stdout

    def put(self, relative: str, text: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def commit(self, message: str = "work") -> None:
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)

    @property
    def head(self) -> str:
        return self.git("rev-parse", "HEAD").strip()

    @property
    def run_folder(self) -> Path:
        return self.root / ".minions" / "changes" / CHANGE

    def judge(
        self, role: str, text: str | None = None, head: str | None = None
    ) -> None:
        folder = self.run_folder
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{role}.md").write_text(
            text or _findings_text(role, head or self.head)
        )

    def settle(self) -> None:
        """Commit what changed and judge the new `HEAD` clean."""
        self.commit()
        self.judge("conformance")
        self.judge("adversarial")

    def fake(self, constant: str, body: str) -> None:
        path = self.fakes / f"{constant}.py"
        path.write_text(body)
        self.swap(constant, path)

    def swap(self, constant: str, value: object) -> None:
        setattr(self.ns, constant, value)

    def main(self, *argv: str) -> tuple[int, list[str]]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = self.ns.main(list(argv))
        return code, out.getvalue().splitlines()

    def pre(self, *flags: str) -> tuple[int, list[str]]:
        return self.main("pre", CHANGE, *flags)

    def ready(self) -> None:
        """Run `pre` to its tag, so `finish` finds the mark."""
        code, lines = self.pre()
        assert code == 0, lines

    def finish(self, *flags: str) -> tuple[int, list[str]]:
        return self.main("finish", CHANGE, *flags)


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Repo:
    root = tmp_path / "project"
    root.mkdir()
    fakes = tmp_path / "fakes"
    fakes.mkdir()
    spec = importlib.util.spec_from_file_location("release_under_test", _SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    made = Repo(root, module, fakes)
    made.fake("GATE_RUN", GREEN)
    made.fake("GATE_CHECK", PLANNED)
    made.git("init", "-q", "-b", "main")
    made.git("config", "user.name", "mf")
    made.git("config", "user.email", "mf@example.invalid")
    made.put(".gitignore", ".minions/\n")
    made.put("CHANGELOG.md", CHANGELOG.format(entries=""))
    made.commit("base")
    made.git("tag", "v0.1.0")
    made.git("switch", "-q", "-c", CHANGE)
    made.put(f"{FOLDER}/proposal.md", "---\nbump: minor\n---\n\n# todo\n")
    made.put(f"{FOLDER}/tasks.md", "# tasks\n")
    made.put("CHANGELOG.md", CHANGELOG.format(entries="- a phase's entry\n\n"))
    made.settle()
    monkeypatch.chdir(root)
    return made


def test_findings_prints_a_files_verdict(repo: Repo) -> None:
    repo.judge(
        "adversarial", _findings_text("adversarial", "81d2d09d", "changes-requested")
    )
    code, lines = repo.main("findings", str(repo.run_folder / "adversarial.md"))
    assert (code, lines) == (
        0,
        ["release: ok — adversarial verdict changes-requested head 81d2d09d"],
    )


@pytest.mark.parametrize(
    "text",
    [
        "no frontmatter\n",
        "---\nhead: a\nverdict: clean\n---\n",
        "---\ntype: conformance\nverdict: clean\n---\n",
        "---\ntype: conformance\nhead: a\nverdict: maybe\n---\n",
    ],
    ids=["no-frontmatter", "no-type", "no-head", "no-verdict"],
)
def test_findings_cannot_run_on_a_file_it_cannot_parse(repo: Repo, text: str) -> None:
    repo.judge("conformance", text)
    code, lines = repo.main("findings", str(repo.run_folder / "conformance.md"))
    assert code == 2
    assert lines[0].startswith("release: cannot run — conformance.md has no ")


def test_main_exits_0_1_and_2_by_line(repo: Repo) -> None:
    good = repo.main("findings", str(repo.run_folder / "conformance.md"))
    assert good[0] == 0
    assert good[1][0].startswith("release: ok — ")
    repo.put("stray.txt", "x\n")
    held = repo.pre()
    assert held[0] == 1
    assert held[1][-1] == "release: halt — tree: dirty at stray.txt"
    missing = repo.main("findings", str(repo.root / "nowhere.md"))
    assert missing == (2, ["release: cannot run — nowhere.md is missing"])


def test_the_script_runs_as_a_command(repo: Repo) -> None:
    done = subprocess.run(
        [sys.executable, str(_SCRIPT), "findings", "nowhere.md"],
        cwd=repo.root,
        capture_output=True,
        text=True,
    )
    assert done.returncode == 2
    assert done.stdout == "release: cannot run — nowhere.md is missing\n"


def test_the_git_helper_adds_the_run_options(repo: Repo) -> None:
    git, stop = repo.ns.Git, repo.ns.Stop
    assert git(repo.root).argv("status") == ["git", "status"]
    run = git(repo.root, True).argv("status")
    options = repo.ns.RUN_OPTIONS
    assert run == ["git", *options, "status"]
    assert "commit.gpgsign=false" in run
    assert "tag.gpgsign=false" in run
    assert "core.hooksPath=/dev/null" in run
    assert "core.fsmonitor=false" in run
    assert git(repo.root, True).out("rev-parse", "HEAD").strip() == repo.head
    assert git(repo.root).ok("rev-parse", "HEAD")
    assert not git(repo.root).ok("rev-parse", "no-such-rev")
    with pytest.raises(stop) as failed:
        git(repo.root.parent / "fakes").out("rev-parse", "HEAD")
    assert failed.value.code == 2
    assert str(failed.value).startswith("release: cannot run — git rev-parse failed: ")


def test_a_command_that_cannot_start_or_runs_long_cannot_run(
    repo: Repo, monkeypatch: pytest.MonkeyPatch
) -> None:
    def start(*_: object, **__: object) -> None:
        raise FileNotFoundError(2, "No such file or directory")

    def long(*_: object, **__: object) -> None:
        raise subprocess.TimeoutExpired("git", 1)

    for fault, said in ((start, "could not run: No such file"), (long, "timed out")):
        monkeypatch.setattr(subprocess, "run", fault)
        with pytest.raises(repo.ns.Stop) as failed:
            repo.ns._exec(["git"], repo.root, "git x")
        assert failed.value.code == 2
        assert said in str(failed.value)


def test_pre_halts_on_an_old_layout(repo: Repo) -> None:
    old = repo.root / ".minions" / "findings" / f"{CHANGE}_review.md"
    old.parent.mkdir(parents=True)
    old.write_text("x\n")
    code, lines = repo.pre()
    assert code == 1
    assert lines == [
        f"release: halt — .minions/findings/{CHANGE}_review.md is the old layout:"
        " /mf-ship moves it"
    ]


def _dead_release(repo: Repo) -> None:
    """Leave the work a release that died after its archive and changelog cut leaves."""
    repo.put("CHANGELOG.md", "# Changelog\n\n## [Unreleased]\n\n## [0.2.0] - x\n")
    (repo.root / "openspec" / "changes" / "archive").mkdir()
    repo.git("mv", FOLDER, f"openspec/changes/archive/{CHANGE}")
    repo.put("metrics/changes/" + CHANGE + ".json", "{}\n")
    repo.put("openspec/specs/new/spec.md", "# new\n")
    (repo.run_folder / "release.flag").write_text("the preamble\n")
    (repo.run_folder / "release.pre").write_text("tag: v9.9.9\n")


def test_pre_restores_a_dead_releases_derived_work(repo: Repo) -> None:
    _dead_release(repo)
    code, lines = repo.pre("--run")
    assert (code, lines[-1]) == (0, "release: tag — v0.2.0")
    assert (
        "release: ok — restore — a dead release's derived work is back at HEAD" in lines
    )
    assert repo.git("status", "--porcelain") == ""
    assert (repo.root / FOLDER / "proposal.md").is_file()
    assert not (repo.root / "openspec" / "changes" / "archive" / CHANGE).exists()
    assert not (repo.root / "metrics" / "changes" / f"{CHANGE}.json").exists()
    assert not (repo.run_folder / "release.flag").exists()
    assert "tag: v0.2.0" in (repo.run_folder / "release.pre").read_text()


def test_pre_restore_removes_a_stale_flag_and_an_untracked_spec(repo: Repo) -> None:
    _dead_release(repo)
    repo.judge(
        "conformance", _findings_text("conformance", repo.head, "changes-requested")
    )
    code, lines = repo.pre("--run")
    assert (code, lines[-1]) == (
        1,
        "release: halt — conformance: verdict changes-requested",
    )
    assert not (repo.root / "openspec" / "specs" / "new" / "spec.md").exists()
    assert not (repo.run_folder / "release.flag").exists()
    assert not (repo.run_folder / "release.pre").exists()
    assert repo.git("status", "--porcelain") == ""


def test_a_hand_pre_keeps_the_clean_tree_halt(repo: Repo) -> None:
    _dead_release(repo)
    code, lines = repo.pre()
    assert code == 1
    assert lines[-1].startswith("release: halt — tree: dirty at ")
    assert (repo.run_folder / "release.flag").exists()
    assert (repo.root / "openspec" / "specs" / "new" / "spec.md").exists()


def test_a_run_pre_restores_nothing_beside_a_path_outside_the_derived_set(
    repo: Repo,
) -> None:
    _dead_release(repo)
    repo.put("src/code.py", "x = 1\n")
    code, lines = repo.pre("--run")
    assert (code, lines[-1]) == (1, "release: halt — tree: dirty at CHANGELOG.md")
    assert (repo.root / "src" / "code.py").exists()
    assert (repo.root / "openspec" / "specs" / "new" / "spec.md").exists()
    assert not (repo.run_folder / "release.flag").exists()


def _clear(repo: Repo) -> None:
    for role in ("conformance", "adversarial"):
        (repo.run_folder / f"{role}.md").unlink()


def _models(repo: Repo, text: str) -> None:
    _clear(repo)
    (repo.run_folder / "models.toml").write_text(text)


def _card(role: str, repo: Repo, priority: str, status: str) -> None:
    body = CARD.format(id="R1", priority=priority, status=status)
    text = _findings_text(role, repo.head)
    repo.judge(role, text + "\n" + body)


def _stale(repo: Repo) -> None:
    repo.judge("adversarial", head=repo.git("rev-parse", "HEAD~1").strip())


def _gate_red(repo: Repo) -> None:
    repo.fake("GATE_RUN", RED)


_FINDINGS = {
    "gate-red": (_gate_red, "release: halt — gate: red — exit 2 · 3s"),
    "conformance-changes": (
        lambda r: r.judge(
            "conformance", _findings_text("conformance", r.head, "changes-requested")
        ),
        "release: halt — conformance: verdict changes-requested",
    ),
    "blocking-card-fixed": (
        lambda r: _card("conformance", r, "blocking", "fixed"),
        "release: halt — conformance: R1 is fixed, not verified or accepted",
    ),
    "high-card-open": (
        lambda r: _card("adversarial", r, "high · adversarial", "open"),
        "release: halt — adversarial: R1 is open, not verified or accepted",
    ),
    "wrong-type": (
        lambda r: r.judge("conformance", _findings_text("adversarial", r.head)),
        "release: halt — conformance.md: its type is adversarial, not conformance",
    ),
    "one-file": (
        lambda r: (r.run_folder / "adversarial.md").unlink(),
        "release: halt — converge ran, and adversarial.md is missing",
    ),
    "patch-only": (
        lambda r: (_clear(r), (r.run_folder / "diff.patch").write_text("x\n")),
        "release: halt — converge froze its diff and stopped: run /mf-converge",
    ),
    "stale-head": (
        _stale,
        "release: halt — adversarial: head {old} is not HEAD {new}"
        " — run /mf-converge: its catch-up round judges {old}..HEAD",
    ),
    "broken-models": (
        lambda r: _models(r, "skip = = 1\n"),
        "release: halt — models.toml: ",
    ),
}


@pytest.mark.parametrize("name", _FINDINGS)
def test_pre_halts_on_each_failed_precondition_of_the_findings(
    repo: Repo, name: str
) -> None:
    mutate, said = _FINDINGS[name]
    mutate(repo)
    code, lines = repo.pre()
    said = said.format(
        old=repo.git("rev-parse", "--short=8", "HEAD~1").strip(), new=repo.head[:8]
    )
    assert code == 1
    assert lines[-1].startswith(said)
    assert not (repo.run_folder / "release.pre").exists()


@pytest.mark.parametrize(
    ("models", "line"),
    [
        (None, "release: ok — converge: skipped — no findings files"),
        ("[converge]\nskip = true\n", "release: ok — converge: skipped — by plan"),
    ],
    ids=["no-findings", "by-plan"],
)
def test_pre_reads_a_skipped_converge(
    repo: Repo, models: str | None, line: str
) -> None:
    _models(repo, models or "")
    code, lines = repo.pre()
    assert (code, lines[-1]) == (0, "release: tag — v0.2.0")
    assert line in lines
    assert not any(text.startswith("release: ok — conformance") for text in lines)


def test_pre_reads_a_skipped_checker(repo: Repo) -> None:
    repo.judge("adversarial", _findings_text("adversarial", repo.head, mode="skipped"))
    code, lines = repo.pre()
    assert code == 0
    assert "release: ok — adversarial: skipped" in lines
    assert "release: ok — conformance: clean" in lines


def test_pre_prints_the_tag_and_writes_the_mark(repo: Repo) -> None:
    code, lines = repo.pre()
    assert code == 0
    assert lines == [
        "release: ok — old layout",
        "release: ok — tree · clean",
        "release: ok — gate · 41s",
        "release: ok — conformance: clean",
        "release: ok — adversarial: clean",
        "release: ok — converge: ran",
        f"release: ok — head · {repo.head[:8]}",
        "release: ok — bump · minor",
        "release: ok — tag · v0.2.0 is free",
        "release: ok — changelog · Unreleased holds entries",
        "release: ok — gate check · no unplanned change",
        "release: ok — base · main is merged in",
        "release: ok — after · each dependency is archived",
        "release: tag — v0.2.0",
    ]
    mark = (repo.run_folder / "release.pre").read_text()
    assert mark == f"tag: v0.2.0\nversion: v0.2\ngate: 41\nhead: {repo.head}\n"


def test_pre_names_a_patch_release_by_its_whole_version(repo: Repo) -> None:
    repo.put(f"{FOLDER}/proposal.md", "---\nbump: patch\n---\n\n# todo\n")
    repo.settle()
    code, lines = repo.pre()
    assert (code, lines[-1]) == (0, "release: tag — v0.1.1")
    assert "version: v0.1.1\n" in (repo.run_folder / "release.pre").read_text()


@pytest.mark.parametrize(
    ("front", "named"),
    [("bump: major\n", "major"), ("", "missing")],
    ids=["major", "missing"],
)
def test_pre_halts_on_a_bad_bump(repo: Repo, front: str, named: str) -> None:
    repo.put(f"{FOLDER}/proposal.md", f"---\n{front}---\n\n# todo\n")
    repo.settle()
    code, lines = repo.pre()
    assert code == 1
    assert (
        lines[-1] == f"release: halt — proposal.md: bump is {named}, not minor or patch"
    )


def test_pre_halts_on_an_existing_tag(repo: Repo) -> None:
    repo.git("tag", "v0.2.0")
    code, lines = repo.pre()
    assert (code, lines[-1]) == (1, "release: halt — tag: v0.2.0 already exists")
    assert not (repo.run_folder / "release.pre").exists()


def _moved(repo: Repo) -> None:
    repo.git("switch", "-q", "main")
    repo.put("other.txt", "x\n")
    repo.commit("main moves")
    repo.git("switch", "-q", CHANGE)


_TREE: dict[str, tuple[Callable[[Repo], None], str]] = {
    "no-entries": (
        lambda r: (
            r.put("CHANGELOG.md", CHANGELOG.format(entries="")),
            r.settle(),
        )[1],
        "release: halt — CHANGELOG.md: ## [Unreleased] holds no entries",
    ),
    "no-changelog": (
        lambda r: (r.git("rm", "-q", "CHANGELOG.md"), r.settle())[1],
        "release: halt — CHANGELOG.md: ## [Unreleased] holds no entries",
    ),
    "gate-check-halt": (
        lambda r: r.fake(
            "GATE_CHECK",
            'print("gate: halt — Makefile changed")\nraise SystemExit(1)\n',
        ),
        "release: halt — gate check — gate: halt — Makefile changed",
    ),
    "gate-check-cannot": (
        lambda r: r.fake(
            "GATE_CHECK", 'print("gate: cannot check")\nraise SystemExit(2)\n'
        ),
        "release: cannot run — gate_check.py: gate: cannot check",
    ),
    "base-moved": (
        _moved,
        "release: halt — base: main is not an ancestor of HEAD — run /mf-integrate "
        + CHANGE,
    ),
    "after-unshipped": (
        lambda r: (
            r.put(
                f"{FOLDER}/proposal.md",
                "---\nbump: minor\nafter: [0000-first]\n---\n\n# todo\n",
            ),
            r.settle(),
        )[1],
        "release: halt — after: 0000-first is not archived at HEAD",
    ),
}


@pytest.mark.parametrize("name", _TREE)
def test_pre_halts_on_each_failed_precondition_of_the_tree(
    repo: Repo, name: str
) -> None:
    mutate, said = _TREE[name]
    mutate(repo)
    code, lines = repo.pre()
    assert code == (2 if "cannot run" in said else 1)
    assert lines[-1] == said
    assert not (repo.run_folder / "release.pre").exists()


def test_pre_passes_an_after_id_archived_at_head(repo: Repo) -> None:
    repo.put(
        f"{FOLDER}/proposal.md",
        "---\nbump: minor\nafter: [0000-first]\n---\n\n# todo\n",
    )
    repo.put("openspec/changes/archive/0000-first/tasks.md", "# done\n")
    repo.settle()
    assert repo.pre()[1][-1] == "release: tag — v0.2.0"


def _no_time(repo: Repo) -> None:
    repo.fake("GATE_RUN", 'print("gate: green — abc")\n')


def _bad_tag(repo: Repo) -> None:
    repo.fake("NEXT_TAG", 'print("v0.x")\n')


def _tag_fails(repo: Repo) -> None:
    repo.fake("NEXT_TAG", 'print("no default branch")\nraise SystemExit(2)\n')


def _no_proposal(repo: Repo) -> None:
    repo.git("rm", "-q", f"{FOLDER}/proposal.md")
    repo.settle()


def _linked_findings(repo: Repo) -> None:
    (repo.run_folder / "conformance.md").unlink()
    (repo.run_folder / "conformance.md").symlink_to(repo.root / "CHANGELOG.md")


_CANNOT = {
    "gate-prints-no-time": (
        _no_time,
        "release: cannot run — gate_run.py printed no time",
    ),
    "next-tag-prints-junk": (_bad_tag, "release: cannot run — next_tag.py: v0.x"),
    "next-tag-fails": (
        _tag_fails,
        "release: cannot run — next_tag.py: no default branch",
    ),
    "no-proposal": (_no_proposal, "release: cannot run — proposal.md cannot be read: "),
    "findings-link": (
        _linked_findings,
        "release: cannot run — conformance.md cannot be read: ",
    ),
}


@pytest.mark.parametrize("name", _CANNOT)
def test_pre_cannot_run_when_a_script_or_file_fails(repo: Repo, name: str) -> None:
    mutate, said = _CANNOT[name]
    mutate(repo)
    code, lines = repo.pre()
    assert code == 2
    assert lines[-1].startswith(said)


def test_pre_cannot_run_when_the_mark_cannot_be_written(
    repo: Repo, monkeypatch: pytest.MonkeyPatch
) -> None:
    statefile = repo.ns.mflib.statefile

    def refuse(*_: object, **__: object) -> None:
        raise statefile.WriteFailed("create", OSError(13, "Permission denied"))

    monkeypatch.setattr(statefile, "write", refuse)
    code, lines = repo.pre()
    assert code == 2
    assert (
        lines[-1]
        == "release: cannot run — release.pre could not be written: Permission denied"
    )


def test_pre_cannot_run_on_a_name_that_is_no_change_id(repo: Repo) -> None:
    code, lines = repo.main("pre", "../escape")
    assert (code, lines) == (2, ["release: cannot run — ../escape is no change id"])


ARCHIVE = f"openspec/changes/archive/{CHANGE}"
DONE = "release: ok — v0.2.0 committed and tagged"


def _shown(repo: Repo) -> list[str]:
    """Return the paths the release commit holds."""
    return repo.git("show", "--name-only", "--format=", "HEAD").split()


def _untouched(repo: Repo, head: str) -> None:
    """Assert no commit and no tag was made."""
    assert repo.head == head
    assert repo.git("tag", "--list", "v0.2.0") == ""


def test_finish_takes_the_workers_paths(repo: Repo) -> None:
    repo.ready()
    repo.put("openspec/specs/todo/spec.md", "# todo\n")
    repo.put("README.md", "# readme\n")
    code, lines = repo.finish()
    assert (code, lines[-1]) == (0, DONE)
    assert "release: ok — paths · README.md, openspec/specs/todo/spec.md" in lines
    assert {"README.md", "openspec/specs/todo/spec.md"} <= set(_shown(repo))
    assert repo.git("status", "--porcelain") == ""


@pytest.mark.parametrize(
    ("change", "said"),
    [
        (
            lambda r: r.put("src/code.py", "x = 1\n"),
            "paths: src/code.py is no spec and no Markdown file",
        ),
        (
            lambda r: r.git("mv", "CHANGELOG.md", "NEWS.md"),
            "paths: CHANGELOG.md → NEWS.md is a rename",
        ),
    ],
    ids=["python-file", "rename"],
)
def test_finish_halts_on_a_python_file(
    repo: Repo, change: Callable[[Repo], object], said: str
) -> None:
    repo.ready()
    head = repo.head
    change(repo)
    code, lines = repo.finish()
    assert (code, lines) == (1, [f"release: halt — {said}"])
    _untouched(repo, head)
    assert (repo.root / FOLDER / "proposal.md").is_file()


def _another_head(repo: Repo) -> None:
    repo.ready()
    repo.put("notes.md", "x\n")
    repo.settle()


def _mark_text(repo: Repo, text: str) -> None:
    repo.ready()
    (repo.run_folder / "release.pre").write_text(text)


def _linked_mark(repo: Repo) -> None:
    repo.ready()
    (repo.run_folder / "release.pre").unlink()
    (repo.run_folder / "release.pre").symlink_to(repo.root / "CHANGELOG.md")


_MARKS = {
    "missing": (
        lambda r: None,
        1,
        f"release: halt — release.pre is missing — run release.py pre {CHANGE}",
    ),
    "another-head": (
        _another_head,
        1,
        "release: halt — release.pre: head {old} is not HEAD {new}"
        f" — run release.py pre {CHANGE}",
    ),
    "no-gate": (
        lambda r: _mark_text(r, "tag: v0.2.0\nversion: v0.2\nhead: x\n"),
        2,
        "release: cannot run — release.pre has no gate:",
    ),
    "bad-tag": (
        lambda r: _mark_text(r, "tag: 2\nversion: v0.2\ngate: 41\nhead: x\n"),
        2,
        "release: cannot run — release.pre holds no tag or gate seconds",
    ),
    "link": (_linked_mark, 2, "release: cannot run — release.pre cannot be read: "),
}


@pytest.mark.parametrize("name", _MARKS)
def test_finish_halts_without_the_mark(repo: Repo, name: str) -> None:
    change, want, said = _MARKS[name]
    change(repo)
    head = repo.head
    code, lines = repo.finish()
    said = said.format(
        old=repo.git("rev-parse", "--short=8", "HEAD~1").strip(), new=head[:8]
    )
    assert code == want
    assert lines[-1].startswith(said)
    _untouched(repo, head)


def test_finish_archives_the_change_and_writes_its_version(repo: Repo) -> None:
    repo.ready()
    code, lines = repo.finish()
    assert (code, lines[-1]) == (0, DONE)
    assert f"release: ok — archive · {ARCHIVE} · version: v0.2" in lines
    assert not (repo.root / FOLDER).exists()
    proposal = (repo.root / ARCHIVE / "proposal.md").read_text()
    assert proposal == "---\nbump: minor\nversion: v0.2\n---\n\n# todo\n"
    tracked = repo.git("ls-files", "openspec/changes").split()
    assert tracked == [f"{ARCHIVE}/proposal.md", f"{ARCHIVE}/tasks.md"]


@pytest.mark.parametrize(
    ("path", "text", "said"),
    [
        (
            f"{FOLDER}/proposal.md",
            "---\nversion: x\n---\n",
            "proposal.md: no bump: line to write version: below",
        ),
        ("CHANGELOG.md", "# Changelog\n", "CHANGELOG.md: no ## [Unreleased] heading"),
    ],
    ids=["no-bump", "no-unreleased"],
)
def test_finish_halts_on_a_file_the_worker_broke(
    repo: Repo, path: str, text: str, said: str
) -> None:
    repo.ready()
    head = repo.head
    repo.put(path, text)
    code, lines = repo.finish()
    assert (code, lines[-1]) == (1, f"release: halt — {said}")
    _untouched(repo, head)


def test_finish_cannot_run_on_a_linked_changelog(repo: Repo) -> None:
    repo.ready()
    (repo.root / "CHANGELOG.md").unlink()
    (repo.root / "CHANGELOG.md").symlink_to(repo.root / ".gitignore")
    code, lines = repo.finish()
    assert code == 2
    assert lines[-1].startswith("release: cannot run — CHANGELOG.md cannot be read: ")


def test_finish_cannot_run_when_a_file_cannot_be_written(
    repo: Repo, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo.ready()
    statefile = repo.ns.mflib.statefile

    def refuse(*_: object, **__: object) -> None:
        raise statefile.WriteFailed("create", OSError(13, "Permission denied"))

    monkeypatch.setattr(statefile, "write", refuse)
    code, lines = repo.finish()
    assert (code, lines[-1]) == (
        2,
        "release: cannot run — proposal.md could not be written: Permission denied",
    )


def _today() -> str:
    return date.today().isoformat()


def test_finish_cuts_the_changelog_heading(repo: Repo) -> None:
    repo.ready()
    code, _ = repo.finish()
    assert code == 0
    assert (repo.root / "CHANGELOG.md").read_text() == (
        "# Changelog\n\n## [Unreleased]\n\n"
        f"## [0.2.0] - {_today()}\n\n"
        "Gate: local 0m41s · CI none · 0.1.0: none\n\n"
        "- a phase's entry\n\n"
        "## [0.1.0] - 2026-01-01\n\n- first\n"
    )
    assert "CHANGELOG.md" in _shown(repo)


def _gate_line(repo: Repo) -> str:
    text = (repo.root / "CHANGELOG.md").read_text()
    return next(line for line in text.splitlines() if line.startswith("Gate: "))


def _gh(repo: Repo, body: str) -> None:
    """Give the repo an `origin` and a fake `gh` that runs `body`."""
    repo.git("remote", "add", "origin", str(repo.root.parent / "origin.git"))
    path = repo.fakes / "gh.py"
    path.write_text(body)
    repo.swap("GH", (sys.executable, str(path)))


_RUNS = [
    ("CI", "d5162e4aaaa", "2026-11-24T10:00:00Z", "2026-11-24T10:00:12Z"),
    ("Lint", "0123456789", "2026-11-24T10:00:00Z", "2026-11-24T10:01:05Z"),
    ("CI", "0ldersha000", "2026-11-23T10:00:00Z", "2026-11-23T10:09:00Z"),
]


def test_finish_writes_the_gate_line(repo: Repo) -> None:
    runs = [
        dict(
            zip(("workflowName", "headSha", "startedAt", "updatedAt"), run, strict=True)
        )
        for run in _RUNS
    ]
    said = repo.fakes / "gh-argv.json"
    _gh(
        repo,
        "import json, sys\n"
        f"open({str(said)!r}, 'w').write(json.dumps(sys.argv[1:]))\n"
        f"print({json.dumps(runs)!r})\n",
    )
    repo.ready()
    assert repo.finish()[0] == 0
    assert (
        _gate_line(repo)
        == "Gate: local 0m41s · CI 1m5s (Lint at 0123456) · 0.1.0: none"
    )
    argv = json.loads(said.read_text())
    assert argv[:6] == ["run", "list", "--branch", "main", "--status", "success"]
    assert argv[6:] == [
        "--limit",
        "50",
        "--json",
        "workflowName,headSha,startedAt,updatedAt",
    ]


@pytest.mark.parametrize(
    "body",
    [
        None,
        "raise SystemExit(1)\n",
        "print('not json')\n",
        "print('[]')\n",
        'print(\'[{"workflowName": "CI"}]\')\n',
        "missing",
    ],
    ids=["no-origin", "gh-fails", "junk", "no-run", "a-run-with-no-times", "no-gh"],
)
def test_finish_writes_ci_none_when_gh_fails(repo: Repo, body: str | None) -> None:
    if body is not None:
        _gh(repo, body)
    if body == "missing":
        repo.swap("GH", (str(repo.fakes / "no-such-gh"),))
    repo.ready()
    assert repo.finish()[0] == 0
    assert _gate_line(repo) == "Gate: local 0m41s · CI none · 0.1.0: none"


def test_finish_writes_ci_not_read_under_a_run(repo: Repo) -> None:
    _gh(repo, "raise SystemExit('gh must not run under a run')\n")
    repo.ready()
    assert repo.finish("--run")[0] == 0
    assert _gate_line(repo) == (
        "Gate: local 0m41s · CI not read under mf-ship · 0.1.0: none"
    )


@pytest.mark.parametrize(
    ("previous", "line"),
    [
        (
            "## [0.1.0] - 2026-01-01\n\n"
            "Gate: local 7m49s · CI none · 0.0.9: local 1m0s · CI none\n\n- first\n",
            "Gate: local 0m41s · CI none · 0.1.0: local 7m49s · CI none",
        ),
        ("", "Gate: local 0m41s · CI none"),
    ],
    ids=["copied", "first-release"],
)
def test_finish_copies_the_previous_gate_line(
    repo: Repo, previous: str, line: str
) -> None:
    repo.put(
        "CHANGELOG.md", f"# Changelog\n\n## [Unreleased]\n\n- an entry\n\n{previous}"
    )
    repo.settle()
    repo.ready()
    assert repo.finish()[0] == 0
    assert _gate_line(repo) == line


PYPROJECT = (
    '[tool.other]\nversion = "keep"\n\n'
    '[project]\nname = "todo"\nversion = "0.1.0"\nrequires-python = ">=3.12"\n'
    "dependencies = []\n"
)


def test_finish_bumps_the_version_file_and_its_lock(repo: Repo) -> None:
    repo.put("pyproject.toml", PYPROJECT)
    subprocess.run(["uv", "lock", "--offline"], cwd=repo.root, check=True)
    repo.settle()
    repo.ready()
    code, lines = repo.finish()
    assert (code, lines[-1]) == (0, DONE)
    assert "release: ok — version file · pyproject.toml, uv.lock" in lines
    assert (repo.root / "pyproject.toml").read_text() == PYPROJECT.replace(
        'version = "0.1.0"', 'version = "0.2.0"'
    )
    assert 'name = "todo"\nversion = "0.2.0"' in (repo.root / "uv.lock").read_text()
    assert {"pyproject.toml", "uv.lock"} <= set(_shown(repo))


def test_finish_bumps_a_version_file_with_no_lock(repo: Repo) -> None:
    repo.put("pyproject.toml", PYPROJECT)
    repo.settle()
    repo.ready()
    code, lines = repo.finish()
    assert code == 0
    assert "release: ok — version file · pyproject.toml" in lines
    assert not (repo.root / "uv.lock").exists()


def test_finish_halts_when_uv_lock_fails(repo: Repo) -> None:
    repo.put("pyproject.toml", PYPROJECT)
    repo.put("uv.lock", "version = 1\n")
    repo.settle()
    repo.ready()
    head = repo.head
    path = repo.fakes / "uv.py"
    path.write_text("print('error: no lock offline')\nraise SystemExit(2)\n")
    repo.swap("UV", (sys.executable, str(path)))
    code, lines = repo.finish()
    assert (code, lines[-1]) == (1, "release: halt — uv lock: error: no lock offline")
    _untouched(repo, head)


PACKAGE = {"name": "todo", "version": "0.1.0", "private": True}
LOCK = {
    "name": "todo",
    "version": "0.1.0",
    "lockfileVersion": 3,
    "requires": True,
    "packages": {"": {"name": "todo", "version": "0.1.0"}},
}


def _npm(data: object) -> str:
    return json.dumps(data, indent=2) + "\n"


@pytest.mark.parametrize("locked", [True, False], ids=["with-lock", "no-lock"])
def test_finish_bumps_package_json_and_its_lock(repo: Repo, locked: bool) -> None:
    repo.put("package.json", _npm(PACKAGE))
    if locked:
        repo.put("package-lock.json", _npm(LOCK))
    repo.settle()
    repo.ready()
    code, lines = repo.finish()
    assert code == 0
    assert (repo.root / "package.json").read_text() == _npm(
        PACKAGE | {"version": "0.2.0"}
    )
    if locked:
        assert "release: ok — version file · package.json, package-lock.json" in lines
        bumped = LOCK | {"version": "0.2.0"}
        bumped["packages"] = {"": {"name": "todo", "version": "0.2.0"}}
        assert (repo.root / "package-lock.json").read_text() == _npm(bumped)
        assert {"package.json", "package-lock.json"} <= set(_shown(repo))
    else:
        assert "release: ok — version file · package.json" in lines


@pytest.mark.parametrize(
    "pyproject",
    [None, "[tool.ruff]\nline-length = 88\n", '[project]\nname = "todo"\n'],
    ids=["no-file", "no-project", "no-version"],
)
def test_finish_records_none_for_no_version_file(
    repo: Repo, pyproject: str | None
) -> None:
    if pyproject is not None:
        repo.put("pyproject.toml", pyproject)
        repo.settle()
    repo.ready()
    code, lines = repo.finish()
    assert code == 0
    assert "release: ok — version file: none" in lines
    assert (repo.root / "pyproject.toml").exists() == (pyproject is not None)


@pytest.mark.parametrize(
    ("package", "lock", "named"),
    [
        (_npm(PACKAGE), _npm(LOCK | {"lockfileVersion": "3"}), "package-lock.json"),
        (_npm(PACKAGE), _npm(LOCK | {"lockfileVersion": True}), "package-lock.json"),
        (
            _npm(PACKAGE),
            _npm({k: v for k, v in LOCK.items() if k != "version"}),
            "package-lock.json",
        ),
        (_npm(PACKAGE), _npm(LOCK | {"packages": {}}), "package-lock.json"),
        (_npm(PACKAGE), "not json\n", "package-lock.json"),
        ("[]\n", _npm(LOCK), "package.json"),
    ],
    ids=["text-level", "bool-level", "no-version", "no-root", "junk", "package-list"],
)
def test_finish_halts_on_a_lock_of_another_shape(
    repo: Repo, package: str, lock: str, named: str
) -> None:
    repo.put("package.json", package)
    repo.put("package-lock.json", lock)
    repo.settle()
    repo.ready()
    head = repo.head
    code, lines = repo.finish()
    assert code == 1
    assert lines[-1].startswith(f"release: halt — {named}: ")
    _untouched(repo, head)


CATALOGUE = (
    '[[metric]]\nid = "gate-seconds"\ntitle = "Gate time"\ngroup = "proof"\n'
    'unit = "seconds"\nbetter = "lower"\nnoise = 5\nsource = "station"\n'
)
DATA = f"metrics/changes/{CHANGE}.json"


def test_finish_collects_the_metrics(repo: Repo) -> None:
    repo.put("metrics/catalogue.toml", CATALOGUE)
    repo.settle()
    repo.ready()
    code, lines = repo.finish()
    assert (code, lines[-1]) == (0, DONE)
    assert f"release: ok — metrics · {DATA}" in lines
    data = json.loads((repo.root / DATA).read_text())
    assert data["version"] == "v0.2"
    assert data["model"] == "unidentified"
    assert data["values"]["gate-seconds"] == {"value": 41}
    assert DATA in _shown(repo)


def test_finish_records_none_for_no_catalogue(repo: Repo) -> None:
    repo.ready()
    code, lines = repo.finish()
    assert code == 0
    assert "release: ok — metrics: none — no catalogue" in lines
    assert not (repo.root / "metrics").exists()


_WRITES = (
    "import sys\n"
    "out = sys.argv[sys.argv.index('--out') + 1]\n"
    "__import__('pathlib').Path(out).parent.mkdir(parents=True, exist_ok=True)\n"
    "open(out, 'w').write({!r})\n"
)


@pytest.mark.parametrize(
    ("body", "want", "said"),
    [
        (
            _WRITES.format('{"version": "unreleased"}'),
            1,
            f"release: halt — metrics: {DATA} says version unreleased, not v0.2",
        ),
        ("print('boom')\nraise SystemExit(2)\n", 1, "release: halt — metrics: boom"),
        (
            _WRITES.format("[]"),
            2,
            f"release: cannot run — {DATA} holds no JSON object",
        ),
    ],
    ids=["stale-version", "collect-fails", "junk"],
)
def test_finish_halts_on_a_stale_metrics_version(
    repo: Repo, body: str, want: int, said: str
) -> None:
    repo.put("metrics/catalogue.toml", CATALOGUE)
    repo.settle()
    repo.ready()
    head = repo.head
    repo.fake("METRICS", body)
    code, lines = repo.finish()
    assert (code, lines[-1]) == (want, said)
    _untouched(repo, head)


def test_finish_halts_on_a_red_gate(repo: Repo) -> None:
    repo.ready()
    head = repo.head
    repo.fake("GATE_RUN", RED)
    code, lines = repo.finish()
    assert (code, lines[-1]) == (
        1,
        "release: halt — gate: red — exit 2 · 3s — nothing is committed",
    )
    _untouched(repo, head)


@pytest.mark.parametrize(
    ("touch", "said"),
    [
        (
            "open('CHANGELOG.md', 'a').write('x\\n')\n",
            "tree: CHANGELOG.md changed after staging — nothing is committed",
        ),
        (
            "open('stray.txt', 'w').write('x\\n')\n",
            "tree: stray.txt is untracked — nothing is committed",
        ),
    ],
    ids=["unstaged", "untracked"],
)
def test_finish_halts_on_an_unstaged_change_after_the_gate(
    repo: Repo, touch: str, said: str
) -> None:
    repo.ready()
    head = repo.head
    repo.fake("GATE_RUN", touch + GREEN)
    code, lines = repo.finish()
    assert (code, lines[-1]) == (1, f"release: halt — {said}")
    _untouched(repo, head)


def _hook(repo: Repo, name: str, body: str) -> None:
    hook = repo.root / ".git" / "hooks" / name
    hook.write_text(f"#!/bin/sh\n{body}")
    hook.chmod(0o755)


def _host_config_off(monkeypatch: pytest.MonkeyPatch) -> None:
    """Drop a host's own git keys, which may turn hooks and signing off already."""
    monkeypatch.delenv("GIT_CONFIG_COUNT", raising=False)


def test_finish_halts_on_a_tree_dirty_after_the_commit(
    repo: Repo, monkeypatch: pytest.MonkeyPatch
) -> None:
    _host_config_off(monkeypatch)
    repo.ready()
    _hook(repo, "post-commit", "echo x > stray.txt\n")
    code, lines = repo.finish()
    assert (code, lines[-1]) == (
        1,
        "release: halt — tree: dirty after the commit — ?? stray.txt",
    )
    assert repo.git("tag", "--list", "v0.2.0") == ""


def test_finish_commits_once_and_tags(repo: Repo) -> None:
    repo.ready()
    head = repo.head
    repo.fake(
        "GATE_RUN",
        "import sys\nif '--fresh' not in sys.argv:\n    raise SystemExit(2)\n" + GREEN,
    )
    code, lines = repo.finish()
    assert (code, lines[-1]) == (0, DONE)
    assert "release: ok — gate · 41s" in lines
    assert repo.git("rev-list", "--count", f"{head}..HEAD").strip() == "1"
    message = repo.git("log", "-1", "--format=%B").strip()
    assert message == f"chore(release): v0.2.0\n\nChange: {CHANGE}"
    assert repo.git("cat-file", "-t", "v0.2.0").strip() == "tag"
    assert repo.git("rev-parse", "v0.2.0^{commit}").strip() == repo.head
    assert repo.git("status", "--porcelain") == ""


@pytest.mark.parametrize(
    ("change", "body"),
    [
        (lambda r: _models(r, ""), "converge: skipped — no findings files"),
        (
            lambda r: _models(r, "[converge]\nskip = true\n"),
            "converge: skipped — by plan",
        ),
        (
            lambda r: r.judge(
                "adversarial", _findings_text("adversarial", r.head, mode="skipped")
            ),
            "adversarial: skipped",
        ),
    ],
    ids=["no-findings", "by-plan", "a-skipped-checker"],
)
def test_finish_states_a_skipped_converge_in_the_body(
    repo: Repo, change: Callable[[Repo], object], body: str
) -> None:
    change(repo)
    repo.ready()
    assert repo.finish()[0] == 0
    message = repo.git("log", "-1", "--format=%B").strip()
    assert message == f"chore(release): v0.2.0\n\n{body}\n\nChange: {CHANGE}"


def _signing(repo: Repo, key: str) -> None:
    repo.git("config", key, "true")
    repo.git("config", "gpg.program", str(repo.fakes / "no-such-gpg"))


_GUARDS: dict[str, tuple[Callable[[Repo], None], str]] = {
    "hook": (lambda r: _hook(r, "pre-commit", "exit 1\n"), "git commit"),
    "commit-sign": (lambda r: _signing(r, "commit.gpgsign"), "git commit"),
    "tag-sign": (lambda r: _signing(r, "tag.gpgsign"), "git tag"),
}


@pytest.mark.parametrize("run", [True, False], ids=["run", "by-hand"])
@pytest.mark.parametrize("guard", _GUARDS)
def test_finish_under_run_signs_nothing_and_runs_no_hook(
    repo: Repo, monkeypatch: pytest.MonkeyPatch, guard: str, run: bool
) -> None:
    _host_config_off(monkeypatch)
    repo.ready()
    setup, failing = _GUARDS[guard]
    setup(repo)
    code, lines = repo.finish(*(["--run"] if run else []))
    if run:
        assert (code, lines[-1]) == (0, DONE)
        assert "BEGIN PGP" not in repo.git("cat-file", "-p", "v0.2.0")
    else:
        assert code == 2
        assert lines[-1].startswith(f"release: cannot run — {failing} failed")


DEBT = (
    "# Debt\n\n## 0000-old\n\n- **0000·R1 — paid**\n  - **Status:** open\n\n"
    "## 0000-other\n\n- **0000·R2 — kept**\n  - **Status:** open\n"
)


def _paying(repo: Repo, front: str, debt: str | None = DEBT) -> None:
    """Name the cards the change pays in its proposal, and write the debt."""
    repo.put(f"{FOLDER}/proposal.md", f"---\nbump: minor\n{front}---\n\n# todo\n")
    repo.settle()
    if debt is not None:
        (repo.root / ".minions" / "debt.md").write_text(debt)


@pytest.mark.parametrize("key", ["debt", "backlog"])
def test_finish_clears_the_paid_cards(repo: Repo, key: str) -> None:
    _paying(repo, f"{key}: [0000·R1, 0000·R1]\n")
    repo.ready()
    code, lines = repo.finish()
    assert (code, lines[-1]) == (0, DONE)
    assert "release: ok — debt: 0000·R1 cleared" in lines
    assert (repo.root / ".minions" / "debt.md").read_text() == (
        "# Debt\n\n## 0000-other\n\n- **0000·R2 — kept**\n  - **Status:** open\n"
    )
    assert not (repo.root / ".minions" / "debt.lock").exists()


def test_finish_reports_an_unknown_card(repo: Repo) -> None:
    _paying(repo, "debt: [0000·R9]\n")
    repo.ready()
    code, lines = repo.finish()
    assert (code, lines[-1]) == (0, DONE)
    assert "release: ok — debt: 0000·R9 not found" in lines
    assert (repo.root / ".minions" / "debt.md").read_text() == DEBT


@pytest.mark.parametrize("front", ["after: []\n", "debt: []\n"], ids=["none", "empty"])
def test_finish_records_debt_none(repo: Repo, front: str) -> None:
    _paying(repo, front)
    repo.ready()
    code, lines = repo.finish()
    assert (code, lines[-1]) == (0, DONE)
    assert "release: ok — debt: none" in lines


def test_finish_halts_on_an_old_backlog_file(repo: Repo) -> None:
    _paying(repo, "debt: [0000·R1]\n", None)
    (repo.root / ".minions" / "backlog.md").write_text(DEBT)
    repo.ready()
    code, lines = repo.finish()
    assert (code, lines[-1]) == (
        1,
        "release: halt — .minions/backlog.md is the old debt file: /mf-ship moves it",
    )
    assert repo.git("cat-file", "-t", "v0.2.0").strip() == "tag"


def _held(repo: Repo) -> None:
    (repo.root / ".minions" / "debt.lock").mkdir()
    repo.swap("DEBT_WAIT", 0)


def _linked_debt(repo: Repo) -> None:
    (repo.root / ".minions" / "debt.md").unlink()
    (repo.root / ".minions" / "debt.md").symlink_to(repo.root / "CHANGELOG.md")


@pytest.mark.parametrize(
    ("change", "want", "said"),
    [
        (_held, 1, "release: halt — .minions/debt.lock held for 0 minutes"),
        (
            _linked_debt,
            1,
            "release: halt — .minions/debt.md cannot be read: it is a link",
        ),
        (
            "write",
            2,
            "release: cannot run — .minions/debt.md could not be written:"
            " Permission denied",
        ),
    ],
    ids=["held", "link", "write-fails"],
)
def test_finish_halts_when_the_debt_cannot_be_cleared(
    repo: Repo,
    monkeypatch: pytest.MonkeyPatch,
    change: Callable[[Repo], None] | str,
    want: int,
    said: str,
) -> None:
    _paying(repo, "debt: [0000·R1]\n")
    repo.ready()
    if isinstance(change, str):
        debtfile = repo.ns.mflib.debtfile
        failed = repo.ns.mflib.statefile.WriteFailed

        def refuse(*_: object, **__: object) -> None:
            raise failed("create", OSError(13, "Permission denied"))

        monkeypatch.setattr(debtfile, "write", refuse)
    else:
        change(repo)
    code, lines = repo.finish()
    assert (code, lines[-1]) == (want, said)


def test_finish_stops_on_the_flag(repo: Repo) -> None:
    repo.ready()
    (repo.run_folder / "release.flag").write_text("README.md states v0.1\n")
    code, lines = repo.finish()
    assert (code, lines[-1]) == (
        1,
        f"release: halt — .minions/changes/{CHANGE}/release.flag stands"
        " — read the prose it names, then merge",
    )
    assert repo.git("rev-parse", "v0.2.0^{commit}").strip() == repo.head


OWN = "release: ok — tag · v0.2.0 is own, on no branch"
FREE = ("--origin", "free")


def _tagged_on(repo: Repo) -> str:
    """Return the commit the release's tag is on."""
    return repo.git("rev-parse", "v0.2.0^{commit}").strip()


def _orphan(repo: Repo) -> str:
    """Tag the release on a commit no branch holds; return that commit."""
    sha = repo.git("commit-tree", "HEAD^{tree}", "-p", "HEAD", "-m", "dead").strip()
    repo.git("tag", "-a", "v0.2.0", "-m", "v0.2.0", sha)
    return sha


def _origin(repo: Repo) -> None:
    """Give the repo a bare `origin` it can read."""
    bare = repo.root.parent / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
    repo.git("remote", "add", "origin", str(bare))


def _cut_release(repo: Repo) -> str:
    """Run `pre` and `finish` to the tagged release commit; return its parent."""
    repo.ready()
    head = repo.head
    code, lines = repo.finish()
    assert (code, lines[-1]) == (0, DONE), lines
    return head


@pytest.mark.parametrize("held", ["tag", "tracking", "neither"])
def test_a_hand_run_reads_origin_itself(repo: Repo, held: str) -> None:
    _origin(repo)
    sha = _orphan(repo)
    if held == "tag":
        repo.git("push", "-q", "origin", "v0.2.0")
    if held == "tracking":
        repo.git("update-ref", "refs/remotes/origin/main", sha)
    code, lines = repo.pre()
    if held == "neither":
        assert (code, lines[-1]) == (0, "release: tag — v0.2.0")
        assert OWN in lines
    else:
        assert (code, lines[-1]) == (1, "release: halt — tag: v0.2.0 is on origin")


@pytest.mark.parametrize("case", ["unreadable", "a-run-gives-none"])
def test_an_unreadable_origin_cannot_run(repo: Repo, case: str) -> None:
    _orphan(repo)
    if case == "unreadable":
        repo.git("remote", "add", "origin", str(repo.root.parent / "no-such.git"))
        code, lines = repo.pre()
        assert code == 2
        assert lines[-1].startswith("release: cannot run — origin cannot be read: ")
    else:
        code, lines = repo.pre("--run")
        assert (code, lines[-1]) == (
            2,
            "release: cannot run — a run gives --origin held or free",
        )
    assert not (repo.run_folder / "release.pre").exists()


def test_no_origin_is_free(repo: Repo) -> None:
    _orphan(repo)
    code, lines = repo.pre()
    assert (code, lines[-1]) == (0, "release: tag — v0.2.0")
    assert OWN in lines


class Died(Exception):
    """A release killed mid-step."""


_STEPS = (
    "_workers",
    "_archive",
    "_changelog",
    "_package",
    "_metrics",
    "_gate",
    "_committed",
    "_tag_at",
    "_debt",
)


def _conducted(repo: Repo) -> tuple[int, list[str]]:
    """Run `pre`, the worker's fold and `finish` under a run, as the conductor does."""
    code, lines = repo.pre("--run", *FREE)
    assert code == 0, lines
    if lines[-1].startswith("release: tag — "):
        repo.put("openspec/specs/todo/spec.md", "# todo\n")
    return repo.finish("--run", *FREE)


@pytest.mark.parametrize("step", _STEPS)
def test_a_second_finish_after_a_death_at_each_step_ends_the_same(
    repo: Repo, monkeypatch: pytest.MonkeyPatch, step: str
) -> None:
    repo.put("package.json", _npm(PACKAGE))
    _paying(repo, "debt: [0000·R1]\n")
    start = repo.head
    assert _conducted(repo)[1][-1] == DONE
    whole = repo.git("rev-parse", "HEAD^{tree}").strip()
    paid = (repo.root / ".minions" / "debt.md").read_text()
    repo.git("tag", "-d", "v0.2.0")
    repo.git("reset", "-q", "--hard", start)
    (repo.root / ".minions" / "debt.md").write_text(DEBT)
    (repo.run_folder / "release.pre").unlink()
    real = getattr(repo.ns, step)

    def dies(*args: object, **kwargs: object) -> object:
        done = real(*args, **kwargs)
        if step != "_gate" or kwargs.get("fresh"):
            raise Died(step)
        return done

    monkeypatch.setattr(repo.ns, step, dies)
    with pytest.raises(Died):
        _conducted(repo)
    monkeypatch.setattr(repo.ns, step, real)
    assert _conducted(repo)[1][-1] == DONE
    assert repo.git("rev-parse", "HEAD^{tree}").strip() == whole
    assert repo.git("rev-list", "--count", f"{start}..HEAD").strip() == "1"
    assert _tagged_on(repo) == repo.head
    assert (repo.root / ".minions" / "debt.md").read_text() == paid
    assert repo.git("status", "--porcelain") == ""


def test_finish_at_a_release_commit_tags_a_missing_tag(repo: Repo) -> None:
    _cut_release(repo)
    repo.git("tag", "-d", "v0.2.0")
    code, lines = repo.finish()
    assert (code, lines[-1]) == (0, DONE)
    assert "release: ok — resume · v0.2.0: every step before the tag is done" in lines
    assert "release: ok — tag · v0.2.0" in lines
    assert _tagged_on(repo) == repo.head
    code, lines = repo.finish()
    assert (code, lines[-1]) == (0, DONE)
    assert "release: ok — tag · v0.2.0 is on HEAD" in lines


def test_finish_at_a_release_commit_runs_the_gate_before_tagging(repo: Repo) -> None:
    _cut_release(repo)
    repo.git("tag", "-d", "v0.2.0")
    said = repo.fakes / "gate-argv.json"
    repo.fake(
        "GATE_RUN",
        f"import json, sys\nopen({str(said)!r}, 'w').write(json.dumps(sys.argv[1:]))\n"
        + RED,
    )
    code, lines = repo.finish()
    assert (code, lines[-1]) == (1, "release: halt — gate: red — exit 2 · 3s")
    assert json.loads(said.read_text()) == []
    assert repo.git("tag", "--list", "v0.2.0") == ""


def test_finish_at_a_release_commit_halts_on_a_dirty_tree(repo: Repo) -> None:
    _cut_release(repo)
    repo.git("tag", "-d", "v0.2.0")
    repo.put("stray.md", "x\n")
    code, lines = repo.finish("--run", *FREE)
    assert (code, lines[-1]) == (1, "release: halt — tree: dirty at stray.md")
    assert repo.git("tag", "--list", "v0.2.0") == ""


def _forged(repo: Repo, path: str, subject: str = "chore(release): v0.2.0") -> None:
    """Commit `path` under a release subject, on top of `HEAD`."""
    repo.put(path, "x = 1\n")
    repo.commit(subject)


def test_a_release_commit_with_a_code_path_halts(repo: Repo) -> None:
    repo.ready()
    repo.put("README.md", "# readme\n")
    _forged(repo, "src/code.py")
    code, lines = repo.finish()
    said = "release: halt — release commit: src/code.py is no path a release writes"
    assert (code, lines[-1]) == (1, said)
    assert repo.pre()[1][-1] == said
    assert repo.git("tag", "--list", "v0.2.0") == ""


def test_a_release_commit_whose_parent_is_not_the_marks_head_halts(
    repo: Repo,
) -> None:
    repo.ready()
    head = repo.head
    repo.put("notes.md", "x\n")
    repo.commit("notes")
    _forged(repo, "README.md")
    code, lines = repo.finish()
    assert (code, lines[-1]) == (
        1,
        f"release: halt — release commit: its parent is not release.pre's {head[:8]}",
    )
    assert repo.git("tag", "--list", "v0.2.0") == ""


def test_a_release_commit_without_the_mark_halts(repo: Repo) -> None:
    _cut_release(repo)
    repo.git("tag", "-d", "v0.2.0")
    (repo.run_folder / "release.pre").unlink()
    code, lines = repo.finish()
    assert (code, lines[-1]) == (
        1,
        "release: halt — HEAD is chore(release): v0.2.0, and release.pre is missing",
    )
    assert repo.git("tag", "--list", "v0.2.0") == ""


def test_pre_passes_an_own_tag(repo: Repo) -> None:
    _orphan(repo)
    code, lines = repo.pre(*FREE)
    assert (code, lines[-1]) == (0, "release: tag — v0.2.0")
    assert OWN in lines


@pytest.mark.parametrize("at", ["the-cut", "a-resume"])
def test_a_tag_on_an_orphan_commit_is_moved(repo: Repo, at: str) -> None:
    if at == "the-cut":
        sha = _orphan(repo)
        assert repo.pre(*FREE)[0] == 0
    else:
        _cut_release(repo)
        repo.git("tag", "-d", "v0.2.0")
        sha = _orphan(repo)
    code, lines = repo.finish(*FREE)
    assert (code, lines[-1]) == (0, DONE)
    assert OWN in lines
    assert f"release: ok — tag · v0.2.0 · moved from {sha[:8]}" in lines
    assert _tagged_on(repo) == repo.head
    assert repo.git("cat-file", "-t", "v0.2.0").strip() == "tag"


def test_a_tag_origin_holds_halts(repo: Repo) -> None:
    head = repo.head
    sha = _orphan(repo)
    said = "release: halt — tag: v0.2.0 is on origin"
    code, lines = repo.pre("--origin", "held")
    assert (code, lines[-1]) == (1, said)
    assert not (repo.run_folder / "release.pre").exists()
    assert repo.pre(*FREE)[0] == 0
    code, lines = repo.finish("--origin", "held")
    assert (code, lines[-1]) == (1, said)
    assert repo.head == head
    assert _tagged_on(repo) == sha


def test_a_tag_the_default_branch_holds_halts(repo: Repo) -> None:
    head = repo.head
    repo.ready()
    repo.git("tag", "-a", "v0.2.0", "-m", "v0.2.0", "main")
    said = "release: halt — tag: v0.2.0 is on main"
    code, lines = repo.finish(*FREE)
    assert (code, lines[-1]) == (1, said)
    assert repo.head == head
    repo.fake("NEXT_TAG", 'print("v0.2.0")\n')
    assert repo.pre(*FREE)[1][-1] == said


def test_a_stranded_release_is_dropped(repo: Repo) -> None:
    head = _cut_release(repo)
    (repo.run_folder / "release.flag").write_text("README.md states v0.1\n")
    _moved(repo)
    code, lines = repo.pre(*FREE)
    assert (code, lines[-1]) == (0, "release: drop — v0.2.0 and its commit")
    assert "release: ok — base · main moved past HEAD" in lines
    assert repo.head == head
    assert repo.git("tag", "--list", "v0.2.0") == ""
    assert not (repo.run_folder / "release.pre").exists()
    assert not (repo.run_folder / "release.flag").exists()
    assert repo.git("status", "--porcelain") == ""
    assert repo.pre()[1][-1] == (
        "release: halt — base: main is not an ancestor of HEAD"
        f" — run /mf-integrate {CHANGE}"
    )


@pytest.mark.parametrize(
    ("bound", "said"),
    [
        ("tag-elsewhere", "drop: v0.2.0 is not on HEAD — nothing is dropped"),
        ("dirty", "tree: dirty at stray.md"),
    ],
    ids=["tag-elsewhere", "dirty"],
)
def test_a_stranded_release_past_a_failed_bound_halts(
    repo: Repo, bound: str, said: str
) -> None:
    _cut_release(repo)
    _moved(repo)
    if bound == "tag-elsewhere":
        repo.git("tag", "-d", "v0.2.0")
        _orphan(repo)
    else:
        repo.put("stray.md", "x\n")
    head = repo.head
    code, lines = repo.pre(*FREE)
    assert (code, lines[-1]) == (1, f"release: halt — {said}")
    assert repo.head == head
    assert (repo.run_folder / "release.pre").exists()


def test_a_release_the_default_branch_holds_is_not_dropped(repo: Repo) -> None:
    _cut_release(repo)
    head = repo.head
    repo.git("switch", "-q", "main")
    repo.git("merge", "-q", "--no-ff", "-m", f"Merge branch '{CHANGE}'", CHANGE)
    repo.git("switch", "-q", CHANGE)
    code, lines = repo.pre(*FREE)
    assert (code, lines[-1]) == (
        1,
        "release: halt — drop: HEAD is on main — nothing is dropped",
    )
    assert repo.head == head
    assert _tagged_on(repo) == head


@pytest.mark.parametrize("origin", ["given", "read"])
def test_a_release_origin_holds_is_not_dropped(repo: Repo, origin: str) -> None:
    _cut_release(repo)
    head = repo.head
    _moved(repo)
    flags: tuple[str, ...] = ("--origin", "held")
    if origin == "read":
        _origin(repo)
        repo.git("push", "-q", "origin", "v0.2.0")
        flags = ()
    code, lines = repo.pre(*flags)
    assert (code, lines[-1]) == (
        1,
        "release: halt — drop: origin holds v0.2.0 or HEAD — nothing is dropped",
    )
    assert repo.head == head
    assert _tagged_on(repo) == head


def test_pre_reads_a_release_commit_as_a_resume(repo: Repo) -> None:
    head = _cut_release(repo)
    mark = (repo.run_folder / "release.pre").read_text()
    (repo.run_folder / "release.flag").write_text("README.md states v0.1\n")
    repo.fake("GATE_RUN", RED)
    code, lines = repo.pre("--run", *FREE)
    assert (code, lines) == (
        0,
        [
            "release: ok — old layout",
            "release: ok — release commit · HEAD is chore(release): v0.2.0",
            "release: ok — tree · clean",
            "release: ok — conformance: clean",
            "release: ok — adversarial: clean",
            "release: ok — converge: ran",
            f"release: ok — head · {head[:8]}",
            "release: resume — v0.2.0",
        ],
    )
    assert (repo.run_folder / "release.pre").read_text() == mark
    assert (repo.run_folder / "release.flag").exists()


def test_pre_at_a_release_commit_restores_nothing(repo: Repo) -> None:
    _cut_release(repo)
    repo.put("openspec/specs/todo/spec.md", "# todo\n")
    code, lines = repo.pre("--run", *FREE)
    assert (code, lines[-1]) == (
        1,
        "release: halt — tree: dirty at openspec/specs/todo/spec.md",
    )
    assert (repo.root / "openspec" / "specs" / "todo" / "spec.md").exists()
    assert (repo.run_folder / "release.pre").exists()


def _forge_code(repo: Repo) -> str:
    _forged(repo, "src/code.py")
    return "release commit: src/code.py is no path a release writes"


def _forge_parent(repo: Repo) -> str:
    head = repo.head
    repo.put("notes.md", "x\n")
    repo.commit("notes")
    _forged(repo, "README.md")
    return f"release commit: its parent is not release.pre's {head[:8]}"


def _forge_no_mark(repo: Repo) -> str:
    (repo.run_folder / "release.pre").unlink()
    _forged(repo, "README.md")
    return "HEAD is chore(release): v0.2.0, and release.pre is missing"


def _forge_tag(repo: Repo) -> str:
    _forged(repo, "README.md", "chore(release): v0.3.0")
    return "release commit: HEAD says v0.3.0, release.pre says v0.2.0"


@pytest.mark.parametrize(
    "forge",
    [_forge_code, _forge_parent, _forge_no_mark, _forge_tag],
    ids=["code-path", "another-parent", "no-mark", "another-tag"],
)
def test_pre_halts_on_a_forged_release_commit(
    repo: Repo, forge: Callable[[Repo], str]
) -> None:
    repo.ready()
    said = forge(repo)
    head = repo.head
    code, lines = repo.pre("--run", *FREE)
    assert (code, lines[-1]) == (1, f"release: halt — {said}")
    assert repo.head == head
    assert repo.git("tag", "--list", "v0.2.0") == ""


MERGED = f"release: ok — {CHANGE} merged into main"


def _merge(repo: Repo, *flags: str) -> tuple[int, list[str]]:
    return repo.main("merge", CHANGE, *flags)


def _main_at(repo: Repo) -> str:
    return repo.git("rev-parse", "main").strip()


def _linked(repo: Repo, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Put the primary on `main`, the branch in a linked worktree the test runs in."""
    repo.git("switch", "-q", "main")
    tree = repo.root.parent / "tree"
    repo.git("worktree", "add", "-q", str(tree), CHANGE)
    monkeypatch.chdir(tree)
    return tree


def test_merge_merges_with_its_trailer_and_the_trees_are_equal(
    repo: Repo, monkeypatch: pytest.MonkeyPatch
) -> None:
    _cut_release(repo)
    release = repo.head
    _linked(repo, monkeypatch)
    code, lines = _merge(repo, "--run")
    assert (code, lines[-1]) == (0, MERGED)
    assert f"release: ok — trees · main equals {CHANGE}" in lines
    assert repo.git("rev-list", "--parents", "-n", "1", "main").split()[2] == release
    assert repo.git("log", "-1", "--format=%s", "main").strip() == (
        f"Merge branch '{CHANGE}'"
    )
    assert repo.git("log", "-1", "--format=%(trailers)", "main").strip() == (
        f"Change: {CHANGE}"
    )
    tree = repo.git("rev-parse", f"{CHANGE}^{{tree}}")
    assert repo.git("rev-parse", "main^{tree}") == tree
    assert repo.git("branch", "--show-current").strip() == "main"


def test_merge_halts_on_an_untagged_branch(repo: Repo) -> None:
    before = _main_at(repo)
    then = f" — run release.py finish {CHANGE}"
    said = f"release: halt — merge: HEAD is no release commit{then}"
    assert _merge(repo) == (1, [said])
    _cut_release(repo)
    repo.git("tag", "-d", "v0.2.0")
    code, lines = _merge(repo)
    assert (code, lines[-1]) == (
        1,
        f"release: halt — merge: v0.2.0 is not on HEAD{then}",
    )
    assert _main_at(repo) == before


def test_merge_halts_when_the_default_branch_moved(repo: Repo) -> None:
    _cut_release(repo)
    _moved(repo)
    before = _main_at(repo)
    code, lines = _merge(repo)
    assert (code, lines[-1]) == (
        1,
        f"release: halt — base: main moved past HEAD — run /mf-release {CHANGE} again:"
        " its pre drops the release",
    )
    assert _main_at(repo) == before


def test_merge_halts_on_a_dirty_primary(
    repo: Repo, monkeypatch: pytest.MonkeyPatch
) -> None:
    _cut_release(repo)
    _linked(repo, monkeypatch)
    before = _main_at(repo)
    repo.put("stray.txt", "x\n")
    code, lines = _merge(repo)
    assert (code, lines[-1]) == (1, "release: halt — primary: dirty — ?? stray.txt")
    assert _main_at(repo) == before


def test_merge_halts_on_a_primary_off_the_default_branch(
    repo: Repo, monkeypatch: pytest.MonkeyPatch
) -> None:
    _cut_release(repo)
    _linked(repo, monkeypatch)
    repo.git("switch", "-q", "-c", "elsewhere")
    before = _main_at(repo)
    code, lines = _merge(repo)
    assert (code, lines[-1]) == (1, "release: halt — primary: on elsewhere, not main")
    assert _main_at(repo) == before


def test_merge_halts_while_the_flag_stands(repo: Repo) -> None:
    _cut_release(repo)
    flag = repo.run_folder / "release.flag"
    flag.write_text("README.md states v0.1\n")
    before = _main_at(repo)
    code, lines = _merge(repo)
    assert (code, lines[-1]) == (
        1,
        f"release: halt — .minions/changes/{CHANGE}/release.flag stands"
        " — read the prose it names, then merge",
    )
    assert _main_at(repo) == before
    flag.unlink()
    assert _merge(repo)[1][-1] == MERGED


def test_merge_switches_a_primary_that_is_this_checkout(repo: Repo) -> None:
    _cut_release(repo)
    release = repo.head
    code, lines = _merge(repo)
    assert (code, lines[-1]) == (0, MERGED)
    assert repo.git("branch", "--show-current").strip() == "main"
    assert repo.git("rev-list", "--parents", "-n", "1", "main").split()[2] == release


def test_merge_halts_when_the_merged_tree_differs(
    repo: Repo, monkeypatch: pytest.MonkeyPatch
) -> None:
    _cut_release(repo)
    real = repo.ns.Git.ok

    def differs(git: object, *args: str) -> bool:
        return args[0] != "diff" and real(git, *args)

    monkeypatch.setattr(repo.ns.Git, "ok", differs)
    code, lines = _merge(repo)
    assert (code, lines[-1]) == (
        1,
        f"release: halt — merge: main's tree is not {CHANGE}'s",
    )
