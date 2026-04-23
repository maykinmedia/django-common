import logging
import time

from django_yubin.engine import send_db_message
from django_yubin.models import Message
from filelock import FileLock, Timeout

from ..settings import get_setting

logger = logging.getLogger(__name__)


def send_all() -> None:
    """
    Query all the queued messages and attempt to deliver them.

    This is the equivalent of the original :func:`django_yubin.tasks.send_email`.
    """

    lock = FileLock(get_setting("MKN_YUBIN_LOCK_PATH"))

    logger.debug(
        "acquiring_lock", extra={"path": str(get_setting("MKN_YUBIN_LOCK_PATH"))}
    )
    try:
        # skip timeout in favour of frequent cronjobs
        with lock.acquire(blocking=False):
            logger.debug("lock_acquired")
            start_time = time.time()

            for message in (
                Message.objects.filter(status=Message.STATUS_QUEUED)
                .only("pk")
                .iterator()
            ):
                send_db_message(message.pk, "Sending email")
            logger.debug("releasing_lock")

        logger.debug("lock_released")
        logger.debug(
            "email_sending_completed", extra={"duration": time.time() - start_time}
        )

    except Timeout:
        logger.debug("lock_acquiry_failed")
