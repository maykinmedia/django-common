from django.apps import AppConfig
from django.db.models.signals import post_delete, post_save
from django.utils.translation import gettext_lazy as _


class CSPConfig(AppConfig):
    name = "maykin_common.csp"
    # django-csp itself uses the "csp" app label, which would otherwise collide
    label = "maykin_common_csp"
    verbose_name = _("Content Security Policy")
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from . import checks  # noqa: F401
        from .cache import invalidate_directives_cache
        from .models import CSPSetting

        post_save.connect(
            invalidate_directives_cache,
            sender=CSPSetting,
            dispatch_uid="maykin_common_csp.invalidate_on_save",
        )
        post_delete.connect(
            invalidate_directives_cache,
            sender=CSPSetting,
            dispatch_uid="maykin_common_csp.invalidate_on_delete",
        )
