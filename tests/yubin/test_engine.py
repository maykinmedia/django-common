import pytest

from maykin_common.yubin.engine import send_all

pytestmark = [
    pytest.mark.django_db,
]


def test_send_all(settings):
    """
    Test YUBIN_LOCK_WAIT_TIMEOUT setting works without exception
    Fixes coverage
    """

    settings.YUBIN_LOCK_WAIT_TIMEOUT = 10
    send_all()

    settings.YUBIN_LOCK_WAIT_TIMEOUT = None
    send_all()

    settings.YUBIN_LOCK_WAIT_TIMEOUT = -1
    send_all()
