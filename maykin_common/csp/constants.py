from django.db import models


class CSPDirective(models.TextChoices):
    """
    The CSP directives that can be extended through the database.

    The directive names match the keys used in the ``DIRECTIVES`` mapping of
    django-csp's ``CONTENT_SECURITY_POLICY`` setting.

    Only directives that take a list of sources are included - boolean directives
    (such as ``upgrade-insecure-requests``) cannot meaningfully be extended with
    additional values and are deliberately absent.
    """

    # Fetch directives
    CHILD_SRC = "child-src", "child-src"
    """Deprecated in CSP v3 - use ``frame-src`` and ``worker-src`` instead."""
    CONNECT_SRC = "connect-src", "connect-src"
    DEFAULT_SRC = "default-src", "default-src"
    FONT_SRC = "font-src", "font-src"
    FRAME_SRC = "frame-src", "frame-src"
    IMG_SRC = "img-src", "img-src"
    MANIFEST_SRC = "manifest-src", "manifest-src"
    MEDIA_SRC = "media-src", "media-src"
    OBJECT_SRC = "object-src", "object-src"
    PREFETCH_SRC = "prefetch-src", "prefetch-src"
    """Deprecated."""
    SCRIPT_SRC = "script-src", "script-src"
    SCRIPT_SRC_ATTR = "script-src-attr", "script-src-attr"
    SCRIPT_SRC_ELEM = "script-src-elem", "script-src-elem"
    STYLE_SRC = "style-src", "style-src"
    STYLE_SRC_ATTR = "style-src-attr", "style-src-attr"
    STYLE_SRC_ELEM = "style-src-elem", "style-src-elem"
    WORKER_SRC = "worker-src", "worker-src"

    # Document directives
    BASE_URI = "base-uri", "base-uri"
    """Does not fall back to ``default-src``."""
    PLUGIN_TYPES = "plugin-types", "plugin-types"
    """Deprecated. Does not fall back to ``default-src``."""
    SANDBOX = "sandbox", "sandbox"
    """Does not fall back to ``default-src``."""

    # Navigation directives
    FORM_ACTION = "form-action", "form-action"
    """Does not fall back to ``default-src``."""
    FRAME_ANCESTORS = "frame-ancestors", "frame-ancestors"
    """Does not fall back to ``default-src``."""
    NAVIGATE_TO = "navigate-to", "navigate-to"
    """Does not fall back to ``default-src``."""

    # Reporting directives
    REPORT_TO = "report-to", "report-to"
    """A string describing a reporting group. Does not fall back to ``default-src``."""
    REPORT_URI = "report-uri", "report-uri"
    """Full or relative URIs. Does not fall back to ``default-src``."""
    REQUIRE_SRI_FOR = "require-sri-for", "require-sri-for"
    """Valid values: ``script``, ``style``, or both."""
