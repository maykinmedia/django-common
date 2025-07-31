.. _otel:

==============
Open Telemetry
==============

.. versionadded:: 0.7.0

    Added tooling for open telemetry.

`Open Telemetry`_ (OTEL) is a framework and standard to collect telemetry data from systems with
the goal of making them observable.

.. contents:: Jump to
    :local:
    :depth: 2

Telemetry data covers three major types:

* **logs** - allow you to reconstruct what and why something happened
* **metrics** - collect measurements from interesting state of the system
* **traces** - correlate units of work and establish there parent/child relationship, even
  across system boundaries

Open Telemetry has *things to say* about all this data.

.. note:: Currently, we don't use Open Telemetry tooling for logs, but projects
   typically set up `structlog <https://www.structlog.org/>`_ which get scraped and
   persisted in some monitoring backend. In the future, we will include the helpers for
   this in maykin-common.

.. note:: Tracing is set up, but not fully fleshed out yet.


Quickstart (tl;dr)
==================

Install the extra dependencies:

.. code-block:: bash

    uv pip install maykin-common[otel]

Call the initialization code:

.. code-block:: python
   :linenos:
   :caption: src/my_awesome_project/setup.py
   :emphasize-lines: 3,9,11

    import os

    from maykin_common.otel import setup_otel

    def setup_env():
        load_dotenv(...)

        os.environ.setdefault("DJANGO_SETTINGS_MODULE", ...)
        os.environ.setdefault("OTEL_SERVICE_NAME", "my-awesome-project")

        setup_otel()

        # other initialization...

Architecture
============

The essence is simple: instrumented *services* produce telemetry data that gets *exported*
to a telemetry *receiver* which ensures the data gets *persisted*. Visualisation and
monitoring tooling queries the telemetry data, making the service observable and provides
(automated) alerting options.

We have made some decisions at the library level that correspond to the following
diagram:

.. code-block:: none

                                                          +----------------+
                                                          | metrics time   |
                                                          | series storage | >---+
                                                          +----------------+     |
      +-----------+   telemetry                          ^                       | pull/query
      | Service A |-------------+                       /                        |
      +-----------+             |                      /                         |
                                |   +----------------+                           |
                                +-> |                |     +---------------+     |   +------------+
                                    | OTel Collector |---> | spans storage | >---+---| Dashboards |
                                +-> |                |     +---------------+     |   +------------+
                                |   +----------------+                           |
      +-----------+   telemetry |                     \                          |
      | Service B |-------------+                      \                         |
      +-----------+                                     v                        |
                                                        +--------------+         |
                                                        | logs storage | >-------+
                                                        +--------------+


Services
--------

The services are the applications producing telemetry data. They can be different
projects that each depend on ``maykin_common[otel]``, but they can also be different
aspects of the same project, e.g.:

* ``project`` - the django project that responds to HTTP requests
* ``project-worker-celery``, ``project-worker-highprio`` - each (dedicated) celery
  worker queue. If you have different queues set up, you each one is typially its
  own service
* ``project-flower`` - the celery monitoring service
* ``project-scheduler`` - the celery beat task scheduler

:func:`maykin_common.otel.setup_otel` sets up the application so that the produced
telemetry data gets exported using the OTLP_ protocol. Telemetry gets pushed over
``gRPC`` or ``http/protobuf`` to an endpoint that can receive OTLP data.

.. _otel_architecture_collector:

Open Telemetry receiver
-----------------------

The receivers are applications deployed/running somewhere that can accept telemetry
data in the OTLP format. They receive the telemetry from the services.

`Open Telemetry Collector`_ is a vendor-agnostic software that can receive, process and
export telemetry data. It does not have a storage of its own, but instead exports the
telemetry data according to configuration parameters.

The collector is not a hard requirement - many storage backends support ingesting OTLP
data directly, but having a centralised collector is very convenient and simplifies the
service configuration.

Storage
-------

The storage backends are applications that can receive and persist the telemetry data.

Typically, you can configure retention periods, and they used optimized databases for
the nature of the telemetry data. They're usually also the applications that expose a
query interface for the visualization tooling.

Different vendors typically compete with each other at this level. Some well known
examples are:

* Prometheus, InfluxDB, Datadog, Splunk for time-series data (typically metrics)
* Loki, Signoz, Logtail, Datadog, Splunk for logs
* Jaeger, Elastic APM, Tempo, Datadog, Splunk for distributed traces

Commercial offerings typically provide an all-in-one solution for all types of telemetry.

Dashboards/visualisation/alerting
---------------------------------

Software like Grafana and Kibana specialize in querying and displaying observability
data. Typically you can define dashboards with visualisations to explore the data that
was ingested.

