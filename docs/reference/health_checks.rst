.. _reference_health_checks:

============================
Infrastructure health checks
============================

.. automodule:: maykin_common.health_checks
    :members:

Health check endpoints
======================

The defaults included in maykin-common produce the following absolute URLs. The endpoints
return an HTTP status code ``200`` if all is well, and ``500`` otherwise.

``/_healthz/``
    Reports all the configured checks, such as database connection and permissions,
    configured caches and tests if all migrations have been executed. This is the most
    expensive check.

    It is suitable for the Kubernetes startup probe.

``/_healthz/livez/``
    The cheapest check - it does not check any dependencies like the database or caches.
    Extremely suitable for the the HTTP liveness probe (Kubernetes) or Docker engine
    health check.

``/_healthz/readyz/``
    A check slightly more expensive than the liveness subset. It checks the database
    and default cache connections. Suitable for the readiness probe in Kubernetes.

.. tip:: Use the unspecified endpoint for the startup probe, ``livez`` for the liveness
    probe and Docker engine health check and the ``readyz`` subset for the readiness
    probe.

    Alternatively, you can also use the ``livez`` endpoint for the readiness probe,
    and configure a higher failure treshold for the liveness probe to allow the
    application to recover before restarting it.

All health check endpoints return an overview of the checks that have passed or failed.
The response format depends on the ``Accept`` header:

* ``text/html``: Human-readable overview (default for browsers)
* ``application/json``: Machine-readable format (for monitoring tools)

You can force JSON output by appending ``?format=json`` to any health check URL.

Django setting defaults
=======================

The setting defaults should be imported from :mod:`maykin_common.health_checks`:

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

.. automodule:: maykin_common.health_checks.defaults
    :members:

Celery
======

.. automodule:: maykin_common.health_checks.celery.apps
    :members:

.. automodule:: maykin_common.health_checks.celery.probes
    :members:
    :undoc-members:

Settings
--------

* :attr:`maykin_common.settings.MKN_HEALTH_CHECKS_BEAT_LIVENESS_FILE`
