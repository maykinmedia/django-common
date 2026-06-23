from __future__ import annotations

from typing import Protocol, runtime_checkable

from django.contrib.auth.models import Group, Permission
from django.db import models


@runtime_checkable
class PermissionAwareUser(Protocol):
    is_superuser: bool
    groups: models.Manager[Group]
    user_permissions: models.Manager[Permission]

    def get_all_permissions(self, obj=None) -> set[str]: ...
