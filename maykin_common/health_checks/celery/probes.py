import atexit
import logging
from pathlib import Path

from celery.beat import Service as BeatService
from celery.signals import after_task_publish, beat_init

from maykin_common.settings import get_setting

logger = logging.getLogger(__name__)

#
# Utilities for checking the health of celery beat
#

_RUNNING_IN_BEAT = False


def on_beat_init(*, sender: BeatService, **kwargs):
    global _RUNNING_IN_BEAT
    _RUNNING_IN_BEAT = True
    logger.debug("beat_process_marked")
    liveness_file: Path = get_setting("MKN_HEALTH_CHECKS_BEAT_LIVENESS_FILE")
    # on shutdown, clear up the liveness file
    atexit.register(liveness_file.unlink, missing_ok=True)


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

    liveness_file: Path = get_setting("MKN_HEALTH_CHECKS_BEAT_LIVENESS_FILE")
    logger.debug(
        "beat_task_published", extra={"task": sender, "routing_key": routing_key}
    )
    # create intermediate directories if they don't yet exist
    if not (parent_dir := liveness_file.parent).exists():
        parent_dir.mkdir(parents=True, exist_ok=True)
    # touching the file updates the last modified timestamp, which can be checked by
    # the health-check command
    liveness_file.touch()


def connect_beat_signals():
    # register signals for beat so that we can health-check it
    beat_init.connect(on_beat_init, dispatch_uid="probes.on_beat_init")
    after_task_publish.connect(
        on_beat_task_published, dispatch_uid="probes.on_beat_task_published"
    )
