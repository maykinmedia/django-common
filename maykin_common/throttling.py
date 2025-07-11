"""
Provide mixins for throttling/rate limiting in views.

Depends on ``django-axes``.

.. todo:: Decouple from django-axes - make IP address getter function configurable.
"""

import warnings
from collections.abc import Container
from time import time
from typing import Literal

from django.core.cache import caches
from django.core.cache.backends.base import BaseCache
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.http import HttpRequest, HttpResponse, HttpResponseBase

from axes.helpers import get_client_ip_address

ONE_MINUTE = 60
ONE_HOUR = ONE_MINUTE * 60


class ThrottleMixin:
    """
    A very simple throttling implementation with, hopefully, sane defaults.

    You can specifiy the amount of visits (``throttle_visits``) a view can get,
    for a specific period (in seconds) ``throttle_period``.
    """

    throttle_visits = 100
    """
    Number of allowed visits in the specified period.
    """

    throttle_period = ONE_HOUR
    """
    Period/time window (in seconds) in which the visits are counted.

    Visits older than this window are discarded.
    """

    throttle_name = "default"
    """
    Identifier for the throttle, used in the cache key.
    """

    throttle_cache = "default"
    """
    Name of the cache (in ``settings.CACHES``) to use to track visits.

    .. note:: Ensure you use a globally shared cached. Local memory caches are limited
       to their respective Python process and not aware of other processes/caches.
    """

    throttle_403 = False
    """
    Marker to opt-in to return 403 responses.

    DeprecationWarning - implement :meth:`ThrottleMixin.handle_rate_limit_exceeded`
    instead or use the default 429 response.

    .. versionchanged:: 0.7.0

        The default is changed to return 429 instead of 403 and the attribute has been
        deprecated.
    """

    # get and options should always be fast. By default
    # do not throttle them.
    throttle_methods: Container[str] | Literal["all"] = (
        "post",
        "put",
        "patch",
        "delete",
        "head",
        "trace",
    )

    request: HttpRequest

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        if cls.throttle_403:
            warnings.warn(
                f"'{cls.__name__}.throttle_403' attribute is deprecated - consider "
                "returning a HTTP 429 response instead.",
                category=DeprecationWarning,
                stacklevel=2,
            )

    def get_throttle_cache(self) -> BaseCache:
        return caches[self.throttle_cache]

    def get_throttle_identifier(self) -> str:
        user = self.request.user
        return str(user.pk)

    def _get_throttle_window(self):
        """
        Calculate the start of the window based on the current time.

        This uses the current time (unix timestamp) as input and looks up the most
        recent moment when a non-completed block of ``trottle_period`` started. It is
        used as input in the cache key, meaning that once ``throttle_period`` has
        elapsed, the throttle quota is fully reinstated.

        Effectively, throttle intervals are fixed and not a sliding window.
        """
        current_time = int(time())
        return current_time - (current_time % self.throttle_period)

    def _get_num_visits_in_window(self) -> int:
        cache = self.get_throttle_cache()
        cache_key = (
            f"throttling_{self.get_throttle_identifier()}_"
            f"{self.throttle_name}_{self._get_throttle_window()}"
        )

        added = cache.add(cache_key, value=1, timeout=self.throttle_period)
        if (
            added
        ):  # key added, we had no counter before -> one visit returned and stored
            return 1

        try:
            return cache.incr(cache_key)
        except ValueError:  # XXX: when does this happen?
            return 1

    def should_be_throttled(self) -> bool:
        """
        Determine if throttling is enabled for the request.
        """
        if self.throttle_methods == "all":
            return True
        assert isinstance(self.request.method, str)
        return self.request.method.lower() in self.throttle_methods

    def check_rate_limit_exceeded(self) -> bool:
        """
        Determine if the rate limit is exceeded or not.

        The limit is considered exceeded when:

        * the request matches the conditions to be throttled
        * the amount of visits in the time window exceeds the maximum allowed
        """
        enabled = self.should_be_throttled()
        # deliberate method call after the *and* to benefit from short-circuiting and
        # avoid hitting the cache if it's not needed
        return enabled and self._get_num_visits_in_window() > self.throttle_visits

    def handle_rate_limit_exceeded(self) -> HttpResponseBase:
        """
        Return the appropriate response for throttled requests.

        Override this to customize behaviour. By default, an HTTP 429 response is
        returned.
        """
        if self.throttle_403:
            raise PermissionDenied()
        return HttpResponse("rate limit exceeded", status=429)

    def dispatch(self, request, *args, **kwargs):
        if self.check_rate_limit_exceeded():
            return self.handle_rate_limit_exceeded()
        return super().dispatch(request, *args, **kwargs)  # pyright:ignore[reportAttributeAccessIssue]


class IPThrottleMixin(ThrottleMixin):
    """
    Same behavior as ThrottleMixin except it limits the amount of tries
    per IP-address a user can access a certain view.
    """

    def get_throttle_identifier(self):
        ip_address = get_client_ip_address(self.request)
        if not ip_address:
            raise ImproperlyConfigured(
                "Could not determine IP address. "
                "Check your reverse proxy configuration."
            )
        return ip_address
