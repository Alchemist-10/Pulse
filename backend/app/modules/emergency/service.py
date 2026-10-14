"""Emergency card business rules.

No SQL, no FastAPI imports. The card is the only thing break-glass and the
QR reveal — never Medical Entries (ADR-0017). Every view by someone other
than the owner emits one `EMERGENCY_CARD_VIEWED` audit event and a mandatory
notification, neither carrying card contents (clinical-safety.md).
"""

from __future__ import annotations

import secrets
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.actor import Actor
from app.core.errors import ErrorCode
from app.core.exceptions import PulseError
from app.core.transactions import transactional
from app.modules.audit import service as audit_service
from app.modules.audit.service import AuditAction, AuditOutcome
from app.modules.consent import service as consent_service
from app.modules.emergency import repository
from app.modules.emergency.models import EmergencyCard as CardRow
from app.modules.emergency.schemas import (
    EmergencyCard,
    EmergencyCardUpdate,
    EmergencyCardView,
)
from app.modules.notifications import service as notifications_service
from app.modules.notifications.schemas import NotificationType
from app.modules.users import service as users_service


def _not_found() -> PulseError:
    return PulseError(ErrorCode.NOT_FOUND, "No such emergency card.", http_status=404)


def _owner_wire(row: CardRow | None) -> EmergencyCard:
    if row is None:
        return EmergencyCard()
    return EmergencyCard(
        blood_type=row.blood_type,
        allergies=row.allergies,
        conditions=row.conditions,
        medications=row.medications,
        next_of_kin_name=row.next_of_kin_name,
        next_of_kin_phone=row.next_of_kin_phone,
        next_of_kin_relation=row.next_of_kin_relation,
        notes=row.notes,
        show_blood_type=row.show_blood_type,
        show_allergies=row.show_allergies,
        show_conditions=row.show_conditions,
        show_medications=row.show_medications,
        show_next_of_kin=row.show_next_of_kin,
        show_notes=row.show_notes,
        qr_token=row.qr_token,
        updated_at=row.updated_at,
    )


def _view(row: CardRow | None, patient_id: UUID, patient_name: str) -> EmergencyCardView:
    view = EmergencyCardView(patient_id=patient_id, patient_name=patient_name)
    if row is None:
        return view
    if row.show_blood_type:
        view.blood_type = row.blood_type
    if row.show_allergies:
        view.allergies = row.allergies
    if row.show_conditions:
        view.conditions = row.conditions
    if row.show_medications:
        view.medications = row.medications
    if row.show_next_of_kin:
        view.next_of_kin_name = row.next_of_kin_name
        view.next_of_kin_phone = row.next_of_kin_phone
        view.next_of_kin_relation = row.next_of_kin_relation
    if row.show_notes:
        view.notes = row.notes
    return view


async def _own_patient_id(session: AsyncSession, actor: Actor) -> UUID:
    own = await users_service.get_own_patient_profile(session, actor)
    if own is None:
        raise _not_found()
    return own.id


async def get_own(session: AsyncSession, actor: Actor) -> EmergencyCard:
    patient_id = await _own_patient_id(session, actor)
    return _owner_wire(await repository.get_by_patient(session, patient_id))


@transactional
async def update_own(
    session: AsyncSession, actor: Actor, payload: EmergencyCardUpdate
) -> EmergencyCard:
    patient_id = await _own_patient_id(session, actor)
    row = await repository.upsert(session, patient_id, payload.model_dump(by_alias=False))
    return _owner_wire(row)


@transactional
async def rotate_qr(session: AsyncSession, actor: Actor) -> EmergencyCard:
    patient_id = await _own_patient_id(session, actor)
    row = await repository.upsert(session, patient_id, {"qr_token": secrets.token_urlsafe(24)})
    return _owner_wire(row)


@transactional
async def disable_qr(session: AsyncSession, actor: Actor) -> EmergencyCard:
    patient_id = await _own_patient_id(session, actor)
    row = await repository.upsert(session, patient_id, {"qr_token": None})
    return _owner_wire(row)


async def _record_view(session: AsyncSession, actor: Actor, patient_id: UUID) -> None:
    patient = await users_service.get_patient(session, patient_id)
    if patient is None:
        raise _not_found()
    if patient.user_id == actor.user_id:
        return
    await audit_service.emit(
        session,
        actor=actor,
        action=AuditAction.EMERGENCY_CARD_VIEWED,
        resource_type="emergency_card",
        resource_id=None,
        patient_id=patient_id,
        outcome=AuditOutcome.SUCCESS,
    )
    if patient.user_id is not None:
        await notifications_service.notify(
            session, patient.user_id, NotificationType.EMERGENCY_CARD_VIEWED, {}
        )


@transactional
async def view_by_token(session: AsyncSession, actor: Actor, token: str) -> EmergencyCardView:
    """Any signed-in non-admin actor who holds the token. Unknown or rotated
    token -> 404."""
    row = await repository.get_by_token(session, token)
    if row is None:
        raise _not_found()
    patient = await users_service.get_patient(session, row.patient_id)
    if patient is None:
        raise _not_found()
    await _record_view(session, actor, row.patient_id)
    return _view(row, patient.id, patient.full_name)


@transactional
async def view_for_patient(
    session: AsyncSession, actor: Actor, patient_id: UUID
) -> EmergencyCardView:
    """Clinician with an active break-glass grant or a live Consent."""
    patient = await users_service.get_patient(session, patient_id)
    if patient is None:
        raise _not_found()
    allowed = patient.user_id == actor.user_id or await consent_service.active_break_glass_for(
        session, patient_id, actor.user_id
    )
    if not allowed:
        allowed = bool(
            await consent_service.live_permissions_for(session, patient_id, actor.user_id)
        )
    if not allowed:
        raise _not_found()
    await _record_view(session, actor, patient_id)
    return _view(
        await repository.get_by_patient(session, patient_id), patient.id, patient.full_name
    )
