from opentelemetry.context import Context
from opentelemetry.sdk.trace import Span, SpanProcessor


class CustomAttributeSpanProcessor(SpanProcessor):
    def on_start(self, span: Span, parent_context: Context | None = None) -> None:
        """
        Determine type and subtype based on the active instrumentation library.
        """
        if span.attributes and span.attributes.get("span.type"):
            return

        instrumentation_scope = span.instrumentation_scope
        library_name = (
            instrumentation_scope.name.lower() if instrumentation_scope else ""
        )

        span_type: str
        span_subtype: str

        match library_name:
            case "opentelemetry.instrumentation.redis":
                span_type = "db"
                span_subtype = "redis"
            case "opentelemetry.instrumentation.psycopg":
                span_type = "db"
                span_subtype = "postgresql"
            case "opentelemetry.instrumentation.django":
                span_type = (
                    "web"
                    if span.attributes and span.attributes.get("http.method")
                    else "app"
                )
                span_subtype = "django"
            case "opentelemetry.instrumentation.requests":
                span_type = "external"
                span_subtype = "http"
            case "opentelemetry.instrumentation.celery":
                span_type = "async"
                span_subtype = "celery"
            case _:
                span_type = "unknown"
                span_subtype = "unknown"

        span.set_attribute("span.type", span_type)
        span.set_attribute("span.subtype", span_subtype)
