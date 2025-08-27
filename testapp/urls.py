from django.contrib import admin
from django.urls import path

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
