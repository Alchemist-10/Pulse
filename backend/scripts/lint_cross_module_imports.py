"""Cross-module import lint (backend.md, issue #23 story 60).

A file under `app/modules/<X>/` may not import from `app.modules.<Y>` when
`Y != X`, except `app.modules.<Y>.{service,schemas,dependencies}` — modules
communicate through service interfaces, wire schemas, and the auth module's
FastAPI DI surface (`requires`/`public`/`current_user`, ADR-0004). What stays
forbidden is another module's `models` / `repository` — its tables.

Prints `file:line -> import` for each violation. Exit 1 if any, else exit 0
after an explicit `clean` line. Relative imports are resolved to absolute
before checking, so `from ..consent import repository` is caught too.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parents[1]
_MODULES_DIR = _BACKEND_DIR / "app" / "modules"
_ALLOWED_SUBMODULES = {"service", "schemas", "dependencies"}


def _own_module(path: Path) -> str:
    """`app/modules/auth/foo/bar.py` -> `auth`."""
    return path.relative_to(_MODULES_DIR).parts[0]


def _package_parts(path: Path) -> list[str]:
    """Dotted package of the file, e.g. `['app', 'modules', 'auth']`."""
    rel = path.relative_to(_BACKEND_DIR).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        parts.pop()
    else:
        parts.pop()  # drop the module filename; keep the package
    return parts


def _resolve(node: ast.ImportFrom, path: Path) -> str | None:
    if node.level == 0:
        return node.module
    base = _package_parts(path)
    # level 1 == current package, level 2 == parent, ...
    trimmed = base[: len(base) - (node.level - 1)] if node.level > 1 else base
    return ".".join(trimmed + ([node.module] if node.module else []))


def _violation(target: str, names: list[str], own: str) -> str | None:
    """`target` is a resolved dotted module path being imported."""
    parts = target.split(".")
    if parts[:2] != ["app", "modules"] or len(parts) < 3:
        return None
    other = parts[2]
    if other == own:
        return None
    if len(parts) >= 4:
        return None if parts[3] in _ALLOWED_SUBMODULES else target
    # Exactly `app.modules.<other>`: legal only if it imports service/schemas.
    bad = [n for n in names if n not in _ALLOWED_SUBMODULES]
    return f"{target} ({', '.join(bad)})" if bad else None


def main() -> int:
    violations: list[str] = []
    files = sorted(_MODULES_DIR.rglob("*.py"))
    for path in files:
        own = _own_module(path)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    hit = _violation(alias.name, [], own)
                    if hit:
                        rel = path.relative_to(_BACKEND_DIR)
                        violations.append(f"{rel}:{node.lineno} -> import {hit}")
            elif isinstance(node, ast.ImportFrom):
                resolved = _resolve(node, path)
                if resolved is None:
                    continue
                hit = _violation(resolved, [a.name for a in node.names], own)
                if hit:
                    rel = path.relative_to(_BACKEND_DIR)
                    violations.append(f"{rel}:{node.lineno} -> from {hit}")

    if violations:
        for v in violations:
            print(v)
        print(f"{len(violations)} cross-module import violation(s) in {len(files)} module files")
        return 1

    print(f"clean — {len(files)} module files scanned, 0 violations")
    return 0


if __name__ == "__main__":
    sys.exit(main())
