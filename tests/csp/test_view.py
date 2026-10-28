"""
Tests for the test project's /csp/ debug page.

It is a manual debugging aid, but it is also the only place the middleware runs
against the project's real settings, so it is worth keeping honest.
"""

from django.core.cache import BaseCache, caches
from django.test import Client
from django.utils.html import escape

import pytest
from csp.constants import HEADER

from maykin_common.csp.cache import CACHE_KEY
from maykin_common.csp.models import CSPSetting

pytestmark = [pytest.mark.django_db]


def parse_policy(header: str) -> dict[str, str]:
    """
    Parse a CSP header into a directive mapping.

    django-csp builds the header by iterating a set, so the directives come out in a
    different order from one process to the next and the header cannot be compared as
    a string. The values within a directive are ordered.
    """
    parsed = {}
    for directive in header.split(";"):
        name, _, value = directive.strip().partition(" ")
        parsed[name] = value
    return parsed


def test_page_reports_the_header_it_sets(client: Client):
    CSPSetting.objects.create(directive="img-src", value="https://analytics.example")

    response = client.get("/csp/")

    assert response.status_code == 200
    # the settings configure default-src and img-src; the database adds to img-src
    assert parse_policy(response[HEADER]) == {
        "default-src": "'self'",
        "img-src": "'self' https://cdn.example.com https://analytics.example",
    }
    # the page shows the very header it just set, escaped for HTML
    assert escape(response[HEADER]) in response.content.decode()


def test_page_renders_without_any_database_entries(client: Client):
    response = client.get("/csp/")

    assert response.status_code == 200
    assert parse_policy(response[HEADER]) == {
        "default-src": "'self'",
        "img-src": "'self' https://cdn.example.com",
    }


def test_a_dedicated_cache_alias_is_used_through_a_real_request(
    dedicated_cache: BaseCache, client: Client
):
    CSPSetting.objects.create(directive="img-src", value="https://analytics.example")

    response = client.get("/csp/")

    assert parse_policy(response[HEADER])["img-src"] == (
        "'self' https://cdn.example.com https://analytics.example"
    )
    assert dedicated_cache.get(CACHE_KEY) == {"img-src": ["https://analytics.example"]}
    assert caches["default"].get(CACHE_KEY) is None
