"""Patients HTTP surface.

Endpoints (Wave 1, Agent A):
  GET /api/v1/patients/me       requires(PATIENT_PROFILE_READ_SELF) — real, seeded row
  GET /api/v1/patients/{id}     requires(PATIENT_PROFILE_READ_SELF) — @stub, X-Pulse-Stub: true
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/patients", tags=["patients"])
