import os
from typing import Literal, assert_never
from uuid import uuid4

from django.core.exceptions import ImproperlyConfigured

from opentelemetry import metrics, trace
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.sdk.environment_variables import OTEL_EXPORTER_OTLP_PROTOCOL
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import (
    DEPLOYMENT_ENVIRONMENT,
    SERVICE_INSTANCE_ID,
    SERVICE_VERSION,
    Resource,
    get_aggregated_resources,
)
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from maykin_common.settings import get_setting

__all__ = [
    "setup_otel",
]

# The Python SDK only supports gRPC and HTTP/protobuf. HTTP/json is not supported.
type ExportProtocol = Literal["grpc", "http/protobuf"]

DEFAULT_PROTOCOL: ExportProtocol = "grpc"

_OTEL_INITIALIZED: bool = False


def setup_otel() -> None:
    """
    Initialize the Open Telemetry machinery.

    This is an application-global hook to configure the Open Telemetry machinery:

    * set up the metadata about the resource being monitored
    * initialize the metrics processor and exporter
    * initialize the traces processor and exporter
    * instrument the python code so that metrics and traces are captured

    The exports are responsible for shipping the telemetry data to an endpoint that
    supports OpenTelemetryProtocol (OTLP), either over gRPC or HTTP/protobuf protocols.
    Often, this will be an OpenTelemetry Collector running somewhere.

    The Python OpenTelemetery SDK supports the standardized environment variables,
    see the `environment variables reference`.

    Part of the SDK initialization process is starting a background thread to
    periodically ship the telemetry to the configured endpoint.

    .. _`environment variables reference`: https://opentelemetry.io/docs/specs/otel/configuration/sdk-environment-variables/
    """
    global _OTEL_INITIALIZED
    if _OTEL_INITIALIZED:
        return

    if "OTEL_SERVICE_NAME" not in os.environ:
        raise ImproperlyConfigured(
            "You must define the 'OTEL_SERVICE_NAME' environment variable."
        )

    # service name is guaranteed to be set through envvars

    resource = Resource.create(
        attributes={
            SERVICE_VERSION: get_setting("RELEASE") or "",
            SERVICE_INSTANCE_ID: str(uuid4()),
            DEPLOYMENT_ENVIRONMENT: get_setting("ENVIRONMENT") or "",
        }
    )
    resource = aggregate_resource(resource)

    OTLPMetricExporter, OTLPSpanExporter = load_exporters()

    tracer_provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(OTLPSpanExporter())
    tracer_provider.add_span_processor(processor)
    trace.set_tracer_provider(tracer_provider)

    reader = PeriodicExportingMetricReader(OTLPMetricExporter())
    meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(meter_provider)

    # set up instrumenters that (usually) monkeypatch modules or inject the right
    # wrappers/middleware etc.
    DjangoInstrumentor().instrument()

    _OTEL_INITIALIZED = True


def load_exporters():
    # TODO: replace with `config` helper once it's added to this library
    protocol: ExportProtocol = os.getenv(  # pyright: ignore[reportAssignmentType]
        OTEL_EXPORTER_OTLP_PROTOCOL, default=DEFAULT_PROTOCOL
    )
    match protocol:
        case "grpc":
            from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
                OTLPMetricExporter,
            )
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )

            return (OTLPMetricExporter, OTLPSpanExporter)
        case "http/protobuf":
            from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
                OTLPMetricExporter,
            )
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                OTLPSpanExporter,
            )

            return (OTLPMetricExporter, OTLPSpanExporter)
        case _:
            assert_never(protocol)


def aggregate_resource(resource: Resource) -> Resource:
    # TODO: replace with `config` helper once it's added to this library
    _enable_resource_detector = (
        os.getenv("_OTEL_ENABLE_CONTAINER_RESOURCE_DETECTOR", default="false")
        .lower()
        .strip()
        == "true"
    )
    if not _enable_resource_detector:
        return resource

    from opentelemetry.resource.detector.containerid import ContainerResourceDetector

    return get_aggregated_resources(
        detectors=[ContainerResourceDetector()], initial_resource=resource
    )
