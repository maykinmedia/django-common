"""
Tests for the config helper.

The pytest tests themselves test the behaviour of the utility, while the type
annotations in the tests are validated by pyright and check that the type overloads are
set up as expected.
"""

from datetime import date

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


def test_read_setting_with_None_default():
    result: str | None = config("SOME_OPTIONAL_SETTING", default=None)

    assert result is None


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
