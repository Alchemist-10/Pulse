"""Roles, Permissions, and the pure Role -> Permission resolution.

`ROLE_PERMISSIONS` is the whole authorization model for Phase 1: a static
table, resolved without a database or a request. No entry grants a read of
clinical data, so no Administrator can hold one (ADR-0007).
"""

from enum import StrEnum


class Role(StrEnum):
    PATIENT = "PATIENT"
    CLINICIAN = "CLINICIAN"
    PROVIDER_STAFF = "PROVIDER_STAFF"
    ADMINISTRATOR = "ADMINISTRATOR"


class Permission(StrEnum):
    # A signed-in Patient reading their own Patient profile.
    PATIENT_PROFILE_READ_SELF = "PATIENT_PROFILE_READ_SELF"
    # Changing one's own credentials (password / email). Step-up guarded.
    USER_CREDENTIALS_CHANGE = "USER_CREDENTIALS_CHANGE"


ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.PATIENT: frozenset(
        {
            Permission.PATIENT_PROFILE_READ_SELF,
            Permission.USER_CREDENTIALS_CHANGE,
        }
    ),
    Role.CLINICIAN: frozenset({Permission.USER_CREDENTIALS_CHANGE}),
    Role.PROVIDER_STAFF: frozenset({Permission.USER_CREDENTIALS_CHANGE}),
    Role.ADMINISTRATOR: frozenset({Permission.USER_CREDENTIALS_CHANGE}),
}


def resolve_permissions(role: Role) -> frozenset[Permission]:
    """Every Permission a Role holds. Total over Role; never raises."""
    return ROLE_PERMISSIONS.get(role, frozenset())


def role_has_permission(role: Role, permission: Permission) -> bool:
    return permission in resolve_permissions(role)
