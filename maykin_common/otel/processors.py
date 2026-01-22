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

        if "redis" in library_name:
            span_type = "db"
            span_subtype = "redis"

        elif "psycopg" in library_name:
            span_type = "db"
            span_subtype = "postgresql"

        elif "django" in library_name:
            span_type = (
                "web"
                if span.attributes and span.attributes.get("http.method")
                else "app"
            )
            span_subtype = "django"

        elif "requests" in library_name:
            span_type = "external"
            span_subtype = "http"

        elif "celery" in library_name:
            span_type = "async"
            span_subtype = "celery"

        else:
            span_type = "unknown"
            span_subtype = "unknown"

        span.set_attribute("span.type", span_type)
        span.set_attribute("span.subtype", span_subtype)
