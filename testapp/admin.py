from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as _UserAdmin
from django.contrib.auth.models import User

# Unregister old admin
admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(_UserAdmin):
    pass
