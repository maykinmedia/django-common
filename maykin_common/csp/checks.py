"""
System checks guarding against CSP middleware misconfiguration.

These are registered when :mod:`maykin_common.csp` is added to ``INSTALLED_APPS``.
"""

from collections.abc import Sequence

from django.apps import AppConfig
from django.conf import settings
from django.core.checks import Error, Warning, register
from django.utils.module_loading import import_string

from ..settings import get_setting
from .middleware import DatabaseDirectivesMixin

UPSTREAM_MIDDLEWARE = "csp.middleware.CSPMiddleware"
OUR_MIDDLEWARE = "maykin_common.csp.middleware.CSPMiddleware"


def _merges_database_directives(path: str) -> bool:
    """
    Check whether the middleware at ``path`` applies the database-managed directives.

    Resolving the class rather than comparing the dotted path means a project that
    mixes :class:`~maykin_common.csp.middleware.DatabaseDirectivesMixin` into its own
    middleware is recognized too, wherever that middleware lives.
    """
    try:
        middleware = import_string(path)
    except ImportError:
        # Django reports unimportable middleware with a better error of its own when
        # it builds the middleware chain.
        return False
    return isinstance(middleware, type) and issubclass(
        middleware, DatabaseDirectivesMixin
    )


@register
def check_csp_cache_timeout(app_configs: Sequence[AppConfig] | None, **kwargs):
    """
    Check that the cache timeout is a number of seconds we can work with.

    Caching indefinitely (``None``) is rejected rather than passed on to the cache
    backend. The timeout is what lets the cache recover from writes that do not go
    through the invalidation signals, and a per-process cache would otherwise keep
    serving a directive that has since been deleted for as long as the process lives.
    """
    timeout = get_setting("MKN_CSP_CACHE_TIMEOUT")

    # bool is a subclass of int, and neither True nor False means anything sensible
    # as a number of seconds
    valid = isinstance(timeout, int) and not isinstance(timeout, bool) and timeout >= 0
    if valid:
        return []

    return [
        Error(
            "MKN_CSP_CACHE_TIMEOUT must be a whole number of seconds, "
            f"got {timeout!r}.",
            hint=(
                "Use a positive number of seconds, or 0 to disable caching entirely. "
                "Caching indefinitely is not supported."
            ),
            id="maykin.E001",
        )
    ]


@register
def check_csp_middleware_installed(app_configs: Sequence[AppConfig] | None, **kwargs):
    """
    Check that a middleware merging the database-managed directives is installed.

    Without it the ``CSPSetting`` records are never applied, which is easy to miss
    because the CSP header itself looks perfectly fine.
    """
    middleware = tuple(getattr(settings, "MIDDLEWARE", None) or ())

    if any(_merges_database_directives(path) for path in middleware):
        return []

    if UPSTREAM_MIDDLEWARE in middleware:
        return [
            Warning(
                f"'{UPSTREAM_MIDDLEWARE}' is installed, but it ignores the CSP "
                "directives managed in the database.",
                hint=(
                    f"Replace it with '{OUR_MIDDLEWARE}' in MIDDLEWARE, or mix "
                    "'maykin_common.csp.middleware.DatabaseDirectivesMixin' into your "
                    "own CSP middleware."
                ),
                id="maykin.W003",
            )
        ]

    return [
        Warning(
            "'maykin_common.csp' is installed, but no CSP middleware was found in "
            "MIDDLEWARE.",
            hint=(
                f"Add '{OUR_MIDDLEWARE}' to MIDDLEWARE, otherwise no "
                "Content-Security-Policy header is sent at all."
            ),
            id="maykin.W004",
        )
    ]
