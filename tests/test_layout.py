"""The run directory's paths, each against the path spelled by hand, and the old layout.

Why: 0134-run-layout design D2, D3 and D5.
"""

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


def test_old_layout_names_the_first_sorted_path(tmp_path: Path) -> None:
    for old in ("findings/{}_review.md", "build/{}.done"):
        plant(layout.run_dir(tmp_path), "0001-todo", old)

    assert layout.old_layout(tmp_path, "0001-todo") == ".minions/build/0001-todo.done"
