from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from django.contrib.auth.models import Group, Permission

if TYPE_CHECKING:  # pragma: no cover
    from django_stubs_ext.db.models.manager import RelatedManager


@runtime_checkable
class PermissionAwareUser(Protocol):
    is_superuser: bool
    groups: RelatedManager[Group]
    user_permissions: RelatedManager[Permission]

    def get_all_permissions(self, obj=None) -> set[str]: ...
