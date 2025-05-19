from django.apps import AppConfig


class MaykinCommonConfig(AppConfig):
    name = "maykin_common"

    def ready(self):
        from . import checks  # noqa
        from . import settings  # noqa
