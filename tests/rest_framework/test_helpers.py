from django.db import models
from django.db.models import Model
from django.urls import NoReverseMatch, include, path

import pytest
from factory.django import DjangoModelFactory
from pytest_django import Settings

from maykin_common.rest_framework import (
    NoModelFound,
    get_drf_views,
    get_view_kwargs,
    get_view_model,
)
from maykin_common.tests.rest_framework import (
    NoFactoryFound,
    get_endpoints,
    get_model_factory,
)
from testapp.endpoints import (
    AuthorAPIView,
    BookAPIView,
    ComicAPIView,
    EpisodeAPIView,
    GameAPIView,
    GenericAPIView,
    MovieViewSet,
    PublisherAPIView,
    ShowAPIView,
    ViewWithLookupKwarg,
    ViewWithoutLookupField,
)
from testapp.models import Actor, Book, Genre
from testapp.tests.factories import GenreFactory

pytestmark = [
    pytest.mark.urls("testapp.urls"),
    pytest.mark.django_db,
]


def test_get_drf_views_detail_view_filter(settings: Settings):
    url_conf = __import__(settings.ROOT_URLCONF, {}, {}, [""])
    drf_views = get_drf_views("testapp", url_conf.urlpatterns)

    # note the missing genre view (as it is a list view)
    assert drf_views == {
        "book-detail": BookAPIView,
        "author-detail": AuthorAPIView,
        "publisher-detail": PublisherAPIView,
        "media:movies:movies-detail": MovieViewSet,
        "media:shows-detail": ShowAPIView,
        "media:episode-detail": EpisodeAPIView,
        "comic-detail": ComicAPIView,
        "game-detail": GameAPIView,
    }


def test_get_drf_views_excluded_url_patterns(settings: Settings):
    url_conf = __import__(settings.ROOT_URLCONF, {}, {}, [""])
    drf_views = get_drf_views(
        "testapp", url_conf.urlpatterns, excluded_url_patterns=["book-detail"]
    )

    assert drf_views == {
        "author-detail": AuthorAPIView,
        "publisher-detail": PublisherAPIView,
        "media:movies:movies-detail": MovieViewSet,
        "media:shows-detail": ShowAPIView,
        "media:episode-detail": EpisodeAPIView,
        "comic-detail": ComicAPIView,
        "game-detail": GameAPIView,
    }


def test_get_drf_views_url_resolver(settings: Settings):
    drf_views = get_drf_views(
        "testapp",
        [
            path(
                "api/",
                include(
                    (
                        [
                            path(
                                "public/books/<int:pk>/",
                                BookAPIView.as_view(),
                                name="book-detail",
                            )
                        ],
                        "movies",
                    ),
                    namespace="api",
                ),
            )
        ],
    )

    assert drf_views == {
        "api:book-detail": BookAPIView,
    }


def test_testapp_book_view_model():
    view_model = get_view_model(BookAPIView)

    assert view_model == Book


def test_testapp_api_view_model_raises_exception():
    with pytest.raises(NoModelFound):
        get_view_model(GenericAPIView)  # pyright:ignore[reportArgumentType]


def test_testapp_view_without_lookup_field():
    instance = Genre(name="Action", pk=1)
    with pytest.raises(NoReverseMatch):
        get_view_kwargs(ViewWithoutLookupField, instance)


def test_testapp_view_with_url_kwarg():
    instance = Genre(name="Action", pk=1)
    view_kwargs = get_view_kwargs(ViewWithLookupKwarg, instance)

    assert view_kwargs == {"id": instance.pk}


def test_testapp_genre_factory_lookup():
    factory = get_model_factory(Genre)

    assert factory == GenreFactory


def test_testapp_unknown_factory():
    with pytest.raises(NoFactoryFound):
        get_model_factory(Actor)


@pytest.mark.django_isolate_apps("testapp2")
def test_unknown_factories_module():
    class TestModel(models.Model):
        title = models.CharField(max_length=255)

        class Meta:
            app_label = "testapp2"

        def __str__(self) -> str:
            return self.title

    with pytest.raises(NoFactoryFound):
        get_model_factory(TestModel)


def get_factory_function(factory: type[DjangoModelFactory]) -> Model:
    return factory.build(pk=1)


def test_get_endpoints(settings: Settings):
    endpoint_results = [
        result.url_pattern_name
        for result in get_endpoints(get_factory_function=get_factory_function)
    ]
    assert endpoint_results == [
        "book-detail",
        "author-detail",
        "publisher-detail",
        "media:movies:movies-detail",
        "media:shows-detail",
    ]


def test_get_endpoints_excluded_patterns(settings: Settings):
    endpoint_results = [
        result.url_pattern_name
        for result in get_endpoints(
            get_factory_function=get_factory_function,
            excluded_url_patterns=["media:movies:movies-detail"],
        )
    ]
    assert endpoint_results == [
        "book-detail",
        "author-detail",
        "publisher-detail",
        "media:shows-detail",
    ]
