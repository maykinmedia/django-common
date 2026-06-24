from django import template
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.utils.html import escape, format_html
from django.utils.safestring import mark_safe

from maykin_common.settings import get_setting

from ..branding import DerivedProductDefinition, ProductDefinition

register = template.Library()


@register.inclusion_tag("maykin_common/includes/product_branding.html")
def show_product_branding():
    """
    Template displaying the product branding.
    """
    product_definition: ProductDefinition | None = get_setting(
        "MKN_BRANDING_PRODUCT_DEFINITION"
    )
    derived_product_definition: DerivedProductDefinition | None = get_setting(
        "MKN_BRANDING_DERIVED_PRODUCT_DEFINITION"
    )

    if derived_product_definition is not None:
        assert product_definition is not None, (
            "Both derived and white label product definitions must be provided"
        )
        derived_product_definition.derived_from = product_definition

    return {
        "product_definition": derived_product_definition or product_definition,
    }


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
