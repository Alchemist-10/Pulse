"""P2.5 — every entry-returning function in the records module takes an actor.

Two checks, two seams:

* ``test_actor_first_lint_armed`` runs ``scripts/lint_actor_first.py`` — the
  AST lint that bites in CI. Green today (records service/repository are empty
  bar ``accessible_entries``, which already takes an actor). Prior art:
  ``tests/test_entry_query_lint.py``.
* ``test_timeline_service_surface_is_actor_first`` imports the records service
  and asserts it exposes ``list_timeline`` / ``get_entry`` with an ``actor``
  parameter. Red today — ``service.py`` is empty.
"""

from __future__ import annotations

import importlib
import inspect
import subprocess
import sys
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "lint_actor_first.py"

_ENTRY_RETURNING = ("list_timeline", "get_entry", "insert_entry", "supersede_entry")


def test_actor_first_lint_armed() -> None:
    result = subprocess.run([sys.executable, str(_SCRIPT)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "actor-first lint armed for Phase 2" in result.stdout


def test_actor_first_lint_bites_on_a_missing_actor(tmp_path: Path) -> None:
    """Positive control: a records-shaped function with no actor must be caught."""
    bad = tmp_path / "lint_actor_first_probe.py"
    bad.write_text(
        "import ast, sys\n"
        f"sys.path.insert(0, {str(_SCRIPT.parent)!r})\n"
        "import lint_actor_first as m\n"
        "src = 'async def list_timeline(session, patient_id):\\n    return []\\n'\n"
        "tree = ast.parse(src)\n"
        "fn = tree.body[0]\n"
        "assert m._returns_entries(fn) is True\n"
        "assert m._has_actor_param(fn) is False\n"
    )
    result = subprocess.run([sys.executable, str(bad)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_timeline_service_surface_is_actor_first() -> None:
    service = importlib.import_module("app.modules.records.service")
    missing = [name for name in _ENTRY_RETURNING if not hasattr(service, name)]
    assert not missing, f"records.service is missing {missing}"
    for name in _ENTRY_RETURNING:
        sig = inspect.signature(getattr(service, name))
        assert "actor" in sig.parameters, f"records.service.{name} takes no `actor`"
