"""The structure rules over the scripts, per 0124 design D1."""

import ast
import re
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent
_FOLDERS = ("skills", "scripts")
_OWNERS = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
_MAP = "docs/modules.md"
_LAYERS = ("conductor", "station", "reader", "gate", "home")

LOADS_OUTSIDE: frozenset[tuple[str, str]] = frozenset(
    {
        ("brief_check.py", "conduct.py"),
        ("brief_check.py", "verify_check.py"),
        ("converge.py", "integrate.py"),
        ("cut_check.py", "gate_check.py"),
        ("cut_check.py", "plan_check.py"),
        ("cut_context.py", "brief_check.py"),
        ("cut_context.py", "bundle.py"),
        ("cut_context.py", "debt_match.py"),
        ("facts.py", "brief_check.py"),
        ("review_metrics.py", "conduct.py"),
        ("review_metrics.py", "metrics.py"),
        ("review_metrics.py", "overlap.py"),
        ("viewer.py", "conduct.py"),
        ("viewer.py", "converge.py"),
    }
)
CYCLE_FILES: frozenset[str] = frozenset({"brief_check.py", "conduct.py", "pin.py"})
PRIVATE_REACH: frozenset[tuple[str, str]] = frozenset(
    {
        ("brief_check.py", "_plain_row"),
        ("brief_check.py", "_rows"),
        ("pin.py", "_kept_origin"),
        ("pin.py", "_scratch"),
        ("review_metrics.py", "_STYLE"),
        ("viewer.py", "_build_halt"),
        ("viewer.py", "_claim"),
        ("viewer.py", "_cuts"),
        ("viewer.py", "_frontmatter"),
        ("viewer.py", "_maybe"),
        ("viewer.py", "_progress"),
        ("viewer.py", "_queue"),
        ("viewer.py", "_rating"),
    }
)
OS_NAMES: frozenset[tuple[str, str]] = frozenset(
    {
        ("awake.py", "caffeinate"),
        ("awake.py", "ps"),
        ("conduct.py", "caffeinate"),
        ("conduct.py", "ps"),
        ("conduct.py", "sandbox-exec"),
        ("conduct.py", "sysctl"),
        ("viewer.py", "ps"),
    }
)
_OS_WORDS = re.compile(r"\b(sandbox-exec|caffeinate|sysctl|ps)\b")
_PLAIN = ("self", "cls")


def python_files(root: Path) -> list[str]:
    """Return the sorted repo-relative path of each `*.py` under the script folders.

    e.g. `["scripts/corpus.py", "skills/mf-ship/scripts/conduct.py"]`
    """
    return sorted(
        path.relative_to(root).as_posix()
        for folder in _FOLDERS
        for path in (root / folder).rglob("*.py")
    )


def _docstrings(tree: ast.Module) -> set[int]:
    """Return the ids of the module, class and function docstring nodes in `tree`."""
    found: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, _OWNERS) or not node.body:
            continue
        first = node.body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            found.add(id(first.value))
    return found


def _strings(tree: ast.Module) -> list[str]:
    """Return each string constant in `tree` outside its docstrings."""
    skip = _docstrings(tree)
    return [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in skip
    ]


def _parse(root: Path) -> dict[str, ast.Module]:
    """Return each script's path mapped to its syntax tree."""
    return {
        path: ast.parse((root / path).read_text(encoding="utf-8"))
        for path in python_files(root)
    }


def edges(root: Path) -> dict[str, list[str]]:
    """Return each script's path mapped to the sorted paths of the scripts it names.

    e.g. `"b/y.py"` in `a/x.py` → `{"a/x.py": ["b/y.py"], "b/y.py": []}`
    """
    return _edges(_parse(root))


def _edges(trees: dict[str, ast.Module]) -> dict[str, list[str]]:
    """Return each path of `trees` mapped to the sorted paths its strings name."""
    by_base: dict[str, list[str]] = {}
    for path in trees:
        by_base.setdefault(path.rpartition("/")[2], []).append(path)
    found: dict[str, list[str]] = {}
    for path, tree in trees.items():
        bases = {text.rpartition("/")[2] for text in _strings(tree)}
        found[path] = sorted(
            other for base in bases for other in by_base.get(base, []) if other != path
        )
    return found


def map_rows(root: Path) -> dict[str, tuple[str, str]]:
    """Return each path in the map's table mapped to its layer and `names` cell.

    e.g. `{"skills/mf-ship/scripts/pin.py": ("conductor", "conduct.py")}`
    """
    rows: dict[str, tuple[str, str]] = {}
    for line in (root / _MAP).read_text(encoding="utf-8").splitlines():
        if not line.startswith("| `"):
            continue
        path, layer, names = (cell.strip() for cell in line.strip("|").split("|"))
        rows[path.strip("`")] = (layer, names)
    return rows


