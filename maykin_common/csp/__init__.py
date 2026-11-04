"""
Database-managed directives on top of `django-csp`_.

.. _django-csp: https://django-csp.readthedocs.io/en/latest/
"""

import importlib.util

from django.core.exceptions import ImproperlyConfigured

# NOTE: absolute import semantics mean "csp" is django-csp here, not this package.
if importlib.util.find_spec("csp") is None:  # pragma: no cover
    raise ImproperlyConfigured("You must install the csp extra to use CSP settings.")
