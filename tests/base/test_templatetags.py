from django.contrib.auth.models import AnonymousUser, User
from django.template import Context, Template

from pytest_django.asserts import assertInHTML


def _render_environment_info(context=None):
    tpl = Template(
        """
        {%load maykin_common%}
        {%show_environment_info%}
    """
    )
    return tpl.render(Context(context or {})).strip()


def test_environment_disabled(settings):
    settings.SHOW_ENVIRONMENT = False

    # without user
    result = _render_environment_info()
    assert result == ""

    # with user
    result = _render_environment_info({"user": User})
    assert result == ""


def test_environment_enabled(settings):
    settings.SHOW_ENVIRONMENT = True
    settings.ENVIRONMENT_BACKGROUND_COLOR = "orange"
    settings.ENVIRONMENT_FOREGROUND_COLOR = "black"
    settings.ENVIRONMENT_LABEL = "my super duper env"

    # with anonymous user
    result = _render_environment_info({"user": AnonymousUser()})
    assert result == ""

    # with user

    result = _render_environment_info({"user": User})
    assert result != ""
    assertInHTML("my super duper env", result)


def test_version_info(settings):
    def _render(context=None):
        tpl = Template(
            """
            {%load maykin_common%}
            {%show_version_info%}
        """
        )
        return tpl.render(Context(context or {})).strip()

    settings.RELEASE = "1.0.0"
    settings.GIT_SHA = "2605a7ab0149"

    result = _render()
    assertInHTML(
        '<span class="version__release">\n        version 1.0.0\n    </span>',
        result,
    )
    assertInHTML(
        '<code class="version__git-hash">\n            GIT SHA: 2605a7ab0149\n'
        "        </code>",
        result,
    )
