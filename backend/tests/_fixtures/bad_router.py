"""Fixture: a router with one route that declares no authorization marker.

`test_route_coverage.py`'s positive case mounts this on a throwaway
`FastAPI()` and asserts the coverage check reports the undeclared route.
Never mounted on the real app.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/api/v1/deliberately-undeclared")
async def undeclared() -> dict[str, str]:
    return {"status": "undeclared"}
