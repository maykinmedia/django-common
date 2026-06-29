.. _reference_branding:

========
Branding
========

maykin-common is typically used in Open Source products developed by
`Maykin <https://maykin.nl>`_. We provide some tooling to add branding information to
the footer of the admin to make it clear which product is being used. Additionally,
when the product is repackaged/redistributed under a custom name, the branding for this
custom name can also be added.

.. versionadded:: 0.20.0

Enable branding
===============

Settings
--------

Configuration is primarily done through Django settings:

.. code-block:: python

    from maykin_common.branding import ProductDefinition

    MKN_BRANDING_PRODUCT_DEFINITION = ProductDefinition(
        name="Maykin Common",
        hyperlink="https://github.com/maykinmedia/django-common",
        logo_path="maykin_common/ico/favicon-32x32.png",
    )

    MKN_BRANDING_DERIVED_PRODUCT_DEFINITION = ProductDefinition(
        name="Derived Common",
        hyperlink="https://github.com/maykinmedia/django-common",
        logo_path="maykin_common/ico/favicon-32x32.png",
    )

where only the ``name`` is a required parameter. If URLs are provided, the name will
link to them.

Logo configuration
~~~~~~~~~~~~~~~~~~

Optionally, you can display a small favicon sized logo in front of the product name.
This image should not be bigger than 32x32.

For the developers of the product, we recommend checking in the logo in one of your
staticfiles directories, and configuring ``logo_path`` accordingly.

For derived products, we recommend specifying the URL of a logo image via ``logo_url``.
You can make sure the logo exists in the ``settings.MEDIA_ROOT`` and configure it as
``/media/path/to/logo.png``, or host it somewhere else and provide the fully qualified
URL, e.g. ``https://example.com/my-awesome/logo.svg``.

.. warning:: When hosting the logo externally, you may need to tweak the
   Content-Security-Policy configuration to make sure the browser loads the logo.

Templates
---------

In your project, define a custom template for the admin base site:
``templates/admin/base_site.html`` and override the footer block:

.. code-block:: django

    {# Django 5.2 puts this block inside the <footer id="footer"> element #}
    {% block footer %}
        {% include "maykin_common/includes/footer.html" with user=user only %}
    {% endblock %}

This will emit the branding (if configured) and version information.

Styling
=======

Styling options are limited, though you can define CSS variables for the logo sizes:

``--mkn-product-branding-logo-maykin-max-block-size``
    Maximum block size (height, in this case) of the Maykin logo. Defaults to 20px.

``--mkn-product-branding-logo-favicon-max-block-size``
    Maximum block size (height, in this case) of a product favicon logo. Defaults to
    24px.

Reference
=========

.. autoclass:: maykin_common.branding.ProductDefinition
    :members:
