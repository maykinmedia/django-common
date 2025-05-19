import pytest


def test_module_import(settings):
    settings.INSTALLED_APPS = settings.INSTALLED_APPS + ["axes"]
    try:
        import maykin_common.mixins  # noqa: F401
    except ImportError:
        pytest.fail("Module 'mixins' is not imported correctly.")