def check_map(root: Path) -> list[str]:
    """Return a breach line for each way the map and the tree differ — rule 5.

    e.g. `["scripts/x.py: no row in docs/modules.md"]`
    """
    found = edges(root)
    rows = map_rows(root)
    breaches = [f"{path}: no row in {_MAP}" for path in found if path not in rows]
    breaches += [f"{path}: a row with no file" for path in rows if path not in found]
    by_base: dict[str, list[str]] = {}
    for path in found:
        by_base.setdefault(path.rpartition("/")[2], []).append(path)
    breaches += [
        f"{base}: a base name held by {', '.join(paths)}"
        for base, paths in by_base.items()
        if len(paths) > 1
    ]
    for path, (layer, names) in rows.items():
        if layer not in _LAYERS:
            breaches.append(f"{path}: layer {layer!r} is none of {', '.join(_LAYERS)}")
        if path in found:
            named = ", ".join(sorted(other.rpartition("/")[2] for other in found[path]))
            if names != (named or "—"):
                breaches.append(
                    f"{path}: the map names {names!r}, the file {named or '—'!r}"
                )
    return breaches


def _against(found: set[str], listed: set[str], what: str, name: str) -> list[str]:
    """Return a line for each entry found and not listed, and each listed, not found.

    e.g. `["x.py: in a cycle, not listed in CYCLE_FILES"]`
    """
    new = [f"{entry}: {what}, not listed in {name}" for entry in sorted(found - listed)]
    gone = [f"{entry}: listed in {name}, not found" for entry in sorted(listed - found)]
    return new + gone


def _allowed(path: str, other: str, layer: dict[str, str]) -> bool:
    """Return whether rule 1 lets the script at `path` name the one at `other`."""
    return (
        path.rpartition("/")[0] == other.rpartition("/")[0]
        or layer.get(other) == "home"
        or (layer.get(path) == "conductor" and layer.get(other) == "station")
    )


def check_loads(
    root: Path, listed: frozenset[tuple[str, str]] = LOADS_OUTSIDE
) -> list[str]:
    """Return a breach line for each name the layers do not allow — rule 1.

    e.g. `["converge.py → integrate.py: a load the layers do not allow, …"]`
    """
    layer = {path: cells[0] for path, cells in map_rows(root).items()}
    found = {
        f"{path.rpartition('/')[2]} → {other.rpartition('/')[2]}"
        for path, named in edges(root).items()
        for other in named
        if not _allowed(path, other, layer)
    }
    shown = {" → ".join(pair) for pair in listed}
    return _against(found, shown, "a load the layers do not allow", "LOADS_OUTSIDE")


def _reach(found: dict[str, list[str]], start: str) -> set[str]:
    """Return the paths reachable from `start` by one edge or more."""
    seen: set[str] = set()
    todo = list(found[start])
    while todo:
        path = todo.pop()
        if path not in seen:
            seen.add(path)
            todo.extend(found[path])
    return seen


def check_cycles(root: Path, listed: frozenset[str] = CYCLE_FILES) -> list[str]:
    """Return a breach line for each file in a cycle and not listed — rule 3.

    e.g. `["pin.py: in a cycle, not listed in CYCLE_FILES"]`
    """
    found = edges(root)
    cyclic = {path.rpartition("/")[2] for path in found if path in _reach(found, path)}
    return _against(cyclic, set(listed), "in a cycle", "CYCLE_FILES")


def _top_names(tree: ast.Module) -> set[str]:
    """Return the names `tree` defines by `def`, `class` or assignment at its top."""
    found: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            found.add(node.name)
        elif isinstance(node, ast.Assign | ast.AnnAssign):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            found.update(
                name.id
                for target in targets
                for name in ast.walk(target)
                if isinstance(name, ast.Name)
            )
    return found


