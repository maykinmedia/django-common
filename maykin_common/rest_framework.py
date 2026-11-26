import inspect
import logging
from collections.abc import Sequence

from django.db.models import Model
from django.urls import NoReverseMatch, URLPattern, URLResolver
from django.utils.module_loading import import_string

from rest_framework.generics import GenericAPIView

try:  # pragma: no cover
    import structlog  # pyright:ignore[reportMissingImports]

    logger = structlog.stdlib.get_logger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)


class NoModelFound(Exception): ...


def get_drf_views(
    project_name: str,
    url_patterns: list[URLResolver | URLPattern],
    namespace: str | None = None,
    excluded_url_patterns: Sequence[str] | None = None,
) -> dict[str, type[GenericAPIView]]:
    endpoint_results: dict[str, type[GenericAPIView]] = {}
    _excluded_url_patterns = excluded_url_patterns or []

    for pattern in url_patterns:
        if isinstance(pattern, URLPattern):
            assert isinstance(pattern.lookup_str, str)
            # filter only on project endpoints
            is_project_endpoint = pattern.lookup_str.startswith(project_name)
            if not all((is_project_endpoint, is_detail_endpoint(pattern))):
                continue

            url_pattern_name = (
                pattern.name if not namespace else f"{namespace}:{pattern.name}"
            )
            assert url_pattern_name
            if url_pattern_name in _excluded_url_patterns:
                continue

            endpoint_results[url_pattern_name] = import_string(pattern.lookup_str)
        elif isinstance(pattern, URLResolver):
            current_namespace = pattern.namespace or pattern.app_name
            _namespace: str | None = None
            if namespace and current_namespace:
                _namespace = f"{namespace}:{current_namespace}"
            elif namespace:
                _namespace = namespace
            elif current_namespace:
                _namespace = current_namespace

            endpoint_results.update(
                **get_drf_views(
                    project_name,
                    pattern.url_patterns,
                    namespace=_namespace,
                    excluded_url_patterns=_excluded_url_patterns,
                )
            )

    return endpoint_results


def is_detail_endpoint(pattern: URLPattern) -> bool:
    try:
        view_class = import_string(pattern.lookup_str)
    except ImportError:
        logger.debug(
            "Unable to import view class", extra={"pattern": pattern.lookup_str}
        )
        return False

    # Class based views and a GenericAPIView subclass is required to lookup
    # the view's model and use it's lookup_field property.
    if not inspect.isclass(view_class) or not issubclass(view_class, GenericAPIView):
        return False

    view_methods = [name for name, value in inspect.getmembers(view_class)]
    has_detail_action = "retrieve" in view_methods
    return has_detail_action and not (pattern.name and pattern.name.endswith("list"))


# TODO: add fallback methods to determine the model?
def get_view_model(view_class: type[GenericAPIView]) -> type[Model]:
    view = view_class()
    try:
        serializer_class = view.get_serializer_class()
        return serializer_class.Meta.model
    except Exception as e:
        raise NoModelFound from e


# TODO: implement multiple view kwargs (support NestedViewSets)?
# TODO: add support for custom ViewSet actions
def get_view_kwargs(
    view_class: type[GenericAPIView],
    instance: Model,
) -> dict[str, str | int]:
    lookup_field: str | None = view_class.lookup_field
    lookup_value = getattr(instance, lookup_field, None) if lookup_field else None
    if not all((lookup_field, lookup_value)):
        raise NoReverseMatch("Unable to determine lookup value from view")
    assert lookup_value
    return {(view_class.lookup_url_kwarg or lookup_field): lookup_value}
