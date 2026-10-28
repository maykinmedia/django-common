"""
Caching of the CSP directives managed in the database.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.core.cache import BaseCache, caches
from django.db import transaction

from ..settings import get_setting
from .typing import DirectiveMapping

if TYPE_CHECKING:  # pragma: no cover
    from django.db.models.base import Model

logger = logging.getLogger(__name__)

CACHE_KEY = "maykin_common.csp.directives"
"""
The cache key the database-managed directives are stored under.
"""


def get_cache() -> BaseCache:
    """
    Return the cache backend used to store the database-managed directives.
    """
    # a misconfigured alias is a programming error and should not be swallowed
    return caches[get_setting("MKN_CSP_CACHE_ALIAS")]


def get_directives() -> DirectiveMapping:
    """
    Return the directives managed in the database, using the cache where possible.

    The cache is invalidated whenever a
    :class:`~maykin_common.csp.models.CSPSetting` is created, modified or deleted.
    """
    # deferred: models imports this module for cache invalidation, so importing it at
    # module level would be circular
    from .models import CSPSetting

    # a system check guarantees this is a whole, non-negative number of seconds, where
    # 0 means "do not cache at all"
    timeout = get_setting("MKN_CSP_CACHE_TIMEOUT")
    if timeout == 0:
        return CSPSetting.objects.as_dict()

    cache = get_cache()
    try:
        directives = cache.get(CACHE_KEY)
    except Exception:
        # log, but do not break the response cycle; IGNORE_EXCEPTIONS would do this
        # for us, but that is django-redis only
        logger.warning(
            "csp_directives_cache_read_failed",
            exc_info=True,
            extra={"cache_alias": get_setting("MKN_CSP_CACHE_ALIAS")},
        )
        return CSPSetting.objects.as_dict()

    # an empty mapping is a legitimate cached value, so only ``None`` counts as a miss
    if directives is None:
        directives = CSPSetting.objects.as_dict()
        try:
            cache.set(CACHE_KEY, directives, timeout)
        except Exception:
            logger.warning(
                "csp_directives_cache_write_failed",
                exc_info=True,
                extra={"cache_alias": get_setting("MKN_CSP_CACHE_ALIAS")},
            )

    return directives


def _delete_cached_directives() -> None:
    try:
        get_cache().delete(CACHE_KEY)
    except Exception:
        # log, but do not fail a write whose transaction has already committed
        logger.warning(
            "csp_directives_cache_invalidation_failed",
            exc_info=True,
            extra={"cache_alias": get_setting("MKN_CSP_CACHE_ALIAS")},
        )


def invalidate_directives_cache(
    sender: type[Model] | None = None, using: str | None = None, **kwargs: object
) -> None:
    """
    Drop the cached directives so that the next request reads them from the database.

    This is connected to the ``post_save`` and ``post_delete`` signals of
    :class:`~maykin_common.csp.models.CSPSetting`, and can also be called directly after
    bulk operations that bypass those signals.

    The cache is cleared once the surrounding transaction commits, or immediately when
    there is no transaction.
    """
    # Clearing before the commit would let a concurrent request read the pre-commit
    # state and cache it again, which would then be served until the timeout expires.
    transaction.on_commit(_delete_cached_directives, using=using)
