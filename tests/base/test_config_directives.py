import textwrap

import pytest
from docutils.core import publish_doctree
from docutils.parsers.rst import directives

import maykin_common.config_helpers
from maykin_common.config_helpers import config
from maykin_common.documentation.config_directives import (
    ConfigAllParamsDirective,
    ConfigGroupDirective,
    ConfigParamDirective,
)

directives.register_directive("config-param", ConfigParamDirective)
directives.register_directive("config-group", ConfigGroupDirective)
directives.register_directive("config-all-params", ConfigAllParamsDirective)


def parse_rst(rst: str) -> str:
    document = publish_doctree(rst)
    return document.astext()


@pytest.fixture(autouse=True)
def clean_registry():
    """
    Make sure the envvar registry is reset between tests
    """
    maykin_common.config_helpers.ENVVAR_REGISTRY.clear()
    yield
    maykin_common.config_helpers.ENVVAR_REGISTRY.clear()


#
# Single parameter directive tests
#


def test_config_param():
    config("DISABLE_2FA", help_text="disable 2fa", default=False)

    rst = textwrap.dedent("""
        .. config-param:: DISABLE_2FA
    """)

    doc = parse_rst(rst)

    expected = "* DISABLE_2FA: disable 2fa. Defaults to: False.<br>"

    assert expected == doc


def test_config_param_override_default():
    config("DISABLE_2FA", help_text="disable 2fa", default=False)

    rst = textwrap.dedent("""
        .. config-param:: DISABLE_2FA
            :default: True
    """)

    doc = parse_rst(rst)

    expected = "* DISABLE_2FA: disable 2fa. Defaults to: True.<br>"

    assert expected == doc


def test_config_param_do_not_display_default():
    config(
        "DISABLE_2FA",
        help_text="disable 2fa",
        default=False,
        auto_display_default=False,
    )

    rst = textwrap.dedent("""
        .. config-param:: DISABLE_2FA
            :default: True
    """)

    doc = parse_rst(rst)

    expected = "* DISABLE_2FA: disable 2fa.<br>"

    assert expected == doc


def test_config_param_default_empty_string():
    config("SUBPATH", help_text="subpath", default="")

    rst = textwrap.dedent("""
        .. config-param:: SUBPATH
    """)

    doc = parse_rst(rst)

    expected = "* SUBPATH: subpath. Defaults to: (empty string).<br>"

    assert expected == doc


def test_config_param_missing_help_text():
    config("DISABLE_2FA", default=False)

    rst = textwrap.dedent("""
        .. config-param:: DISABLE_2FA
    """)

    doc = parse_rst(rst)

    expected = "* DISABLE_2FA:  Defaults to: False.<br>"

    assert expected == doc


def test_config_param_no_default(monkeypatch):
    monkeypatch.setenv("SOME_VAR", "foo")

    config("SOME_VAR", help_text="some var")

    rst = textwrap.dedent("""
        .. config-param:: SOME_VAR
    """)

    doc = parse_rst(rst)

    expected = "* SOME_VAR: some var.<br>"

    assert expected == doc


def test_config_param_variable_does_not_exist(monkeypatch):
    rst = textwrap.dedent("""
        .. config-param:: NON_EXISTENT_VAR
    """)

    with pytest.raises(ValueError):
        parse_rst(rst)


#
# Config group directive tests
#


def test_config_group():
    config("DB_USER", help_text="db username.", group="Database", default="foo")
    config("DB_PASSWORD", help_text="db password", group="Database", default="bar")

    rst = textwrap.dedent("""
        .. config-group:: Database
    """)

    doc = parse_rst(rst)

    expected = (
        "* DB_USER: db username. Defaults to: foo.<br>"
        "* DB_PASSWORD: db password. Defaults to: bar.<br>"
    )

    assert expected == doc


def test_config_group_cannot_use_members_groups_and_exclude_groups_together():
    config("DB_USER", help_text="db username", group="Database", default="foo")
    config("DB_PASSWORD", help_text="db password", group="Database", default="bar")

    rst = textwrap.dedent("""
        .. config-group:: Database
            :members: DB_USER
            :exclude: DB_PASSWORD
    """)

    with pytest.raises(ValueError):
        parse_rst(rst)


