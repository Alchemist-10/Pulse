"""Route-coverage test (ADR-0004): every API route declares exactly one of
`requires(...)` or `public()`, or CI fails.

The markers are attributes on the dependency callable (`PERMISSION_ATTR` /
`PUBLIC_ATTR` in `app.modules.auth.dependencies`), so this test introspects
`app.routes` without executing any handler.
"""

import importlib.util
from collections.abc import Iterable, Iterator
from pathlib import Path

from fastapi import FastAPI
from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRoute

from app.main import app
from app.modules.auth.dependencies import PERMISSION_ATTR, PUBLIC_ATTR

# FastAPI's own auto-generated routes carry no domain markers by design.
_FASTAPI_OWN = {"/openapi.json", "/docs", "/redoc", "/docs/oauth2-redirect"}

# Explicit allowlist: the liveness probe is intentionally unauthenticated and
# predates the `public()` marker convention. Anything else must declare.
_ALLOWLIST = {("GET", "/api/v1/health")}


def _collect_api_routes(
    routes: Iterable[object], seen: set[int], acc: list[APIRoute]
) -> list[APIRoute]:
    """Flatten every APIRoute reachable from `routes`.

    FastAPI 0.141's `include_router` leaves the sub-routes nested inside an
    `_IncludedRouter` object rather than splicing them onto `app.routes`, so a
    flat `app.routes` scan would miss every module route. Descend through
    `.original_router` / `.router` / `.routes` to reach them.
    """
    for route in routes:
        if id(route) in seen:
            continue
        seen.add(id(route))
        if isinstance(route, APIRoute):
            acc.append(route)
            continue
        sub = getattr(route, "original_router", None) or getattr(route, "router", None)
        nested = getattr(sub, "routes", None) if sub is not None else getattr(route, "routes", None)
        if isinstance(nested, Iterable):
            _collect_api_routes(nested, seen, acc)
    return acc


def _walk(dependant: Dependant) -> Iterator[object]:
    """Yield every `.call` in the dependency tree, depth-first."""
    for sub in dependant.dependencies:
        if sub.call is not None:
            yield sub.call
        yield from _walk(sub)


def _declares_marker(route: APIRoute) -> bool:
    return any(
        hasattr(call, PERMISSION_ATTR) or hasattr(call, PUBLIC_ATTR)
        for call in _walk(route.dependant)
    )


def _undeclared(target: FastAPI) -> list[str]:
    offending: list[str] = []
    for route in _collect_api_routes(target.routes, set(), []):
        if route.path in _FASTAPI_OWN:
            continue
        methods = sorted(route.methods or {"GET"})
        if all((m, route.path) in _ALLOWLIST for m in methods):
            continue
        if not _declares_marker(route):
            offending.append(f"{','.join(methods)} {route.path}")
    return offending


def test_every_route_declares_an_authorization_marker() -> None:
    offending = _undeclared(app)
    assert not offending, (
        "Routes declaring neither requires(...) nor public() (ADR-0004):\n  "
        + "\n  ".join(offending)
    )


def test_coverage_check_bites_on_an_undeclared_route() -> None:
    """Positive case: a router with a deliberately undeclared route must be
    reported by the same check."""
    fixture = Path(__file__).parent / "_fixtures" / "bad_router.py"
    spec = importlib.util.spec_from_file_location("bad_router", fixture)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    throwaway = FastAPI()
    throwaway.include_router(module.router)

    offending = _undeclared(throwaway)
    assert offending == ["GET /api/v1/deliberately-undeclared"]