This is typically done by defining queries (in ``promql`` for Prometheus, ``logql`` for
Loki etc.) which filter on labels of telemetry data (e.g. show only metrics from
production and exclude test/acceptance environments) and may combine different metrics
even, ultimately leading to easy-to-understand graphs to see what the state of the
system is/was.

Python Open Telemetry SDK
=========================

:func:`maykin_common.otel.setup_otel` calls the setup functions from the
`python SDK <https://opentelemetry.io/docs/languages/python/>`_. The toolchain is
roughly compromised of two core packages + some extensions:

* ``opentelemetry-api`` - for library authors, foundation for the SDK
* ``opentelemetry-sdk`` - the concrete implementations and project-specific integrations

``maykin-common`` uses the SDK package to provide an opinionated, pre-configured ready
to use setup. You should not have a need to override this.

If/when we define metrics in other modules of maykin-common, you can only use the API
exposed from ``opentelemetry-api``. Usage of the ``opentelemetry-sdk`` package is
restricted to the :mod:`maykin_common.otel` module.

There are additional contrib packages with library/framework specific instrumentation,
like the ``opentelemetry-instrumentation-django`` package. This has all been
pre-configured in maykin-common.

The `examples <https://opentelemetry-python.readthedocs.io/en/stable/examples/>`__
documentation can be interesting.

.. todo:: handle https://opentelemetry-python.readthedocs.io/en/stable/examples/fork-process-model/README.html

Defining metrics
----------------

By default, the wsgi instrumentation (set up via the Django instrumentation) captures
spans of request/response cycles. It also captures request metrics, like the duration,
annotated with context like the path, method etc.

Application developers can provide a lot of extra value by defining and tracking their
application-specific metrics, because you have the context of the application and know
which data/information is interesting.

Defining and using a metric is pretty straightforward:

.. code-block:: python
   :linenos:
   :emphasize-lines: 4,6-9,16

    # in metrics.py
    from opentelemetry import metrics

    meter = metrics.get_meter("my_awesome_project.my_module")

    export_counter = meter.create_counter(
        "exports",
        description="The number of exports triggered by users",
    )


    # in views.py
    from .metrics import export_counter

    def export(request, pk: int):
        export_counter.add(1, {"pk": pk, "user": request.user.username})
        return _create_export(pk=pk)


.. note::

    Other packages that we maintain can also opt-in to defining and tracking metrics in
    the future.


Best practices
==============

**Service name vs. deployment environment**

Don't put the deployment target (prod, acc, test...) in the service name, as that leads
to higher cardinality labels which has a negative impact on storage and query
performance. Instead, make sure to properly define the ``ENVIRONMENT`` Django setting,
which is also used by our Sentry SDK initialisation.

**Use different service names for different logical units**

The Django application (deployed with uwsgi, for example) is a different logical unit
than the celery worker processing background tasks. In fact, even different task queues
(e.g. high/low prio) are different units, and deserve their own easy-to-identify
service name.

.. tip:: Define ``OTEL_SERVICE_NAME`` as environment variable in the entrypoint shell
   scripts like ``bin/docker_start.sh`` and ``bin/celery_worker.sh``:

   .. code-block:: bash
      :caption: bin/celery_worker.sh

      QUEUE=${CELERY_WORKER_QUEUE:=celery}
      WORKER_NAME=${CELERY_WORKER_NAME:="${QUEUE}"@%n}

      # Set defaults for OTEL
      : "${OTEL_SERVICE_NAME:=my-project-worker-"${QUEUE}"}"

**Extract resource attributes for containers**

Usually our applications are deployed in one of two ways:

* on Kubernetes
* on (virtual) servers with Docker engine

For the docker engine case, we can extract additional resource attributes by setting
``_OTEL_ENABLE_CONTAINER_RESOURCE_DETECTOR=true``. Don't do this on Kubernetes, as it
may lead to conflicting information.

On Kubernetes, the recommendation is to enable the k8sattributeprocessor_ when deploying
the :ref:`Collector <otel_architecture_collector>`.

**Authentication**

The Collector may be API key or username/password protected. In that case, you can pass
additional headers via the standardized environment variable:

.. code-block:: bash

    OTEL_EXPORTER_OTLP_HEADERS="Authorization=Basic <base64-username:password>"

.. _Open Telemetry: https://opentelemetry.io/
.. _OTLP: https://opentelemetry.io/docs/specs/otlp/
.. _Open Telemetry Collector: https://opentelemetry.io/docs/collector/
.. _k8sattributeprocessor: https://opentelemetry.io/docs/platforms/kubernetes/collector/components/#kubernetes-attributes-processor
