import textwrap
from dataclasses import dataclass
from typing import Literal

from django.templatetags.static import static
from django.utils.html import escape, format_html
from django.utils.safestring import SafeString
from django.utils.translation import gettext as _


def get_maykin_logo() -> SafeString:
    return format_html(
        textwrap.dedent("""
        <a
            href="https://maykin.nl/"
            target="_blank"
            rel="noopener nofollower"
            class="product-branding__logo-link"
        >
            <img
                src="{logo_src}"
                alt="Maykin"
                class="product-branding__logo product-branding__logo--maykin">
        </a>
        """),
        logo_src=static("maykin_common/logo-wide.svg"),
    )


@dataclass
class ProductDefinition:
    """
    Metadata about the product as developed by Maykin.
    """

    name: str
    """
    Name of the white-label product.

    Examples: Open Zaak, Open Inwoner, Open Formulieren...
    """

    repository_link: str = ""
    """
    URL to the (Github) repository.

    If configured, the product name will link to this address. Should be an
    ``https://github.com/...`` hyperlink.
    """

    logo_path: str = ""
    """
    (Relative) path to the static asset of the fagicon logo.

    The path is fed into the ``{% static %}`` template tag, so the asset should be
    included in your staticfiles. The file should be favicon-sized. CSS will apply
    maximum block and inline sizes too.
    """

    def as_html(self) -> SafeString:
        """
        Build up the complex HTML structure while making sure to escape untrusted input.

        We need quite a bit of conditionals that affect the final HTML generated, which
        does not play nice with the translatable strings in the template engine itself.
        So instead we do the processing in Python, but need to be careful to properly
        escape input coming from untrusted input (like environment variables or
        translation catalogs).
        """

        logo_markup: SafeString | Literal[""] = (
            format_html(
                """
            <img
                src="{src}"
                alt="{alt}"
                class="product-branding__logo product-branding__logo--favicon"
            >""",
                src=static(path),
                alt=_("Favicon of the product {name}").format(name=self.name),
            )
            if (path := self.logo_path)
            else ""
        )

        name: SafeString = escape(self.name)
        if href := self.repository_link:
            name = format_html(
                '<a href="{href}" target="_blank" rel="noopener nofollower">{name}</a>',
                href=href,
                name=name,
            )

        return format_html(
            _("{product_logo} <span>{product_name}, developed by</span> {maykin}"),
            product_logo=logo_markup,
            product_name=name,
            maykin=get_maykin_logo(),
        )
