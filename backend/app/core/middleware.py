"""Request-id middleware: generates/propagates X-Request-Id, stashed in a contextvar."""

import re
import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# A client-supplied id is kept only if it fits `audit_event.request_id`
# (String(64)) and is plain token characters; anything else is replaced.
_VALID_REQUEST_ID = re.compile(r"[A-Za-z0-9._:-]{1,64}")

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    return _request_id.get()


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        supplied = request.headers.get("X-Request-Id", "")
        request_id = supplied if _VALID_REQUEST_ID.fullmatch(supplied) else str(uuid.uuid4())
        token = _request_id.set(request_id)
        try:
            response = await call_next(request)
        finally:
            _request_id.reset(token)
        response.headers["X-Request-Id"] = request_id
        return response
