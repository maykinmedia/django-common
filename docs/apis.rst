.. _apis:

============
API projects
============

Many of the Maykin projects are API-first projects with only a minimum of "public
frontend" requirements. maykin-common facilitates these by providing some base
templates, CSS and JS for the landing page.

Templates
=========

Two templates are provided from the library that you should extend:

* ``maykin_common/api/index_base.html``, use it in ``index.html`` for your landing page
* ``maykin_common/api/includes/footer.html``, use it to extend your
  ``includes/footer.html`` from

If your project has multiple API components, there is a third template you should extend to create the page for each component.

* ``maykin_common/api/index_component.html``, use it in ``api_component.html`` for your API component page.

You'll need to make some modifications to the root ``urls.py`` and ``master.html`` to
wire up everything automatically.

.. tip:: With the default project setup, the necessary CSS and Javascript are
   automatically loaded. If you use another master template, make sure to define the
   ``view_class``, ``extra_css`` and ``content`` blocks to override.

``maykin_common/api/index_base.html``
-------------------------------------

Provides the general scaffolding of the language page with the tabbed layout for
Dutch and English content and the general branding.

In your child template, make sure to override the blocks that are specific to your
project:

* ``page_title``
* ``page_subtitle``
* ``content_nl``
* ``content_en``
* ``license_link``
* ``api_links``

.. tip:: The base template defines a block called ``api_links`` that displays two links for the API interface: **API docs (ReDoc)** and
  **Open API specification**. If the variables ``api_docs_link`` and ``api_schema_link`` are not provided to the template, the fallback values ``default_api_docs_link`` and ``default_api_schema_link`` are used instead. A child template can override the ``api_links`` block and explicitly provide the URLs.

For example:

.. code-block:: django

    {% block api_links %}

        {% url 'schema-redoc' version=version as api_docs_link %}
        {% url 'schema-json' as api_schema_link %}

        {% with api_docs_link=api_docs_link api_schema_link=api_schema_link %}
            {{ block.super }}
        {% endwith %}

    {% endblock %}

.. tip:: To add extra buttons next to the ``api_links`` in the template, use the ``extra_buttons`` block.
    This allows you to include custom actions without modifying the base template.

``maykin_common/api/index_component.html``
------------------------------------------

Provides the standard initialization for an API component page and contains the links for ``api_docs``, ``api_schema`` and ``notifications``.

In your child template, make sure to override the blocks that are specific to your API component:

* ``page_title``
* ``page_subtitle``
* ``title_component``
* ``subtitle_component``
* ``api_links``

``maykin_common/api/includes/footer.html``
------------------------------------------

Provides the standard footer layout with sensible defaults. You can override (default)
values by clever usage of the ``with`` tag:

.. code-block:: django

    {% block footer %}
        {% capture as issues_link silent %}<a class="link link--muted" href="https://github.com/maykinmedia/awesome-project/issues">issues</a>{% endcapture %}

        {% with issues_link=issues_link %}
            {{ block.super }}
        {% endwith %}

    {% endblock %}

.. tip:: Consider installing django-capture-tag for cleaner templates, like the example
   above.

.. tip:: To add extra buttons next to the ``api_links`` in the template, use the ``extra_buttons`` block.
    This allows you to include custom actions without modifying the base template.

Blocks you'll typically want to override are:

* ``footer``
* ``links`` - the middle column with project-specific links

Other blocks you can override are:

* ``other_links`` - the links in the rightmost column

Stylesheets
===========

The base template automatically loads the ``maykin_common/css/api.css`` stylesheets
which contains the majority of the styles for the landing page components.

.. note:: While the default template uses font-awesome class names, the font-awesome
   stylesheet is **not** included as we want to avoid any frontend toolchains as long
   as possible. You have to make sure your project includes the styles and font assets
   yourself.

.. tip:: No default values are provided, however the default-project template does
   provide a starter setup in the ``_os_api`` directory.

The CSS is written with theming in mind. At the time of writing, the following CSS
variables are supported, grouped by component:

**Page title**

* ``--page-title-color``
* ``--page-title-font-family``

**Footer**

* ``--footer-border-color``

**Tabs**

* ``--tabs-border-color``
* ``--tabs-item-color``
* ``--tabs-item-hover-color``
* ``--tabs-item-hover-border-color``

**Button**

* ``--button-color``
* ``--button-background-color``
* ``--button-hover-background-color``
* ``--button-alert-background-color``
* ``--button-alert-hover-background-color``

**Link**

* ``--link-color``
* ``--link-color-hover``
* ``--link-color-muted``

Javascript
==========

We ship a minimal amount of Javascript and it's automatically loaded from the base
template.

``maykin_common/js/nav-tabs.js``
--------------------------------

Controls the (active) tab state for the ``.tabs`` component.
