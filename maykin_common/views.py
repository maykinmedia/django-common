from django import http
from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.template import TemplateDoesNotExist, loader
from django.views.csrf import (
    CSRF_FAILURE_TEMPLATE_NAME,
    csrf_failure as original_csrf_failure,
)
from django.views.decorators.csrf import requires_csrf_token
from django.views.defaults import ERROR_500_TEMPLATE_NAME

from maykin_common.settings import get_setting


@requires_csrf_token
def server_error(
    request: HttpRequest, template_name: str = ERROR_500_TEMPLATE_NAME
) -> http.HttpResponseServerError:
    """
    500 error handler.
    """

    try:
        template = loader.get_template(template_name)
    except TemplateDoesNotExist:
        if template_name != ERROR_500_TEMPLATE_NAME:
            # Reraise if it's a missing custom template.
            raise
        return http.HttpResponseServerError(
            b"<h1>Server Error (500)</h1>", content_type="text/html"
        )
    context = {"request": request}
    return http.HttpResponseServerError(template.render(context))


def csrf_failure(
    request: HttpRequest,
    reason: str = "",
    template_name: str = CSRF_FAILURE_TEMPLATE_NAME,
) -> HttpResponse:
    """
    Catch CSRF failure when trying to login a second time, when already logged
    in, by redirecting to the LOGIN_REDIRECT_URL.
    """
    if request.path in get_setting("LOGIN_URLS") and request.user.is_authenticated:
        return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)
    return original_csrf_failure(request, reason=reason, template_name=template_name)
