from pathlib import Path
from typing import Literal

from django.conf import settings

GOOGLE_ANALYTICS_ID = None
"""
Google analytics id added to the request context.
"""

SHOW_ENVIRONMENT = False
"""
Enable or disable the ``{% environment_info %}`` template tag.
"""

ENVIRONMENT_BACKGROUND_COLOR = "orange"
"""
The background color of the ``{% environment_info %}`` template tag.
"""

ENVIRONMENT_FOREGROUND_COLOR = "black"
"""
The foreground color of the ``{% environment_info %}`` template tag.
"""

ENVIRONMENT_LABEL = None
"""
The textual content of the ``{% environment_info %}`` template tag.
"""

ENVIRONMENT = ""
"""
The deployment environment label, e.g. 'staging' or 'prod'.

This setting is included in the OpenTelemetry resource attributes.
"""

RELEASE = None
"""
The release version shown in the ``{% version_info %}`` template tag.

This setting is included in the OpenTelemetry resource attributes.
"""

GIT_SHA = None
"""
The commit hash shown in the ``{% version_info %}`` template tag.
"""

PDF_BASE_URL_FUNCTION = None
"""
Function that returns the base url needed to download/resolve custom fonts and/or any
image URLs included in the document to render.

Required for the :ref:`quickstart_pdf` extra.
"""

LOGIN_URLS = []
"""
Collection of login URLs.

This setting is used in the :func:`maykin_common.views.csrf_failure` view to handle CSRF
errors that occur when attempting to log in a second time.
"""

MKN_HEALTH_CHECKS_BEAT_LIVENESS_FILE: Path = Path("/tmp") / "celery_beat_live"
"""
Path to the file that acts as a liveness marker of Celery Beat.

Used when :mod:`maykin_common.health_checks.celery` is installed, which registers health
check mechanisms for Celery Beat. The intermediate directories will be created if
absent. The file itself will be created when beat publishes its first task, and will
be unlinked again when beat exits.
"""

MKN_HEALTH_CHECKS_WORKER_EVENT_LOOP_LIVENESS_FILE: Path = (
    Path("/tmp") / "celery_worker_event_loop_live"
)
"""
Path to the file that acts as a liveness marker of the Celery Worker event loop.

Used when the :class:`maykin_common.health_checks.celery.probes.EventLoopProbe` is added
as a Celery Worker bootstep, which periodically updates the liveness file with the last
timer tick. The intermediate directories will be created if absent. The file itself will
be created when the worker main process starts, and will be unlinked again when the
worker exits.
"""

MKN_HEALTH_CHECKS_WORKER_EVENT_LOOP_PROBE_FREQUENCY_SECONDS: int = 60
"""
Frequency in seconds on how often the event loop should update the liveness file.
"""

MKN_HEALTH_CHECKS_WORKER_READINESS_FILE: Path = Path("/tmp") / "celery_worker_ready"
"""
Path to the file that acts as a readiness marker of Celery Worker.

Used when :mod:`maykin_common.health_checks.celery` is installed, which registers health
check mechanisms for Celery Worker. The intermediate directories will be created if
absent. The file itself will be created when the worker is ready to accept work, i.e.
once the consumer blueprint is finished as part of the celery worker startup. It means
that a connection with the broker is established and tasks can be processed.

When the worker shuts down, the file is unlinked.
"""

type SettingName = Literal[
    "GOOGLE_ANALYTICS_ID",
    "ENVIRONMENT",
    "SHOW_ENVIRONMENT",
    "ENVIRONMENT_BACKGROUND_COLOR",
    "ENVIRONMENT_FOREGROUND_COLOR",
    "ENVIRONMENT_LABEL",
    "RELEASE",
    "GIT_SHA",
    "PDF_BASE_URL_FUNCTION",
    "LOGIN_URLS",
    "MKN_HEALTH_CHECKS_BEAT_LIVENESS_FILE",
    "MKN_HEALTH_CHECKS_WORKER_EVENT_LOOP_LIVENESS_FILE",
    "MKN_HEALTH_CHECKS_WORKER_EVENT_LOOP_PROBE_FREQUENCY_SECONDS",
    "MKN_HEALTH_CHECKS_WORKER_READINESS_FILE",
]


def get_setting(name: SettingName):
    default = globals()[name]
    return getattr(settings, name, default)
