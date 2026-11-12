from django.test import Client
from django.urls import reverse

import pytest

from maykin_common.csp.models import CSPSetting

pytestmark = [pytest.mark.django_db]


def test_changelist_renders(admin_client: Client):
    CSPSetting.objects.create(
        directive="img-src",
        value="https://cdn.example.com",
        identifier="analytics",
    )

    response = admin_client.get(
        reverse("admin:maykin_common_csp_cspsetting_changelist")
    )

    assert response.status_code == 200
    assert "https://cdn.example.com" in response.content.decode()


def test_add_form_renders(admin_client: Client):
    response = admin_client.get(reverse("admin:maykin_common_csp_cspsetting_add"))

    assert response.status_code == 200


def test_an_entry_can_be_added_by_hand(admin_client: Client):
    response = admin_client.post(
        reverse("admin:maykin_common_csp_cspsetting_add"),
        {"directive": "img-src", "value": "https://cdn.example.com", "identifier": ""},
    )

    assert response.status_code == 302
    setting = CSPSetting.objects.get()
    assert setting.directive == "img-src"
    assert setting.value == "https://cdn.example.com"
    # entries added by hand are standalone
    assert setting.content_object is None


def test_change_form_renders(admin_client: Client):
    setting = CSPSetting.objects.create(
        directive="img-src", value="https://cdn.example.com"
    )

    response = admin_client.get(
        reverse("admin:maykin_common_csp_cspsetting_change", args=(setting.pk,))
    )

    assert response.status_code == 200


def test_the_generic_relation_is_not_editable(admin_client: Client):
    response = admin_client.get(reverse("admin:maykin_common_csp_cspsetting_add"))

    form_fields = response.context["adminform"].form.fields
    assert "content_type" not in form_fields
    assert "object_id" not in form_fields
