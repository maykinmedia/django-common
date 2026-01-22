"""
Utilities to read and process configuration for a project.

.. todo:: Incorporate the Team Bron documentation options for parameters.
"""

from collections.abc import Callable, Sequence
from typing import Literal, Never, assert_never, overload

from decouple import Csv, Undefined, config as _config, undefined

__all__ = ["config"]


@overload
def config(option: str) -> str: ...


@overload
def config[T](
    option: str,
    *,
    default: Sequence[T],
    split: Literal[True],
    cast: Callable[[str], T] | Undefined = undefined,
) -> list[T]: ...


@overload
def config(
    option: str,
    *,
    default: Undefined = undefined,
    split: Literal[True],
    cast: Undefined = undefined,
) -> list[str]: ...


@overload
def config[T](
    option: str,
    *,
    default: Undefined = undefined,
    split: Literal[True],
    cast: Callable[[str], T],
) -> list[T]: ...


@overload
def config(option: str, *, default: None) -> str | None: ...


@overload
def config[T](option: str, *, default: T | Undefined = undefined) -> T: ...


# because we can't express difference / negation types: object \ None
@overload
def config(option: str, *, default: None, cast: Callable) -> Never: ...


@overload
def config[T](
    option: str, *, default: object = undefined, cast: Callable[[str], T]
) -> T: ...


def config[T](
    option: str,
    *,
    default: T | Sequence[T] | None | Undefined = undefined,
    split: bool = False,
    cast: Callable[[str], T] | Undefined = undefined,
) -> str | None | T | Sequence[T]:
    """
    Pull a config parameter from the environment.

    Read the config variable ``option``. If it's optional, use the ``default`` value.

    If not ``cast`` parameter is provided, then the ``cast`` is derived from the
    ``default`` type when a default is provided. However, when you provide a ``cast``
    parameter explicitly, you must provide any ``default`` as a string as it will be
    passed to the provided ``cast`` callback.

    Note that ``default=None`` does not mean there's no default;
    omitting the ``default`` kwarg entirely means there's no default.

    Pass ``split=True`` to split the comma-separated input into a list. If a default is
    provided, it must be a list.

    Examples::

        >>> SECRET_KEY: str = config("SECRET_KEY")
        >>> DB_NAME: str = config("DB_NAME", default="my-awesome-project")
        >>> DB_PORT: int = config("DB_PORT", default=5432")
        >>> SESSION_COOKIE_DOMAIN: str | None = config(
        ...     "SESSION_COOKIE_DOMAIN", default=None
        ... )
        >>> ALLOWED_HOSTS: list[str] = config("ALLOWED_HOSTS", split=True, default=[])
        >>> CUSTOM = config(
        ...     "CUSTOM",
        ...     default="123",
        ...     cast=lambda v: int(v) if v is not None else None,
        ... )  # typed as int | None
    """

    if split:
        assert isinstance(default, Undefined | Sequence), (
            "You must provide a sequence default argument"
        )
        match default:
            case [t, *rest]:
                return _config(
                    option,
                    cast=Csv(cast=cast if callable(cast) else type(t)),
                    # python-decouple Csv cast expects the default as a string -
                    # serialize it again.
                    default=",".join((str(t), *(str(v) for v in rest))),
                )
            case [] if callable(cast):
                return _config(
                    option,
                    cast=Csv(cast=cast),
                    default="",
                )
            case _:
                if callable(cast):
                    return _config(option, cast=Csv(cast=cast))
                return _config(option, cast=Csv())

    # infer the ``cast`` from the default if not provided explicitly
    match (cast, default):
        #
        # cases without explicit cast
        #
        case Undefined(), Undefined():
            return _config(option)
        case Undefined(), None:
            # explicit `None` default values cannot be used as cast, ignore it.
            return _config(option, default=default)
        case Undefined(), _:
            return _config(option, default=default, cast=type(default))
        #
        # with explicit cast
        #
        case _, Undefined():
            return _config(option, cast=cast)
        case _, _:
            # the combination of a default + cast is odd and goes against the common
            # behaviour when it's derived from the default type - unfortunately we can't
            # simply take the ``str(default)``, as there's no guarantee that
            # ``default == cast(str(default))`` (e.g. ``cast=date.fromisoformat``
            # already falls apart)
            if not isinstance(default, str):
                raise TypeError(
                    "'default' must be a string when providing a cast callback"
                )
            return _config(option, default=default, cast=cast)
        case _:  # pragma: no cover
            assert_never((cast, default))
