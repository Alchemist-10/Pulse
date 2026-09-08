"""Actor: the minimum a clinical read needs to know about who is asking.

No function returning Medical Entries takes less than an Actor — if a
signature has no actor, the access rules have nowhere to apply
(clinical-safety.md).
"""

from dataclasses import dataclass
from uuid import UUID

from app.core.authz import Role


@dataclass(frozen=True)
class Actor:
    user_id: UUID
    role: Role
