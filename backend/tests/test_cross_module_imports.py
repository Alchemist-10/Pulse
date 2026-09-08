"""The cross-module import lint must pass on the real tree."""

import subprocess
import sys
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "lint_cross_module_imports.py"


def test_no_cross_module_imports() -> None:
    result = subprocess.run(
        [sys.executable, str(_SCRIPT)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "clean —" in result.stdout
