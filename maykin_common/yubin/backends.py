from collections.abc import Iterable

from django.core.mail import EmailMessage
from django.core.mail.backends.base import BaseEmailBackend

from maykin_common.yubin.utils import queue_email_message


class QueuedEmailBackend(BaseEmailBackend):
    """
    Un-celeries your QueuedEmailBackend

    Copied of django_yubin.backends.QueuedEmailBackend replacing queue_email_message
    """

    def send_messages(self, email_messages: Iterable[EmailMessage]) -> int:
        """
        Add new messages to the email queue, return the number of messages queued.

        The ``email_messages`` argument should be one or more instances
        of Django's core mail ``EmailMessage`` class.
        """

        return sum(map(queue_email_message, email_messages))
