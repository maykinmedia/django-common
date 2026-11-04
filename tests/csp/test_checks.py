import pytest

from maykin_common.csp.checks import (
    check_csp_cache_timeout,
    check_csp_middleware_installed,
)

CUSTOM_MIDDLEWARE = "tests.csp.middleware.CustomCSPMiddleware"


def test_no_warning_when_our_middleware_is_installed(settings):
    settings.MIDDLEWARE = ["maykin_common.csp.middleware.CSPMiddleware"]

    assert check_csp_middleware_installed(None) == []


def test_no_warning_for_a_mixin_based_middleware_in_another_namespace(
    settings,
):
    settings.MIDDLEWARE = [
        "django.middleware.common.CommonMiddleware",
        CUSTOM_MIDDLEWARE,
    ]

    assert check_csp_middleware_installed(None) == []


def test_warns_for_an_importable_class_that_is_not_our_mixin(settings):
    settings.MIDDLEWARE = ["tests.csp.middleware.NotAMiddleware"]

    errors = check_csp_middleware_installed(None)

    assert [error.id for error in errors] == ["maykin.W004"]


def test_warns_when_the_upstream_middleware_is_used(settings):
    settings.MIDDLEWARE = [
        "django.middleware.common.CommonMiddleware",
        "csp.middleware.CSPMiddleware",
    ]

    errors = check_csp_middleware_installed(None)

    assert [error.id for error in errors] == ["maykin.W003"]


def test_warns_when_no_csp_middleware_is_installed(settings):
    settings.MIDDLEWARE = ["django.middleware.common.CommonMiddleware"]

    errors = check_csp_middleware_installed(None)

    assert [error.id for error in errors] == ["maykin.W004"]


def test_warns_when_middleware_is_empty(settings):
    settings.MIDDLEWARE = []

    errors = check_csp_middleware_installed(None)

    assert [error.id for error in errors] == ["maykin.W004"]


def test_unimportable_middleware_is_ignored(settings):
    settings.MIDDLEWARE = ["does.not.Exist"]

    errors = check_csp_middleware_installed(None)

    assert [error.id for error in errors] == ["maykin.W004"]


def test_no_error_for_the_default_cache_timeout():
    assert check_csp_cache_timeout(None) == []


def test_no_error_when_caching_is_disabled(settings):
    settings.MKN_CSP_CACHE_TIMEOUT = 0

    assert check_csp_cache_timeout(None) == []


@pytest.mark.parametrize(
    "timeout",
    [
        pytest.param(None, id="caching indefinitely is no longer supported"),
        pytest.param(-1, id="a negative timeout expires the entry immediately"),
        pytest.param("60", id="a string is not a number of seconds"),
        pytest.param(True, id="bool is an int subclass, but means nothing here"),
    ],
)
def test_errors_for_an_unusable_cache_timeout(settings, timeout):
    settings.MKN_CSP_CACHE_TIMEOUT = timeout

    errors = check_csp_cache_timeout(None)

    assert [error.id for error in errors] == ["maykin.E001"]
    assert repr(timeout) in errors[0].msg
