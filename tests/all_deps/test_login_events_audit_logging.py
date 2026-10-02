import json

from django.contrib.auth import authenticate, login
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
def test_login_event_is_logged(rf: RequestFactory, log_output: LogCapture):
    request = rf.post("/accounts/login", REMOTE_ADDR="192.168.0.42")
    request.session = SessionStore()
    user = User.objects.create_user(username="testuser")

    login(request, user)

    entry = next(
        (entry for entry in log_output.entries if entry["event"] == "user_logged_in"),
        None,
    )
    assert entry is not None
    assert entry["login_path"] == "/accounts/login"
    assert entry["ip_address"] == "192.168.0.42"
    assert entry["username"] == "testuser"


@pytest.mark.django_db
def test_login_failure_event_is_logged(rf: RequestFactory, log_output: LogCapture):
    request = rf.post("/accounts/login", REMOTE_ADDR="192.168.0.42")
    request.session = SessionStore()
    User.objects.create_user(username="testuser", password="letmein")

    authenticate(request=request, username="testuser", password="wrongpassword")

    entry = next(
        (
            entry
            for entry in log_output.entries
            if entry["event"] == "user_login_failed"
        ),
        None,
    )
    assert entry is not None
    assert entry["login_path"] == "/accounts/login"
    assert entry["ip_address"] == "192.168.0.42"
    assert entry["username"] == "testuser"

    stringified_log_line = json.dumps(entry)
    assert "wrongpassword" not in stringified_log_line


def test_login_failure_event_without_request_context_or_username(
    log_output: LogCapture,
):
    authenticate(token="abcdefgh")

    entry = next(
        (
            entry
            for entry in log_output.entries
            if entry["event"] == "user_login_failed"
        ),
        None,
    )
    assert entry is not None
    assert "username" not in entry
    assert "login_path" not in entry
    assert "ip_address" not in entry


def test_login_failure_no_request_context_but_credentials_supplied(
    log_output: LogCapture,
):
    authenticate(username="bruteforce")

    entry = next(
        (
            entry
            for entry in log_output.entries
            if entry["event"] == "user_login_failed"
        ),
        None,
    )
    assert entry is not None
    assert entry["username"] == "bruteforce"
    assert "login_path" not in entry
    assert "ip_address" not in entry
