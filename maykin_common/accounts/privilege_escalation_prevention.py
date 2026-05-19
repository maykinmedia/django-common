from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.exceptions import ValidationError
from django.db.models import QuerySet, Value
from django.db.models.functions import Concat
from django.utils.translation import gettext as _


def check_privilege_escalation_attempt(
    acting_user: AbstractUser,
    other_permissions: QuerySet[Permission],
    other_groups: QuerySet[Group],
    other_is_superuser: bool,
) -> None:
    """
    Check the requested permissions against the acting user's current permissions.

    :param acting_user: The currently authenticated user changing another user.
    :param other_permissions: The permissions to test against possible privilege
      escalation attempts. Can be a new set of permissions to assign, or the set of
      permissions of the target user being modified.
    :param other_groups: The groups to test against possible privilege escalation
      attempts. Can be a new set of groups to assign, or the set of groups of the
      target user being modified.
    :param other_is_superuser: Whether the user is being made superuser or the current
      superuser status of the reference user.

    :raises ValidationError: if the reuested permissions would grant more permissions
      to the currently assigned permissions of the acting user.
    """

    # if the acting user is superuser, they can do *ANYTHING*
    if acting_user.is_superuser:
        return

    # and the other way around, if the target is superuser and the acting user isn't -->
    # DENIED.
    if other_is_superuser:
        raise ValidationError(_("You need to be superuser to create other superusers."))

    acting_permission_codes: set[str] = acting_user.get_all_permissions()

    code_annotation = Concat("content_type__app_label", Value("."), "codename")
    new_permission_codes: set[str] = set(
        other_permissions.annotate(_full_code=code_annotation)
        .union(
            Permission.objects.filter(group__in=other_groups).annotate(
                _full_code=code_annotation
            )
        )
        .values_list("_full_code", flat=True)
    )

    if not new_permission_codes.issubset(acting_permission_codes):
        raise ValidationError(
            _("You cannot create or update a user with more permissions than yourself.")
        )


def check_max_user_permissions(
    *,
    acting_user: AbstractUser,
    target_user: AbstractUser,
) -> None:
    """
    Ensure that the target user does not have more permissions than the acting user.
    """
    check_privilege_escalation_attempt(
        acting_user=acting_user,
        other_permissions=target_user.user_permissions.all(),
        other_groups=target_user.groups.all(),
        other_is_superuser=target_user.is_superuser,
    )
