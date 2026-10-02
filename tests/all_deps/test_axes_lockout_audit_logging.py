from django.test import Client

import pytest
from structlog.testing import LogCapture

from ..utils import is_dependency_installed

pytestmark = [
    pytest.mark.skipif(
        not is_dependency_installed("structlog"), reason="Structlog not installed"
    ),
]


@pytest.mark.django_db
def test_axes_lockout_event_is_audit_logged(
    log_output: LogCapture,
    client: Client,
    settings,
):
    settings.AXES_FAILURE_LIMIT = 1

    admin_login_response = client.post(
        "/admin/login/",
        data={"username": "admin", "password": "password123"},
        REMOTE_ADDR="192.168.0.42",
    )

    assert admin_login_response.status_code == 429
    assert b"Account locked" in admin_login_response.content

    entry = next(
        (entry for entry in log_output.entries if entry["event"] == "user_locked_out"),
        None,
    )
    assert entry is not None
    assert entry["ip_address"] == "192.168.0.42"
    assert entry["username"] == "admin"

    failure_entry = next(
        (
            entry
            for entry in log_output.entries
            if entry["event"] == "user_login_failed"
        ),
        None,
    )
    assert failure_entry is not None
    assert failure_entry["login_path"] == "/admin/login/"
    assert failure_entry["ip_address"] == "192.168.0.42"
    assert failure_entry["username"] == "admin"
