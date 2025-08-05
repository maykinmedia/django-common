from typing import Literal

from django.conf import settings

GOOGLE_ANALYTICS_ID = None
"""
Google analytics id added to the request context.
"""

SHOW_ENVIRONMENT = False
"""
Enable or disable the ``{% environment_info %}`` template tag.
"""

ENVIRONMENT_BACKGROUND_COLOR = "orange"
"""
The background color of the ``{% environment_info %}`` template tag.
"""

ENVIRONMENT_FOREGROUND_COLOR = "black"
"""
The foreground color of the ``{% environment_info %}`` template tag.
"""

ENVIRONMENT_LABEL = None
"""
The textual content of the ``{% environment_info %}`` template tag.
"""

ENVIRONMENT = ""
"""
The deployment environment label, e.g. 'staging' or 'prod'.

This setting is included in the OpenTelemetry resource attributes.
"""

RELEASE = None
"""
The release version shown in the ``{% version_info %}`` template tag.

This setting is included in the OpenTelemetry resource attributes.
"""

GIT_SHA = None
"""
The commit hash shown in the ``{% version_info %}`` template tag.
"""

PDF_BASE_URL_FUNCTION = None
"""
Function that returns the base url needed to download/resolve custom fonts and/or any
image URLs included in the document to render.

Required for the :ref:`quickstart_pdf` extra.
"""

type SettingName = Literal[
    "GOOGLE_ANALYTICS_ID",
    "ENVIRONMENT",
    "SHOW_ENVIRONMENT",
    "ENVIRONMENT_BACKGROUND_COLOR",
    "ENVIRONMENT_FOREGROUND_COLOR",
    "ENVIRONMENT_LABEL",
    "RELEASE",
    "GIT_SHA",
    "PDF_BASE_URL_FUNCTION",
]


def get_setting(name: SettingName):
    default = globals()[name]
    return getattr(settings, name, default)
