from collections.abc import Mapping

from django.template import Context, Template
from django.test import Client
from django.urls import reverse

import pytest
from pytest_django.asserts import assertInHTML, assertTemplateUsed

from maykin_common.branding import ProductDefinition


def _render_product_branding(context=None):
    tpl = Template(
        """
        {% load maykin_common %}
        {% show_product_branding %}
    """
    )
    return tpl.render(Context(context or {})).strip()


@pytest.mark.parametrize(
    "settings_values",
    (
        {
            "MKN_BRANDING_PRODUCT_DEFINITION": None,
            "MKN_BRANDING_DERIVED_PRODUCT_DEFINITION": None,
        },
        {
            "MKN_BRANDING_PRODUCT_DEFINITION": None,
            "MKN_BRANDING_DERIVED_PRODUCT_DEFINITION": ProductDefinition(
                name="Ignore me"
            ),
        },
    ),
)
def test_no_product_definition_defined(settings, settings_values: Mapping[str, object]):
    """
    Assert the tag renders nothing if no white label product definition is defined.
    """
    for setting, value in settings_values.items():
        setattr(settings, setting, value)

    result = _render_product_branding()

    assert result == ""


def test_white_label_product_defined_but_no_derived_product(settings):
    settings.MKN_BRANDING_PRODUCT_DEFINITION = ProductDefinition(name="Product name")
    settings.MKN_BRANDING_DERIVED_PRODUCT_DEFINITION = None

    result = _render_product_branding()

    assert "Product name" in result
    assertInHTML(
        """
        <img
            src="/static/maykin_common/logo-wide.svg"
            alt="Maykin"
            class="product-branding__logo product-branding__logo--maykin"
        >
        """,
        result,
    )


def test_logo_rendered_and_product_name_clickable_link(settings):
    settings.MKN_BRANDING_PRODUCT_DEFINITION = ProductDefinition(
        name="Product name",
        hyperlink="https://example.com",
        logo_path="maykin_common/ico/favicon.png",
    )
    settings.MKN_BRANDING_DERIVED_PRODUCT_DEFINITION = None

    result = _render_product_branding()

    assertInHTML(
        """
        <img
            src="/static/maykin_common/ico/favicon.png"
            alt="Favicon of the product Product name"
            class="product-branding__logo product-branding__logo--favicon"
        >
        """,
        result,
    )
    assertInHTML(
        """
        <a href="https://example.com" target="_blank" rel="noopener nofollow">
            Product name
        </a>
        """,
        result,
    )


def test_logo_rendered_with_url_and_path_configured(settings):
    settings.MKN_BRANDING_PRODUCT_DEFINITION = ProductDefinition(
        name="Product name",
        hyperlink="https://example.com",
        logo_path="maykin_common/ico/favicon.png",
        logo_url="/media/some-icon.png",
    )
    settings.MKN_BRANDING_DERIVED_PRODUCT_DEFINITION = None

    result = _render_product_branding()

    assertInHTML(
        """
        <img
            src="/media/some-icon.png"
            alt="Favicon of the product Product name"
            class="product-branding__logo product-branding__logo--favicon"
        >
        """,
        result,
    )


def test_minimal_product_definition_with_custom_product(settings):
    settings.MKN_BRANDING_PRODUCT_DEFINITION = ProductDefinition(name="Product name")
    settings.MKN_BRANDING_DERIVED_PRODUCT_DEFINITION = ProductDefinition(
        name="Custom name"
    )

    result = _render_product_branding()

    assert "Product name" in result
    assert "Custom name" in result


def test_escapes_content(settings):
    settings.MKN_BRANDING_PRODUCT_DEFINITION = ProductDefinition(
        name="Product <xss> name"
    )
    settings.MKN_BRANDING_DERIVED_PRODUCT_DEFINITION = ProductDefinition(
        name="Custom <xss> name"
    )

    result = _render_product_branding()

    assert "&lt;xss&gt;" in result
    assert "<xss>" not in result


def test_renders_both_logos_and_links(settings):
    settings.MKN_BRANDING_PRODUCT_DEFINITION = ProductDefinition(
        name="Product name",
        hyperlink="https://example.com/white-label",
        logo_path="maykin_common/ico/favicon.png",
    )
    settings.MKN_BRANDING_DERIVED_PRODUCT_DEFINITION = ProductDefinition(
        name="Custom name",
        hyperlink="https://example.com/custom",
        logo_path="maykin_common/ico/favicon.svg",
    )

    result = _render_product_branding()

    # white label product
    assertInHTML(
        """
        <img
            src="/static/maykin_common/ico/favicon.png"
            alt="Favicon of the product Product name"
            class="product-branding__logo product-branding__logo--favicon"
        >
        """,
        result,
    )
    assertInHTML(
        """
        <a
            href="https://example.com/white-label"
            target="_blank"
            rel="noopener nofollow"
        >
            Product name
        </a>
        """,
        result,
    )
    # custom product
    assertInHTML(
        """
        <img
            src="/static/maykin_common/ico/favicon.svg"
            alt="Favicon of the product Custom name"
            class="product-branding__logo product-branding__logo--favicon"
        >
        """,
        result,
    )
    assertInHTML(
        """
        <a
            href="https://example.com/custom"
            target="_blank"
            rel="noopener nofollow"
        >
            Custom name
        </a>
        """,
        result,
    )


def test_no_footer_displayed_on_admin_login_page(settings, client: Client):
    settings.MKN_BRANDING_PRODUCT_DEFINITION = ProductDefinition(
        name="Product name",
        hyperlink="https://example.com/white-label",
        logo_path="maykin_common/ico/favicon.png",
    )
    admin_login_url = reverse("admin:login")

    response = client.get(admin_login_url)

    assertTemplateUsed(response, "admin/login.html")
    assertInHTML('<footer id="footer"></footer>', response.text)
    assert "Product name" not in response.text
