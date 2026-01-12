.. _health-checks:

=============
Health checks
=============

Health checks are used to mark (crashed) containers as unhealthy, so that they can be
restarted by the container orchestration (Kubernetes, Docker engine...).

The health check tooling in maykin-common covers the HTTP health checks for the Django
app and the Celery components, like the worker and beat.

.. versionadded:: 0.13.0

    Added tooling for Django health checks.

.. versionadded:: 0.14.0

    Added support for Celery.

.. contents:: Jump to
    :local:
    :depth: 2

There is also :ref:`reference documentation <reference_health_checks>` available.

Quickstart (tl;dr)
==================

Install the extra dependencies:

.. code-block:: bash

    uv pip install maykin-common[cli,health-checks]

Update your settings accordingly:

.. code-block:: python

    from maykin_common.health_checks import (
        default_health_check_apps,
        default_health_check_subsets,
    )

    INSTALLED_APPS = [
        ...,
        *default_health_check_apps,
        ...
    ]

    HEALTH_CHECK = {
        "SUBSETS": default_health_check_subsets,
    }

and your root ``urls.py``:

.. code-block:: python

    urlpatterns = [
        ...,
        path("", include("maykin_common.health_checks.urls")),
        ...,
    ]

Command line
============

HTTP health checks
------------------

You can use the ``maykin-common`` CLI to probe the health check endpoint(s):

.. code-block:: bash

    maykin-common health-check --endpoint=/_healthz/livez/

Which will exit with exit code ``0`` for success responses (HTTP status code between 200
and 399).

.. note:: Make sure the install the ``cli`` extra:

    .. code-block:: bash

        uv pip install maykin-common[cli]

Celery beat health checks
-------------------------

If you use Celery Beat and install the health checks (see below), you can test the
Beat liveness too:

.. code-block:: bash

    maykin-common beat-health-check --file /app/tmp/celery/beat.live --max-age 120

Which will exit with exit code ``0`` if the specified file exists and is last modified
within the specified number of seconds. The file path should match the value of the
``MKN_HEALTH_CHECKS_BEAT_LIVENESS_FILE`` setting.

.. tip:: Use a ``--max-age`` that's 2x the interval of your most frequently scheduled
   task. E.g. if you have a task that runs every minute, pick 120 seconds.

.. tip:: Use startup probes if possible to give Beat time to load, start and schedule
   a task for the first time.

Celery
======

If you use Celery in your project, there are health check tools for the Celery
components too.

Beat
----

We can monitor Beat's liveness by tracking when was the last time a task was scheduled.
Instrumentation is done by adding a Django app and (optionally) specifying the file path
to the liveness file:

.. code-block:: python

    from pathlib import Path

    INSTALLED_APPS = [
        ...,
        "maykin_common.health_checks.celery",
        ...
    ]

    MKN_HEALTH_CHECKS_BEAT_LIVENESS_FILE = Path("/tmp/celery_beat_live")

The file specified through ``MKN_HEALTH_CHECKS_BEAT_LIVENESS_FILE`` will be touched
every time Beat successfully schedules a task to the broker. The health check can then
test how long ago the file was last touched. For example, if your Beat schedule runs a
task every hour, you could run the health check that expects the file to be modified
less than 2 hours ago.

.. tip:: If your normal schedule has very infrequent tasks (e.g. once per week), you
   may want to set up a smoke test task that runs more frequently (e.g. every hour).

Worker
------

.. todo:: To be implemented.
