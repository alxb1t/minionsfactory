"""Spec-binding checker: enforce that behavioral scenarios have proving tests.

A pure, stdlib-only module (no new dependency). It reads two sides of the binding
from disk and compares them:

- the **spec side** — scenario keys parsed from `specs/**/spec.md` (shipped) and each
  active `changes/*/specs/**/spec.md` delta (`changes/archive/` excluded);
- the **test side** — `@pytest.mark.spec(...)` / `@pytest.mark.spec_exempt(...)` markers
  collected *statically* with `ast` (the checker never imports or runs the tests).

Checks: **orphan** (a shipped unit-layer scenario with no proving test), **dangling**
(a `spec` marker whose key resolves to no scenario), and — under `--strict` — **full
traceability** (every collected test carries a `spec` or `spec_exempt` marker). Exit 0
when clean, exit 1 on any violation.
"""

import ast
import re
import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

_SECTION_RE = re.compile(
    r"^##\s+(ADDED|MODIFIED|REMOVED)\s+Requirements", re.IGNORECASE
)
_SCENARIO_RE = re.compile(r"^####\s+Scenario:")
_KEY_RE = re.compile(r"^\s*-\s*\*\*Key:\*\*\s*(.+?)\s*$")
_LAYERS_RE = re.compile(r"^\s*-\s*\*\*Layers:\*\*\s*(.+?)\s*$")


@dataclass(frozen=True)
class ParsedScenario:
    """One scenario parsed from a spec file: its stable key, layers, and delta section.

    `section` is `""` for a shipped (living) spec, or `ADDED` / `MODIFIED` / `REMOVED`
    when the scenario sits under a change delta's requirement section.
    """

    key: str
    layers: frozenset[str]
    section: str


@dataclass(frozen=True)
class TestBinding:
    """A collected test function and the spec markers statically found on it."""

    path: Path
    name: str
    bindings: tuple[tuple[str, str], ...]
    exempt: bool


@dataclass(frozen=True)
class CheckResult:
    """The verdict of a `specs check` run — the empty lists are the green state."""

    orphans: tuple[str, ...]
    dangling: tuple[str, ...]
    untraceable: tuple[str, ...]

    @property
    def ok(self) -> bool:
        """Whether the binding holds (no orphan, dangling, or untraceable finding)."""
        return not (self.orphans or self.dangling or self.untraceable)


def parse_scenarios(text: str) -> list[ParsedScenario]:
    """Parse a spec file's text into its scenarios (`Key:` + `Layers:` bullets).

    A line parser: `## ADDED/MODIFIED/REMOVED Requirements` sets the delta section for
    the scenarios beneath it; each `#### Scenario:` opens a scenario whose `Key:` and
    `Layers:` bullets follow. Scenarios without a `Key:` bullet are ignored (a prose
    scenario is not a binding target).
    """
    scenarios: list[ParsedScenario] = []
    section = ""
    key: str | None = None
    layers: frozenset[str] = frozenset()

    def flush() -> None:
        nonlocal key, layers
        if key is not None:
            scenarios.append(ParsedScenario(key=key, layers=layers, section=section))
        key, layers = None, frozenset()

    for line in text.splitlines():
        section_match = _SECTION_RE.match(line)
        if section_match:
            flush()
            section = section_match.group(1).upper()
            continue
        if _SCENARIO_RE.match(line):
            flush()
            continue
        key_match = _KEY_RE.match(line)
        if key_match:
            key = key_match.group(1).strip().strip("`").strip()
            continue
        layers_match = _LAYERS_RE.match(line)
        if layers_match:
            layers = frozenset(
                part.strip()
                for part in layers_match.group(1).split(",")
                if part.strip()
            )
    flush()
    return scenarios


def collect_spec_keys(repo: Path) -> tuple[dict[str, frozenset[str]], set[str]]:
    """Read spec keys from disk into (shipped scenarios, resolvable keys).

    `shipped` maps each top-level `specs/` scenario key to its layers — these are the
    keys the orphan check enforces. `resolvable` is the wider set a marker may point at:
    the shipped keys plus every active-delta ADDED/MODIFIED key (pending, orphan-exempt
    until folded), minus any the delta marks REMOVED.
    """
    shipped: dict[str, frozenset[str]] = {}
    specs_dir = repo / "specs"
    if specs_dir.exists():
        for path in sorted(specs_dir.rglob("spec.md")):
            for scenario in parse_scenarios(path.read_text()):
                shipped[scenario.key] = scenario.layers

    resolvable: set[str] = set(shipped)
    changes_dir = repo / "changes"
    if changes_dir.exists():
        for change_dir in sorted(changes_dir.iterdir()):
            if not change_dir.is_dir() or change_dir.name == "archive":
                continue
            for path in sorted((change_dir / "specs").rglob("spec.md")):
                for scenario in parse_scenarios(path.read_text()):
                    if scenario.section == "REMOVED":
                        resolvable.discard(scenario.key)
                        shipped.pop(scenario.key, None)
                    else:
                        resolvable.add(scenario.key)
    return shipped, resolvable


