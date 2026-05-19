from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as _UserAdmin
from django.contrib.auth.models import User

from maykin_common.accounts.admin import PreventPrivilegeEscalationMixin

# Unregister old admin
admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(PreventPrivilegeEscalationMixin, _UserAdmin):
    pass
