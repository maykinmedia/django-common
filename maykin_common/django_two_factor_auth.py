"""
Combine maykin-2fa and django-admin-index utilities.

Depends on ``django-admin-index``.
"""

from django.http import HttpRequest

from django_admin_index.utils import (
    should_display_dropdown_menu as default_should_display_dropdown_menu,
)


def should_display_dropdown_menu(request: HttpRequest) -> bool:
    """
    Overrides the default `should_display_dropdown_menu` from `django_admin_index.utils`
    to:
    - not display the dropdown in `maykin_2fa` views.
    - only display the dropdown to verified users.
    """
    default = default_should_display_dropdown_menu(request)

    assert request.resolver_match is not None

    # never display the dropdown in two-factor admin views
    if request.resolver_match.view_name.startswith("maykin_2fa:"):
        return False

    # do not display the dropdown until the user is verified.
    return default and request.user.is_verified()  # pyright: ignore[reportAttributeAccessIssue]
