from django.urls import include, path

# Default/convention for URL patterns. With all the defaults, this makes the following
# URLs available:
#
# * ``/_healthz/`` -> reports on all health checks configured
# * ``/_healthz/livez/`` -> no plugins at all, simple check if the app is alive
# * ``/_healthz/readyz/`` -> essential plugins, check if the app can do useful work
urlpatterns = [
    path("_healthz/", include("health_check.urls")),
]
