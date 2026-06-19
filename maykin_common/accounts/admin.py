from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from django import forms
from django.contrib.admin.utils import unquote
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpRequest

from .privilege_escalation_prevention import (
    check_max_user_permissions,
    check_privilege_escalation_attempt,
)
from .typing import PermissionAwareUser

# yes, this means all the rest is *private* API
__all__ = ["PreventPrivilegeEscalationMixin"]

type UserModelT = type[AbstractUser]

if TYPE_CHECKING:  # pragma: no cover

    class AdminMixinBase[ModelT: UserModelT](BaseUserAdmin): ...

    class FormMixinBase(forms.ModelForm[AbstractUser]): ...
else:

    class AdminMixinBase[ModelT: UserModelT]:
        pass

    FormMixinBase = object


class PreventPrivilegeEscalationFormMixin(FormMixinBase):
    current_user: ClassVar[PermissionAwareUser]
    """
    The user of the current admin request, i.e. the authenticated user making changes.

    Note that this is a class attribute that needs to be set dynamically for each
    request. :class:`PreventPrivilegeEscalationMixin` takes care of that in
    :meth:`PreventPrivilegeEscalationMixin.get_form`.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # err on the side of caution
        if self.current_user is None:  # pragma: no cover
            raise RuntimeError("Could not determine current user.")
        if self.instance is None:  # pragma: no cover
            raise RuntimeError("Could not determine target user.")

    def clean(self):
        super().clean()
        target_user = self.instance
        assert isinstance(target_user, PermissionAwareUser)

        user_permissions = self.cleaned_data.get(
            "user_permissions", Permission.objects.none()
        )
        groups = self.cleaned_data.get("groups", Group.objects.none())
        is_superuser = self.cleaned_data.get("is_superuser", False)

        # Validate that the permissions that the current user WANTS to give are
        # not more than what the current user has.
        check_privilege_escalation_attempt(
            self.current_user, user_permissions, groups, is_superuser
        )

        # Validate that the EXISTING permissions of the target user, are not
        # more than your the current user permissions.
        check_max_user_permissions(
            acting_user=self.current_user, target_user=target_user
        )

        # Why do we need the above 2 calls?
        #
        # The best example is if a current user has permissions A, and
        # target user has permission A and B. If I try to remove permission B
        # from the target user, the POST-request matches the current users
        # permissions (only A) in the `check_privilege_escalation_attempt` call.
        # However, when you check the existing permissions with
        # `check_max_user_permissions`, it detects that the target user
        # actually has permission B as well so you cannot change this user
        # (since they have more permissions).

        return self.cleaned_data


class PreventPrivilegeEscalationMixin(AdminMixinBase[UserModelT]):
    """
    Wire up the protections to prevent users from giving themselves more permissions.

    By default, a Django user that has the user change permissions in the admin can
    change their own user account, giving out additional permissions or even make
    themselves superuser. Or, they can add additional users with more permissions than
    themselves, or change the password of more-privileged accounts to gain access that
    way.

    This mixin prevents such mechanisms.

    Example usage, in your ``admin.py`` for your (custom) user model:

    .. code-block:: python

        from django.contrib import admin
        from django.contrib.auth.admin import UserAdmin as _UserAdmin
        from django.contrib.auth.models import User

        from maykin_common.accounts.admin import PreventPrivilegeEscalationMixin

        # Unregister old admin
        admin.site.unregister(User)


        @admin.register(User)
        class CustomUserAdmin(PreventPrivilegeEscalationMixin, _UserAdmin):
            pass
    """

    def get_form(
        self,
        request: HttpRequest,
        obj: AbstractUser | None = None,
        change: bool = False,
        **kwargs,
    ):
        kwargs["change"] = change  # necessary to satisfy type checker :)
        base = super().get_form(request, obj, **kwargs)
        # The user-add flow is excluded, because that typically does not contain the
        # permissions/groups fields and after adding, you go to the change form which
        # is covered by our protections
        if issubclass(base, self.add_form):
            return base

        # add our own mixin to the form class by dynamically constructing a new form
        # class - downstream projects don't need to worry about specifying ``form``
        # on the admin class this way.
        #
        # Unfortunately we need to rely on meta-programming here to inject the current
        # request.user because the django admin does not have a convenient hook to pass
        # additional form instantiation kwargs.
        form_cls = type(
            f"Defused{base.__name__}",
            (PreventPrivilegeEscalationFormMixin, base),
            {
                "current_user": request.user,
            },
        )
        return form_cls

    def user_change_password(self, request: HttpRequest, id: str, form_url: str = ""):
        target_user = self.get_object(request, unquote(id))
        assert isinstance(target_user, PermissionAwareUser)
        assert isinstance(request.user, PermissionAwareUser)

        try:
            check_max_user_permissions(
                acting_user=request.user, target_user=target_user
            )
        except ValidationError as exc:
            raise PermissionDenied from exc
        return super().user_change_password(request, id, form_url)