def _dotted(node: ast.expr) -> str:
    """Flatten an attribute/name chain to its dotted form (`pytest.mark.spec`)."""
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def _first_str_arg(args: list[ast.expr]) -> str | None:
    """Return the first positional string-literal argument, if any."""
    for arg in args:
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            return arg.value
    return None


def _keyword_str(keywords: list[ast.keyword], name: str) -> str | None:
    """Return the string-literal value of a keyword argument, if present."""
    for keyword in keywords:
        if keyword.arg == name and isinstance(keyword.value, ast.Constant):
            value = keyword.value.value
            if isinstance(value, str):
                return value
    return None


def parse_test_module(path: Path) -> list[TestBinding]:
    """Statically collect spec markers from one test module via `ast` (no import/run).

    Every `def test*` (module- or class-level) is a collected test; its `spec` markers
    contribute (key, layer) pairs (layer defaults to `unit`) and a `spec_exempt` marker
    sets its exemption. Only literal marker arguments are read — dynamic markers are
    unsupported in v0.3 (documented limitation).
    """
    tree = ast.parse(path.read_text())
    bindings: list[TestBinding] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not node.name.startswith("test"):
            continue
        keys: list[tuple[str, str]] = []
        exempt = False
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            dotted = _dotted(decorator.func)
            if dotted.endswith("mark.spec_exempt"):
                exempt = True
            elif dotted.endswith("mark.spec"):
                key = _first_str_arg(decorator.args)
                if key is not None:
                    layer = _keyword_str(decorator.keywords, "layer") or "unit"
                    keys.append((key, layer))
        bindings.append(
            TestBinding(path=path, name=node.name, bindings=tuple(keys), exempt=exempt)
        )
    return bindings


def _testpaths(repo: Path) -> list[str]:
    """Read `[tool.pytest.ini_options].testpaths` from pyproject (default `tests`)."""
    pyproject = repo / "pyproject.toml"
    if not pyproject.exists():
        return ["tests"]
    with pyproject.open("rb") as config_file:
        config = tomllib.load(config_file)
    ini = config.get("tool", {}).get("pytest", {}).get("ini_options", {})
    return ini.get("testpaths", ["tests"])


def collect_test_markers(repo: Path) -> list[TestBinding]:
    """Collect every test's spec markers across the configured test paths."""
    bindings: list[TestBinding] = []
    for base in _testpaths(repo):
        root = repo / base
        if not root.exists():
            continue
        for path in sorted(root.rglob("test_*.py")):
            bindings.extend(parse_test_module(path))
    return bindings


def check(repo: Path, strict: bool = False) -> CheckResult:
    """Compare the spec and test sides of the binding and return the verdict.

    Orphan: a shipped scenario declaring the `unit` layer with no `unit` marker on its
    key. Dangling: a referenced key present in neither `specs/` nor an active delta.
    Untraceable (`--strict` only): a collected test with neither a `spec` nor a
    `spec_exempt` marker.
    """
    shipped, resolvable = collect_spec_keys(repo)
    tests = collect_test_markers(repo)

    unit_bound = {
        key for test in tests for (key, layer) in test.bindings if layer == "unit"
    }
    referenced = {key for test in tests for (key, _) in test.bindings}

    orphans = tuple(
        sorted(
            key
            for key, layers in shipped.items()
            if "unit" in layers and key not in unit_bound
        )
    )
    dangling = tuple(sorted(key for key in referenced if key not in resolvable))
    untraceable: tuple[str, ...] = ()
    if strict:
        untraceable = tuple(
            sorted(
                f"{test.path.relative_to(repo)}::{test.name}"
                for test in tests
                if not test.exempt and not test.bindings
            )
        )
    return CheckResult(orphans=orphans, dangling=dangling, untraceable=untraceable)


def run_check(
    repo: Path, strict: bool = False, out: Callable[[str], None] = print
) -> int:
    """Run the check, report each violation, and return the process exit code (0/1)."""
    result = check(repo, strict=strict)
    for key in result.orphans:
        out(f"orphan: shipped scenario '{key}' has no proving unit test")
    for key in result.dangling:
        out(f"dangling: spec marker references unknown scenario key '{key}'")
    for test in result.untraceable:
        out(f"untraceable: test '{test}' has no spec or spec_exempt marker")
    if result.ok:
        out("specs check: ok")
        return 0
    return 1
