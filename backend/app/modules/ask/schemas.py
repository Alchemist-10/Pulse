"""Ask-your-record wire contract. Rule-based, no LLM. Blocks are typed data; the
frontend renders interface text from `key`. Clinical content is verbatim, never
translated. Responses are never persisted.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field

from app.core.schema import PulseSchema
from app.modules.ask.intents import AskIntent
from app.modules.audit.schemas import AuditEventProjection
from app.modules.emergency.schemas import EmergencyCardView
from app.modules.records.schemas import LabTrendPoint

__all__ = [
    "AccessLogBlock",
    "AskBlock",
    "AskReceipt",
    "AskRequest",
    "AskResponse",
    "ChangesBlock",
    "EmergencyPreviewBlock",
    "EntryItem",
    "EntryListBlock",
    "LabTrendBlock",
    "LabValueBlock",
    "Locale",
    "MessageBlock",
    "SuggestionsBlock",
]

Locale = Literal["en", "hi", "ta", "ml"]


class AskRequest(PulseSchema):
    question: str = Field(min_length=1, max_length=300)
    locale: Locale = "en"
    window_days: Literal[7, 30, 90] | None = None


class MessageBlock(PulseSchema):
    """Interface text only. `key` names a catalog entry; `params` fill its
    placeholders. Never clinical values."""

    kind: Literal["message"] = "message"
    key: str
    params: dict[str, str | int | float] = {}


class LabValueBlock(PulseSchema):
    kind: Literal["lab_value"] = "lab_value"
    test_name: str
    value_numeric: Decimal | None = None
    value_text: str | None = None
    unit: str | None = None
    reference_low: Decimal | None = None
    reference_high: Decimal | None = None
    is_abnormal: bool
    observed_at: datetime


class LabTrendBlock(PulseSchema):
    kind: Literal["lab_trend"] = "lab_trend"
    test_name: str
    unit: str | None = None
    points: list[LabTrendPoint]


class EntryItem(PulseSchema):
    # None for rows derived from aggregates (medication summary, emergency card).
    entry_id: UUID | None = None
    display_name: str
    detail: str | None = None
    recorded_at: datetime


class EntryListBlock(PulseSchema):
    kind: Literal["entry_list"] = "entry_list"
    list_kind: Literal["medications", "allergies", "conditions"]
    items: list[EntryItem]


class ChangesBlock(PulseSchema):
    kind: Literal["changes"] = "changes"
    window_days: int
    since: datetime | None = None
    added: list[EntryItem]
    superseded: list[EntryItem]


class AccessLogBlock(PulseSchema):
    kind: Literal["access_log"] = "access_log"
    window_days: int
    total: int
    # True when more events exist than were fetched; the list is a prefix.
    truncated: bool = False
    items: list[AuditEventProjection]


class EmergencyPreviewBlock(PulseSchema):
    kind: Literal["emergency_preview"] = "emergency_preview"
    # None = emergency card not set up.
    card: EmergencyCardView | None = None


class SuggestionsBlock(PulseSchema):
    kind: Literal["suggestions"] = "suggestions"
    intents: list[AskIntent]


AskBlock = Annotated[
    MessageBlock
    | LabValueBlock
    | LabTrendBlock
    | EntryListBlock
    | ChangesBlock
    | AccessLogBlock
    | EmergencyPreviewBlock
    | SuggestionsBlock,
    Field(discriminator="kind"),
]


class AskReceipt(PulseSchema):
    """What the answer was read from. `entry_ids` are identifiers only, never
    names or values."""

    filter: Literal["accessible_entries", "audit_projection", "emergency_card", "none"]
    entry_ids: list[UUID] = []
    # Rows read when the source was an aggregate with no per-row ids.
    entry_count: int = 0
    audit_logged: bool = True


class AskResponse(PulseSchema):
    intent: AskIntent
    blocks: list[AskBlock]
    receipt: AskReceipt
