from unittest.mock import patch

from django.core.mail import send_mail

import pytest
from django_yubin.models import Message

pytestmark = [
    pytest.mark.django_db,
]


def test_send_email_uses_maykin_common_backend(settings):
    """
    Assert that django's send_mail() queues a yubin Message
    instead of creating a celery task
    """

    assert settings.EMAIL_BACKEND == "maykin_common.yubin.backends.QueuedEmailBackend"

    with patch("django_yubin.tasks.send_email") as mock_task_send_email:
        send_mail(
            "Test Subject",
            "Test Message",
            "sender@example.com",
            ["recipient_1@example.com", "recipient_2@example.com"],
        )

    assert not mock_task_send_email.called

    assert Message.objects.count() == 1

    message = Message.objects.get()
    assert message.status == Message.STATUS_QUEUED
