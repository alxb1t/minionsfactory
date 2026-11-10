"""The gate's ast-grep rule: a `subprocess.run` call must pass a timeout.

A temp project holds copies of the repo's `sgconfig.yml` and rule. Why: 0110 design D3.
"""

import shutil
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_AST_GREP = Path(sys.executable).parent / "ast-grep"
_NO_TIMEOUT = "import subprocess\nsubprocess.run(['true'])\n"
_TIMEOUT = "import subprocess\nsubprocess.run(['true'], timeout=5)\n"
_SECONDS = 60


def _scan(project: Path, source: str, where: str) -> subprocess.CompletedProcess[str]:
    target = project / where
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source)
    return subprocess.run(
        [str(_AST_GREP), "scan", where],
        cwd=project,
        capture_output=True,
        text=True,
        timeout=_SECONDS,
    )


def test_the_timeout_rule_flags_a_run_with_no_timeout(tmp_path: Path) -> None:
    shutil.copy(_REPO / "sgconfig.yml", tmp_path / "sgconfig.yml")
    shutil.copytree(_REPO / "sg-rules", tmp_path / "sg-rules")

    flagged = _scan(tmp_path, _NO_TIMEOUT, "skills/a.py")
    assert flagged.returncode == 1
    assert "subprocess-run-needs-timeout" in flagged.stdout
    assert "skills/a.py:2" in flagged.stdout

    assert _scan(tmp_path, _TIMEOUT, "scripts/b.py").returncode == 0
    assert _scan(tmp_path, _NO_TIMEOUT, "tests/c.py").returncode == 0
