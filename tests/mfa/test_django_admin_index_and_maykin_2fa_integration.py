from django.http import HttpRequest, HttpResponse
from django.template import RequestContext, Template
from django.test import Client
from django.urls import include, path

import pytest

pytestmark = [pytest.mark.urls(__name__)]


@pytest.fixture(autouse=True)
def _add_installed_apps(settings):
    settings.INSTALLED_APPS = [
        *settings.INSTALLED_APPS,
        "django_admin_index",
        # maykin-2fa:
        "django_otp",
        "django_otp.plugins.otp_static",
        "django_otp.plugins.otp_totp",
        "two_factor",
        "maykin_2fa",
    ]

    settings.MIDDLEWARE = [
        *settings.MIDDLEWARE,
        "maykin_2fa.middleware.OTPMiddleware",
    ]

    settings.ADMIN_INDEX_SHOW_MENU = True
    settings.ADMIN_INDEX_DISPLAY_DROP_DOWN_MENU_CONDITION_FUNCTION = (
        "maykin_common.django_two_factor_auth.should_display_dropdown_menu"
    )


def djai_view(request: HttpRequest) -> HttpResponse:
    content = (
        Template(
            r"""
        {% load django_admin_index %}
        {% display_dropdown_menu request %}
        """
        )
        .render(RequestContext(request))
        .strip()
    )
    return HttpResponse(content.encode("utf-8"))


urlpatterns = [
    path("admin-index", djai_view),
    path(
        "mfa-ns/",
        include(
            (
                [path("admin-index", djai_view)],
                "maykin_2fa",
            ),
            namespace="maykin_2fa",
        ),
    ),
]


def test_display_dropdown_menu_is_false_when_show_menu_disabled_in_settings(
    settings, client: Client
):
    settings.ADMIN_INDEX_SHOW_MENU = False

    response = client.get("/admin-index")

    assert response.content == b"False"


def test_display_dropdown_menu_is_false_when_not_authenticated(client: Client):
    response = client.get("/admin-index")

    assert response.content == b"False"


@pytest.mark.django_db
def test_display_dropdown_menu_is_false_when_authenticated_but_not_staff(
    client: Client, django_user_model
):
    user = django_user_model.objects.create_user(
        username="dummy", password="dummy", is_staff=False
    )
    client.force_login(user=user)

    response = client.get("/admin-index")

    assert response.content == b"False"


def test_display_dropdown_menu_is_true_for_staff_user_with_default_setting(
    settings,
    admin_client: Client,
):
    settings.ADMIN_INDEX_DISPLAY_DROP_DOWN_MENU_CONDITION_FUNCTION = (
        "django_admin_index.utils.should_display_dropdown_menu"
    )
    response = admin_client.get("/admin-index")

    assert response.content == b"True"


def test_display_dropdown_menu_is_false_for_staff_user_with_extra_mfa_check(
    settings,
    admin_client: Client,
):
    response = admin_client.get("/admin-index")

    assert response.content == b"False"


def test_display_dropdown_menu_is_true_for_verified_staff_user_with_extra_mfa_check(
    settings,
    admin_client: Client,
):
    # mark user as verified by allowing the auth backend as bypass
    settings.MAYKIN_2FA_ALLOW_MFA_BYPASS_BACKENDS = [
        "django.contrib.auth.backends.ModelBackend"
    ]

    response = admin_client.get("/admin-index")

    assert response.content == b"True"


def test_display_dropdown_menu_is_false_for_verified_staff_user_in_mfa_namespace(
    settings,
    admin_client: Client,
):
    # mark user as verified by allowing the auth backend as bypass
    settings.MAYKIN_2FA_ALLOW_MFA_BYPASS_BACKENDS = [
        "django.contrib.auth.backends.ModelBackend"
    ]

    response = admin_client.get("/mfa-ns/admin-index")

    assert response.content == b"False"
