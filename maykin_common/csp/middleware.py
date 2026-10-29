from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import TYPE_CHECKING

from csp.middleware import CSPMiddleware as _CSPMiddleware, PolicyParts

from .cache import get_directives

if TYPE_CHECKING:  # pragma: no cover
    from django.http import HttpRequest, HttpResponseBase


def _as_list(value: object) -> list[object]:
    """
    Normalize a single django-csp directive value into a list.

    django-csp accepts bare strings, lists, tuples and sets as directive values, and
    sorts sets before rendering them. Mirror that here so merging is predictable.
    """
    match value:
        case None:
            return []
        case str():
            return [value]
        case set():
            return sorted(value)
        case Iterable():
            return list(value)
        case _:
            return [value]


def merge_directives(
    base: Mapping[str, object] | None,
    extra: Mapping[str, Sequence[str]],
) -> dict[str, object]:
    """
    Merge ``extra`` into ``base``, appending values rather than replacing them.

    ``base`` holds values in any of the shapes django-csp accepts, while ``extra``
    holds the plain lists of sources coming from the database.

    Directives that only appear in ``base`` are passed through untouched, so that a
    ``None`` recorded by one of django-csp's decorators keeps its meaning. Values
    already present for a directive are not added a second time.

    A new mapping is returned - ``base`` is never mutated, since it may be a dict that
    django-csp's decorators share between requests.

    Examples::

        >>> merge_directives(
        ...     {"default-src": ["'self'"]}, {"img-src": ["https://cdn.example.com"]}
        ... )
        {'default-src': ["'self'"], 'img-src': ['https://cdn.example.com']}

        >>> merge_directives(
        ...     {"img-src": ["https://cdn.example.com"]},
        ...     {"img-src": ["https://cdn.example.com"]},
        ... )
        {'img-src': ['https://cdn.example.com']}

        >>> merge_directives({"font-src": None}, {})
        {'font-src': None}
    """
    merged: dict[str, object] = dict(base or {})
    for directive, values in extra.items():
        existing = _as_list(merged.get(directive))
        merged[directive] = existing + [
            value for value in values if value not in existing
        ]
    return merged


class DatabaseDirectivesMixin:
    """
    Middleware mixin that merges the database-managed directives into the policy.

    Mix this into :class:`csp.middleware.CSPMiddleware` or one of its subclasses, such
    as ``csp.contrib.rate_limiting.RateLimitedCSPMiddleware``. The mixin must come
    first in the bases so that its ``get_policy_parts`` runs.

    The directives are applied to both the enforced and the report-only policy. The
    browser evaluates the two independently, so merging into only one would leave the
    other reporting violations for a source that was deliberately allowed and is not
    actually being blocked.
    """

    def get_policy_parts(
        self,
        request: HttpRequest,
        response: HttpResponseBase,
        report_only: bool = False,
    ) -> PolicyParts:
        policy_parts: PolicyParts = super().get_policy_parts(  # pyright: ignore[reportAttributeAccessIssue]
            request, response, report_only
        )

        directives = get_directives()
        if not directives:
            return policy_parts

        policy_parts.update = merge_directives(policy_parts.update, directives)
        return policy_parts


class CSPMiddleware(DatabaseDirectivesMixin, _CSPMiddleware):
    """
    Drop-in replacement for :class:`csp.middleware.CSPMiddleware`.

    It behaves exactly like the django-csp middleware, except that the directives
    managed in the database are merged into the policy configured in the settings.

    Use this *instead of* ``csp.middleware.CSPMiddleware`` in ``MIDDLEWARE``, not
    alongside it.
    """
