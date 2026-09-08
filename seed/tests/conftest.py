"""Make the backend package importable when this suite runs from repo root.

The loader test is self-contained (its own Postgres container) but it does
import ``app.db.seed_loader``; that lives under ``backend/``. Run with the
backend's environment, e.g. from the repo root::

    uv run --project backend pytest seed/tests/
"""

import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[2] / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))
