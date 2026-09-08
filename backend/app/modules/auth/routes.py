"""Auth HTTP surface. HTTP only — parse, validate, delegate to service.

Endpoints (Wave 1, Agent A):
  POST /api/v1/auth/register         public
  POST /api/v1/auth/verify/resend    public
  POST /api/v1/auth/verify           public
  POST /api/v1/auth/login            public
  POST /api/v1/auth/logout           requires(...) — any authenticated user
  POST /api/v1/auth/logout-all       requires(...)
  POST /api/v1/auth/step-up          requires(...)
  GET  /api/v1/auth/me               requires(...)

Every route declares `public()` or `requires(...)` in its `dependencies=`.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
