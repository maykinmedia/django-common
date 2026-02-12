from django.contrib import admin
from django.test import Client
from django.urls import include, path

import pytest

urlpatterns = [
    # admin is required on django 4.2 for the technical debug info, because we have
    # settings that refer to the ``admin:index`` urls.
    path("admin/", admin.site.urls),
    path("", include("maykin_common.health_checks.urls")),
]

pytestmark = [
    pytest.mark.urls("tests.health_checks.test_endpoints"),
    pytest.mark.django_db,
]


def test_generic_healthz_endpoint(client: Client):
    response = client.get("/_healthz/")

    # there are pending migrations because of the added health check installed apps,
    # which results in HTTP 500 response (as intended).
    assert response.status_code in (200, 500)


def test_livez_subset_endpoint(client: Client):
    response = client.get("/_healthz/livez/")

    # This is not supposed to perform any checks at all with the defaults, so a 200
    # is expected, despite there being pending migrations.
    assert response.status_code == 200


def test_readyz_subset_endpoint(client: Client):
    response = client.get("/_healthz/readyz/")

    # there are pending migrations because of the added health check installed apps,
    # which results in HTTP 500 response (as intended).
    assert response.status_code in (200, 500)


def test_unknown_subset_endpoint(client: Client):
    response = client.get("/_healthz/UNKNOWN/")

    assert response.status_code == 404
