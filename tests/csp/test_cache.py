from typing import Protocol
from unittest.mock import patch

from django.contrib.auth.models import Group
from django.core.cache import BaseCache, InvalidCacheBackendError, caches

import pytest
from csp.constants import HEADER

from maykin_common.csp.cache import CACHE_KEY, get_cache, get_directives
from maykin_common.csp.constants import CSPDirective
from maykin_common.csp.models import CSPSetting

pytestmark = [pytest.mark.django_db]


class UnreachableCache:
    """
    Stand-in for a cache server that is down.

    Backends raise driver-specific errors, so the exact type does not matter here.
    """

    def get(self, *args, **kwargs):
        raise ConnectionError("the cache is down")

    def set(self, *args, **kwargs):
        raise ConnectionError("the cache is down")

    def delete(self, *args, **kwargs):
        raise ConnectionError("the cache is down")


class ReadOnlyCache:
    """
    Stand-in for a cache whose reads work, but whose writes fail.
    """

    def get(self, *args, **kwargs):
        return None

    def set(self, *args, **kwargs):
        raise ConnectionError("the cache is read-only")


class _FakeCache(Protocol):
    def get(self, *args: object, **kwargs: object) -> object: ...
    def set(self, *args: object, **kwargs: object) -> object: ...


def patched_cache(cache: _FakeCache):
    return patch("maykin_common.csp.cache.get_cache", return_value=cache)


def test_directives_are_read_from_the_database_once(
    django_assert_num_queries,
):
    CSPSetting.objects.create(directive="img-src", value="https://cdn.example.com")

    with django_assert_num_queries(1):
        first = get_directives()
    with django_assert_num_queries(0):
        second = get_directives()

    assert first == second == {"img-src": ["https://cdn.example.com"]}


def test_an_empty_result_is_cached_too(
    django_assert_num_queries,
):
    with django_assert_num_queries(1):
        assert get_directives() == {}
    with django_assert_num_queries(0):
        assert get_directives() == {}


def test_zero_timeout_disables_caching(settings, django_assert_num_queries):
    settings.MKN_CSP_CACHE_TIMEOUT = 0
    CSPSetting.objects.create(directive="img-src", value="https://cdn.example.com")

    with django_assert_num_queries(1):
        get_directives()
    with django_assert_num_queries(1):
        get_directives()

    assert get_cache().get(CACHE_KEY) is None


def test_a_different_cache_alias_is_honoured(dedicated_cache: BaseCache):
    CSPSetting.objects.create(directive="img-src", value="https://cdn.example.com")

    get_directives()

    assert dedicated_cache.get(CACHE_KEY) == {"img-src": ["https://cdn.example.com"]}
    assert caches["default"].get(CACHE_KEY) is None


def test_creating_a_setting_invalidates_the_cache(
    django_capture_on_commit_callbacks,
):
    assert get_directives() == {}

    with django_capture_on_commit_callbacks(execute=True):
        CSPSetting.objects.create(directive="img-src", value="https://cdn.example.com")

    assert get_directives() == {"img-src": ["https://cdn.example.com"]}


def test_updating_a_setting_invalidates_the_cache(
    django_capture_on_commit_callbacks,
):
    setting = CSPSetting.objects.create(directive="img-src", value="https://a.example")
    assert get_directives() == {"img-src": ["https://a.example"]}

    with django_capture_on_commit_callbacks(execute=True):
        setting.value = "https://b.example"
        setting.save()

    assert get_directives() == {"img-src": ["https://b.example"]}


def test_deleting_a_setting_invalidates_the_cache(
    django_capture_on_commit_callbacks,
):
    setting = CSPSetting.objects.create(directive="img-src", value="https://a.example")
    assert get_directives() == {"img-src": ["https://a.example"]}

    with django_capture_on_commit_callbacks(execute=True):
        setting.delete()

    assert get_directives() == {}


def test_set_for_invalidates_the_cache(
    django_capture_on_commit_callbacks,
):
    group = Group.objects.create(name="config")
    assert get_directives() == {}

    with django_capture_on_commit_callbacks(execute=True):
        CSPSetting.objects.set_for(
            group, [(CSPDirective.IMG_SRC, "https://cdn.example.com")]
        )

    assert get_directives() == {"img-src": ["https://cdn.example.com"]}


def test_cache_is_invalidated_only_once_the_transaction_commits(
    django_capture_on_commit_callbacks,
):
    assert get_directives() == {}

    with django_capture_on_commit_callbacks(execute=False) as callbacks:
        CSPSetting.objects.create(directive="img-src", value="https://cdn.example.com")

        # still the pre-commit state
        assert get_cache().get(CACHE_KEY) == {}

    # run the callbacks, as committing would
    for callback in callbacks:
        callback()

    assert get_cache().get(CACHE_KEY) is None


def test_an_unreachable_cache_falls_back_to_the_database(
    caplog: pytest.LogCaptureFixture,
):
    CSPSetting.objects.create(directive="img-src", value="https://cdn.example.com")

    with patched_cache(UnreachableCache()):
        directives = get_directives()

    assert directives == {"img-src": ["https://cdn.example.com"]}
    (record,) = [
        record
        for record in caplog.records
        if record.msg == "csp_directives_cache_read_failed"
    ]
    # which cache failed is the actionable part for whoever reads the log
    assert record.__dict__["cache_alias"] == "default"


@pytest.mark.usefixtures("policy")
def test_an_unreachable_cache_does_not_break_the_response(apply_middleware):
    CSPSetting.objects.create(directive="img-src", value="https://cdn.example.com")

    with patched_cache(UnreachableCache()):
        response = apply_middleware()

    assert "img-src https://cdn.example.com" in response[HEADER]


def test_a_cache_that_cannot_be_written_to_still_returns_directives(
    caplog: pytest.LogCaptureFixture,
):
    CSPSetting.objects.create(directive="img-src", value="https://cdn.example.com")

    with patched_cache(ReadOnlyCache()):
        directives = get_directives()

    assert directives == {"img-src": ["https://cdn.example.com"]}
    assert "csp_directives_cache_write_failed" in caplog.text


def test_an_unreachable_cache_does_not_break_saving(
    django_capture_on_commit_callbacks,
    caplog: pytest.LogCaptureFixture,
):
    with (
        patched_cache(UnreachableCache()),
        django_capture_on_commit_callbacks(execute=True),
    ):
        CSPSetting.objects.create(directive="img-src", value="https://cdn.example.com")

    CSPSetting.objects.get(directive="img-src", value="https://cdn.example.com")
    assert "csp_directives_cache_invalidation_failed" in caplog.text


def test_an_unknown_cache_alias_is_not_swallowed(settings):
    settings.MKN_CSP_CACHE_ALIAS = "does-not-exist"

    with pytest.raises(InvalidCacheBackendError):
        get_directives()


@pytest.mark.django_db(transaction=True)
def test_a_real_commit_invalidates_the_cache():
    assert get_directives() == {}

    CSPSetting.objects.create(directive="img-src", value="https://cdn.example.com")

    assert get_directives() == {"img-src": ["https://cdn.example.com"]}
