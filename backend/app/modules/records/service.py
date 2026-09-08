"""Records business rules (P2.5).

No SQL, no FastAPI imports (backend.md). Every entry-returning function
takes an `Actor`; there are no "internal" helpers that skip it — the pure
ORM->wire mappers live in `projections.py` precisely so they are not
somewhere a filter could have been dropped.

Phase 2 access — a Patient reads their own history, and a Provider Staff
user reads/writes coarsely (any record; narrowed to the authoring
Provider in Phase 3). A Clinician, an Administrator or another Patient
gets **404, never 403**: a 403 would confirm the record exists
(clinical-safety.md). Consent, break-glass and audit emission all land in
Phase 3; the read paths carry `# TODO(P3): emit ENTRY_VIEWED`.
"""

from __future__ import annotations

import hashlib
from pathlib import PurePosixPath
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.storage import StorageProvider
from app.core.actor import Actor
from app.core.authz import Role
from app.core.errors import ErrorCode
from app.core.exceptions import PulseError
from app.core.pagination import Page
from app.modules.records import projections, repository
from app.modules.records.models import EntryType
from app.modules.records.schemas import (
    Document,
    DocumentCreate,
    EntryCreate,
    EntryDetail,
    EntrySummary,
)
from app.modules.users import service as users_service

# 25 MiB — larger than any scanned report; the Caddy body limit (P2.11)
# is the outer guard, this is the app-level one.
_MAX_UPLOAD_BYTES = 25 * 1024 * 1024

