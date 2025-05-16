import pytest


def test_module_import():
    try:
        import maykin_common.django_two_factor_auth  # noqa: F401
    except ImportError:
        pytest.fail("Module 'django_two_factor_auth' is not imported correctly.")
