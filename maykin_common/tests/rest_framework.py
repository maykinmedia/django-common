import inspect
import logging
from collections.abc import Callable, Sequence
from importlib import import_module
from typing import NamedTuple
from unittest import SkipTest

from django.conf import settings
from django.db.models import Model
from django.test import TestCase
from django.urls import NoReverseMatch, reverse

from factory.django import DjangoModelFactory
from rest_framework import status
from rest_framework.generics import GenericAPIView

from maykin_common.rest_framework import (
    NoModelFound,
    get_drf_views,
    get_view_kwargs,
    get_view_model,
)

try:  # pragma: no cover
    import structlog  # pyright:ignore[reportMissingImports]

    logger = structlog.stdlib.get_logger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)


class NoFactoryFound(Exception): ...


# TODO: build a list of known factory models in the project to increase the likelyhood
# to find a matching factory.
def get_model_factory[T: Model](model_class: type[T]) -> type[DjangoModelFactory[T]]:
    """
    Return the first found factory for the given model.
    """
    app_config = model_class._meta.app_config
    factories_module_path = f"{app_config.name}.tests.factories"
    try:
        factory_module = import_module(factories_module_path)
    except ImportError as e:
        raise NoFactoryFound(f"Unable to find factory for model {model_class}") from e

    factory = None
    for attribute_name in dir(factory_module):
        attribute = getattr(factory_module, attribute_name)
        if not inspect.isclass(attribute) or not issubclass(
            attribute, DjangoModelFactory
        ):
            continue

        if not attribute or attribute._meta.model != model_class:
            continue

        factory = attribute
        break

    if not factory:
        raise NoFactoryFound(f"Unable to find factory for model {model_class}")
    return factory


class EndpointResult(NamedTuple):
    view_class: type[GenericAPIView]
    url_pattern_name: str
    constructed_url: str


def get_endpoints(
    url_conf: str | None = None,
    excluded_url_patterns: Sequence[str] | None = None,
    get_factory_function: Callable[[type[DjangoModelFactory]], Model] | None = None,
) -> list[EndpointResult]:
    _url_conf = __import__(url_conf or settings.ROOT_URLCONF, {}, {}, [""])
    project_name = (url_conf or settings.ROOT_URLCONF).split(".")[0]
    _excluded_url_patterns = excluded_url_patterns or []
    views = get_drf_views(
        project_name,
        _url_conf.urlpatterns,
        excluded_url_patterns=_excluded_url_patterns,
    )

    logger.debug(
        "Project DRF endpoints collected", extra={"endpoint_count": len(views)}
    )

    endpoints = []
    for url_pattern, view_class in views.items():
        try:
            model = get_view_model(view_class)
            factory = get_model_factory(model)
        except NoModelFound:
            logger.debug(
                "Unable to determine model from view",
                extra={
                    "view": view_class,
                    "pattern": url_pattern,
                },
            )
            continue
        except NoFactoryFound:
            logger.debug(
                "Unable to determine factory from model",
                extra={
                    "view": view_class,
                    "pattern": url_pattern,
                },
            )
            continue

        if get_factory_function:
            _get_factory_function = get_factory_function
        else:
            _get_factory_function = lambda _factory: _factory.create()  # noqa: E731  # pragma: no cover
        instance = _get_factory_function(factory)
        try:
            view_kwargs = get_view_kwargs(view_class, instance)
            url = reverse(url_pattern, kwargs=view_kwargs)
        except NoReverseMatch:
            url = None
        if not url:
            logger.debug(
                "Unable to construct URL for view",
                extra={
                    "view": view_class,
                    "pattern": url_pattern,
                },
            )
            continue

        endpoints.append(
            EndpointResult(
                view_class=view_class, url_pattern_name=url_pattern, constructed_url=url
            )
        )
    return endpoints


class APIPermissionsTests(TestCase):  # pragma: no cover
    user_factory_class: type[DjangoModelFactory]
    excluded_url_patterns: Sequence[str] | None = None
    urlconf: str | None = None

    @classmethod
    def setUpClass(cls) -> None:
        if cls is APIPermissionsTests:
            raise SkipTest("Skip running abstact testcase class")
        super().setUpClass()

        assert cls.user_factory_class, "user_factory_class attribute has to be set!"

    def test_permissionless_user(self):
        endpoints = get_endpoints(
            url_conf=self.urlconf, excluded_url_patterns=self.excluded_url_patterns
        )

        for endpoint in endpoints:
            with self.subTest(
                url=endpoint.constructed_url,
                view_class=endpoint.view_class,
                url_pattern=endpoint.url_pattern_name,
            ):
                self.client.force_login(self.user_factory_class.create())
                with self.subTest(method="get"):
                    response = self.client.get(endpoint.constructed_url)
                    self.assertIn(
                        response.status_code,
                        (status.HTTP_403_FORBIDDEN, status.HTTP_405_METHOD_NOT_ALLOWED),
                        "Response with did not return the expected response code.",
                    )

                with self.subTest(method="post"):
                    response = self.client.post(endpoint.constructed_url)
                    self.assertIn(
                        response.status_code,
                        (status.HTTP_403_FORBIDDEN, status.HTTP_405_METHOD_NOT_ALLOWED),
                        "Response did not return the expected response code.",
                    )

    def test_anonymous_user(self):
        endpoints = get_endpoints(
            url_conf=self.urlconf, excluded_url_patterns=self.excluded_url_patterns
        )

        for endpoint in endpoints:
            with self.subTest(
                url=endpoint.constructed_url,
                view_class=endpoint.view_class,
                url_pattern=endpoint.url_pattern_name,
            ):
                with self.subTest(method="get"):
                    response = self.client.get(endpoint.constructed_url)
                    self.assertIn(
                        response.status_code,
                        (
                            status.HTTP_401_UNAUTHORIZED,
                            status.HTTP_405_METHOD_NOT_ALLOWED,
                        ),
                        "Response with did not return the expected response code.",
                    )

                with self.subTest(method="post"):
                    response = self.client.post(endpoint.constructed_url)
                    self.assertIn(
                        response.status_code,
                        (
                            status.HTTP_401_UNAUTHORIZED,
                            status.HTTP_405_METHOD_NOT_ALLOWED,
                        ),
                        "Response with did not return the expected response code.",
                    )
