"""The release script's `pre`, `findings` and git helper, over a temporary repository.

Why: 0152-release-script design D1, D2 and D14.
"""

import contextlib
import importlib.util
import io
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
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
        setattr(self.ns, constant, path)

    def main(self, *argv: str) -> tuple[int, list[str]]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = self.ns.main(list(argv))
        return code, out.getvalue().splitlines()

    def pre(self, *flags: str) -> tuple[int, list[str]]:
        return self.main("pre", CHANGE, *flags)


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
