"""Async Redis client.

`REDIS_URL` defaults to the value compose.yaml sets for the backend
service, so this is unconfigured inside the compose network and only
needs overriding for local/CI runs. Redis holds sessions, verification
challenges, step-up markers and rate-limit counters — all TTL'd, none a
source of truth (ADR-0005).
"""

import os

from redis.asyncio import Redis

DEFAULT_REDIS_URL = "redis://redis:6379/0"

_client: Redis | None = None


def get_redis() -> Redis:
    """Process-wide client. `decode_responses` so callers get str, not bytes.
    Reads REDIS_URL on first use; call `reset_redis()` to rebind."""
    global _client
    if _client is None:
        url = os.environ.get("REDIS_URL", DEFAULT_REDIS_URL)
        _client = Redis.from_url(url, decode_responses=True)
    return _client


async def close_redis() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
