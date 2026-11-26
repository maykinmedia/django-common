from django.db.models import Model
from django.http import HttpRequest
from django.views import View

from rest_framework import permissions


class BookPermission(permissions.BasePermission):
    def has_object_permission(  # pyright:ignore[reportIncompatibleMethodOverride]
        self, request: HttpRequest, view: View, obj: Model
    ) -> bool:
        return False


class AuthorPermission(permissions.BasePermission):
    def has_object_permission(self, request: HttpRequest, view: View, obj: Model):  # pyright:ignore[reportIncompatibleMethodOverride]
        return False
