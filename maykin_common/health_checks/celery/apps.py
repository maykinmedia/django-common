from django.apps import AppConfig

from .probes import connect_beat_signals, connect_worker_signals


class CeleryHealthChecksAppConfig(AppConfig):
    name = "maykin_common.health_checks.celery"

    def ready(self):
        connect_worker_signals()
        connect_beat_signals()
