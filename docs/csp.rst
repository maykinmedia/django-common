.. _csp:

=======================
Content Security Policy
=======================

.. versionadded:: 0.24.0

    Added database-managed CSP directives on top of django-csp.

`django-csp`_ builds the ``Content-Security-Policy`` header from a policy defined in
your settings. That policy is static: changing it requires a code change and a deploy.

This extra provides a middleware that will merge, via a Django model,
administrator-supplied CSP directives into the statically configured base policy. This
is to allow administrators to configure an extra CDN, analytics, or other media,
without a code change or a deploy.

Reading those entries is cached, so the performance penalty per request is minimal.

.. note:: The directives in the database can only *add* sources to the policy. They
   cannot remove or relax anything that is configured in the settings, and they cannot
   turn a boolean directive such as ``upgrade-insecure-requests`` on or off.

Quickstart (tl;dr)
==================

Install the extra dependencies:

.. code-block:: bash

    uv pip install maykin-common[csp]

Update your settings:

.. code-block:: python

    INSTALLED_APPS = [
        ...,
        # both are needed: "csp" is django-csp itself, which builds the header,
        # while "maykin_common.csp" provides the model holding the extra directives
        "csp",
        "maykin_common.csp",
        ...
    ]

    MIDDLEWARE = [
        ...,
        # use this *instead of* "csp.middleware.CSPMiddleware"
        "maykin_common.csp.middleware.CSPMiddleware",
        ...
    ]

``django.contrib.contenttypes`` must be installed too, though it is part of the
Django defaults.

Then run the migrations:

.. code-block:: bash

    ./manage.py migrate

Finally, define your policy the way `django-csp`_ documents it. Nothing changes from
the library's own instructions:

.. code-block:: python

    from csp.constants import SELF

    CONTENT_SECURITY_POLICY = {
        "DIRECTIVES": {
            "default-src": [SELF],
            "img-src": [SELF, "https://cdn.example.com"],
        },
    }

A system check warns you when ``maykin_common.csp`` is installed but the middleware is
missing, because in that case the database entries are silently ignored.

How the merge works
===================

Database entries are appended to a directive rather than replacing it, the same way
django-csp's ``@csp_update`` decorator behaves.

Given the settings above and a database entry of ``img-src``
``https://analytics.example.com``, the response header becomes:

.. code-block:: none

    default-src 'self'; img-src 'self' https://cdn.example.com https://analytics.example.com

A few details worth knowing:

* Directives that are not present in the settings at all are added to the policy.
* Duplicate values are collapsed, and values are sorted, so the header is stable.
* Entries are applied to both ``CONTENT_SECURITY_POLICY`` and
  ``CONTENT_SECURITY_POLICY_REPORT_ONLY``. The browser evaluates the two
  independently, so a source added to only one of them would still be reported as a
  violation under the other.
* Values added by django-csp's decorators are preserved and merged with the ones from
  the database.
* Responses marked as exempt, and URLs matching ``EXCLUDE_URL_PREFIXES``, are left
  alone. Nonces keep working as before.

Caching
=======

The directives are cached, so they do not incur the cost of a database query on
every response. The caching behavior can be controlled via two settings:

* :attr:`~maykin_common.settings.MKN_CSP_CACHE_TIMEOUT` - how long to cache the
  directives, in seconds. Defaults to ``60``. Use ``0`` to disable caching entirely.
  Caching indefinitely through ``None`` is not supported: a system check flags it
  as an error.
* :attr:`~maykin_common.settings.MKN_CSP_CACHE_ALIAS` - which entry of the ``CACHES``
  setting to use. Defaults to ``"default"``.

Saving or deleting a CSP setting invalidates the cache, so changes made in the admin
take effect immediately. With a local-memory cache that only applies to the worker
process that handled the save, and the others keep their own copy until the timeout
expires.

If the cache cannot be reached, the directives are read from the database instead.

Managing entries
================

Through the admin
-----------------

The ``CSPSetting`` model is registered in the Django admin. Each entry is a directive
and a single value, for example ``img-src`` and ``https://analytics.example.com``. Add
one row per value.

The ``identifier`` field is a free-form label to record where an entry came from. It is
never sent to the browser.

From a configuration model
--------------------------

Projects often have a configuration model where an administrator pastes, say, an
analytics URL. The sources that URL needs can be registered alongside it, using the
generic relation on the model:

.. code-block:: python

    from maykin_common.csp.constants import CSPDirective
    from maykin_common.csp.models import CSPSetting


    class AnalyticsConfiguration(models.Model):
        matomo_url = models.URLField(blank=True)

        def save(self, *args, **kwargs):
            super().save(*args, **kwargs)
            CSPSetting.objects.set_for(
                self,
                [
                    (CSPDirective.SCRIPT_SRC, self.matomo_url),
                    (CSPDirective.CONNECT_SRC, self.matomo_url),
                ],
                identifier="matomo",
            )

``CSPSetting.objects.set_for`` deletes the entries previously recorded for that object
before creating the new ones, so it is safe to call on every save. Entries recorded
under a different ``identifier``, or for a different object, are left untouched.

Custom middleware
=================

If you already use a different django-csp middleware - the rate-limiting one, for
instance - mix the behaviour into it rather than replacing it:

.. code-block:: python

    from csp.contrib.rate_limiting import RateLimitedCSPMiddleware

    from maykin_common.csp.middleware import DatabaseDirectivesMixin


    class CSPMiddleware(DatabaseDirectivesMixin, RateLimitedCSPMiddleware):
        pass

The mixin must come first in the bases. The system check resolves each entry of
``MIDDLEWARE`` and looks for the mixin, so a middleware of your own is recognized just
as well as the one shipped here.

For details about the API, see :ref:`reference_csp`.

.. _django-csp: https://django-csp.readthedocs.io/en/latest/
