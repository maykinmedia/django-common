"""
Custom Django system checks to prevent common mistakes.
"""

import os
from collections.abc import Sequence

from django.apps import AppConfig, apps
from django.conf import settings
from django.contrib.admin import site as default_admin_site
from django.contrib.admin.exceptions import NotRegistered
from django.contrib.auth import get_user_model
from django.core.checks import Warning, register

from maykin_common.accounts.admin import PreventPrivilegeEscalationMixin


@register
def check_missing_init_files(app_configs: Sequence[AppConfig] | None, **kwargs):
    """
    Check that all packages have __init__.py files.

    If they don't, the code will still run, but tests aren't picked up by the
    test runner, for example.
    """
    errors = []

    for dirpath, _, filenames in os.walk(settings.DJANGO_PROJECT_DIR):
        dirname = os.path.split(dirpath)[1]
        if dirname == "__pycache__":
            continue

        if "__init__.py" in filenames:
            continue

        extensions = [os.path.splitext(fn)[1] for fn in filenames]
        if ".py" not in extensions:
            continue

        errors.append(
            Warning(
                f"Directory {dirpath} does not contain an `__init__.py` file "
                f"{dirname}.",
                hint="Consider adding this module to make sure tests are picked up",
                id="maykin.W001",
            )
        )

    return errors


@register
def check_privilege_escalation_prevention_enabled(
    app_configs: Sequence[AppConfig] | None, **kwargs
):
    """
    Test that the user account privilege escalation protections are enabled.
    """
    run_check = (
        app_configs is None
        or any(c.name in ("maykin_common", "django.contrib.admin") for c in app_configs)
        and apps.is_installed("django.contrib.admin")
    )
    if not run_check:
        return []

    # look up which admin class is used for the user model
    UserModel = get_user_model()
    try:
        user_admin = default_admin_site.get_model_admin(UserModel)
    except NotRegistered:
        return []

    mixin_enabled = isinstance(user_admin, PreventPrivilegeEscalationMixin)
    if mixin_enabled:
        return []

    return [
        Warning(
            "Your UserAdmin does not use the 'PreventPrivilegeEscalationMixin' "
            "protections.",
            hint=(
                "Use a custom UserAdmin that includes 'maykin_common.accounts.admin."
                "PreventPrivilegeEscalationMixin'."
            ),
            id="maykin.W002",
        )
    ]
