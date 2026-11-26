import importlib.util

from django.contrib import admin
from django.urls import include, path

from .views import ApiLandingPageView, CustomComponentIndexView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/index/", ApiLandingPageView.as_view(), name="index"),
    path(
        "api/component/",
        CustomComponentIndexView.as_view(
            component="component",
            api_version="1",
            notification_url="http://testserver/notifications",
        ),
        name="index-component",
    ),
]

if importlib.util.find_spec("health_check") is not None:
    urlpatterns += [
        path("", include("maykin_common.health_checks.urls")),
    ]

if importlib.util.find_spec("hijack") is not None:
    urlpatterns += [
        path("hijack/", include("hijack.urls")),
    ]


if importlib.util.find_spec("rest_framework") is not None:
    from rest_framework import routers

    from .endpoints import (
        AuthorAPIView,
        BookAPIView,
        ComicAPIView,
        EpisodeAPIView,
        GameAPIView,
        GenreAPIView,
        MovieViewSet,
        PublisherAPIView,
        ShowAPIView,
    )

    router = routers.DefaultRouter(trailing_slash=True)
    router.register(r"movies", MovieViewSet, basename="movies")

    urlpatterns += [
        path("api/public/books/<int:pk>/", BookAPIView.as_view(), name="book-detail"),
        path("api/authors/<uuid:uuid>/", AuthorAPIView.as_view(), name="author-detail"),
        path(
            "api/publishers/<int:pk>/",
            PublisherAPIView.as_view(),
            name="publisher-detail",
        ),
        path("api/genres/", GenreAPIView.as_view(), name="genres-list"),
        path(
            "api/",
            include(
                (
                    (
                        path("", include((router.urls, "movies"), namespace="movies")),
                        path(
                            "shows/<int:pk>/",
                            ShowAPIView.as_view(),
                            name="shows-detail",
                        ),
                        path(
                            "shows/<int:show_pk>/<uuid:episode_uuid>/",
                            EpisodeAPIView.as_view(),
                            name="episode-detail",
                        ),
                    ),
                    "media",
                ),
                namespace="media",
            ),
        ),
        path("api/comics/<int:pk>/", ComicAPIView.as_view(), name="comic-detail"),
        path("api/games/<int:pk>/", GameAPIView.as_view(), name="game-detail"),
    ]
