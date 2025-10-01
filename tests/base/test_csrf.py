from django.conf import settings
from django.test import Client, override_settings
from django.urls import reverse

import pytest
import pytest_django


@pytest.mark.django_db
def test_redirect_on_csrf_failure_if_logged_in(django_user_model):
    user = django_user_model.objects.create_superuser(username="one")
    client = Client(enforce_csrf_checks=True)
    client.force_login(user)
    response = client.post(reverse("admin:login"), {})

    pytest_django.asserts.assertRedirects(response, settings.LOGIN_REDIRECT_URL)


@pytest.mark.django_db
def test_normal_csrf_failure_when_not_logged_in():
    client = Client(enforce_csrf_checks=True)
    response = client.post(reverse("admin:login"), {})
    assert response.status_code == 403
    assert (
        "csrf verification failed. request aborted."
        in response.content.decode().lower()
    )
