from collections.abc import Callable, Generator

from django.core.cache import BaseCache, caches
from django.http import HttpRequest, HttpResponse
from django.http.response import HttpResponseBase
from django.test import RequestFactory

import pytest
from csp.constants import SELF

from maykin_common.csp.cache import get_cache
from maykin_common.csp.middleware import CSPMiddleware


@pytest.fixture(autouse=True)
def clear_csp_cache() -> Generator[None, None, None]:
    """
    The directives are cached process-wide, so leaking them between tests is lethal.
    """
    get_cache().clear()
    yield
    get_cache().clear()


@pytest.fixture()
def policy(settings) -> None:
    """
    Configure a minimal enforced policy, and no report-only one.
    """
    settings.CONTENT_SECURITY_POLICY = {"DIRECTIVES": {"default-src": [SELF]}}
    settings.CONTENT_SECURITY_POLICY_REPORT_ONLY = None


@pytest.fixture()
def dedicated_cache(settings) -> Generator[BaseCache, None, None]:
    """
    Point the CSP cache at an alias of its own, and hand that cache back.
    """
    settings.CACHES = {
        **settings.CACHES,
        "csp": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "csp-directives",  # unique so it doesn't share storage
        },
    }
    settings.MKN_CSP_CACHE_ALIAS = "csp"

    cache = caches["csp"]
    cache.clear()
    yield cache
    cache.clear()


def ok_view(request: HttpRequest) -> HttpResponse:
    return HttpResponse("ok")


@pytest.fixture()
def apply_middleware():
    """
    Run a view through the middleware and hand back the processed response.
    """

    def _apply(
        view: Callable[[HttpRequest], HttpResponse] = ok_view,
        path: str = "/",
        middleware_class: type = CSPMiddleware,
    ) -> HttpResponseBase:
        middleware = middleware_class(view)
        response = middleware(RequestFactory().get(path))
        # MiddlewareMixin.__call__ may return an awaitable, but only for an async
        # get_response, which this is not
        assert isinstance(response, HttpResponseBase)
        return response

    return _apply
