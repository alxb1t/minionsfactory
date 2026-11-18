"""The run directory's and home folder's paths, each against its spelling by hand.

Why: 0134-run-layout design D2, D3 and D5; 0135-home-layout design D2.
"""

import hashlib
from collections.abc import Callable
from pathlib import Path

import pytest
from fake_worker import _commit, _git
from mflib import layout
from old_layout import ENTRIES, LOG, ROLES, plant


def test_the_run_directory_is_the_primarys_minions(tmp_path: Path) -> None:
    assert layout.run_dir(tmp_path) == tmp_path / ".minions"


def test_a_change_folder_is_under_changes(tmp_path: Path) -> None:
    assert layout.change_dir(tmp_path, "0001-todo") == (
        tmp_path / ".minions" / "changes" / "0001-todo"
    )
    assert layout.CHANGES == "changes"


@pytest.mark.parametrize(
    ("name", "spelled"),
    [
        (layout.runs_dir, ".minions/runs"),
        (layout.claim_file, ".minions/runs/active"),
        (layout.debt_file, ".minions/debt.md"),
        (layout.debt_lock, ".minions/debt.lock"),
        (layout.backlog_file, ".minions/backlog.md"),
        (layout.backlog_lock, ".minions/backlog.lock"),
        (layout.gate_dir, ".minions/gate"),
    ],
    ids=["runs", "claim", "debt", "debt-lock", "backlog", "backlog-lock", "gate"],
)
def test_a_generic_entry_is_its_spelled_path(
    tmp_path: Path, name: Callable[[Path], Path], spelled: str
) -> None:
    assert name(tmp_path) == tmp_path / spelled


def test_a_cut_reservation_is_under_cuts(tmp_path: Path) -> None:
    assert layout.cut_reservation(tmp_path, "0001-todo") == (
        tmp_path / ".minions" / "cuts" / "0001-todo"
    )


def test_a_metrics_page_is_the_changes_html(tmp_path: Path) -> None:
    assert layout.metrics_page(tmp_path, "0001-todo") == (
        tmp_path / ".minions" / "metrics" / "0001-todo.html"
    )


def test_a_path_follows_the_primary_it_is_given(tmp_path: Path) -> None:
    assert layout.run_dir(tmp_path / "a") != layout.run_dir(tmp_path / "b")


@pytest.mark.parametrize("given", [str, Path], ids=["text", "path"])
def test_primary_of_takes_text_or_a_path(
    tmp_path: Path, given: Callable[[str], str | Path]
) -> None:
    common = tmp_path / "main" / ".git"
    assert layout.primary_of(given(str(common))) == tmp_path / "main"


def test_primary_of_gives_one_primary_from_a_linked_worktree(tmp_path: Path) -> None:
    primary = tmp_path / "main"
    primary.mkdir()
    _git(primary, "init", "-q", "-b", "main")
    _commit(primary, {".gitignore": ".minions/\n"}, "base")
    linked = tmp_path / "0001-a"
    _git(primary, "worktree", "add", "-q", "-b", "0001-a", str(linked))
    asked = ("rev-parse", "--path-format=absolute", "--git-common-dir")

    found = {layout.primary_of(_git(cwd, *asked)) for cwd in (primary, linked)}

    assert found == {primary.resolve()}


@pytest.mark.parametrize("old", [*ENTRIES, *ROLES, *LOG])
def test_old_files_finds_each_old_entry_alone(tmp_path: Path, old: str) -> None:
    path = plant(layout.run_dir(tmp_path), "0001-todo", old)
    new = {**ENTRIES, **ROLES, **LOG}[old]

    assert layout.old_files(tmp_path) == {"0001-todo": [(path, new)]}
    assert layout.old_layout(tmp_path, "0001-todo") == str(path.relative_to(tmp_path))
    assert layout.old_layout(tmp_path, "0002-other") is None