def test_config_group_do_not_add_var_to_docs():
    config("DB_USER", help_text="db username", group="Database", default="foo")
    config("DB_PASSWORD", help_text="db password", group="Database", default="bar")
    config(
        "VAR_TO_IGNORE",
        help_text="ignore",
        group="Database",
        default="bar",
        add_to_docs=False,
    )

    rst = textwrap.dedent("""
        .. config-group:: Database
    """)

    doc = parse_rst(rst)

    expected = (
        "* DB_USER: db username. Defaults to: foo.<br>"
        "* DB_PASSWORD: db password. Defaults to: bar.<br>"
    )

    assert expected == doc


def test_config_group_members():
    config("DB_USER", help_text="db username", group="Database", default="foo")
    config("DB_PASSWORD", help_text="db password", group="Database", default="bar")
    config("PARAM_TO_EXCLUDE1", help_text="exclude", group="Database", default="bar")
    config("PARAM_TO_EXCLUDE2", help_text="exclude", group="Database", default="bar")

    rst = textwrap.dedent("""
        .. config-group:: Database
            :members: DB_USER, DB_PASSWORD
    """)

    doc = parse_rst(rst)

    expected = (
        "* DB_USER: db username. Defaults to: foo.<br>"
        "* DB_PASSWORD: db password. Defaults to: bar.<br>"
    )

    assert expected == doc


def test_config_group_exclude_params():
    config("DB_USER", help_text="db username", group="Database", default="foo")
    config("DB_PASSWORD", help_text="db password", group="Database", default="bar")
    config("PARAM_TO_EXCLUDE1", help_text="exclude", group="Database", default="bar")
    config("PARAM_TO_EXCLUDE2", help_text="exclude", group="Database", default="bar")

    rst = textwrap.dedent("""
        .. config-group:: Database
            :exclude: PARAM_TO_EXCLUDE1, PARAM_TO_EXCLUDE2
    """)

    doc = parse_rst(rst)

    expected = (
        "* DB_USER: db username. Defaults to: foo.<br>"
        "* DB_PASSWORD: db password. Defaults to: bar.<br>"
    )

    assert expected == doc


#
# All config params directive tests
#


def test_config_all_params():
    config("DB_USER", help_text="db username", group="Database", default="foo")
    config("DB_PASSWORD", help_text="db password", group="Database", default="bar")
    config(
        "ALLOWED_HOSTS",
        help_text="allowed hosts",
        group="Required",
        split=True,
        default="",
    )
    config("SESSION_COOKIE_AGE", help_text="session cookie age", default=1234)

    rst = textwrap.dedent("""
        .. config-all-params::
    """)

    doc = parse_rst(rst)

    expected = (
        "Required\n\n"
        "* ALLOWED_HOSTS: allowed hosts. Defaults to: (empty string).<br>\n\n"
        "Database\n\n"
        "* DB_USER: db username. Defaults to: foo.<br>"
        "* DB_PASSWORD: db password. Defaults to: bar.<br>\n\n"
        "Optional\n\n"
        "* SESSION_COOKIE_AGE: session cookie age. Defaults to: 1234.<br>"
    )

    assert expected == doc


def test_config_all_params_cannot_use_members_groups_and_exclude_groups_together():
    config("DB_USER", help_text="db username", group="Database", default="foo")
    config("DB_PASSWORD", help_text="db password", group="Database", default="bar")
    config(
        "ALLOWED_HOSTS",
        help_text="allowed hosts",
        group="Required",
        split=True,
        default="",
    )
    config("SESSION_COOKIE_AGE", help_text="session cookie age", default=1234)

    rst = textwrap.dedent("""
        .. config-all-params::
            :members-groups: Database
            :exclude-groups: Required
    """)

    with pytest.raises(ValueError):
        parse_rst(rst)


