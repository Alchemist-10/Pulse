"""Shared helpers for the Wave 1 auth/identity suite.

`conftest.py` is the read-only Wave 0 spine. Its `db_session` fixture
truncates the identity tables on teardown, but the `pulse_app` role is
granted DML only (no `TRUNCATE`), so tests here use `wipe_identity`
(plain `DELETE`, which `pulse_app` may do) for isolation and open their
own short-lived session via `identity_session` when they need raw SQL.

Import as top-level `helpers` (never `tests.helpers`) so mypy resolves
the module under a single name.
"""

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from httpx import Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Signature of conftest.py's `register_and_login` fixture.
RegisterAndLogin = Callable[..., Awaitable[Response]]

# Child-first so foreign keys never block the delete.
_IDENTITY_TABLES = ("provider_staff", "patient", '"user"', "provider")


async def wipe_identity(app_database_url: str) -> None:
    engine = create_async_engine(app_database_url)
    try:
        async with engine.begin() as conn:
            for table in _IDENTITY_TABLES:
                await conn.execute(text(f"DELETE FROM {table}"))
    finally:
        await engine.dispose()


@asynccontextmanager
async def identity_session(app_database_url: str) -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(app_database_url)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with maker() as session:
            yield session
    finally:
        await engine.dispose()
