"""
Define configuration defaults for Django project settings.
"""

from collections.abc import Sequence

default_health_check_apps: Sequence[str] = [
    "health_check",
]
"""
The default health check app and plugins to enable.

This set of plugins is configured because they're 99% guaranteed to be used in every
project. Other contrib plugins are omitted because they require more configuration for
which we cannot easily provide defaults.

See https://codingjoe.dev/django-health-check/install/ for more details.
"""
