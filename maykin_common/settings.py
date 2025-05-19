from django.conf import settings

GOOGLE_ANALYTICS_ID = None
"""Google analytics id added to the request context"""


SHOW_ENVIRONMENT = False
"""enable or disable the `environment_info` template tag."""

ENVIRONMENT_BACKGROUND_COLOR = "orange"
"""The background color of the `environment_info` template tag."""

ENVIRONMENT_FOREGROUND_COLOR = "black"
"""The foreground color of the `environment_info` template tag."""

ENVIRONMENT_LABEL = None
"""The foreground color of the `environment_info` template tag."""

RELEASE = None
"""The environment label shown in the `version_info` template tag."""

GIT_SHA = None
"""The git hash shown in the `version_info` template tag."""

PDF_BASE_URL_FUNCTION = None
"""
Function that returns the base url needed to download/resolve custom fonts and/or any
image URLs included in the document to render.
"""


def get_setting(name: str):
    default = globals()[name]
    return getattr(settings, name, default)
