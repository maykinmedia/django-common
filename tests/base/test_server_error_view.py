from uuid import uuid4

from django.template import TemplateDoesNotExist
from django.test import RequestFactory

import pytest

from maykin_common.views import server_error


def test_error_view_plain_request_uses_500_template(rf: RequestFactory):
    request = rf.get("/irrelevant")

    response = server_error(request)

    assert response.status_code == 500
    assert b"We have been automatically notified" in response.content


def test_error_view_with_request_nonce(rf: RequestFactory):
    request = rf.get("/irrelevant")
    # set via django-csp, if enabled
    request.csp_nonce = "unique-nonce"  # type: ignore

    response = server_error(request)

    assert b'<style type="text/css" nonce="unique-nonce"' in response.content


def test_error_view_with_sentry_reference(rf: RequestFactory):
    request = rf.get("/irrelevant")
    # set by sentry-sdk when enabled
    request.sentry = {"id": "unique-sentry-id"}  # type: ignore

    response = server_error(request)

    assert b"unique-sentry-id" in response.content


def test_it_raises_with_non_default_template(rf: RequestFactory):
    request = rf.post("/irrelevant")

    with pytest.raises(TemplateDoesNotExist):
        server_error(request, template_name=str(uuid4()))


def test_fallback_if_500_template_cannot_be_loaded(
    rf: RequestFactory,
    monkeypatch: pytest.MonkeyPatch,
):
    def _raise(*args, **kwargs):
        raise TemplateDoesNotExist("mocked error")

    monkeypatch.setattr("django.template.loader.get_template", _raise)
    request = rf.patch("/irrelevant")

    response = server_error(request)

    assert response.status_code == 500
    assert response.content == b"<h1>Server Error (500)</h1>"
