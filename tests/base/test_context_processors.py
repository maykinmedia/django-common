from django.test.client import RequestFactory

from maykin_common.context_processors import settings as context_processors_settings


def test_settings(settings):
    settings.GOOGLE_ANALYTICS_ID = "abc"
    settings.PROJECT_NAME = "maykin_common"

    context = context_processors_settings(RequestFactory())

    assert context == {
        "settings": {
            "GOOGLE_ANALYTICS_ID": "abc",
            "PROJECT_NAME": "maykin_common",
            "RELEASE": None,
            "GIT_SHA": None,
        }
    }


def test_settings_none():
    context = context_processors_settings(RequestFactory())

    assert context == {
        "settings": {
            "GOOGLE_ANALYTICS_ID": None,
            "PROJECT_NAME": None,
            "RELEASE": None,
            "GIT_SHA": None,
        }
    }


def test_settings_with_sentry_config_without_public_dsn(settings):
    settings.SENTRY_CONFIG = {}

    context = context_processors_settings(RequestFactory())
    assert context["dsn"] == ""


def test_settings_with_sentry_config_with_public_dsn(settings):
    settings.SENTRY_CONFIG = {"public_dsn": "sentry.io/1234"}

    context = context_processors_settings(RequestFactory())
    assert context["dsn"] == "sentry.io/1234"
