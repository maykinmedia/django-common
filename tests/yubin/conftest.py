from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def install_django_yubin_settings(settings):
    settings.EMAIL_BACKEND = "maykin_common.yubin.backends.QueuedEmailBackend"


@pytest.fixture()
def lock_file(settings, tmp_path: Path) -> Path:
    lock_path = tmp_path / "test.lock"
    settings.MKN_YUBIN_LOCK_PATH = lock_path
    return lock_path
