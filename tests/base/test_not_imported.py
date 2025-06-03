import pytest


def test_pdf():
    with pytest.raises(ImportError):
        import maykin_common.pdf  # noqa: F401


def test_2fa():
    with pytest.raises(ImportError):
        import maykin_common.django_two_factor_auth  # noqa: F401


def test_mixins():
    with pytest.raises(ImportError):
        import maykin_common.throttling  # noqa: F401
