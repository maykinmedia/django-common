from django.core.mail import send_mail

import pytest
from django_yubin.models import Message

pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture(autouse=True)
def install_django_yubin_settings(settings):
    settings.INSTALLED_APPS = [
        *settings.INSTALLED_APPS,
        "maykin_common.yubin",
    ]

    settings.EMAIL_BACKEND = "maykin_common.yubin.backends.QueuedEmailBackend"


def test_send_email(settings):
    """
    Test that django's send_mail() queues a yubin Message
    instead of creating a celery task
    """

    assert settings.EMAIL_BACKEND == "maykin_common.yubin.backends.QueuedEmailBackend"

    send_mail(
        "Test Subject",
        "Test Message",
        "sender@example.com",
        ["recipient_1@example.com", "recipient_2@example.com"],
    )

    assert Message.objects.count() == 1

    message = Message.objects.get()
    assert message.status == Message.STATUS_QUEUED
