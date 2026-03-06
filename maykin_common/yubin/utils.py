import logging

from django.core.mail import EmailMessage

from django_yubin import _set_message_test_mode, settings
from django_yubin.models import Message

logger = logging.getLogger(__name__)


def enqueue(message: Message, log_message: str | None = None) -> bool:
    """
    Un-celeries your Message.enqueue
    Sends the task to enqueue the message on commit.
    """
    if not message.can_be_enqueued():
        message.add_log("Message can not be enqueued in it's current status")
        return False

    # mark as queued instead of creating a new task
    message.mark_as(Message.STATUS_QUEUED, log_message)

    return True


def retry_messages(max_retries: int = 3) -> tuple[int, int]:
    """
    Un-celeries your Message.retry_messages
    """

    enqueued = 0
    messages = Message.objects.retryable(max_retries)  # type: ignore
    for message in messages:
        enqueued += enqueue(message, "Retry sending the email.")
    failed = len(messages) - enqueued
    return enqueued, failed


def queue_email_message(
    email_message: EmailMessage, fail_silently: bool = False
) -> int:
    """
    Un-celeries your django_yubin.queue_email_message

    Add new messages to the email queue.

    The ``email_message`` argument should be an instance of Django's core mail
    ``EmailMessage`` class.

    The ``fail_silently`` argument is not used and is only provided to match
    the signature of the ``EmailMessage.send`` function which it may emulate.
    """

    if settings.MAILER_TEST_MODE and settings.MAILER_TEST_EMAIL:
        email_message = _set_message_test_mode(
            email_message, settings.MAILER_TEST_EMAIL
        )

    if not email_message.recipients():
        return 0

    message = Message.objects.create(
        to_address=",".join(email_message.to),
        cc_address=",".join(email_message.cc),
        bcc_address=",".join(email_message.bcc),
        from_address=email_message.from_email,
        subject=email_message.subject,
        message_data=email_message.message().as_string(),
        storage=settings.MAILER_STORAGE_BACKEND,
    )
    message.add_log("Message created")

    if enqueue(message, "Enqueued from a Backend or django-yubin itself."):
        return 1
    else:
        logger.exception("Error enqueuing an email", extra={"email_message": message})
        return 0