@pytest.mark.parametrize("change", ["1-x", "10000-x"], ids=["short", "five-digit"])
def test_old_files_finds_an_id_of_any_width(tmp_path: Path, change: str) -> None:
    every = {**ENTRIES, **ROLES, **LOG}
    planted = [
        (plant(layout.run_dir(tmp_path), change, old), new)
        for old, new in every.items()
    ]

    assert sorted(layout.old_files(tmp_path)[change]) == sorted(planted)
    assert layout.old_layout(tmp_path, change) == str(
        min(planted)[0].relative_to(tmp_path)
    )


def test_the_table_equals_the_literals() -> None:
    roles = {f"changes/{{}}/{name}": new for name, new in layout.OLD_ROLES.items()}
    logs = {}
    for old in LOG:
        _runs, stamp, name = old.split("/")
        assert layout.OLD_STAMP.fullmatch(stamp), stamp
        found = layout.OLD_LOG.fullmatch(name.format("0001-todo"))
        assert found, name
        assert found[1] == "0001-todo", name
        logs[old] = f"logs/{stamp}-{found[2]}{found[3] or ''}.log"

    assert layout.OLD_LAYOUT == ENTRIES
    assert roles == ROLES
    assert logs == LOG


def test_old_layout_names_the_first_sorted_path(tmp_path: Path) -> None:
    for old in ("findings/{}_review.md", "build/{}.done"):
        plant(layout.run_dir(tmp_path), "0001-todo", old)

    assert layout.old_layout(tmp_path, "0001-todo") == ".minions/build/0001-todo.done"


def _spelled_digest(primary: Path) -> str:
    return hashlib.sha256(str(primary.resolve()).encode()).hexdigest()[:16]


@pytest.mark.parametrize(
    ("name", "spelled"),
    [
        (lambda _: layout.kept_dir(), "~/.mf-ship-origin"),
        (layout.kept_file, "~/.mf-ship-origin/{d}"),
        (layout.released_dir, "~/.mf-ship-origin/{d}.released"),
        (layout.default_file, "~/.mf-ship-origin/{d}.default"),
        (layout.pushed_file, "~/.mf-ship-origin/{d}.pushed"),
        (layout.queue_dir, "~/.mf-ship-origin/{d}.queue"),
        (layout.queue_lock, "~/.mf-ship-origin/{d}.queue/lock"),
        (layout.queue_cuts, "~/.mf-ship-origin/{d}.queue/cuts"),
        (layout.queue_rejoin, "~/.mf-ship-origin/{d}.queue/rejoin"),
        (layout.queue_briefs, "~/.mf-ship-origin/{d}.queue/briefs"),
        (layout.queue_supervised, "~/.mf-ship-origin/{d}.queue/supervised"),
        (
            lambda primary: layout.gate_approval(primary, "0001-todo"),
            "~/.mf-ship-origin/{d}.gate/0001-todo",
        ),
        (lambda _: layout.live_dir(), "~/.mf-ship-origin/live"),
        (layout.live_mark, "~/.mf-ship-origin/live/{d}"),
        (lambda _: layout.repos_file(), "~/.mf-ship-origin/repos"),
        (
            lambda _: layout.probe_mark("codex", 41),
            "~/.mf-ship-origin/probe-codex-41",
        ),
        (lambda _: layout.pin_source(), "~/.mf-ship-origin/source"),
        (lambda _: layout.pin_pending(), "~/.mf-ship-origin/pending"),
        (lambda _: layout.pin_hold(), "~/.mf-ship-origin/hold"),
        (lambda _: layout.pin_checkout(), "~/.mf-ship-origin/checkout"),
    ],
    ids=[
        "kept_dir",
        "kept_file",
        "released_dir",
        "default_file",
        "pushed_file",
        "queue_dir",
        "queue_lock",
        "queue_cuts",
        "queue_rejoin",
        "queue_briefs",
        "queue_supervised",
        "gate_approval",
        "live_dir",
        "live_mark",
        "repos_file",
        "probe_mark",
        "pin_source",
        "pin_pending",
        "pin_hold",
        "pin_checkout",
    ],
)
def test_a_kept_name_is_its_spelled_path(
    tmp_path: Path, name: Callable[[Path], Path], spelled: str
) -> None:
    primary = tmp_path / "main"
    primary.mkdir()
    expected = Path(spelled.format(d=_spelled_digest(primary))).expanduser()

    assert name(primary) == expected
    assert layout.KEPT_ORIGINS == ".mf-ship-origin"


