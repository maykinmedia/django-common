.. _quickstart:

==========
Quickstart
==========

maykin-common is based around the principle of "zero-cost" utilities and optional
dependency groups. A bare bones installation gives you some useful bits, but depending
on your project needs you likely want to install some extras.

.. note:: A quick recap: extra's in python packages are additional labels you can
   pass between square brackets to opt-in to additional dependencies, like so:

   .. code-block:: bash

      uv pip install maykin-common[extra1,extra2]

Installation
============

You'll always want to install the base package, e.g.:

.. code-block:: bash

    uv pip install maykin-common

However, the usefulness increases with each extra. Each one of them is described below.

.. tip:: default-project is pre-configured with the typical set of extras that apply
   to the majority of projects:

   .. code-block:: bash

       uv pip install maykin-common[axes,mfa]

MFA
---

Install command:

.. code-block:: bash

    uv pip install maykin-common[mfa]

The MFA (multi-factor authentication) extra integrates
`django-admin-index <https://pypi.org/project/django-admin-index>`_ and
`maykin-2fa <https://pypi.org/project/maykin-2fa>`_. In particular, it controls the
navigation menu when you're authenticated but not verified with your second factor yet.

These packages and this extra are by default enabled in default-project.

For more details, see :mod:`maykin_common.django_two_factor_auth`.

Axes
----

Install command:

.. code-block:: bash

    uv pip install maykin-common[axes]

Used for the throttling view mixins.

`django-axes <https://pypi.org/project/django-axes>`_ is our standard solution to
prevent brute forced logins and is included by default via default-project. It provides
a helper to get the remote IP address of the person trying to log in, which is used in
the throttling implementation.

For more details, see :mod:`maykin_common.throttling`.

.. _quickstart_pdf:

PDF
---

Install command:

.. code-block:: bash

    uv pip install maykin-common[pdf]

.. note:: You must define the setting ``PDF_BASE_URL_FUNCTION`` - a callable taking no
   arguments that returns the absolute base URL where your site/project is running. It
   is used to recognize references to your static assets (CSS and uploaded media).

The PDF extra provides an easy to use template-based PDF generation helper, using
`WeasyPrint <https://pypi.org/project/weasyprint>`_. It is optimized to load static
assets (CSS/images/...) from disk rather than making network round trip.

For details about the API, see :mod:`maykin_common.pdf`.

.. _quickstart_vcr:

VCR
---

Use VCR_ to do snapshot testing of outgoing HTTP requests.

Install command:

.. code-block:: bash

    uv pip install maykin-common[vcr]


Record modes
""""""""""""
VCR `record modes`_ can be controlled with the ``VCR_RECORD_MODE`` env
variable. It defaults to ``"none"``. During development add
``VCR_RECORD_MODE=once`` to your dotenv and toggle it on or off either with the
env variable or by setting the bool ``vcr_enabled`` class attribute on the
testcase you're working on.

Checking cassette staleness
~~~~~~~~~~~~~~~~~~~~~~~~~~~
When you're cutting a new release. The easiest way to check if your snapshots
are still a good representation of reality is to delete all cassettes and run
all tests that have the ``vcr`` tag. The diff of failing tests, should be a
helpful pointer to a fix.

For details about the API, see :mod:`maykin_common.vcr`.

.. _VCR: https://vcrpy.readthedocs.io
.. _`record modes`: https://vcrpy.readthedocs.io/en/latest/usage.html#record-modes


Usage
=====

All modules in maykin-common either only require Django to be available, or require some
optional dependencies. Optional modules have zero footprint as long as you don't import
them, and when you do use them, ensure you've installed the appropriate extra.

API projects (team bron)
------------------------

For API projects, see :ref:`apis`.

Open Telemetry
--------------

See :ref:`otel` to configure metrics, traces and logging.

Other
-----

See the reference documentation for details.
