from django.http import HttpResponse
from django.test import Client

import pytest
from csp.constants import HEADER, HEADER_REPORT_ONLY, NONCE, SELF
from csp.decorators import csp_exempt, csp_update

from maykin_common.csp.models import CSPSetting

from .conftest import ok_view
from .middleware import CustomCSPMiddleware

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("policy")]


@pytest.fixture()
def installed_middleware(settings) -> None:
    """
    Install the middleware in the real stack.

    It is not enabled in the test project by default, because it reads from the
    database on every response.
    """
    settings.MIDDLEWARE = [
        *settings.MIDDLEWARE,
        "maykin_common.csp.middleware.CSPMiddleware",
    ]


def test_database_directive_is_added_to_the_header(apply_middleware):
    CSPSetting.objects.create(directive="img-src", value="https://cdn.example.com")

    response = apply_middleware()

    assert "img-src https://cdn.example.com" in response[HEADER]
    assert "default-src 'self'" in response[HEADER]


def test_middleware_picks_up_a_new_setting_immediately(
    apply_middleware,
    django_capture_on_commit_callbacks,
):
    assert apply_middleware()[HEADER] == "default-src 'self'"

    with django_capture_on_commit_callbacks(execute=True):
        CSPSetting.objects.create(directive="img-src", value="https://cdn.example.com")

    assert "img-src https://cdn.example.com" in apply_middleware()[HEADER]


def test_the_mixin_applies_directives_through_another_base_middleware(
    settings, apply_middleware
):
    settings.CONTENT_SECURITY_POLICY = {
        "REPORT_PERCENTAGE": 100,
        "DIRECTIVES": {"default-src": [SELF]},
    }
    CSPSetting.objects.create(directive="img-src", value="https://cdn.example.com")

    response = apply_middleware(middleware_class=CustomCSPMiddleware)

    assert "img-src https://cdn.example.com" in response[HEADER]


def test_database_directive_extends_a_configured_directive(
    apply_middleware,
):
    CSPSetting.objects.create(directive="default-src", value="https://cdn.example.com")

    response = apply_middleware()

    assert "default-src 'self' https://cdn.example.com" in response[HEADER]


def test_multiple_values_for_one_directive_are_combined(
    apply_middleware,
):
    CSPSetting.objects.create(directive="img-src", value="https://b.example.com")
    CSPSetting.objects.create(directive="img-src", value="https://a.example.com")

    response = apply_middleware()

    # values are sorted, so the header is stable
    assert "img-src https://a.example.com https://b.example.com" in response[HEADER]


def test_duplicate_values_are_collapsed(apply_middleware):
    CSPSetting.objects.create(directive="img-src", value="https://a.example.com")
    CSPSetting.objects.create(
        directive="img-src", value="https://a.example.com", identifier="other"
    )

    response = apply_middleware()

    assert "img-src https://a.example.com;" in f"{response[HEADER]};"


def test_without_database_directives_the_policy_is_untouched(
    apply_middleware,
):
    response = apply_middleware()

    assert response[HEADER] == "default-src 'self'"


def test_report_only_policy_is_also_extended(settings, apply_middleware):
    settings.CONTENT_SECURITY_POLICY = None
    settings.CONTENT_SECURITY_POLICY_REPORT_ONLY = {
        "DIRECTIVES": {"default-src": [SELF]}
    }
    CSPSetting.objects.create(directive="img-src", value="https://cdn.example.com")

    response = apply_middleware()

    assert HEADER not in response
    assert "img-src https://cdn.example.com" in response[HEADER_REPORT_ONLY]


def test_both_policies_are_extended(settings, apply_middleware):
    settings.CONTENT_SECURITY_POLICY = {"DIRECTIVES": {"default-src": [SELF]}}
    settings.CONTENT_SECURITY_POLICY_REPORT_ONLY = {
        "DIRECTIVES": {"default-src": [SELF]}
    }
    CSPSetting.objects.create(directive="img-src", value="https://cdn.example.com")

    response = apply_middleware()

    assert "img-src https://cdn.example.com" in response[HEADER]
    assert "img-src https://cdn.example.com" in response[HEADER_REPORT_ONLY]


def test_database_entries_do_not_create_a_policy_from_nothing(
    settings, apply_middleware
):
    settings.CONTENT_SECURITY_POLICY = None
    settings.CONTENT_SECURITY_POLICY_REPORT_ONLY = None
    CSPSetting.objects.create(directive="img-src", value="https://cdn.example.com")

    response = apply_middleware()

    assert HEADER not in response
    assert HEADER_REPORT_ONLY not in response


