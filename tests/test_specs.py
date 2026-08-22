from pathlib import Path

import pytest

from orchestrator.specs import (
    check,
    parse_scenarios,
    parse_test_module,
    run_check,
)


def _write(path: Path, body: str) -> None:
    """Create parent dirs and write a fixture file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)


_SPEC = """\
# Capability: foo

## ADDED Requirements

### Requirement: Bar
The system SHALL bar.

#### Scenario: Baz happens
- **Key:** `foo:bar:baz`
- **Layers:** unit
- **WHEN** a thing
- **THEN** another thing

#### Scenario: Boundary case
- **Key:** `foo:bar:boundary`
- **Layers:** unit, e2e
- **WHEN** a boundary
- **THEN** a result
"""


def _shipped_spec(body: str) -> str:
    """Wrap scenarios in a shipped (non-delta) requirement block."""
    return "# Capability: foo\n\n" + body


def _clean_repo(tmp_path: Path, *, key: str = "foo:bar:baz") -> Path:
    """A tree with one shipped unit scenario and a test that proves it."""
    _write(
        tmp_path / "openspec" / "specs" / "foo" / "spec.md",
        _shipped_spec(
            "### Requirement: Bar\nThe system SHALL bar.\n\n"
            "#### Scenario: Baz\n"
            f"- **Key:** `{key}`\n"
            "- **Layers:** unit\n"
            "- **WHEN** a thing\n- **THEN** a result\n"
        ),
    )
    _write(
        tmp_path / "tests" / "test_foo.py",
        "import pytest\n\n\n"
        f'@pytest.mark.spec("{key}")\n'
        "def test_bar_bars() -> None:\n    assert True\n",
    )
    return tmp_path


# --- plumbing (mechanism) tests -------------------------------------------------


@pytest.mark.spec_exempt("mechanism/plumbing")
def test_parse_scenarios_extracts_keys_and_layers() -> None:
    scenarios = parse_scenarios(_SPEC)
    by_key = {s.key: s for s in scenarios}
    assert set(by_key) == {"foo:bar:baz", "foo:bar:boundary"}
    assert by_key["foo:bar:baz"].layers == frozenset({"unit"})
    assert by_key["foo:bar:boundary"].layers == frozenset({"unit", "e2e"})
    assert by_key["foo:bar:baz"].section == "ADDED"


@pytest.mark.spec_exempt("mechanism/plumbing")
def test_parse_test_module_collects_spec_and_exempt_markers(tmp_path: Path) -> None:
    module = tmp_path / "test_sample.py"
    module.write_text(
        "import pytest\n\n\n"
        '@pytest.mark.spec("cap:req:scn")\n'
        "def test_one() -> None:\n    pass\n\n\n"
        '@pytest.mark.spec_exempt("wiring")\n'
        "def test_two() -> None:\n    pass\n\n\n"
        "def test_three() -> None:\n    pass\n"
    )
    bindings = {b.name: b for b in parse_test_module(module)}
    assert bindings["test_one"].bindings == (("cap:req:scn", "unit"),)
    assert bindings["test_one"].exempt is False
    assert bindings["test_two"].exempt is True
    assert bindings["test_two"].bindings == ()
    assert bindings["test_three"].bindings == ()
    assert bindings["test_three"].exempt is False


# --- behavioral (checker) tests -------------------------------------------------


@pytest.mark.spec("sdd:enforced-binding:orphan-scenario-fails")
def test_orphan_scenario_fails_and_is_named(tmp_path: Path) -> None:
    _write(
        tmp_path / "openspec" / "specs" / "foo" / "spec.md",
        _shipped_spec(
            "### Requirement: Bar\nThe system SHALL bar.\n\n"
            "#### Scenario: Orphaned\n"
            "- **Key:** `foo:bar:orphan`\n"
            "- **Layers:** unit\n"
            "- **WHEN** a thing\n- **THEN** a result\n"
        ),
    )
    (tmp_path / "tests").mkdir()

    result = check(tmp_path)
    assert result.ok is False
    assert "foo:bar:orphan" in result.orphans

    lines: list[str] = []
    assert run_check(tmp_path, out=lines.append) == 1
    assert any("foo:bar:orphan" in line for line in lines)


@pytest.mark.spec("sdd:enforced-binding:dangling-marker-fails")
def test_dangling_marker_fails_and_is_named(tmp_path: Path) -> None:
    (tmp_path / "openspec" / "specs").mkdir(parents=True)
    _write(
        tmp_path / "tests" / "test_foo.py",
        "import pytest\n\n\n"
        '@pytest.mark.spec("foo:bar:ghost")\n'
        "def test_it() -> None:\n    assert True\n",
    )

    result = check(tmp_path)
    assert result.ok is False
    assert "foo:bar:ghost" in result.dangling

    lines: list[str] = []
    assert run_check(tmp_path, out=lines.append) == 1
    assert any("foo:bar:ghost" in line for line in lines)


@pytest.mark.spec("sdd:enforced-binding:pending-delta-resolves")
def test_pending_delta_scenario_resolves(tmp_path: Path) -> None:
    _write(
        tmp_path / "openspec" / "changes" / "0009-x" / "specs" / "foo" / "spec.md",
        _SPEC,
    )
    _write(
        tmp_path / "tests" / "test_foo.py",
        "import pytest\n\n\n"
        '@pytest.mark.spec("foo:bar:baz")\n'
        "def test_it() -> None:\n    assert True\n",
    )

    result = check(tmp_path)
    assert result.ok is True
    assert result.dangling == ()
    assert result.orphans == ()


@pytest.mark.spec("sdd:enforced-binding:clean-passes")
def test_clean_binding_passes(tmp_path: Path) -> None:
    repo = _clean_repo(tmp_path)
    result = check(repo)
    assert result.ok is True
    assert run_check(repo, out=lambda _: None) == 0


@pytest.mark.spec("sdd:enforced-binding:empty-is-noop")
def test_empty_tree_is_a_green_noop(tmp_path: Path) -> None:
    (tmp_path / "tests").mkdir()
    result = check(tmp_path)
    assert result.ok is True
    assert run_check(tmp_path, out=lambda _: None) == 0


@pytest.mark.spec("sdd:enforced-binding:pending-delta-resolves")
def test_archived_change_delta_is_excluded(tmp_path: Path) -> None:
    _write(
        tmp_path
        / "openspec"
        / "changes"
        / "archive"
        / "0001-old"
        / "specs"
        / "foo"
        / "spec.md",
        _SPEC,
    )
    _write(
        tmp_path / "tests" / "test_foo.py",
        "import pytest\n\n\n"
        '@pytest.mark.spec("foo:bar:baz")\n'
        "def test_it() -> None:\n    assert True\n",
    )
    result = check(tmp_path)
    assert result.ok is False
    assert "foo:bar:baz" in result.dangling


@pytest.mark.spec("sdd:full-backfill:untraceable-test-fails")
def test_strict_flags_an_untraceable_test(tmp_path: Path) -> None:
    (tmp_path / "openspec" / "specs").mkdir(parents=True)
    _write(
        tmp_path / "tests" / "test_foo.py",
        "def test_unmarked() -> None:\n    assert True\n",
    )

    assert check(tmp_path, strict=False).ok is True
    result = check(tmp_path, strict=True)
    assert result.ok is False
    assert any("test_unmarked" in item for item in result.untraceable)

    lines: list[str] = []
    assert run_check(tmp_path, strict=True, out=lines.append) == 1
    assert any("test_unmarked" in line for line in lines)


@pytest.mark.spec("sdd:full-backfill:untraceable-test-fails")
def test_strict_accepts_marked_and_exempt_tests(tmp_path: Path) -> None:
    repo = _clean_repo(tmp_path)
    _write(
        repo / "tests" / "test_extra.py",
        'import pytest\n\n\n@pytest.mark.spec_exempt("wiring")\n'
        "def test_structural() -> None:\n    assert True\n",
    )
    assert check(repo, strict=True).ok is True
