from collections.abc import Sequence
from pathlib import Path

from django.apps import AppConfig, apps
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.core.checks import Warning

import pytest

from maykin_common.checks import (
    check_missing_init_files,
    check_privilege_escalation_prevention_enabled,
)


def test_check_missing_init_files(settings):
    settings.DJANGO_PROJECT_DIR = Path(__file__).resolve().parent

    errors = check_missing_init_files(None)

    assert errors == [
        Warning(
            f"Directory {Path(__file__).resolve().parent}/missing_init does not "
            "contain an `__init__.py` file missing_init.",
            hint="Consider adding this module to make sure tests are picked up",
            id="maykin.W001",
        )
    ]


@pytest.fixture
def unregister_user_model():
    _original = type(admin.site.get_model_admin(User))
    admin.site.unregister(User)
    yield
    # pyright complains about invariance here:
    # Type parameter "_ModelT@ModelAdmin" is invariant, but "User" is not the same
    # as "Model"
    admin.site.register(User, _original)  # pyright: ignore[reportArgumentType]


@pytest.fixture
def revert_useradmin_patch(unregister_user_model):
    """
    Restore the default, unpatched user admin.
    """
    admin.site.register(User, UserAdmin)
    yield
    admin.site.unregister(User)


@pytest.mark.parametrize(
    "app_configs",
    [
        None,
        [
            apps.get_app_config("maykin_common"),
            apps.get_app_config("admin"),
            apps.get_app_config("testapp"),
        ],
    ],
)
def test_privilege_escalation_check_skipped_if_admin_not_installed(
    revert_useradmin_patch,
    app_configs: Sequence[AppConfig] | None,
    settings,
):
    UPDATED_APPS = [*settings.INSTALLED_APPS]
    UPDATED_APPS.remove("django.contrib.admin")
    settings.INSTALLED_APPS = UPDATED_APPS
    assert not apps.is_installed("django.contrib.admin")

    errors = check_privilege_escalation_prevention_enabled(app_configs)

    assert errors == []


def test_privilege_escalation_check_skipped_if_not_requested(
    revert_useradmin_patch,
):
    errors = check_privilege_escalation_prevention_enabled(
        [apps.get_app_config("testapp")]
    )

    assert errors == []


def test_privilege_escalation_check_warns_if_admin_not_patched(
    revert_useradmin_patch,
):
    errors = check_privilege_escalation_prevention_enabled(None)

    expected_warning = Warning(
        "Your UserAdmin does not use the 'PreventPrivilegeEscalationMixin' "
        "protections.",
        hint=(
            "Use a custom UserAdmin that includes 'maykin_common.accounts.admin."
            "PreventPrivilegeEscalationMixin'."
        ),
        id="maykin.W002",
    )
    assert expected_warning in errors


def test_privilege_escalation_check_does_not_warn_if_admin_is_patched():
    errors = check_privilege_escalation_prevention_enabled(None)

    assert errors == []


def test_privilege_escalation_check_does_not_warn_for_unregistered_user_model(
    unregister_user_model,
):
    errors = check_privilege_escalation_prevention_enabled(None)

    assert errors == []
