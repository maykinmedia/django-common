import logging
import time
from functools import partial

from django.db import transaction

from django_yubin.engine import send_db_message
from django_yubin.models import Message
from filelock import FileLock, Timeout

from maykin_common.settings import get_setting

logger = logging.getLogger(__name__)


def send_all() -> None:
    """
    Runs the equivalent of a send_email task done in the original Message.enqueue
    """

    lock = FileLock(get_setting("YUBIN_LOCK_PATH"))

    logger.debug("Acquiring lock...")
    try:
        with lock.acquire(blocking=False):
            logger.debug("Lock acquired.")
            start_time = time.time()

            for message in Message.objects.filter(status=Message.STATUS_QUEUED):
                transaction.on_commit(
                    partial(
                        send_db_message,
                        message_pk=message.pk,
                        log_message="Sending email",
                    )
                )
            logger.debug("Releasing lock...")

        logger.debug("Lock released.")
        logger.debug("Completed in %.2f seconds.", (time.time() - start_time))

    except Timeout:
        logger.debug("Waiting for the lock timed out. Exiting.")
