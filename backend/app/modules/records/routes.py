"""Records HTTP surface.

P2.0 (#25): `@stub` reads so the Phase 2 timeline can be built before the
query lands. Real implementations arrive in P2.3 (timeline) and P2.5
(service + routes); the schemas below are not throwaway, only the fixtures.
"""

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authz import Permission
from app.core.pagination import Page
from app.core.stub import stub
from app.db.session import get_session
from app.modules.auth.dependencies import AuthContext, current_user, requires
from app.modules.records.models import EntryType
from app.modules.records.schemas import EntryDetail, EntrySummary

router = APIRouter(prefix="/api/v1", tags=["records"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[AuthContext, Depends(current_user)]

_STUB_PATIENT_ID = UUID("00000000-0000-0000-0000-0000000000aa")
_STUB_ENTRY_ID = UUID("00000000-0000-0000-0000-00000000e001")
_STUB_WHEN = datetime(2025, 3, 14, 9, 30, tzinfo=UTC)

_STUB_TIMELINE = Page[EntrySummary](
    items=[
        EntrySummary(
            id=_STUB_ENTRY_ID,
            patient_id=_STUB_PATIENT_ID,
            entry_type=EntryType.LAB_REPORT,
            occurred_at=_STUB_WHEN,
            recorded_at=_STUB_WHEN,
            is_critical=True,
            summary="Hemoglobin A1c",
        ),
        EntrySummary(
            id=UUID("00000000-0000-0000-0000-00000000e002"),
            patient_id=_STUB_PATIENT_ID,
            entry_type=EntryType.DIAGNOSIS,
            occurred_at=datetime(2025, 1, 2, 11, 0, tzinfo=UTC),
            recorded_at=datetime(2025, 1, 2, 11, 0, tzinfo=UTC),
            summary="Type 2 diabetes mellitus",
        ),
    ],
    next_cursor=None,
)

_STUB_ENTRY_DETAIL = EntryDetail(
    id=_STUB_ENTRY_ID,
    patient_id=_STUB_PATIENT_ID,
    entry_type=EntryType.LAB_REPORT,
    occurred_at=_STUB_WHEN,
    recorded_at=_STUB_WHEN,
    is_critical=True,
    summary="Hemoglobin A1c",
    metadata={"import_batch": "stub"},
    code_system="http://loinc.org",
    code="4548-4",
    display_name="Hemoglobin A1c",
    value_numeric=None,
    value_text="7.8",
    unit="%",
    reference_low=None,
    reference_high=None,
)


@router.get(
    "/patients/{patient_id}/entries",
    dependencies=[requires(Permission.RECORDS_READ)],
)
@stub(_STUB_TIMELINE)
async def list_patient_entries(
    patient_id: UUID,
    response: Response,
    ctx: CurrentUser,
    session: SessionDep,
    entry_type: EntryType | None = None,
    cursor: str | None = None,
    limit: int = 50,
) -> Page[EntrySummary]:
    return _STUB_TIMELINE


@router.get(
    "/entries/{entry_id}",
    dependencies=[requires(Permission.RECORDS_READ)],
)
@stub(_STUB_ENTRY_DETAIL)
async def get_entry_detail(
    entry_id: UUID,
    response: Response,
    ctx: CurrentUser,
    session: SessionDep,
) -> EntryDetail:
    return _STUB_ENTRY_DETAIL
