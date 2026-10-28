from django.contrib.auth.models import Group

import pytest

from maykin_common.csp.constants import CSPDirective
from maykin_common.csp.models import CSPSetting

pytestmark = [pytest.mark.django_db]


def test_dunder_str():
    setting = CSPSetting(directive="img-src", value="https://cdn.example.com")

    assert str(setting) == "img-src 'https://cdn.example.com'"


def test_as_dict_groups_values_per_directive():
    CSPSetting.objects.create(directive="img-src", value="https://b.example.com")
    CSPSetting.objects.create(directive="img-src", value="https://a.example.com")
    CSPSetting.objects.create(directive="font-src", value="https://c.example.com")

    assert CSPSetting.objects.as_dict() == {
        "font-src": ["https://c.example.com"],
        "img-src": ["https://a.example.com", "https://b.example.com"],
    }


def test_as_dict_collapses_duplicate_values():
    CSPSetting.objects.create(directive="img-src", value="https://a.example.com")
    CSPSetting.objects.create(
        directive="img-src", value="https://a.example.com", identifier="elsewhere"
    )

    assert CSPSetting.objects.as_dict() == {"img-src": ["https://a.example.com"]}


def test_as_dict_is_empty_without_records():
    assert CSPSetting.objects.as_dict() == {}


def test_as_dict_can_be_narrowed_with_a_queryset_filter():
    CSPSetting.objects.create(directive="img-src", value="https://a.example.com")
    CSPSetting.objects.create(
        directive="font-src", value="https://b.example.com", identifier="fonts"
    )

    assert CSPSetting.objects.filter(identifier="fonts").as_dict() == {
        "font-src": ["https://b.example.com"]
    }


def test_set_for_creates_entries_linked_to_the_object():
    group = Group.objects.create(name="config")

    CSPSetting.objects.set_for(
        group, [(CSPDirective.IMG_SRC, "https://cdn.example.com")]
    )

    setting = CSPSetting.objects.get()
    assert setting.directive == "img-src"
    assert setting.value == "https://cdn.example.com"
    assert setting.content_object == group


def test_set_for_replaces_previous_entries_for_the_same_object():
    group = Group.objects.create(name="config")
    CSPSetting.objects.set_for(group, [(CSPDirective.IMG_SRC, "https://old.example")])

    assert [setting.value for setting in CSPSetting.objects.all()] == [
        "https://old.example"
    ]

    CSPSetting.objects.set_for(group, [(CSPDirective.IMG_SRC, "https://new.example")])

    assert [setting.value for setting in CSPSetting.objects.all()] == [
        "https://new.example"
    ]


def test_set_for_leaves_other_identifiers_alone():
    group = Group.objects.create(name="config")
    CSPSetting.objects.set_for(
        group, [(CSPDirective.IMG_SRC, "https://a.example")], identifier="first"
    )

    CSPSetting.objects.set_for(
        group, [(CSPDirective.IMG_SRC, "https://b.example")], identifier="second"
    )

    assert CSPSetting.objects.count() == 2


def test_set_for_leaves_other_objects_alone():
    one = Group.objects.create(name="one")
    other = Group.objects.create(name="other")
    CSPSetting.objects.set_for(one, [(CSPDirective.IMG_SRC, "https://a.example")])

    CSPSetting.objects.set_for(other, [(CSPDirective.IMG_SRC, "https://b.example")])

    assert CSPSetting.objects.count() == 2


def test_set_for_with_an_empty_list_clears_the_entries():
    group = Group.objects.create(name="config")
    CSPSetting.objects.set_for(group, [(CSPDirective.IMG_SRC, "https://a.example")])

    CSPSetting.objects.set_for(group, [])

    assert not CSPSetting.objects.exists()
