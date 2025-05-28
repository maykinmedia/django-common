import pytest


def test_module_import(settings):
    settings.INSTALLED_APPS = settings.INSTALLED_APPS + ["axes"]
    try:
        import maykin_common.throttling  # noqa: F401
    except ImportError:
        pytest.fail("Module 'throttling' is not imported correctly.")