def test_config_all_params_exclude_groups():
    config("DB_USER", help_text="db username", group="Database", default="foo")
    config("DB_PASSWORD", help_text="db password", group="Database", default="bar")
    config(
        "ALLOWED_HOSTS",
        help_text="allowed hosts",
        group="Required",
        split=True,
        default="",
    )
    config("SESSION_COOKIE_AGE", help_text="session cookie age", default=1234)
    config("SESSION_COOKIE_AGE", help_text="session cookie age", default=1234)
    config("PARAM_TO_EXCLUDE1", help_text="exclude", group="Database", default="bar")
    config("PARAM_TO_EXCLUDE2", help_text="exclude", default="bar")

    rst = textwrap.dedent("""
        .. config-all-params::
            :exclude-groups: Database, Optional
    """)

    doc = parse_rst(rst)

    expected = (
        "Required\n\n* ALLOWED_HOSTS: allowed hosts. Defaults to: (empty string).<br>"
    )

    assert expected == doc


def test_config_all_params_members_groups():
    config("DB_USER", help_text="db username", group="Database", default="foo")
    config("DB_PASSWORD", help_text="db password", group="Database", default="bar")
    config(
        "ALLOWED_HOSTS",
        help_text="allowed hosts",
        group="Required",
        split=True,
        default="",
    )
    config("SESSION_COOKIE_AGE", help_text="session cookie age", default=1234)

    rst = textwrap.dedent("""
        .. config-all-params::
            :members-groups: Database, Required
    """)

    doc = parse_rst(rst)

    expected = (
        "Required\n\n"
        "* ALLOWED_HOSTS: allowed hosts. Defaults to: (empty string).<br>\n\n"
        "Database\n\n"
        "* DB_USER: db username. Defaults to: foo.<br>"
        "* DB_PASSWORD: db password. Defaults to: bar.<br>"
    )

    assert expected == doc


def test_config_all_params_exclude_params():
    config("DB_USER", help_text="db username", group="Database", default="foo")
    config("DB_PASSWORD", help_text="db password", group="Database", default="bar")
    config("SESSION_COOKIE_AGE", help_text="session cookie age", default=1234)
    config("SESSION_COOKIE_AGE", help_text="session cookie age", default=1234)
    config("PARAM_TO_EXCLUDE1", help_text="exclude", group="Database", default="bar")
    config("PARAM_TO_EXCLUDE2", help_text="exclude", default="bar")

    rst = textwrap.dedent("""
        .. config-all-params::
            :exclude-params: PARAM_TO_EXCLUDE1, PARAM_TO_EXCLUDE2
    """)

    doc = parse_rst(rst)

    expected = (
        "Database\n\n"
        "* DB_USER: db username. Defaults to: foo.<br>"
        "* DB_PASSWORD: db password. Defaults to: bar.<br>\n\n"
        "Optional\n\n"
        "* SESSION_COOKIE_AGE: session cookie age. Defaults to: 1234.<br>"
    )

    assert expected == doc


def test_config_all_params_do_not_add_param_to_docs():
    config("DB_USER", help_text="db username", group="Database", default="foo")
    config("DB_PASSWORD", help_text="db password", group="Database", default="bar")
    config(
        "ALLOWED_HOSTS",
        help_text="allowed hosts",
        group="Required",
        split=True,
        default="",
    )
    config(
        "SESSION_COOKIE_AGE",
        help_text="session cookie age",
        default=1234,
        add_to_docs=False,
    )

    rst = textwrap.dedent("""
        .. config-all-params::
            :exclude-params: PARAM_TO_EXCLUDE1, PARAM_TO_EXCLUDE2
    """)

    doc = parse_rst(rst)

    expected = (
        "Required\n\n"
        "* ALLOWED_HOSTS: allowed hosts. Defaults to: (empty string).<br>\n\n"
        "Database\n\n"
        "* DB_USER: db username. Defaults to: foo.<br>"
        "* DB_PASSWORD: db password. Defaults to: bar.<br>"
    )

    assert expected == doc
