from django.http import HttpRequest, HttpResponse
from django.urls import path
from django.views import View

from maykin_common.throttling import IPThrottleMixin, ThrottleMixin


class BaseView(View):
    def _handler(self, request: HttpRequest, *args, **kwargs):
        return HttpResponse("ok")

    get = _handler
    head = _handler
    post = _handler
    put = _handler
    patch = _handler
    delete = _handler
    options = _handler


class ThrottleView(ThrottleMixin, BaseView):
    pass


class IPThrottleView(IPThrottleMixin, BaseView):
    pass


class ThrottleResponseOverride(ThrottleView):
    throttle_403 = True

    def handle_rate_limit_exceeded(self):
        return HttpResponse("rate limit exceeded", status=499)


urlpatterns = [
    path(
        "throttle/1/second",
        ThrottleView.as_view(
            throttle_visits=1,
            throttle_period=1,
            throttle_methods=("post",),
        ),
    ),
    path(
        "throttle/10/second",
        ThrottleView.as_view(
            throttle_visits=10,
            throttle_period=1,
            throttle_methods=("post",),
        ),
    ),
    path(
        "throttle/all",
        ThrottleView.as_view(
            throttle_visits=0,
            throttle_period=1,
            throttle_methods="all",
        ),
    ),
    path(
        "throttle/1/second/custom-handling",
        ThrottleResponseOverride.as_view(
            throttle_visits=1,
            throttle_period=1,
            throttle_methods=("post",),
        ),
    ),
    path(
        "ip-throttle/1/minute",
        IPThrottleView.as_view(
            throttle_visits=1,
            throttle_period=60,
            throttle_methods=("post",),
        ),
    ),
]
