from django.conf import settings
from django.test import Client
from django.urls import reverse

import pytest
from pytest_django.asserts import assertRedirects


@pytest.mark.django_db
def test_redirect_on_csrf_failure_if_logged_in(django_user_model):
    user = django_user_model.objects.create_superuser(username="one")
    client = Client(enforce_csrf_checks=True)
    client.force_login(user)

    response = client.post(reverse("admin:login"), {})

    assertRedirects(response, settings.LOGIN_REDIRECT_URL)


@pytest.mark.django_db
def test_normal_csrf_failure_when_not_logged_in():
    # Not using fixture because it disables CSRF checks by default
    client = Client(enforce_csrf_checks=True)

    response = client.post(reverse("admin:login"), {})

    assert response.status_code == 403
    assert (
        "csrf verification failed. request aborted."
        in response.content.decode().lower()
    )
