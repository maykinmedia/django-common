from django.apps import AppConfig

from .probes import connect_beat_signals


class CeleryHealthChecksAppConfig(AppConfig):
    name = "maykin_common.health_checks.celery"

    def ready(self):
        connect_beat_signals()
