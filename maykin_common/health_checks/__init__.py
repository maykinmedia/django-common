"""
Defaults and conventions around `django-health-check`_.

Out of the box, we support health checks that verify:

* request-response cycles function
* the application can read and write from/to the database
* there are no pending database migrations
* the (default) cache is functioning

On an individual project basis, you can extend the application with additional checks
and implement your own - see the `upstream documentation`_.

.. _django-health-check: https://pypi.org/project/django-health-check/
.. _upstream documentation: https://codingjoe.dev/django-health-check/
"""

import importlib.util

from django.core.exceptions import ImproperlyConfigured

if importlib.util.find_spec("health_check") is None:  # pragma: no cover
    raise ImproperlyConfigured(
        "You must install the health-checks extra to use health checks."
    )

from .defaults import default_health_check_apps, default_health_check_subsets

__all__ = [
    "default_health_check_apps",
    "default_health_check_subsets",
]
