from django.core.mail.backends.base import BaseEmailBackend

from maykin_common.yubin.utils import queue_email_message


class QueuedEmailBackend(BaseEmailBackend):
    """
    Un-celeries your QueuedEmailBackend

    Copied of django_yubin.backends.QueuedEmailBackend replacing queue_email_message
    """

    def send_messages(self, email_messages):
        """
        Add new messages to the email queue.

        The ``email_messages`` argument should be one or more instances
        of Django's core mail ``EmailMessage`` class.
        """

        num_sent = 0
        for email_message in email_messages:
            num_sent += queue_email_message(email_message)
        return num_sent
