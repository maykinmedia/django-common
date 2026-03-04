"""
Helpers related to structured (JSON) logging.

Maykin projects use ``structlog`` and the Django integration to get structured logging.
"""

from datetime import UTC, datetime

from django.conf import settings

from structlog.typing import EventDict, WrappedLogger

try:
    import uwsgi  # pyright: ignore[reportMissingModuleSource] uwsgi magic...
except ImportError:
    uwsgi = None


class LogVars:
    """
    A WSGI-middleware to inject log variables for uwsgi.

    It makes the following log variables available to uwsgi:

    * ``iso8601timestamp``: ISO-8601 formatted 'now' timestamp.

    Usage::
        from django.core.wsgi import get_wsgi_application

        application = LogVars(get_wsgi_application())
    """

    def __init__(self, application):
        self.application = application

    def __call__(self, environ, start_response):
        if uwsgi is not None:
            now = datetime.now(tz=UTC)
            uwsgi.set_logvar("iso8601timestamp", now.isoformat())
        return self.application(environ, start_response)


def drop_user_agent_in_dev(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
):  # pragma: no cover
    if settings.DEBUG and "user_agent" in event_dict:
        del event_dict["user_agent"]
    return event_dict
