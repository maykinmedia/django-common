import pytest
from csp.constants import NONCE, SELF

from maykin_common.csp.middleware import merge_directives

EXISTING = "https://existing.example.com"
OTHER = "https://other.example.com"
ADDED = "https://added.example.com"
"""
The value coming from the database, which every case below merges in.
"""


@pytest.mark.parametrize(
    "base_value,expected",
    [
        pytest.param([EXISTING], [EXISTING, ADDED], id="list"),
        pytest.param((EXISTING,), [EXISTING, ADDED], id="tuple"),
        pytest.param(EXISTING, [EXISTING, ADDED], id="bare string"),
        pytest.param({OTHER, EXISTING}, [EXISTING, OTHER, ADDED], id="set is sorted"),
        pytest.param(None, [ADDED], id="None, as a decorator may leave it"),
        pytest.param([ADDED], [ADDED], id="value already present"),
        pytest.param([SELF, NONCE], [SELF, NONCE, ADDED], id="nonce sentinel in list"),
        pytest.param(NONCE, [NONCE, ADDED], id="bare nonce sentinel"),
    ],
)
def test_base_value_is_normalized_and_extended(base_value, expected):
    merged = merge_directives({"img-src": base_value}, {"img-src": [ADDED]})

    assert merged == {"img-src": expected}


def test_empty_base():
    assert merge_directives(None, {"img-src": [ADDED]}) == {"img-src": [ADDED]}


def test_untouched_directives_are_passed_through_verbatim():
    merged = merge_directives(
        {"font-src": None, "default-src": [SELF]}, {"img-src": [ADDED]}
    )

    assert merged["font-src"] is None
    assert merged["default-src"] == [SELF]


def test_base_is_not_mutated():
    base = {"img-src": [EXISTING]}

    merge_directives(base, {"img-src": [ADDED]})

    assert base == {"img-src": [EXISTING]}
