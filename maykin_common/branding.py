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
    Metadata about the product, typically displayed in the admin footer.
    """

    name: str
    """
    Name of the product.

    Examples: Open Zaak, Open Inwoner, Open Formulieren... but this can also be the name
    of a derived product (e.g. PodiumD Formulier).
    """

    hyperlink: str = ""
    """
    Optional hyperlink, will make the product name clickable if provided.

    For the white-label products, this should point to the (Github) repositories.
    """

    logo_path: str = ""
    """
    (Relative) path to the static asset of the favicon logo.

    The path is fed into the ``{% static %}`` template tag, so the asset should be
    included in your staticfiles. The file should be favicon-sized. CSS will apply
    maximum block sizes too.
    """

    logo_url: str = ""
    """
    URL to the logo asset/icon.

    Can be a fully qualified URL, or an absolute path to an asset hosted by the
    application. Note that you may need to tweak your Content-Security-Policy if using
    a URL.

    If both the logo URL and path are specified, the URL has precedence.
    """

    def __post_init__(self):
        self.name = escape(self.name)

    def get_logo_markup(self) -> SafeString | Literal[""]:
        url = self.logo_url
        path = self.logo_path
        if not url and not path:
            return ""
        return format_html(
            """
        <img
            src="{src}"
            alt="{alt}"
            class="product-branding__logo product-branding__logo--favicon"
        >""",
            src=url or static(path),
            alt=_("Favicon of the product {name}").format(name=self.name),
        )

    def get_name_markup(self) -> SafeString:
        assert isinstance(self.name, SafeString)
        if not (href := self.hyperlink):
            return self.name
        return format_html(
            '<a href="{href}" target="_blank" rel="noopener nofollower">{name}</a>',
            href=href,
            name=self.name,
        )
