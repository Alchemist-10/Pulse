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


def test_administrator_holds_no_clinical_read_permission() -> None:
    perms = resolve_permissions(Role.ADMINISTRATOR)
    assert Permission.PATIENT_PROFILE_READ_SELF not in perms
    assert perms == frozenset({Permission.USER_CREDENTIALS_CHANGE})


@pytest.mark.parametrize("role", list(Role))
def test_every_role_can_change_own_credentials(role: Role) -> None:
    assert role_has_permission(role, Permission.USER_CREDENTIALS_CHANGE)


@pytest.mark.parametrize("role", list(Role))
def test_only_patient_reads_own_profile(role: Role) -> None:
    has = role_has_permission(role, Permission.PATIENT_PROFILE_READ_SELF)
    assert has is (role is Role.PATIENT)


def test_no_permission_in_the_enum_grants_a_clinical_data_read() -> None:
    # Structural ADR-0007: the whole model grants only these two.
    granted: frozenset[Permission] = frozenset().union(*ROLE_PERMISSIONS.values())
    assert granted == {
        Permission.PATIENT_PROFILE_READ_SELF,
        Permission.USER_CREDENTIALS_CHANGE,
    }
