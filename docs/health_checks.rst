.. _health_checks:

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

    Added support for Celery Beat.

.. contents:: Jump to
    :local:
    :depth: 2

There is also :ref:`reference documentation <reference_health_checks>` available.

Quickstart (tl;dr)
==================

Install the extra dependencies:

.. code-block:: bash

    uv pip install maykin-common[health-checks]

Update your settings accordingly:

.. code-block:: python

    from maykin_common.health_checks import (
        default_health_check_apps,
        default_health_check_subsets,
    )

    INSTALLED_APPS = [
        ...,
        *default_health_check_apps,
        "maykin_common.health_checks.celery",  # optional, add if you use Celery
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

and in your ``celery.py`` entrypoint:

.. code-block:: python

    from maykin_common.health_checks.celery.probes import EventLoopProbe

    app = Celery("my-proj")
    app.steps["worker"].add(EventLoopProbe)

See the :ref:`health_checks_cli` details for how to test the health.

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

    MKN_HEALTH_CHECKS_BEAT_LIVENESS_FILE = Path("/tmp") / "celery_beat_live"

The file specified through ``MKN_HEALTH_CHECKS_BEAT_LIVENESS_FILE`` will be touched
every time Beat successfully schedules a task to the broker. The health check can then
test how long ago the file was last touched. For example, if your Beat schedule runs a
task every hour, you could run the health check that expects the file to be modified
less than 2 hours ago.

.. tip:: If your normal schedule has very infrequent tasks (e.g. once per week), you
   may want to set up a smoke test task that runs more frequently (e.g. every hour).

.. caution::

   If you use the :class:`django_celery_beat.schedulers.DatabaseScheduler` scheduler,
   you should be aware that your schedules are editable at runtime through the admin,
   which may mean your ``max-age`` parameter no longer aligns with your actual schedule,
   leading to erroneously failed health checks. In such cases you might want to consider
   scheduling an explicit heartbeat task, using the task description to make clear that
   the task should be enabled and should not be re-scheduled.

Worker
------

Monitoring Celery Worker's health is complicated due to the complex nature of workers
and how they can fail. The worker system essentially boots up a whole stack of
subsystems that can each fail and contribute to "broken" workers. For details, see the
`blueprints <https://docs.celeryq.dev/en/stable/userguide/extending.html#blueprints>`_
docs.

**Enabling the checks**

Enabling the worker health check machinery requires some small changes to your
configuration.

First, ensure the settings are configured appropriately:

.. code-block:: python

    from pathlib import Path

    INSTALLED_APPS = [
        ...,
        "maykin_common.health_checks.celery",
        ...
    ]

    # optional settings, the defaults are listed
    MKN_HEALTH_CHECKS_WORKER_EVENT_LOOP_PROBE_FREQUENCY_SECONDS = 60
    MKN_HEALTH_CHECKS_WORKER_EVENT_LOOP_LIVENESS_FILE = Path("/tmp") / "celery_worker_event_loop_live"
    MKN_HEALTH_CHECKS_WORKER_READINESS_FILE = Path("/tmp") / "celery_worker_ready"


This installs the signal receiver for the worker ready/shutdown, wich affects the
presence of ``MKN_HEALTH_CHECKS_WORKER_READINESS_FILE``.

Next, in your Celery entrypoint (where you define ``app = Celery("my-celery-app")``),
add the bootstep:

.. code-block:: python
    :linenos:
    :emphasize-lines: 1,4

    from maykin_common.health_checks.celery.probes import EventLoopProbe

    app = Celery("my-project")
    app.steps["worker"].add(EventLoopProbe)
    app.autodiscover_tasks()

Which sets up the event-loop monitoring and affects the last-modified timestamp of the
``MKN_HEALTH_CHECKS_WORKER_EVENT_LOOP_LIVENESS_FILE``.

**Background information**

The health-check tooling we ship hooks into some critical phases:

#. Worker starts
#. Event loop is started, including the timer <-- we hook into the timer to check the
   event loop
#. Consumer starts
#. Consumer establishes broker connection <-- we test the connection by pinging
#. Consumer starts consuming tasks
#. Consumer is ready to process tasks <-- we hook into this signal

Celery's machinery is set up so that the whole consumer subsystem restarts on connection
loss, which should make it recover gracefully without restarting the whole worker
process.

**What we monitor**

* Event loop liveness. Periodically, we touch a heartbeat file that shows the event loop
  is still live and able to orchestrate work. The frequency can be tweaked with the
  ``MKN_HEALTH_CHECKS_WORKER_EVENT_LOOP_PROBE_FREQUENCY_SECONDS`` setting.
* Broker connection health, by sending a PING roundtrip from the worker process to
  itself. This is reliable (especially with the default preforking pool) because the
  ping control machinery lives in the main process, not in the worker processes that
  actually execute tasks, so it cannot be blocked by long-running tasks.
* Worker readiness - a readiness file is created when the worker is ready to start
  processing tasks. It is deleted again when the worker shuts down.

**What we don't monitor**

* Actual tasks execution - while it's possible in theory to create a worker-specific
  queue
  and schedule a task from itself to the worker, this brings a lot of additional
  uncertainty and complexity:

    * the task can be held up by other long-running tasks, because it will execute in a
      worker process
    * the queue name must contain the worker (host) name, which creates many keys in the
      broker. For brokers like Redis, these keys don't automatically expire and pollute
      the system. So, a periodic task and additional machinery are needed to detect stale
      exchanges and clean them up.

* Desired concurrency is available. Some tests showed that Celery seems perfectly
  capable of restarting crashed processes and maintains the desired number of worker
  processes. Unless this becomes an observed failure mode, these sort of things will not
  be added.


.. _health_checks_cli:

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

If you use Celery Beat and install the health checks (see above), you can test the
Beat liveness too:

.. code-block:: bash

    maykin-common beat-health-check --file /tmp/celery_beat_live --max-age 120

Which will exit with exit code ``0`` if the specified file exists and is last modified
within the specified number of seconds. The file path should match the value of the
``MKN_HEALTH_CHECKS_BEAT_LIVENESS_FILE`` setting.

.. tip:: Use a ``--max-age`` that's 2x the interval of your most frequently scheduled
   task. E.g. if you have a task that runs every minute, pick 120 seconds.

.. tip:: Use startup probes if possible to give Beat time to load, start and schedule
   a task for the first time.

Celery worker health checks
---------------------------

If you use Celery and install the health checks (see above), you can test their health:

.. code-block:: bash

    maykin-common worker-health-check \
        --no-skip-event-loop-liveness \
        --liveness-file /tmp/celery_worker_event_loop_live \
        --max-age 70 \
        --no-skip-ping \
        --broker redis://localhost:6379/0 \
        --worker-name celery@localhost \
        --ping-timeout 3 \
        --skip-readiness

The example options closely match the defaults.

.. tip:: Ensure you invoke this command in the worker container itself.

.. tip:: Use startup probes if possible to give the worker time to load, create the
   health check files and establish a broker connection.

The command tests different aspects and will exit with a non-zero exit code when any of
the tests fails.

Event loop liveness
~~~~~~~~~~~~~~~~~~~

Default: enabled.

The event loop liveness test checks that the last modified timestamp of
``--liveness-file`` is not older than ``--max-age``. If the event loop/timer crashes,
then the liveness file will not be touched any more and eventually become older than
the provided max age.

By default, the event loop file is touched every minute, so the default max age accounts
for some potential time drift.

Ping
~~~~

Default: enabled.

The ping roundtrip sends a ping from the worker to itself, which travels via the broker
connection. Ping failures detect potential broker connection issues which definitely
result in the worker not being able to pick up results.

The ping check requires some routing information.

``--broker``
    The address of the broker, matching the ``CELERY_BROKER`` setting. Ping needs to
    connect to the broker to send the control message. In container contexts, you will
    typically use a service or container name, e.g. ``redis://my-redis:6379/0/`` that
    uses DNS resolution.

    .. tip:: The ``localhost`` default points to the container itself. Make sure to
       provide this option explicitly.

``--worker-name``
    The worker name is taken from the envvar ``CELERY_WORKER_NAME`` if set. In
    containerized environments, the worker name usually has the shape ``<queue>@<host>``,
    where the default queue is usually named ``celery``, but projects can define
    dedicated queues/workers for queues.

    The host name is usually taken from the container ``hostname`` and matches either
    the container name on Docker engine or the pod name on Kubernetes.

    Example worker names:

    * ``celery@sparky``
    * ``celery@my-project-client-test-celery-1``
    * ``long-running@my-project-client-test-celery-1``
    * ``celery@celery-worker-554b9c67f9-c5cv4``

.. note::

    Ping requires some additional information to keep the health check lightweight
    without loading the entire application in memory, as that itself can take multiple
    seconds and can fail probe timeouts.

Readiness
~~~~~~~~~

Default: disabled.

The readiness test checks that the readiness file exists. It is created when the worker
signals that it's ready to start processing tasks, at the end of the startup phase. It
is deleted when the worker shuts down.

Absence of the readiness file can indicate that the worker failed to load the
application code. On Kubernetes with rolling deployments, you probably want to add this
as a readiness probe to prevent old pods from being stopped when the new version is
broken.

Recommended usage in a readiness probe:

    .. code-block:: bash

        maykin-common worker-health-check \
            --skip-event-loop-liveness \
            --skip-ping \
            --readiness-file /tmp/celery_worker_ready
