import pytest


def _dependency_installed(dependency: str):
    try:
        __import__(dependency)
        return True
    except ImportError:
        return False


@pytest.mark.skipif(
    _dependency_installed("weasyprint"), reason="The 'pdf' extra seems to be installed"
)
def test_pdf():
    with pytest.raises(ImportError):
        import maykin_common.pdf  # noqa: F401


@pytest.mark.skipif(
    _dependency_installed("maykin_2fa"), reason="The 'mfa' extra seems to be installed"
)
def test_2fa():
    with pytest.raises(ImportError):
        import maykin_common.django_two_factor_auth  # noqa: F401


@pytest.mark.skipif(
    _dependency_installed("axes"), reason="The 'axes' seems to be installed"
)
def test_mixins():
    with pytest.raises(ImportError):
        import maykin_common.throttling  # noqa: F401
