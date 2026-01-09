from django.apps import AppConfig

from celery.signals import after_task_publish, beat_init

from .probes import on_beat_init, on_beat_task_published


class CeleryHealthChecksAppConfig(AppConfig):
    name = "maykin_common.health_checks.celery"

    def ready(self):
        # register signals for beat so that we can health-check it
        beat_init.connect(on_beat_init, dispatch_uid="probes.on_beat_init")
        after_task_publish.connect(
            on_beat_task_published, dispatch_uid="probes.on_beat_task_published"
        )
