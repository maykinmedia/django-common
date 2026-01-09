import pytest


def test_module_import():
    try:
        import maykin_common.health_checks  # noqa: F401
    except ImportError:
        pytest.fail("Module 'health_checks' is not imported correctly.")
