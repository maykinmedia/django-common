from unittest.mock import patch

from django.core.mail import EmailMessage

import pytest
from django_yubin.models import Log, Message

from maykin_common.yubin.utils import enqueue, queue_email_message
from tests.yubin.utils import create_message

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


def test_enqueue_not_allowed_to_enqueue():
    """
    Tests original Message.enqueue functionality
    Should not mark the message as enqueued if not allowed
    """
    message = create_message(status=Message.STATUS_IN_PROCESS)

    result: bool = enqueue(message, "Log message")
    assert not result

    message.refresh_from_db()
    assert message.status == Message.STATUS_IN_PROCESS

    log = Log.objects.get(message=message)
    assert log.log_message == "Message can not be enqueued in it's current status"


def test_queue_email_message_no_recipients():
    """
    Tests original django_yubin.queue_email_message functionality
    Message should not be created if there are no recipients
    """

    email = EmailMessage("subject", "body", to=[], from_email="garry@example.com")

    result: int = queue_email_message(email)

    # no response, no message created
    assert result == 0
    assert Message.objects.count() == 0


def test_queue_email_message_enqueue_fails():
    """
    Tests original django_yubin.queue_email_message functionality
    Message is created but returned 0 if enqueue failed
    """

    email = EmailMessage(
        "subject", "body", to=["barry@example.com"], from_email="garry@example.com"
    )

    with patch("maykin_common.yubin.utils.Message.can_be_enqueued", return_value=False):
        result: int = queue_email_message(email)

    # no response, no message created
    assert result == 0
    assert Message.objects.count() == 1

    message = Message.objects.get()
    assert message.status == Message.STATUS_CREATED

    logs = Log.objects.filter(message=message).order_by("date")
    assert logs.count() == 2
    assert logs[0].log_message == "Message created"
    assert logs[1].log_message == "Message can not be enqueued in it's current status"


def test_queue_email_message_test_mailer():
    """
    Tests original django_yubin.queue_email_message functionality
    Message is reciprocated to the test mailer email addresses
    """

    # yubin does not correctly use django settings
    from django_yubin import settings

    settings.MAILER_TEST_MODE = True
    settings.MAILER_TEST_EMAIL = "test_mailer@example.com,test_mailer2@example.com"

    email = EmailMessage(
        "subject", "body", to=["barry@example.com"], from_email="garry@example.com"
    )

    result: int = queue_email_message(email)

    assert result == 1
    assert Message.objects.count() == 1

    message = Message.objects.get()
    assert message.to() == ["test_mailer@example.com", "test_mailer2@example.com"]
    assert message.status == Message.STATUS_QUEUED

    msg = message.get_message_parser()
    assert msg.headers["X-Yubin-Test-Original"] == "barry@example.com"
