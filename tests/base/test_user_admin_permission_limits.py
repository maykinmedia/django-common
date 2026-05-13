"""
Verify that the privilege escalation mixins prevent privilege escalations.

By default, the Django user allows users to give themselves more permissions if they
have permissions to edit users, including themselves. Our default-project shipped with
protections against this, now implemented in maykin-common.
"""

from collections.abc import Callable

from django.contrib.auth.models import Group, Permission, User
from django.test import Client
from django.urls import reverse

import pytest

pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture
def other_superuser():
    return User.objects.create_superuser(
        username="admin2",
        email="admin2@example.com",
        password="secret",
    )


@pytest.fixture
def staff_user_with_auth_permissions():
    user = User.objects.create_user(
        username="auth_perms_staff_user",
        email="auth_perms_staff_user@example.com",
        password="secret",
        is_staff=True,
    )
    perms = Permission.objects.filter(
        content_type__app_label="auth",
        content_type__model="user",
    )
    user.user_permissions.set(perms)
    return user


@pytest.fixture
def staff_user_with_all_permissions():
    user = User.objects.create_user(
        username="all_perms_staff_user",
        email="all_perms_staff_user@example.com",
        password="secret",
        is_staff=True,
    )
    perms = Permission.objects.all()
    user.user_permissions.set(perms)
    return user


@pytest.mark.parametrize(
    "get_url",
    [
        lambda u: reverse("admin:auth_user_changelist"),
        lambda u: reverse("admin:auth_user_change", args=(u.pk,)),
        lambda u: reverse("admin:auth_user_add"),
    ],
)
def test_can_load_standard_admin_pages(
    admin_user: User,
    admin_client: Client,
    get_url: Callable[[User], str],
):
    """
    Assert that the custom code doesn't break standard admin pages (smoketest).
    """
    url = get_url(admin_user)

    response = admin_client.get(url)

    assert response.status_code == 200


def test_can_change_other_superusers_user_as_superuser(
    admin_user: User, client: Client, other_superuser: User
):
    client.force_login(user=admin_user)
    url = reverse("admin:auth_user_change", args=(other_superuser.pk,))

    response = client.post(
        url,
        {
            "username": "example",
            "date_joined_0": "2022-01-01",
            "date_joined_1": "12:00:00",
            "_save": "1",
        },
    )

    assert response.status_code == 302


def test_cannot_change_other_superusers_user_as_non_superuser(
    client: Client, staff_user_with_all_permissions: User, other_superuser: User
):
    client.force_login(user=staff_user_with_all_permissions)
    url = reverse("admin:auth_user_change", args=(other_superuser.pk,))

    response = client.post(
        url,
        {
            "username": "example",
            "date_joined_0": "2022-01-01",
            "date_joined_1": "12:00:00",
            "_save": "1",
        },
    )

    assert response.status_code != 302  # 302 redirect: successful save


def test_cannot_change_user_as_user_with_less_permissions(
    client: Client,
    staff_user_with_auth_permissions: User,
    staff_user_with_all_permissions: User,
):
    client.force_login(user=staff_user_with_auth_permissions)
    url = reverse("admin:auth_user_change", args=(staff_user_with_all_permissions.pk,))

    response = client.post(
        url,
        {
            "username": "example",
            "date_joined_0": "2022-01-01",
            "date_joined_1": "12:00:00",
            "_save": "1",
        },
    )

    assert response.status_code != 302  # 302 redirect: successful save


def test_can_change_user_as_user_with_more_permissions(
    client: Client,
    staff_user_with_all_permissions: User,
    staff_user_with_auth_permissions: User,
):
    client.force_login(user=staff_user_with_all_permissions)
    url = reverse("admin:auth_user_change", args=(staff_user_with_auth_permissions.pk,))

    response = client.post(
        url,
        {
            "username": "example",
            "date_joined_0": "2022-01-01",
            "date_joined_1": "12:00:00",
            "_save": "1",
        },
    )

    assert response.status_code == 302


def test_cannot_give_own_user_more_permissions(
    client: Client,
    staff_user_with_auth_permissions: User,
):
    group = Group.objects.create(name="all permissions")
    group.permissions.set(Permission.objects.all())
    client.force_login(user=staff_user_with_auth_permissions)
    url = reverse("admin:auth_user_change", args=(staff_user_with_auth_permissions.pk,))

    response = client.post(
        url,
        {
            "username": "example",
            "date_joined_0": "2022-01-01",
            "date_joined_1": "12:00:00",
            "groups": str(group.pk),
            "_save": "1",
        },
    )

    assert response.status_code != 302


def test_can_change_any_user_password_as_superuser(
    admin_user: User, client: Client, other_superuser: User
):
    client.force_login(user=admin_user)
    url = reverse("admin:auth_user_password_change", args=(other_superuser.pk,))

    response = client.get(url)

    assert response.status_code == 200


def test_cannot_change_any_user_password_as_non_superuser(
    client: Client, staff_user_with_all_permissions: User, other_superuser: User
):
    client.force_login(user=staff_user_with_all_permissions)
    url = reverse("admin:auth_user_password_change", args=(other_superuser.pk,))

    response = client.get(url)

    assert response.status_code == 403


def test_cannot_change_user_password_as_user_with_less_permissions(
    client: Client,
    staff_user_with_auth_permissions: User,
    staff_user_with_all_permissions: User,
):

    client.force_login(user=staff_user_with_auth_permissions)
    url = reverse(
        "admin:auth_user_password_change", args=(staff_user_with_all_permissions.pk,)
    )

    response = client.get(url)

    assert response.status_code == 403


def test_can_change_user_password_as_user_with_more_permissions(
    client: Client,
    staff_user_with_all_permissions: User,
    staff_user_with_auth_permissions: User,
):
    client.force_login(user=staff_user_with_all_permissions)
    url = reverse(
        "admin:auth_user_password_change", args=(staff_user_with_auth_permissions.pk,)
    )

    response = client.get(url)

    assert response.status_code == 200
