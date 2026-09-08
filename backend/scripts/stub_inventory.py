"""Stub inventory (backend.md, issue #23 story 36).

Importing `app.main` mounts every router, which runs the `@stub` decorator
and populates `app.core.stub.STUB_ROUTES`. This prints that list so a stub
surviving to the demo is visible in every CI run. Always exits 0 — it
reports, it does not gate.
"""

import sys

import app.main  # noqa: F401  (import side effect: registers @stub routes)
from app.core.stub import STUB_ROUTES


def main() -> int:
    print(f"STUB INVENTORY ({len(STUB_ROUTES)}):")
    for entry in STUB_ROUTES:
        print(f"  {entry}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
