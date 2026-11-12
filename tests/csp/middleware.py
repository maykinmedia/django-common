"""
A custom CSP middleware living outside the ``maykin_common.csp`` namespace.

This is the pattern the documentation recommends for projects that already use another
django-csp middleware.
"""

from csp.contrib.rate_limiting import RateLimitedCSPMiddleware

from maykin_common.csp.middleware import DatabaseDirectivesMixin


class CustomCSPMiddleware(DatabaseDirectivesMixin, RateLimitedCSPMiddleware):
    pass


class NotAMiddleware:
    pass
