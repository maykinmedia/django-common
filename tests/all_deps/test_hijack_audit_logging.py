from django.contrib.auth.models import User
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
def test_hijacking_and_releasing_user_is_logged(
    admin_client: Client, log_output: LogCapture
):
    other_user = User.objects.create_user(username="other_user")

    # hijack
    response = admin_client.post(
        "/hijack/acquire/", data={"user_pk": str(other_user.pk)}
    )

    assert response.status_code == 302
    hijack_started_entry = next(
        (entry for entry in log_output.entries if entry["event"] == "hijack_started"),
        None,
    )
    assert hijack_started_entry is not None
    assert hijack_started_entry["hijacker"] == "admin"
    assert hijack_started_entry["hijacked"] == "other_user"

    # release
    response = admin_client.post("/hijack/release/")

    assert response.status_code == 302
    hijack_ended_entry = next(
        (entry for entry in log_output.entries if entry["event"] == "hijack_ended"),
        None,
    )
    assert hijack_ended_entry is not None
    assert hijack_ended_entry["hijacker"] == "admin"
    assert hijack_ended_entry["hijacked"] == "other_user"
