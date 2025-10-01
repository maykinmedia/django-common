from django.urls import path

from maykin_common.accounts.views import PasswordResetView
from testapp.urls import urlpatterns

# Add the admin password reset path to the existing urlpatterns
# This way, the password reset URL is checked before other routes.
urlpatterns = [
    path(
        "admin/password_reset/",
        PasswordResetView.as_view(),
        name="admin_password_reset",
    ),
] + urlpatterns
