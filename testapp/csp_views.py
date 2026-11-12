"""
A debug page showing the CSP headers the middleware produces for a request.

The middleware is deliberately absent from this project's global ``MIDDLEWARE``,
because it reads from the database on every response and that would force database
access on every test that renders a view. It is applied to this one view instead, so
the behaviour can still be exercised by hand against a running server.
"""

from pprint import pformat

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.http.response import HttpResponseBase
from django.shortcuts import render

from csp.constants import HEADER, HEADER_REPORT_ONLY

from maykin_common.csp.cache import get_directives
from maykin_common.csp.middleware import CSPMiddleware

CSP_HEADERS = (HEADER, HEADER_REPORT_ONLY)


def _probe_headers(request: HttpRequest) -> list[tuple[str, str]]:
    """
    Run the middleware over an empty response to see which headers it would set.
    """
    middleware = CSPMiddleware(lambda _request: HttpResponse(b""))
    probed = middleware(request)
    # MiddlewareMixin.__call__ may return an awaitable, but only for an async
    # get_response, which this is not
    assert isinstance(probed, HttpResponseBase)
    return [(name, probed[name]) for name in CSP_HEADERS if name in probed]


def csp_debug_view(request: HttpRequest) -> HttpResponse:
    headers = _probe_headers(request)
    response = render(
        request,
        "testapp/csp.html",
        {
            "headers": headers,
            "enforced": pformat(getattr(settings, "CONTENT_SECURITY_POLICY", None)),
            "report_only": pformat(
                getattr(settings, "CONTENT_SECURITY_POLICY_REPORT_ONLY", None)
            ),
            "from_database": pformat(get_directives()),
        },
    )
    # set them on the real response too, so the browser's dev tools agree with the page
    for name, value in headers:
        response[name] = value
    return response
