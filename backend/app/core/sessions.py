"""Server-side session records in Redis (ADR-0003).

A session has two clocks: a sliding 60-minute idle window (the Redis key
TTL, refreshed on every authenticated request) and a hard 12-hour cap
(`absolute_expires_at`, stored in the record and never extended). The
raw token lives only in the cookie; Redis is keyed by its SHA-256.

`user_sessions:{user_id}` is a set of token hashes, so "log out
everywhere" is one fan-out.
"""

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from redis.asyncio import Redis

from app.core.authz import Role
from app.core.security import new_token, token_hash

SESSION_IDLE_TTL = timedelta(minutes=60)
SESSION_ABSOLUTE_TTL = timedelta(hours=12)
STEP_UP_TTL = timedelta(minutes=5)

_SESSION_KEY = "session:{}"
_USER_SESSIONS_KEY = "user_sessions:{}"
_STEP_UP_KEY = "stepup:{}"


@dataclass(frozen=True)
class SessionRecord:
    user_id: UUID
    role: Role
    created_at: datetime
    absolute_expires_at: datetime


def _now() -> datetime:
    return datetime.now(UTC)


def _remaining_idle_ttl(absolute_expires_at: datetime) -> int:
    """Seconds to keep the key alive: the idle window, clamped to the cap."""
    until_cap = int((absolute_expires_at - _now()).total_seconds())
    return max(0, min(int(SESSION_IDLE_TTL.total_seconds()), until_cap))


async def create_session(redis: Redis, user_id: UUID, role: Role) -> str:
    """Mint a session, store it, and return the raw token for the cookie."""
    token = new_token()
    key_hash = token_hash(token)
    created = _now()
    absolute = created + SESSION_ABSOLUTE_TTL
    record = {
        "userId": str(user_id),
        "role": role.value,
        "createdAt": created.isoformat(),
        "absoluteExpiresAt": absolute.isoformat(),
    }
    ttl = _remaining_idle_ttl(absolute)
    async with redis.pipeline(transaction=True) as pipe:
        pipe.set(_SESSION_KEY.format(key_hash), json.dumps(record), ex=ttl)
        pipe.sadd(_USER_SESSIONS_KEY.format(user_id), key_hash)
        pipe.expire(
            _USER_SESSIONS_KEY.format(user_id),
            int(SESSION_ABSOLUTE_TTL.total_seconds()),
        )
        await pipe.execute()
    return token


async def read_session(redis: Redis, token: str) -> SessionRecord | None:
    """Resolve a token to a live session, refreshing the idle window.

    Returns None if the token is unknown, or if the absolute cap has
    passed (the record is then cleaned up).
    """
    key_hash = token_hash(token)
    key = _SESSION_KEY.format(key_hash)
    raw = await redis.get(key)
    if raw is None:
        return None
    data = json.loads(raw)
    absolute = datetime.fromisoformat(data["absoluteExpiresAt"])
    user_id = UUID(data["userId"])
    if _now() >= absolute:
        await destroy_session(redis, token)
        return None
    await redis.expire(key, _remaining_idle_ttl(absolute))
    return SessionRecord(
        user_id=user_id,
        role=Role(data["role"]),
        created_at=datetime.fromisoformat(data["createdAt"]),
        absolute_expires_at=absolute,
    )


async def destroy_session(redis: Redis, token: str) -> None:
    key_hash = token_hash(token)
    raw = await redis.get(_SESSION_KEY.format(key_hash))
    async with redis.pipeline(transaction=True) as pipe:
        pipe.delete(_SESSION_KEY.format(key_hash))
        pipe.delete(_STEP_UP_KEY.format(key_hash))
        if raw is not None:
            user_id = json.loads(raw)["userId"]
            pipe.srem(_USER_SESSIONS_KEY.format(user_id), key_hash)
        await pipe.execute()


async def destroy_all_sessions(redis: Redis, user_id: UUID) -> None:
    set_key = _USER_SESSIONS_KEY.format(user_id)
    hashes = await redis.smembers(set_key)
    async with redis.pipeline(transaction=True) as pipe:
        for key_hash in hashes:
            pipe.delete(_SESSION_KEY.format(key_hash))
            pipe.delete(_STEP_UP_KEY.format(key_hash))
        pipe.delete(set_key)
        await pipe.execute()


async def grant_step_up(redis: Redis, token: str) -> None:
    await redis.set(
        _STEP_UP_KEY.format(token_hash(token)),
        "1",
        ex=int(STEP_UP_TTL.total_seconds()),
    )


async def has_step_up(redis: Redis, token: str) -> bool:
    return bool(await redis.exists(_STEP_UP_KEY.format(token_hash(token))))
