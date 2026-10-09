.. _reference_admin_login:

================
Admin login page
================

In many projects, it's possible to login to the admin environment with Single Sign On
via OpenID Connect, we typically provide through ``mozilla-django-oidc-db``. Most
projects also use ``maykin-2fa`` to enforce multifactor authentication for admin users.

``maykin-common`` provides a template and CSS to declutter the login page and allow
users to choose which login option they want to use. When integrated (depending on
whether admin OIDC login is enabled), clean login options are presented and only after
clicking the local user account option are the username and password fields displayed.

Requirements
============

You must have the following packages installed and enabled, as the utility brings their
interaction together:

* ``maykin-2fa``, version 2.2.0 or newer
* ``mozilla-django-oidc-db``, version 1.0 or newer

Configuration
=============

In your project, you must define a template override of the default maykin-2fa admin
login template. In there, include the template and CSS from maykin-common.

.. code-block:: django
   :caption: src/project_name/templates/maykin_2fa/login.html
   :linenos:
   :emphasize-lines: 6,9-11

   {% extends "maykin_2fa/login.html" %}
   {% load static %}

   {% block extrastyle %}
       {{ block.super }}
       <link rel="stylesheet" href="{% static "maykin_common/css/admin_login.css" %}">
   {% endblock %}

   {% block login_form_container %}
       {% include "maykin_common/maykin_2fa/admin/oidc_login_options.html" with block_super=block.super %}
   {% endblock login_form_container %}
