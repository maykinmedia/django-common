from django.test import Client
from django.urls import reverse

import pytest

pytestmark = [pytest.mark.urls("tests.axes.views")]


def test_user_cant_access_the_password_reset_view_more_than_5_times(client: Client):
    url = reverse("admin_password_reset")
    for _ in range(5):
        response = client.get(url)
        assert response.status_code == 200

    response = client.get(url)

    # 429 Too Many Requests
    assert response.status_code == 429
