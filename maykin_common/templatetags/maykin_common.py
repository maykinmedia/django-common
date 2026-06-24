from typing import Literal

from django import template
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.utils.html import escape, format_html
from django.utils.safestring import SafeString, mark_safe
from django.utils.translation import gettext as _

from maykin_common.settings import get_setting

from ..branding import ProductDefinition, get_maykin_logo

register = template.Library()


@register.simple_tag()
def show_product_branding() -> SafeString | Literal[""]:
    """
    Render the product branding.

    We always look at the white label product branding first and render that. If nothing
    is configured, nothing at all is rendered.

    If on top of the white label branding, there is custom product branding provided
    too, we render that and use the white label branding for the "powered by" part.
    """
    product_definition: ProductDefinition | None = get_setting(
        "MKN_BRANDING_PRODUCT_DEFINITION"
    )
    # the product definition is the minimum required information, it's not allowed to
    # display custom branding without the white-label product information.
    if product_definition is None:
        return ""

    product_branding = format_html(
        _("{product_logo} <span>{product_name}, developed by</span> {maykin}"),
        product_logo=product_definition.get_logo_markup(),
        product_name=product_definition.get_name_markup(),
        maykin=get_maykin_logo(),
    )

    derived_product_definition: ProductDefinition | None = get_setting(
        "MKN_BRANDING_DERIVED_PRODUCT_DEFINITION"
    )
    if derived_product_definition is not None:
        product_branding = format_html(
            _("{product_logo} <span>{product_name}, powered by</span> {powered_by}"),
            product_logo=derived_product_definition.get_logo_markup(),
            product_name=derived_product_definition.get_name_markup(),
            powered_by=product_branding,
        )

    return format_html(
        '<div class="product-branding">{}</div>',
        product_branding,
    )


@register.inclusion_tag("maykin_common/includes/version_info.html")
def show_version_info():
    """
    Template that displays version info.
    """
    return {
        "RELEASE": get_setting("RELEASE"),
        "GIT_SHA": get_setting("GIT_SHA"),
    }


@register.simple_tag(takes_context=True)
def show_environment_info(context: dict[str, object]) -> str:
    """
    Template that show the current ENVIRONMENT to an authenticated user.

    Returns an empty string if SHOW_ENVIRONMENT is set to `False`
    """
    if not get_setting("SHOW_ENVIRONMENT"):
        return ""
    user = context.get("user")
    assert isinstance(user, None | AbstractBaseUser | AnonymousUser)
    if user is None or not user.is_authenticated:
        return ""

    style_tokens = {
        "background-color": get_setting("ENVIRONMENT_BACKGROUND_COLOR"),
        "color": get_setting("ENVIRONMENT_FOREGROUND_COLOR"),
    }
    _inline_style_bits = [
        f"--admin-env-info-{key}: {value}".format(key=key, value=escape(value))
        for key, value in style_tokens.items()
    ]
    return format_html(
        """<div class="env-info" style="{style}">{label}</div>""",
        label=get_setting("ENVIRONMENT_LABEL"),
        style=mark_safe("; ".join(_inline_style_bits)),
    )
