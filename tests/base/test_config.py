"""
Tests for the config helper.

The pytest tests themselves test the behaviour of the utility, while the type
annotations in the tests are validated by pyright and check that the type overloads are
set up as expected.
"""

from datetime import date
from typing import assert_never, assert_type

import decouple
import pytest

from maykin_common.config import config


def test_read_unset_and_required_setting_without_default():
    with pytest.raises(decouple.UndefinedValueError):
        config("SOME_REQUIRED_SETTING")


def test_read_provided_and_required_setting_without_default(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("SOME_REQUIRED_SETTING", "expected-result")

    result: str = config("SOME_REQUIRED_SETTING")

    assert result == "expected-result"


def test_read_unset_setting_fallback_to_default():
    result: int = config("SOME_OPTIONAL_SETTING", default=42)

    assert result == 42


def test_read_provided_setting_without_fallback_to_default_and_auto_cast(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("SOME_OPTIONAL_SETTING", "67")

    result: int = config("SOME_OPTIONAL_SETTING", default=42)

    assert result == 67


def test_read_setting_with_None_default(monkeypatch: pytest.MonkeyPatch):
    result = config("SOME_OPTIONAL_SETTING", default=None)

    monkeypatch.setenv("SOME_OPTIONAL_SETTING", "1")
    set_result = config("SOME_OPTIONAL_SETTING", default=None)

    assert_type(set_result, str | None)
    # Because
    assert result is None and isinstance(set_result, str)

    # because casting None is not allowed by config
    with pytest.raises(TypeError):
        cast_result_unset = config(
            "SOME_OPTIONAL_SETTING", default=None, cast=lambda s: s and int(s)
        )
        # we should infer
        assert_never(cast_result_unset)

        # and then pyright will mark all code that follows as unreachable
        more_code = "unreachable"
        assert more_code


def test_read_unset_list_setting_fallback_to_default():
    result: list[str] = config(
        "SOME_OPTIONAL_COMMA_SEPARATED_LIST", default=["default"], split=True
    )

    assert result == ["default"]


def test_read_provided_list_setting_without_fallback_to_default(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("SOME_OPTIONAL_COMMA_SEPARATED_LIST", "first, second")

    result: list[str] = config(
        "SOME_OPTIONAL_COMMA_SEPARATED_LIST", default=["default"], split=True
    )

    assert result == ["first", "second"]


def test_read_provided_list_setting_without_default(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("SOME_REQUIRED_COMMA_SEPARATED_LIST", "first,second")

    result: list[str] = config("SOME_REQUIRED_COMMA_SEPARATED_LIST", split=True)

    assert result == ["first", "second"]


def test_read_provided_list_casting_to_default(monkeypatch: pytest.MonkeyPatch):
    result = config(
        "SOME_REQUIRED_COMMA_SEPARATED_LIST", default=range(6, 8), split=True
    )

    assert_type(result, list[int])
    assert result == [6, 7]

    monkeypatch.setenv("SOME_REQUIRED_COMMA_SEPARATED_LIST", "1,2,3,4")
    set_result = config("SOME_REQUIRED_COMMA_SEPARATED_LIST", default=[1], split=True)

    assert set_result == [1, 2, 3, 4]


def test_read_provided_list_casting(monkeypatch: pytest.MonkeyPatch):
    result = config(
        "SOME_REQUIRED_COMMA_SEPARATED_LIST", default=range(8, 8), split=True, cast=int
    )

    assert_type(result, list[int])
    assert result == []

    monkeypatch.setenv("SOME_REQUIRED_COMMA_SEPARATED_LIST", "1,2,3,4")
    set_result = config(
        "SOME_REQUIRED_COMMA_SEPARATED_LIST", default=range(8, 8), split=True, cast=int
    )

    assert set_result == [1, 2, 3, 4]

    monkeypatch.setenv("SOME_REQUIRED_COMMA_SEPARATED_LIST", "1,2,3,4")
    no_default = config("SOME_REQUIRED_COMMA_SEPARATED_LIST", split=True, cast=int)

    assert no_default == [1, 2, 3, 4]


def test_read_provided_setting_with_custom_cast(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("SOME_OPTIONAL_SETTING", "2025-12-25")

    result: date = config("SOME_OPTIONAL_SETTING", cast=date.fromisoformat)

    assert result == date(2025, 12, 25)


def test_read_unset_setting_with_custom_cast_fallback_to_default():
    result: date = config(
        "SOME_OPTIONAL_SETTING",
        default="2025-01-01",
        cast=date.fromisoformat,
    )

    assert result == date(2025, 1, 1)


def test_raise_typeerror_when_non_string_default_is_specified_together_with_cast():
    with pytest.raises(TypeError):
        config("SOME_OPTIONAL_SETTING", default=123, cast=lambda x: x)  # pyright: ignore  expecting TypeError :)


def test_casting_to_union_type(monkeypatch: pytest.MonkeyPatch):
    result = config("SOME_PORT_OR_SOCKET", default="5432", cast=lambda s: s and int(s))
    assert_type(result, int | str)

    assert result == 5432

    monkeypatch.setenv("SOME_PORT_OR_SOCKET", "")

    set_result = config(
        "SOME_PORT_OR_SOCKET", default="5432", cast=lambda s: s and int(s)
    )
    assert set_result == ""