def _text(node: ast.expr) -> str:
    """Return the text of a string constant, or `""` for any other node."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return ""


def _taken(tree: ast.Module) -> set[str]:
    """Return each private name `tree` reads by key, `getattr`, attribute or import.

    e.g. `ns["_rows"]`, `ns.get("_rows")`, `mod._STYLE`, `from y import _z`
    """
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript):
            found.add(_text(node.slice))
        elif isinstance(node, ast.Call) and node.args:
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr == "get":
                found.add(_text(node.args[0]))
            elif isinstance(func, ast.Name) and func.id == "getattr":
                found.add(_text(node.args[1]) if len(node.args) > 1 else "")
        elif (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id not in _PLAIN
        ):
            found.add(node.attr)
        elif isinstance(node, ast.ImportFrom):
            found.update(alias.name for alias in node.names)
    return {name for name in found if name[:1] == "_" and name[:2] != "__"}


def check_names(
    root: Path, listed: frozenset[tuple[str, str]] = PRIVATE_REACH
) -> list[str]:
    """Return a breach line for each private name taken from a named file — rule 2.

    e.g. `["viewer.py takes _claim: a private name of a file it names, …"]`
    """
    trees = _parse(root)
    defined = {path: _top_names(tree) for path, tree in trees.items()}
    found = {
        f"{path.rpartition('/')[2]} takes {name}"
        for path, named in _edges(trees).items()
        for name in _taken(trees[path])
        if any(name in defined[other] for other in named)
    }
    shown = {f"{file} takes {name}" for file, name in listed}
    return _against(found, shown, "a private name of a file it names", "PRIVATE_REACH")


def check_os(root: Path, listed: frozenset[tuple[str, str]] = OS_NAMES) -> list[str]:
    """Return a breach line for each OS command named outside its files — rule 4.

    e.g. `["awake.py names caffeinate: an OS command, not listed in OS_NAMES"]`
    """
    found = {
        f"{path.rpartition('/')[2]} names {word}"
        for path, tree in _parse(root).items()
        for text in _strings(tree)
        for word in _OS_WORDS.findall(text)
    }
    shown = {f"{file} names {word}" for file, word in listed}
    return _against(found, shown, "an OS command", "OS_NAMES")


def _plant(root: Path, files: dict[str, str]) -> Path:
    """Write each repo-relative file under `root` and return `root`."""
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


def test_edges_finds_a_path_to_another_script(tmp_path: Path) -> None:
    root = _plant(
        tmp_path,
        {
            "skills/mf-a/scripts/x.py": 'HERE = "mf-b/scripts/y.py"\n',
            "skills/mf-b/scripts/y.py": "",
        },
    )
    assert edges(root) == {
        "skills/mf-a/scripts/x.py": ["skills/mf-b/scripts/y.py"],
        "skills/mf-b/scripts/y.py": [],
    }


def test_edges_finds_a_bare_base_name(tmp_path: Path) -> None:
    root = _plant(
        tmp_path,
        {
            "scripts/x.py": 'import runpy\nrunpy.run_path("y.py")\n',
            "scripts/y.py": "",
        },
    )
    assert edges(root)["scripts/x.py"] == ["scripts/y.py"]


def test_edges_skip_a_name_in_a_docstring(tmp_path: Path) -> None:
    source = (
        '"""Run y.py."""\n'
        "class C:\n"
        '    """mf-b/scripts/y.py"""\n'
        "def f() -> None:\n"
        '    """y.py"""\n'
    )
    root = _plant(tmp_path, {"scripts/x.py": source, "scripts/y.py": ""})
    assert edges(root)["scripts/x.py"] == []


def test_edges_skip_a_self_name(tmp_path: Path) -> None:
    root = _plant(tmp_path, {"scripts/x.py": 'ME = "scripts/x.py"\n'})
    assert edges(root) == {"scripts/x.py": []}


def test_edges_skip_a_name_inside_longer_text(tmp_path: Path) -> None:
    root = _plant(
        tmp_path,
        {"scripts/x.py": 'SAY = "run y.py"\nTOO = "y.py now"\n', "scripts/y.py": ""},
    )
    assert edges(root)["scripts/x.py"] == []


def test_edges_cover_each_python_file_of_the_tree() -> None:
    assert sorted(edges(_REPO)) == python_files(_REPO)
    assert "skills/mf-ship/scripts/conduct.py" in python_files(_REPO)


_HEAD = "| path | layer | names |\n|---|---|---|\n"
_X = 'Y = "y.py"\n'


def _mapped(root: Path, files: dict[str, str], rows: str) -> Path:
    """Plant `files` and a map holding `rows` under `root`, and return `root`."""
    return _plant(root, {**files, _MAP: "# map\n\n" + _HEAD + rows})


def test_check_map_holds_on_the_tree() -> None:
    assert check_map(_REPO) == []


def test_check_map_holds_on_a_planted_tree(tmp_path: Path) -> None:
    rows = "| `scripts/x.py` | gate | y.py |\n| `scripts/y.py` | gate | — |\n"
    root = _mapped(tmp_path, {"scripts/x.py": _X, "scripts/y.py": ""}, rows)
    assert check_map(root) == []


def test_check_map_fails_on_a_file_with_no_row(tmp_path: Path) -> None:
    root = _mapped(tmp_path, {"scripts/x.py": ""}, "")
    assert check_map(root) == ["scripts/x.py: no row in docs/modules.md"]


def test_check_map_fails_on_a_row_with_no_file(tmp_path: Path) -> None:
    root = _mapped(tmp_path, {}, "| `scripts/gone.py` | gate | — |\n")
    assert check_map(root) == ["scripts/gone.py: a row with no file"]


def test_check_map_fails_on_a_names_cell_that_differs(tmp_path: Path) -> None:
    rows = "| `scripts/x.py` | gate | — |\n| `scripts/y.py` | gate | — |\n"
    root = _mapped(tmp_path, {"scripts/x.py": _X, "scripts/y.py": ""}, rows)
    assert check_map(root) == ["scripts/x.py: the map names '—', the file 'y.py'"]


def test_check_map_fails_on_a_layer_outside_the_list(tmp_path: Path) -> None:
    root = _mapped(tmp_path, {"scripts/x.py": ""}, "| `scripts/x.py` | helper | — |\n")
    assert check_map(root) == [
        "scripts/x.py: layer 'helper' is none of conductor, station, reader, gate, home"
    ]


def test_check_map_fails_on_a_base_name_two_files_hold(tmp_path: Path) -> None:
    rows = (
        "| `scripts/y.py` | gate | — |\n| `skills/mf-a/scripts/y.py` | station | — |\n"
    )
    root = _mapped(tmp_path, {"scripts/y.py": "", "skills/mf-a/scripts/y.py": ""}, rows)
    assert check_map(root) == [
        "y.py: a base name held by scripts/y.py, skills/mf-a/scripts/y.py"
    ]


_STATIONS = (
    "| `skills/mf-a/scripts/x.py` | station | y.py |\n"
    "| `skills/mf-b/scripts/y.py` | station | — |\n"
)
_STATION_LOAD = {
    "skills/mf-a/scripts/x.py": 'Y = "mf-b/scripts/y.py"\n',
    "skills/mf-b/scripts/y.py": "",
}


def test_check_loads_holds_on_the_tree() -> None:
    assert check_loads(_REPO) == []


def test_check_loads_fails_on_a_station_naming_another_station(
    tmp_path: Path,
) -> None:
    root = _mapped(tmp_path, _STATION_LOAD, _STATIONS)
    assert check_loads(root, listed=frozenset()) == [
        "x.py → y.py: a load the layers do not allow, not listed in LOADS_OUTSIDE"
    ]


def test_check_loads_passes_a_listed_pair(tmp_path: Path) -> None:
    root = _mapped(tmp_path, _STATION_LOAD, _STATIONS)
    assert check_loads(root, listed=frozenset({("x.py", "y.py")})) == []


def test_check_loads_passes_the_folder_the_home_and_the_conductor(
    tmp_path: Path,
) -> None:
    files = {
        "skills/mf-a/scripts/x.py": 'W = "w.py"\nH = "mflib/h.py"\n',
        "skills/mf-a/scripts/w.py": "",
        "skills/mflib/h.py": "",
        "skills/mf-ship/scripts/c.py": 'X = "mf-a/scripts/x.py"\n',
    }
    rows = (
        "| `skills/mf-a/scripts/x.py` | station | h.py, w.py |\n"
        "| `skills/mf-a/scripts/w.py` | station | — |\n"
        "| `skills/mflib/h.py` | home | — |\n"
        "| `skills/mf-ship/scripts/c.py` | conductor | x.py |\n"
    )
    root = _mapped(tmp_path, files, rows)
    assert check_loads(root, listed=frozenset()) == []


def test_check_loads_fails_on_a_listed_pair_the_tree_no_longer_holds(
    tmp_path: Path,
) -> None:
    files = {**_STATION_LOAD, "skills/mf-a/scripts/x.py": ""}
    root = _mapped(tmp_path, files, _STATIONS)
    assert check_loads(root, listed=frozenset({("x.py", "y.py")})) == [
        "x.py → y.py: listed in LOADS_OUTSIDE, not found"
    ]


_CYCLE = {"scripts/x.py": 'Y = "y.py"\n', "scripts/y.py": 'X = "x.py"\n'}


def test_check_cycles_holds_on_the_tree() -> None:
    assert check_cycles(_REPO) == []


def test_check_cycles_fails_on_a_planted_cycle(tmp_path: Path) -> None:
    root = _plant(tmp_path, {**_CYCLE, "scripts/z.py": 'X = "x.py"\n'})
    assert check_cycles(root, listed=frozenset()) == [
        "x.py: in a cycle, not listed in CYCLE_FILES",
        "y.py: in a cycle, not listed in CYCLE_FILES",
    ]


def test_check_cycles_passes_a_listed_cycle(tmp_path: Path) -> None:
    root = _plant(tmp_path, _CYCLE)
    assert check_cycles(root, listed=frozenset({"x.py", "y.py"})) == []


def test_check_cycles_fails_on_a_listed_file_in_no_cycle(tmp_path: Path) -> None:
    root = _plant(tmp_path, {**_CYCLE, "scripts/y.py": ""})
    assert check_cycles(root, listed=frozenset({"x.py", "y.py"})) == [
        "x.py: listed in CYCLE_FILES, not found",
        "y.py: listed in CYCLE_FILES, not found",
    ]


_Y = 'z = 1\n_z: int = 1\n__all__ = ["z"]\n'
_REACH = 'Y = "y.py"\nns["_z"]\n'


def _named(root: Path, source: str) -> Path:
    """Plant `scripts/x.py` holding `source` beside `scripts/y.py`; return `root`."""
    return _plant(root, {"scripts/x.py": source, "scripts/y.py": _Y})


def test_check_names_holds_on_the_tree() -> None:
    assert check_names(_REPO) == []


@pytest.mark.parametrize(
    "source",
    [
        _REACH,
        'Y = "y.py"\nns.get("_z")\n',
        'Y = "y.py"\ngetattr(ns, "_z")\n',
        'Y = "y.py"\nns._z\n',
        'Y = "y.py"\nfrom y import _z\n',
    ],
    ids=["subscript", "get", "getattr", "attribute", "from-import"],
)
def test_check_names_fails_on_a_private_reach(tmp_path: Path, source: str) -> None:
    root = _named(tmp_path, source)
    assert check_names(root, listed=frozenset()) == [
        "x.py takes _z: a private name of a file it names, not listed in PRIVATE_REACH"
    ]


@pytest.mark.parametrize(
    "source",
    [
        'Y = "y.py"\nns["z"]\n',
        'Y = "y.py"\nself._z\ncls._z\n',
        'Y = "y.py"\nns["__all__"]\n',
        'Y = "y.py"\nns["_w"]\ngetattr(ns)\n',
        'ns["_z"]\n',
    ],
    ids=["public", "self-and-cls", "dunder", "undefined", "unnamed-file"],
)
def test_check_names_passes_a_name_that_is_no_reach(
    tmp_path: Path, source: str
) -> None:
    assert check_names(_named(tmp_path, source), listed=frozenset()) == []


def test_check_names_passes_a_listed_pair(tmp_path: Path) -> None:
    root = _named(tmp_path, _REACH)
    assert check_names(root, listed=frozenset({("x.py", "_z")})) == []


def test_check_names_fails_on_a_listed_pair_the_tree_no_longer_holds(
    tmp_path: Path,
) -> None:
    root = _named(tmp_path, 'Y = "y.py"\n')
    assert check_names(root, listed=frozenset({("x.py", "_z")})) == [
        "x.py takes _z: listed in PRIVATE_REACH, not found"
    ]


_AWAKE = 'RUN = ["caffeinate", "-i"]\n'


def test_check_os_holds_on_the_tree() -> None:
    assert check_os(_REPO) == []


def test_check_os_fails_on_caffeinate_in_an_unlisted_file(tmp_path: Path) -> None:
    root = _plant(tmp_path, {"scripts/x.py": _AWAKE})
    assert check_os(root, listed=frozenset()) == [
        "x.py names caffeinate: an OS command, not listed in OS_NAMES"
    ]


@pytest.mark.parametrize(
    "source",
    ['"""Keep awake with caffeinate."""\n', 'U = "https://x"\nW = "caffeinated"\n'],
    ids=["docstring", "longer-word"],
)
def test_check_os_passes_a_word_that_names_no_command(
    tmp_path: Path, source: str
) -> None:
    root = _plant(tmp_path, {"scripts/x.py": source})
    assert check_os(root, listed=frozenset()) == []


def test_check_os_passes_a_listed_pair(tmp_path: Path) -> None:
    root = _plant(tmp_path, {"scripts/x.py": _AWAKE})
    assert check_os(root, listed=frozenset({("x.py", "caffeinate")})) == []


def test_check_os_fails_on_a_listed_pair_the_tree_no_longer_holds(
    tmp_path: Path,
) -> None:
    root = _plant(tmp_path, {"scripts/x.py": ""})
    assert check_os(root, listed=frozenset({("x.py", "caffeinate")})) == [
        "x.py names caffeinate: listed in OS_NAMES, not found"
    ]
