from django.test import Client
from django.urls import reverse


def test_index_component_page(client: Client):
    response = client.get(reverse("index-component"))
    assert response.status_code == 200

    assert b"Testapp API" in response.content  # page_title
    assert b"Component" in response.content  # title_component

    # buttons
    assert b"API docs (ReDoc)" in response.content
    assert b"Open API specification" in response.content
    assert b"Notifications" in response.content
