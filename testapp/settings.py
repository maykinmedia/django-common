import os
from pathlib import Path

from django.urls import reverse_lazy

try:
    import axes
except ImportError:
    axes = None

BASE_DIR = Path(__file__).resolve(strict=True).parent

SECRET_KEY = "so-secret-i-cant-believe-you-are-looking-at-this"

USE_TZ = True

DEBUG = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("PGDATABASE", "maykin-common"),
        "USER": os.getenv("PGUSER", "maykin-common"),
        "PASSWORD": os.getenv("PGPASSWORD", "maykin-common"),
        "HOST": os.getenv("PGHOST", "localhost"),
        "PORT": int(os.getenv("PGHOST", "5432")),
    }
}

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admin",
    "maykin_common",
    "testapp",
]

# ensure migrations run for some tests that rely on axes
if axes is not None:
    INSTALLED_APPS.insert(-2, "axes")

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static_root"

ROOT_URLCONF = "testapp.urls"

#
# CUSTOM SETTINGS
#
DJANGO_PROJECT_DIR = BASE_DIR

#
# CSRF SETTINGS
#

LOGIN_URLS = [reverse_lazy("admin:login")]
LOGIN_REDIRECT_URL = reverse_lazy("admin:index")
CSRF_FAILURE_VIEW = "maykin_common.views.csrf_failure"
