from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.test import Client

import pytest

pytestmark = [pytest.mark.urls("tests.axes.views")]


@pytest.fixture(autouse=True)
def _clear_cache():
    # It's free coverage estate!
    call_command("clear_cache", alias="default")
    yield
    call_command("clear_cache", alias="default")


def test_throttle_view_respects_request_1_per_second_rate(client: Client):
    response = client.post("/throttle/1/second")
    assert response.status_code == 200

    # a second request hits within the second and is expected to be throttled
    response = client.post("/throttle/1/second")
    assert response.status_code == 403


def test_throttle_view_allows_all_requests_in_window(client: Client):
    # assumes all requests completed within a second (!)
    for attempt in range(10):
        response = client.post("/throttle/10/second")
        assert response.status_code == 200, f"Failed on attempt {attempt + 1}"


def test_throttle_all_methods(client: Client):
    for method in ("get", "head", "post", "put", "patch", "options", "head"):
        response = getattr(client, method)("/throttle/all")

        assert response.status_code == 403, f"Failed on {method=}"


def test_view_overrides_throttled_response(client: Client):
    response = client.post("/throttle/1/second/custom-handling")
    assert response.status_code == 200

    # a second request hits within the second and is expected to be throttled
    response = client.post("/throttle/1/second/custom-handling")
    assert response.status_code == 429


@pytest.mark.django_db
def test_thottled_user_does_not_affect_other_user(client: Client, django_user_model):
    user_1 = django_user_model.objects.create_user(username="one")
    user_2 = django_user_model.objects.create_user(username="two")

    client.force_login(user=user_1)
    response_1 = client.post("/throttle/1/second")
    assert response_1.status_code == 200

    # a second request hits within the second and is expected to be throttled
    response_2 = client.post("/throttle/1/second")
    assert response_2.status_code == 403

    # but user 2 should not be affected
    client.force_login(user=user_2)
    response_3 = client.post("/throttle/1/second")
    assert response_3.status_code == 200


def test_throttle_based_on_ip_address_does_not_throttle_other_address(client: Client):
    response = client.post("/ip-throttle/1/minute", REMOTE_ADDR="127.0.0.1")
    assert response.status_code == 200

    # a second request hits within the second and is expected to be throttled
    response = client.post("/ip-throttle/1/minute", REMOTE_ADDR="127.0.0.1")
    assert response.status_code == 403

    # another IP address is not throttled
    response = client.post("/ip-throttle/1/minute", REMOTE_ADDR="127.0.0.2")
    assert response.status_code == 200


def test_throttle_based_on_ip_address_raises_when_no_ip_obtained(client: Client):
    with pytest.raises(ImproperlyConfigured):
        client.post("/ip-throttle/1/minute", REMOTE_ADDR="")
