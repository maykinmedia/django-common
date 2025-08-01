from django.core.exceptions import ImproperlyConfigured

import pytest
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
    OTLPMetricExporter as GRPCOTLPMetricExporter,
)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter as GRPCOTLPSpanExporter,
)
from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
    OTLPMetricExporter as HttpOTLPMetricExporter,
)
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter as HttpOTLPSpanExporter,
)
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.metrics import NoOpMeterProvider, set_meter_provider
from opentelemetry.sdk.metrics.export import MetricExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import SpanExporter
from opentelemetry.trace import NoOpTracerProvider, set_tracer_provider

from maykin_common.otel import (
    ExportProtocol,
    aggregate_resource,
    load_exporters,
    setup_otel,
)


def _reset_otel():
    # This code is absolutely filthy, but there does not appear to be another fork-safe
    # way to test this behaviour.
    from opentelemetry.metrics._internal import _METER_PROVIDER_SET_ONCE
    from opentelemetry.trace import _TRACER_PROVIDER_SET_ONCE

    _METER_PROVIDER_SET_ONCE._done = False
    _TRACER_PROVIDER_SET_ONCE._done = False

    tracer_provider = trace.get_tracer_provider()
    if hasattr(tracer_provider, "shutdown"):
        tracer_provider.shutdown()  # pyright: ignore[reportAttributeAccessIssue]

    meter_provider = metrics.get_meter_provider()
    if hasattr(meter_provider, "shutdown"):
        meter_provider.shutdown()  # pyright: ignore[reportAttributeAccessIssue]

    DjangoInstrumentor().uninstrument()

    # reset to noop
    set_tracer_provider(NoOpTracerProvider())
    set_meter_provider(NoOpMeterProvider())

    _METER_PROVIDER_SET_ONCE._done = False
    _TRACER_PROVIDER_SET_ONCE._done = False


@pytest.fixture(autouse=True)
def setup_teardown(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OTEL_SERVICE_NAME", "maykin-common-tests")
    _reset_otel()

    yield

    _reset_otel()


def test_requires_OTEL_SERVICE_NAME_envvar(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("OTEL_SERVICE_NAME")

    with pytest.raises(
        ImproperlyConfigured,
        match="You must define the 'OTEL_SERVICE_NAME' environment variable.",
    ):
        setup_otel()


def test_initializer_runs_without_raising():
    try:
        setup_otel()
    except Exception:
        pytest.fail("Expected 'setup_otel' to complete without crashing")


def test_initializer_can_run_multiple_times_without_problems(
    caplog: pytest.LogCaptureFixture,
):
    caplog.set_level("WARNING", logger="opentelemetry")

    setup_otel()
    assert len(caplog.records) == 0

    # run it again
    setup_otel()
    assert len(caplog.records) == 0, (
        "Running the initialization multiple times must not produce warnings"
    )


@pytest.mark.parametrize(
    "protocol,expected",
    [
        ("grpc", (GRPCOTLPMetricExporter, GRPCOTLPSpanExporter)),
        ("http/protobuf", (HttpOTLPMetricExporter, HttpOTLPSpanExporter)),
    ],
)
def test_load_exporters(
    monkeypatch: pytest.MonkeyPatch,
    protocol: ExportProtocol,
    expected: tuple[
        type[MetricExporter],
        type[SpanExporter],
    ],
):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_PROTOCOL", protocol)
    expected_metric_exporter_cls, expected_span_exporter_cls = expected

    metric_exporter_cls, span_exporter_cls = load_exporters()

    assert metric_exporter_cls is expected_metric_exporter_cls
    assert span_exporter_cls is expected_span_exporter_cls


def test_load_exporters_raises_for_unknown_protocol(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_PROTOCOL", "invalid")

    with pytest.raises(AssertionError):
        load_exporters()


def test_aggregate_resource_adds_container_detector(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("_OTEL_ENABLE_CONTAINER_RESOURCE_DETECTOR", "True")
    monkeypatch.setattr(
        "opentelemetry.resource.detector.containerid._get_container_id", lambda: "1234"
    )
    initial_resource = Resource(attributes={})

    aggregated_resource = aggregate_resource(initial_resource)

    assert "container.id" in aggregated_resource.attributes
    assert aggregated_resource.attributes["container.id"] == "1234"
