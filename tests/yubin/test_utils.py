from unittest.mock import patch

from django.core.mail import EmailMessage

import pytest
from django_yubin.models import Log, Message

from maykin_common.yubin.utils import enqueue, queue_email_message

from .utils import create_message

pytestmark = [
    pytest.mark.django_db,
]


def test_enqueue_does_not_make_a_message_in_process_queued_again():
    """
    Assert equeue does not make a message in progress queued again

    Tests original Message.enqueue functionality
    """
    message = create_message(status=Message.STATUS_IN_PROCESS)

    result: bool = enqueue(message, "Log message")
    assert not result

    message.refresh_from_db()
    assert message.status == Message.STATUS_IN_PROCESS

    log = Log.objects.get(message=message)
    assert log.log_message == "Message can not be enqueued in its current status"


def test_queue_email_message_does_not_create_message_with_no_recipients():
    """
    Assert queue_email_message does not create a message if there are no recipients

    Tests original django_yubin.queue_email_message functionality
    """

    email = EmailMessage("subject", "body", to=[], from_email="garry@example.com")

    result: int = queue_email_message(email)

    # no response, no message created
    assert result == 0
    assert Message.objects.count() == 0


def test_queue_email_message_is_create_but_enqueue_fails_returns_0():
    """
    Assert queue_email_message's message is created but returned 0 if enqueue failed

    Tests original django_yubin.queue_email_message functionality
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
    assert logs[1].log_message == "Message can not be enqueued in its current status"


def test_queue_email_message_uses_test_mailer_emails_in_test_mode():
    """
    Assert queue_email_message's message uses the test mailer emails
    when using test mode

    Tests original django_yubin.queue_email_message functionality
    """

    # yubin does not correctly use django settings
    from django_yubin import settings

    original_mailer_test_Mode = settings.MAILER_TEST_MODE
    original_mailer_test_email = settings.MAILER_TEST_EMAIL

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

    settings.MAILER_TEST_MODE = original_mailer_test_Mode
    settings.MAILER_TEST_EMAIL = original_mailer_test_email
