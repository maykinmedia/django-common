.. _env_config_and_docs:

====================================================
Environment variable configuration and documentation
====================================================

Configuration helper
--------------------

This library provides utilities and Sphinx directives to generate documentation for environment variables that are
used in your project. The :func:`open_api_framework.conf.utils.config` can be used for this as follows to
specify environment variable documentation. By default, all environment variables are added
to the documentation (unless ``add_to_docs=False`` is passed to ``config``).

For more details, refer to :func:`maykin_common.config_helpers.config`.

.. code:: python

    from maykin_common.config_helpers import config

    ALLOWED_HOSTS = config(
        "ALLOWED_HOSTS",
        default="",
        split=True,
        help_text=(
            "a comma separated (without spaces!) list of domains that serve "
            "the installation. Used to protect against Host header attacks."
        ),
        group="Required",
    )

Documentation helpers
---------------------

In order to document environment variables that are defined in this way, there are three
Sphinx directives that can be used.

To document all groups of environment variables, the ``config-all-params`` directive
(:class:`maykin_common.documentation.config_directives.ConfigAllParamsDirective`) can be used.
This directive accepts the following optional arguments:

* ``members-groups`` to only use the specified groups
* ``exclude-groups`` to exclude the specified groups (cannot be used together with ``members-groups``)
* ``exclude-params`` to exclude the specified environment variables

Example usage:

.. code:: rst

    .. config-all-params::
        :exclude-groups: Celery, Database


To document a specific group of environment variables, the ``config-group`` directive
(:class:`maykin_common.documentation.config_directives.ConfigGroupDirective`) can be used.
This directive accepts the following optional arguments:

* ``members`` to only use the specified environment variables
* ``exclude`` to exclude the specified environment variables (cannot be used together with ``members``)

Example usage:

.. code:: rst

    .. config-group:: Database
        :exclude: DB_POOL_MAX_LIFETIME, DB_POOL_NUM_WORKERS

To document a single environment variable, the ``config-param`` directive
(:class:`maykin_common.documentation.config_directives.ConfigParamDirective`) can be used.
This directive accepts the following optional arguments:

* ``default`` to override the default as defined in the code

.. code:: rst

    .. config-param:: DISABLE_2FA
        :default: True

