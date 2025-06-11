from unittest.mock import patch

from django.core.management import call_command

import pytest

from maykin_common.pdf import render_to_pdf


def get_base_url():
    return "http://testserver"


@pytest.fixture(autouse=True)
def _collectstatic(settings, tmp_path):
    static_root = tmp_path / "static_root"
    settings.STATIC_ROOT = str(static_root)
    call_command("collectstatic", interactive=False, link=True, verbosity=0)
    yield


@pytest.fixture(autouse=True)
def _settings(settings):
    settings.PDF_BASE_URL_FUNCTION = f"{__name__}.get_base_url"


def test_raises_if_setting_not_configured_properly(settings):
    settings.PDF_BASE_URL_FUNCTION = None

    with pytest.raises(NotImplementedError):
        render_to_pdf("testapp/pdf/hello_world.html", {})


def test_render_template_returns_html():
    html, pdf = render_to_pdf("testapp/pdf/hello_world.html", {"world": "pytest"})

    assert isinstance(html, str)
    assert "Hello pytest" in html
    assert isinstance(pdf, bytes)


def test_external_url_uses_default_resolver():
    with patch("maykin_common.pdf.weasyprint.default_url_fetcher") as mock_fetcher:
        render_to_pdf("testapp/pdf/external_url.html", {})

    mock_fetcher.assert_called_once_with("https://example.com/index.css")


def test_local_asset_does_not_use_default_resolver():
    with patch("maykin_common.pdf.weasyprint.default_url_fetcher") as mock_fetcher:
        render_to_pdf("testapp/pdf/local_url.html", {})

    mock_fetcher.assert_not_called()


def test_render_with_missing_asset():
    with patch("maykin_common.pdf.weasyprint.default_url_fetcher") as mock_fetcher:
        render_to_pdf("testapp/pdf/missing_asset.html", {})

    mock_fetcher.assert_called_once_with("http://testserver/static/non_existent.css")


def test_resolves_assets_in_debug_mode(settings):
    settings.STATIC_ROOT = "/bad/path"
    settings.DEBUG = True

    with patch("maykin_common.pdf.weasyprint.default_url_fetcher") as mock_fetcher:
        render_to_pdf("testapp/pdf/local_url.html", {})

    mock_fetcher.assert_not_called()


def test_fully_qualified_static_url(settings):
    settings.STATIC_URL = "http://testserver/static/"

    with patch("maykin_common.pdf.weasyprint.default_url_fetcher") as mock_fetcher:
        render_to_pdf("testapp/pdf/local_url.html", {})

    mock_fetcher.assert_not_called()


def test_other_storages_than_file_system_storage(settings):
    settings.STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.InMemoryStorage",
        },
        "staticfiles": {
            # this causes the /static/ prefix to be absent (!)
            "BACKEND": "django.core.files.storage.InMemoryStorage",
        },
    }

    with patch("maykin_common.pdf.weasyprint.default_url_fetcher") as mock_fetcher:
        render_to_pdf("testapp/pdf/local_url.html", {})

    mock_fetcher.assert_called_with("http://testserver/testapp/some.css")