# Server-side magic-byte sniff. The declared Content-Type and the file
# extension are both attacker-controlled (backend.md), so the allowlist is
# checked against the actual bytes.
_MAGIC: tuple[tuple[bytes, str], ...] = (
    (b"%PDF", "application/pdf"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
)


def _sniff_mime(data: bytes) -> str | None:
    for magic, mime in _MAGIC:
        if data.startswith(magic):
            return mime
    return None

_REQUIRED_FIELDS: dict[EntryType, tuple[str, ...]] = {
    EntryType.DIAGNOSIS: ("code_system", "code", "display_name"),
    EntryType.PROCEDURE: ("code_system", "code", "display_name"),
    EntryType.LAB_REPORT: ("code_system", "code", "display_name"),
    EntryType.PRESCRIPTION: ("medication_name",),
    EntryType.CLINICAL_NOTE: ("text",),
}


def _not_found() -> PulseError:
    return PulseError(ErrorCode.NOT_FOUND, "No such record.", http_status=404)


async def _authorize_entry_access(
    session: AsyncSession, actor: Actor, patient_id: UUID
) -> None:
    """Phase 2 access — rule 1 plus a coarse Provider Staff allowance.

    The Patient reads their own history; a Provider Staff user reads any
    record (narrowed to the authoring Provider, and to live Consent for
    Clinicians, in Phase 3). Everyone else — Clinician, Administrator,
    another Patient — gets 404, never 403 (clinical-safety.md).
    """
    if actor.role is Role.PROVIDER_STAFF:
        return
    patient = await users_service.get_patient(session, patient_id)
    if patient is None or patient.user_id != actor.user_id:
        raise _not_found()


def _validate_payload(payload: EntryCreate) -> None:
    missing = [
        field
        for field in _REQUIRED_FIELDS[payload.entry_type]
        if not getattr(payload, field, None)
    ]
    if missing:
        raise PulseError(
            ErrorCode.ENTRY_TYPE_MISMATCH,
            f"{payload.entry_type.value} requires {', '.join(missing)}.",
            http_status=422,
        )


async def list_timeline(
    session: AsyncSession,
    actor: Actor,
    patient_id: UUID,
    *,
    entry_type: EntryType | None = None,
    cursor: str | None = None,
    limit: int = 50,
) -> Page[EntrySummary]:
    await _authorize_entry_access(session, actor, patient_id)
    rows, next_cursor = await repository.list_timeline(
        session, actor, patient_id, entry_type=entry_type, cursor=cursor, limit=limit
    )
    # TODO(P3): emit ENTRY_VIEWED
    return Page[EntrySummary](
        items=[projections.to_summary(r) for r in rows], next_cursor=next_cursor
    )


async def get_entry(session: AsyncSession, actor: Actor, entry_id: UUID) -> EntryDetail:
    entry = await repository.get_entry(session, actor, entry_id)
    if entry is None:
        raise _not_found()
    await _authorize_entry_access(session, actor, entry.patient_id)
    supersedes_id = await repository.get_superseding_original_id(session, entry_id)
    documents = await repository.list_documents(session, entry_id)
    # TODO(P3): emit ENTRY_VIEWED
    return projections.to_detail(
        entry, supersedes_id=supersedes_id, documents=documents
    )


async def insert_entry(
    session: AsyncSession, actor: Actor, patient_id: UUID, payload: EntryCreate
) -> EntryDetail:
    """File a new Entry for a Patient. The route restricts this to Provider
    Staff (RECORDS_WRITE)."""
    patient = await users_service.get_patient(session, patient_id)
    if patient is None:
        raise _not_found()
    _validate_payload(payload)
    if payload.source_provider_id is None:
        provider_id = await users_service.get_provider_for_staff(
            session, actor.user_id
        )
        payload = payload.model_copy(update={"source_provider_id": provider_id})
    entry = await repository.insert_entry(session, actor, patient_id, payload)
    await session.commit()
    fresh = await repository.get_entry(session, actor, entry.id)
    if fresh is None:  # pragma: no cover - just inserted
        raise _not_found()
    return projections.to_detail(fresh, supersedes_id=None, documents=[])


async def supersede_entry(
    session: AsyncSession,
    actor: Actor,
    patient_id: UUID,
    original_id: UUID,
    payload: EntryCreate,
) -> EntryDetail:
    """Correction path (P2.7): insert a new Entry, stamp `superseded_by_id`
    on the original. Never an in-place update of clinical data. The route
    restricts this to Provider Staff (RECORDS_WRITE)."""
    if await users_service.get_patient(session, patient_id) is None:
        raise _not_found()
    original = await repository.get_entry(session, actor, original_id)
    if original is None or original.patient_id != patient_id:
        raise _not_found()
    _validate_payload(payload)
    if payload.source_provider_id is None:
        provider_id = await users_service.get_provider_for_staff(
            session, actor.user_id
        )
        payload = payload.model_copy(update={"source_provider_id": provider_id})
    replacement = await repository.supersede_entry(
        session, actor, patient_id, original_id, payload
    )
    if replacement is None:
        raise PulseError(
            ErrorCode.ENTRY_ALREADY_SUPERSEDED,
            "This entry has already been corrected.",
            http_status=409,
        )
    await session.commit()
    fresh = await repository.get_entry(session, actor, replacement.id)
    if fresh is None:  # pragma: no cover - just inserted
        raise _not_found()
    return projections.to_detail(fresh, supersedes_id=original_id, documents=[])


async def add_document(
    session: AsyncSession,
    actor: Actor,
    patient_id: UUID,
    entry_id: UUID,
    *,
    storage: StorageProvider,
    data: bytes,
    filename: str,
) -> Document:
    """Attach an uploaded file to an Entry. Size cap first (413), then a
    server-side magic-byte sniff against the allowlist (422), then store
    the bytes and record the checksum. Provider Staff only (route guard)."""
    if len(data) > _MAX_UPLOAD_BYTES:
        raise PulseError(
            ErrorCode.PAYLOAD_TOO_LARGE,
            "The file exceeds the upload size limit.",
            http_status=413,
        )
    sniffed = _sniff_mime(data)
    if sniffed is None:
        raise PulseError(
            ErrorCode.UNSUPPORTED_MEDIA_TYPE,
            "Only PDF, PNG and JPEG documents are accepted.",
            http_status=422,
        )
    entry = await repository.get_entry(session, actor, entry_id)
    if entry is None or entry.patient_id != patient_id:
        raise _not_found()
    await _authorize_entry_access(session, actor, entry.patient_id)
    safe_name = PurePosixPath(filename).name or "upload"
    key = f"{entry_id}/{uuid4()}-{safe_name}"
    storage_path = await storage.put(key, data, sniffed)
    meta = DocumentCreate(
        filename=safe_name,
        mime_type=sniffed,
        size_bytes=len(data),
        storage_path=storage_path,
        checksum_sha256=hashlib.sha256(data).hexdigest(),
    )
    doc = await repository.add_document(session, actor, entry_id, meta)
    await session.commit()
    return projections.to_document(doc)


async def get_document(
    session: AsyncSession,
    actor: Actor,
    document_id: UUID,
    *,
    storage: StorageProvider,
) -> tuple[Document, bytes]:
    """Document metadata + bytes, behind the same access rule as its
    Entry — a denied caller gets 404, never a hint that it exists."""
    doc = await repository.get_document(session, actor, document_id)
    if doc is None:
        raise _not_found()
    entry = await repository.get_entry(session, actor, doc.entry_id)
    if entry is None:
        raise _not_found()
    await _authorize_entry_access(session, actor, entry.patient_id)
    data = await storage.get(doc.storage_path)
    return projections.to_document(doc), data