def test_a_linked_path_has_the_primarys_digest(tmp_path: Path) -> None:
    primary = tmp_path / "main"
    primary.mkdir()
    link = tmp_path / "link"
    link.symlink_to(primary)

    assert layout.digest(link) == layout.digest(primary) == _spelled_digest(primary)
    assert layout.kept_file(link) == layout.kept_file(primary)
    assert layout.digest(tmp_path / "other") != layout.digest(primary)


@pytest.mark.parametrize(
    ("name", "variable", "fallback", "under"),
    [
        (
            layout.ship_file,
            "XDG_CONFIG_HOME",
            "~/.config/minionsfactory/ship.toml",
            "minionsfactory/ship.toml",
        ),
        (
            layout.review_metrics_file,
            "XDG_CONFIG_HOME",
            "~/.config/minionsfactory/review-metrics.toml",
            "minionsfactory/review-metrics.toml",
        ),
        (
            layout.ui_file,
            "XDG_CONFIG_HOME",
            "~/.config/minionsfactory/ui.toml",
            "minionsfactory/ui.toml",
        ),
        (
            layout.data_dir,
            "XDG_DATA_HOME",
            "~/.local/share/minionsfactory",
            "minionsfactory",
        ),
        (
            layout.state_dir,
            "XDG_STATE_HOME",
            "~/.local/state/minionsfactory",
            "minionsfactory",
        ),
        (layout.codex_home, "CODEX_HOME", "~/.codex", ""),
        (layout.claude_home, "CLAUDE_CONFIG_DIR", "~/.claude", ""),
        (lambda: layout.skills_dir("claude"), None, "~/.claude/skills", ""),
        (lambda: layout.skills_dir("codex"), None, "~/.agents/skills", ""),
        (layout.scratch_parent, None, "~", ""),
    ],
    ids=[
        "ship_file",
        "review_metrics_file",
        "ui_file",
        "data_dir",
        "state_dir",
        "codex_home",
        "claude_home",
        "skills_dir-claude",
        "skills_dir-codex",
        "scratch_parent",
    ],
)
def test_a_root_follows_its_variable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    name: Callable[[], Path],
    variable: str | None,
    fallback: str,
    under: str,
) -> None:
    if variable is not None:
        monkeypatch.delenv(variable, raising=False)
    first = name()
    assert first == Path(fallback).expanduser()

    monkeypatch.setenv("HOME", str(tmp_path / "other-home"))
    assert name() == Path(fallback).expanduser() != first

    if variable is not None:
        monkeypatch.setenv(variable, str(tmp_path / "a"))
        assert name() == tmp_path / "a" / under
        monkeypatch.setenv(variable, str(tmp_path / "b"))
        assert name() == tmp_path / "b" / under


@pytest.mark.parametrize(
    ("variable", "name", "fallback"),
    [
        ("XDG_CONFIG_HOME", layout.config_dir, "~/.config/minionsfactory"),
        ("XDG_DATA_HOME", layout.data_dir, "~/.local/share/minionsfactory"),
        ("XDG_STATE_HOME", layout.state_dir, "~/.local/state/minionsfactory"),
        ("CODEX_HOME", layout.codex_home, "~/.codex"),
        ("CLAUDE_CONFIG_DIR", layout.claude_home, "~/.claude"),
    ],
)
def test_an_empty_variable_reads_as_unset(
    monkeypatch: pytest.MonkeyPatch,
    variable: str,
    name: Callable[[], Path],
    fallback: str,
) -> None:
    monkeypatch.setenv(variable, "")

    assert name() == Path(fallback).expanduser()
