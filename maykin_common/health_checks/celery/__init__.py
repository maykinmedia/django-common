import importlib.util

from django.core.exceptions import ImproperlyConfigured

if importlib.util.find_spec("celery") is None:  # pragma: no cover
    raise ImproperlyConfigured("You must install celery to use celery health checks.")
