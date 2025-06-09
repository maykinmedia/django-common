from django.contrib import admin
from django.urls import path

from .views import ApiLandingPageView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/index/", ApiLandingPageView.as_view()),
]
