import pytest


def test_module_import():
    try:
        import maykin_common.otel  # noqa: F401
    except ImportError:
        pytest.fail("Module 'otel' is not imported correctly.")
