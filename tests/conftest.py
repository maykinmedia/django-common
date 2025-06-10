import os

# otherwise pytest-playwright and pytest-django don't play nice :(
# See https://github.com/microsoft/playwright-pytest/issues/46
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "1"
