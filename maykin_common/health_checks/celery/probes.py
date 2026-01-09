import atexit
import logging
from pathlib import Path

from django.conf import settings

from celery.beat import Service as BeatService

logger = logging.getLogger(__name__)

#
# Utilities for checking the health of celery beat
#

_RUNNING_IN_BEAT = False

BEAT_LIVENESS_FILE = Path(settings.BASE_DIR) / "tmp" / "celery_beat_live"


def on_beat_init(*, sender: BeatService, **kwargs):
    global _RUNNING_IN_BEAT
    _RUNNING_IN_BEAT = True
    logger.debug("beat_process_marked")
    # on shutdown, clear up the liveness file
    atexit.register(BEAT_LIVENESS_FILE.unlink, missing_ok=True)


def on_beat_task_published(*, sender: str, routing_key: str, **kwargs):
    """
    Update the celery beat liveness every time a task is successfully published.

    ``after_task_publish`` fires in the process that sent the task, so we must discern
    between the regular Django app that schedules tasks, and celery beat that also
    schedules tasks. We do this by tapping into the ``beat_init`` signal to mark the
    process as a beat process, and only touch the liveness file when running in beat.
    """
    if not _RUNNING_IN_BEAT:
        return

    logger.debug(
        "beat_task_published", extra={"task": sender, "routing_key": routing_key}
    )
    # touching the file updates the last modified timestamp, which can be checked by
    # the health-check command
    BEAT_LIVENESS_FILE.touch()