def test_excluded_url_prefixes_are_respected(settings, apply_middleware):
    settings.CONTENT_SECURITY_POLICY = {
        "EXCLUDE_URL_PREFIXES": ["/excluded/"],
        "DIRECTIVES": {"default-src": [SELF]},
    }
    settings.CONTENT_SECURITY_POLICY_REPORT_ONLY = None
    CSPSetting.objects.create(directive="img-src", value="https://cdn.example.com")

    assert HEADER not in apply_middleware(path="/excluded/page")
    assert HEADER in apply_middleware(path="/included/page")


def test_excluded_url_prefixes_are_respected_per_policy(settings, apply_middleware):
    settings.CONTENT_SECURITY_POLICY = {"DIRECTIVES": {"default-src": [SELF]}}
    settings.CONTENT_SECURITY_POLICY_REPORT_ONLY = {
        "EXCLUDE_URL_PREFIXES": ["/excluded/"],
        "DIRECTIVES": {"default-src": [SELF]},
    }
    CSPSetting.objects.create(directive="img-src", value="https://cdn.example.com")

    excluded = apply_middleware(path="/excluded/page")
    included = apply_middleware(path="/included/page")

    assert HEADER_REPORT_ONLY not in excluded
    assert "img-src https://cdn.example.com" in excluded[HEADER]
    assert "img-src https://cdn.example.com" in included[HEADER_REPORT_ONLY]


def test_csp_update_decorator_values_are_preserved(apply_middleware):
    CSPSetting.objects.create(directive="img-src", value="https://database.example.com")
    view = csp_update({"img-src": ["https://decorator.example.com"]})(ok_view)

    response = apply_middleware(view=view)

    assert "https://decorator.example.com" in response[HEADER]
    assert "https://database.example.com" in response[HEADER]


def test_decorator_config_is_not_mutated_between_requests(
    apply_middleware,
):
    CSPSetting.objects.create(directive="img-src", value="https://database.example.com")
    config = {"img-src": ["https://decorator.example.com"]}
    view = csp_update(config)(ok_view)

    apply_middleware(view=view)
    response = apply_middleware(view=view)

    assert config == {"img-src": ["https://decorator.example.com"]}
    assert response[HEADER].count("https://database.example.com") == 1


def test_decorator_none_directive_is_left_alone_while_db_directive_still_merges(
    apply_middleware,
):
    CSPSetting.objects.create(directive="img-src", value="https://cdn.example.com")
    view = csp_update({"font-src": None})(ok_view)

    response = apply_middleware(view=view)

    assert "font-src" not in response[HEADER]
    assert "img-src https://cdn.example.com" in response[HEADER]


def test_exempt_response_does_not_get_a_header(apply_middleware):
    CSPSetting.objects.create(directive="img-src", value="https://cdn.example.com")
    view = csp_exempt()(ok_view)

    response = apply_middleware(view=view)

    assert HEADER not in response


def test_report_only_exemption_leaves_the_enforced_policy_alone(
    settings, apply_middleware
):
    settings.CONTENT_SECURITY_POLICY = {"DIRECTIVES": {"default-src": [SELF]}}
    settings.CONTENT_SECURITY_POLICY_REPORT_ONLY = {
        "DIRECTIVES": {"default-src": [SELF]}
    }
    CSPSetting.objects.create(directive="img-src", value="https://cdn.example.com")
    view = csp_exempt(REPORT_ONLY=True)(ok_view)

    response = apply_middleware(view=view)

    assert HEADER_REPORT_ONLY not in response
    assert "img-src https://cdn.example.com" in response[HEADER]


def test_nonce_keeps_working(settings, apply_middleware):
    settings.CONTENT_SECURITY_POLICY = {
        "DIRECTIVES": {"default-src": [SELF], "script-src": [SELF, NONCE]}
    }
    settings.CONTENT_SECURITY_POLICY_REPORT_ONLY = None
    CSPSetting.objects.create(directive="script-src", value="https://cdn.example.com")

    def view(request):
        return HttpResponse(str(request.csp_nonce))

    response = apply_middleware(view=view)

    nonce = response.content.decode()
    assert f"'nonce-{nonce}'" in response[HEADER]
    assert "https://cdn.example.com" in response[HEADER]


@pytest.mark.usefixtures("installed_middleware")
def test_end_to_end_through_the_request_stack(client: Client):
    CSPSetting.objects.create(directive="img-src", value="https://cdn.example.com")

    response = client.get("/admin/login/")

    assert "img-src https://cdn.example.com" in response[HEADER]
