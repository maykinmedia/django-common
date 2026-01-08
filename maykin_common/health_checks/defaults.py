"""
Define configuration defaults for Django project settings.
"""

from collections.abc import Mapping, Sequence

default_health_check_apps: Sequence[str] = [
    "health_check",
    "health_check.db",
    "health_check.cache",
    "health_check.contrib.migrations",
]
"""
The default health check app and plugins to enable.

This set of plugins is configured because they're 99% guaranteed to be used in every
project. Other contrib plugins are omitted because they require more configuration for
which we cannot easily provide defaults.

See https://codingjoe.dev/django-health-check/install/ for more details.
"""

default_health_check_subsets: Mapping[str, Sequence[str]] = {
    # deliberately empty - super cheap check to run that verifies HTTP traffic is
    # working
    "livez": (),
    # light-weight checks - if any of these fail, the instance should not accept live
    # traffic
    "readyz": (
        "DatabaseBackend",
        "MigrationsHealthCheck",
        "Cache backend: default",  # 'default' is the cache alias in ``settings.CACHES``
    ),
}
"""
The default subsets of checks to run. Each subset is named (using the keys of the dict).

The liveness check is intended for the liveness probe in Kubernetes. It can also be used
for the readiness probe, but the readiness check does a slightly more thorough check
without becoming expensive.

The startup probes can use the main health check without specifying any subset, which
checks all the plugins, including possibly expensive checks.

See https://codingjoe.dev/django-health-check/container/#subsets for more details
"""
