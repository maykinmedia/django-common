import pytest
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from maykin_common.otel.processors import CustomAttributeSpanProcessor


@pytest.fixture
def span_exporter():
    return InMemorySpanExporter()


@pytest.fixture(autouse=True)
def reset_span_exporter(span_exporter):
    """Automatically clear span exporter after each test"""
    yield
    span_exporter.clear()


@pytest.mark.parametrize(
    "instrumentor,expected",
    [
        ("opentelemetry.instrumentation.redis", ("db", "redis")),
        ("opentelemetry.instrumentation.psycopg", ("db", "postgresql")),
        ("opentelemetry.instrumentation.requests", ("external", "requests")),
        ("opentelemetry.instrumentation.celery", ("async", "celery")),
        ("new", ("unknown", "unknown")),
    ],
)
def test_processor_libs(span_exporter, instrumentor: str, expected: tuple[str, str]):
    provider = TracerProvider()
    provider.add_span_processor(CustomAttributeSpanProcessor())
    provider.add_span_processor(SimpleSpanProcessor(span_exporter))

    # Create tracer with redis instrumentation scope
    tracer = provider.get_tracer(instrumentor)

    with tracer.start_as_current_span("some-span"):
        pass

    spans = span_exporter.get_finished_spans()
    span = spans[0]

    span_type = span.attributes.get("span.type")
    span_subtype = span.attributes.get("span.subtype")
    assert span_type, span_subtype == expected


def test_processor_django(span_exporter):
    provider = TracerProvider()
    provider.add_span_processor(CustomAttributeSpanProcessor())
    provider.add_span_processor(SimpleSpanProcessor(span_exporter))

    tracer = provider.get_tracer("opentelemetry.instrumentation.django")

    with tracer.start_as_current_span("GET /forms", attributes={"http.method": "GET"}):
        pass

    spans = span_exporter.get_finished_spans()
    span = spans[0]

    assert span.attributes.get("span.type") == "web"
    assert span.attributes.get("span.subtype") == "django"


def test_processor_custom(span_exporter):
    provider = TracerProvider()
    provider.add_span_processor(CustomAttributeSpanProcessor())
    provider.add_span_processor(SimpleSpanProcessor(span_exporter))

    tracer = provider.get_tracer(__name__)

    with tracer.start_as_current_span(
        "custom_operation",
        attributes={"span.type": "custom-type", "span.subtype": "custom-subtype"},
    ):
        pass

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1

    span = spans[0]

    assert span.attributes.get("span.type") == "custom-type"
    assert span.attributes.get("span.subtype") == "custom-subtype"
