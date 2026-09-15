"""Actor-first lint (clinical-safety.md, delivery-plan P2.5).

"No function returning Medical Entries takes less than an actor. If a
signature has no actor, the access rules have nowhere to apply."

This scans ``app/modules/records/{service,repository}.py`` for functions that
look like they return Medical Entries — by return annotation or by name — and
flags any that do not take a parameter named ``actor``.

``accessible_entries`` already takes an actor, and ``service.py`` /
``repository.py`` are otherwise empty today, so this is armed and finds
nothing. It exits 1 the moment a records function without an actor appears.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parents[1]
_TARGETS = (
    _BACKEND_DIR / "app" / "modules" / "records" / "service.py",
    _BACKEND_DIR / "app" / "modules" / "records" / "repository.py",
    # P4.3 (#54): admin reads identity + entry counts, never entry content,
    # but a count is still derived from Medical Entry rows (ADR-0007) — the
    # errors.md 2026-09-12 entry is exactly why this list grows here rather
    # than staying records-only.
    _BACKEND_DIR / "app" / "modules" / "admin" / "service.py",
    _BACKEND_DIR / "app" / "modules" / "admin" / "repository.py",
)

# Substrings that mark a function as entry-returning by name.
_ENTRY_NAME_HINTS = ("entry", "entries", "timeline", "record", "supersede", "correction")
# Return-annotation substrings that mark a function as entry-returning.
_ENTRY_RETURN_HINTS = ("MedicalEntry", "Entry", "EntryDetail", "EntrySummary", "Timeline")


def _returns_entries(node: ast.AST) -> bool:
    if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
        return False
    name = node.name.lower()
    if any(h in name for h in _ENTRY_NAME_HINTS):
        return True
    if node.returns is not None:
        src = ast.unparse(node.returns)
        return any(h in src for h in _ENTRY_RETURN_HINTS)
    return False


def _has_actor_param(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    args = node.args
    every = [*args.posonlyargs, *args.args, *args.kwonlyargs]
    return any(a.arg == "actor" for a in every)


def main() -> int:
    offenders: list[str] = []
    for path in _TARGETS:
        if not path.exists() or not path.read_text(encoding="utf-8").strip():
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and _returns_entries(node):
                if not _has_actor_param(node):
                    rel = path.relative_to(_BACKEND_DIR)
                    offenders.append(f"{rel}:{node.lineno} -> {node.name}() takes no `actor`")

    if offenders:
        for line in offenders:
            print(line)
        print(
            f"{len(offenders)} entry-returning function(s) without an `actor` "
            "parameter (clinical-safety.md)"
        )
        return 1

    print("0 offenders — actor-first lint armed for Phase 2")
    return 0


if __name__ == "__main__":
    sys.exit(main())
