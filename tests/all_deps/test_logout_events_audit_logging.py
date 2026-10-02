from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory

import pytest
from structlog.testing import LogCapture

from ..utils import is_dependency_installed

pytestmark = [
    pytest.mark.skipif(
        not is_dependency_installed("structlog"), reason="Structlog not installed"
    ),
]


@pytest.mark.django_db
def test_logout_event_is_logged(rf: RequestFactory, log_output: LogCapture):
    request = rf.post("/accounts/logout", REMOTE_ADDR="192.168.0.42")
    request.session = SessionStore()
    request.user = User.objects.create_user(username="testuser")

    logout(request)

    entry = next(
        (entry for entry in log_output.entries if entry["event"] == "user_logged_out"),
        None,
    )
    assert entry is not None
    assert entry["logout_path"] == "/accounts/logout"
    assert entry["ip_address"] == "192.168.0.42"
    assert entry["username"] == "testuser"


def test_logout_event_for_unauthenticated_requeset_is_not_logged(
    rf: RequestFactory, log_output: LogCapture
):
    request = rf.post("/accounts/logout")
    request.session = SessionStore()

    logout(request)

    assert not log_output.entries
