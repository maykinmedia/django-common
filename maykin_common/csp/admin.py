from django.contrib import admin

from .models import CSPSetting


@admin.register(CSPSetting)
class CSPSettingAdmin(admin.ModelAdmin):
    list_display = (
        "directive",
        "value",
        "identifier",
        "content_type",
    )
    list_filter = (
        "directive",
        "identifier",
        "content_type",
    )
    list_select_related = ("content_type",)
    search_fields = (
        "value",
        "identifier",
        "object_id",
    )
    # entries added by hand are standalone - the generic relation is reserved for
    # entries recorded by configuration models through ``CSPSetting.objects.set_for``
    readonly_fields = (
        "content_type",
        "object_id",
    )
