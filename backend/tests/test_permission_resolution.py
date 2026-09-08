"""Unit seam: pure Role -> Permission resolution. No web server, no database."""

import pytest

from app.core.authz import (
    ROLE_PERMISSIONS,
    Permission,
    Role,
    resolve_permissions,
    role_has_permission,
)


@pytest.mark.parametrize("role", list(Role))
def test_resolution_is_total_over_role(role: Role) -> None:
    perms = resolve_permissions(role)
    assert isinstance(perms, frozenset)
    assert perms == ROLE_PERMISSIONS[role]


# Permissions that gate a read of a Patient's own record or its metadata.
# ADR-0007: no Administrator may hold any of these, in any phase.
_CLINICAL_READ_PERMISSIONS = frozenset(
    {
        Permission.PATIENT_PROFILE_READ_SELF,
        Permission.RECORDS_READ,
        Permission.RECORDS_WRITE,
        Permission.CONSENT_READ_SELF,
        Permission.CONSENT_MANAGE_SELF,
        Permission.AUDIT_READ_SELF,
    }
)


def test_administrator_holds_no_clinical_read_permission() -> None:
    perms = resolve_permissions(Role.ADMINISTRATOR)
    assert perms.isdisjoint(_CLINICAL_READ_PERMISSIONS)


@pytest.mark.parametrize("role", list(Role))
def test_every_role_can_change_own_credentials(role: Role) -> None:
    assert role_has_permission(role, Permission.USER_CREDENTIALS_CHANGE)


@pytest.mark.parametrize("role", list(Role))
def test_only_patient_reads_own_profile(role: Role) -> None:
    has = role_has_permission(role, Permission.PATIENT_PROFILE_READ_SELF)
    assert has is (role is Role.PATIENT)


def test_no_administrator_permission_grants_a_clinical_data_read() -> None:
    # Structural ADR-0007: whatever the model grows to, the Administrator's
    # set never intersects a clinical read. Clinical reads are enforced
    # per-request by `accessible_entries`; this is the coarse backstop.
    assert resolve_permissions(Role.ADMINISTRATOR).isdisjoint(
        _CLINICAL_READ_PERMISSIONS
    )


def test_only_patient_and_care_roles_read_records() -> None:
    for role in Role:
        reads = role_has_permission(role, Permission.RECORDS_READ)
        assert reads is (role in {Role.PATIENT, Role.CLINICIAN, Role.PROVIDER_STAFF})
