.. _reference_csp:

=======================
Content Security Policy
=======================

See :ref:`csp` for the setup and usage guide.

Middleware
==========

.. automodule:: maykin_common.csp.middleware
    :members:
    :undoc-members:

Models
======

.. Not auto-documented: importing this module fails under autodoc's mocked "django"
   (see autodoc_mock_imports in conf.py) because CSPDirective.choices doesn't exist
   on a mocked TextChoices. The fields are documented by hand below instead.

``maykin_common.csp.models.CSPSetting``
---------------------------------------

A single directive/value pair that is merged into the configured policy. The fields
are:

``directive``
    The CSP directive to extend, one of :class:`maykin_common.csp.constants.CSPDirective`.

``value``
    A single source for that directive, e.g. ``https://cdn.example.com``. Add one
    record per source.

``identifier``
    Optional free-form label recording where the entry came from. It is never sent to
    the browser, and it scopes the ``set_for`` manager method.

``content_type`` / ``object_id`` / ``content_object``
    An optional `generic relation`_ to the object that provided the entry. Entries
    added by hand through the admin leave these empty.

``maykin_common.csp.models.CSPSettingManager``
-----------------------------------------------

.. py:method:: CSPSetting.objects.as_dict()

    Return the settings as a mapping of directive name to its list of sources.
    Duplicate values are collapsed, and both directives and values are sorted so that
    the resulting header is stable. Available on querysets too, so it can be narrowed
    with a filter first.

.. py:method:: CSPSetting.objects.set_for(obj, settings, identifier="")

    Replace the entries connected to ``obj`` with the provided ones, in a single
    transaction.

    ``settings`` is a list of two-tuples of the directive and the value. Entries
    previously recorded for the same object *and* identifier are deleted first, so this
    is safe to call on every save of a configuration model. Entries belonging to a
    different object or identifier are left untouched.

    The directive cache is invalidated as part of the call.

.. _generic relation: https://docs.djangoproject.com/en/stable/ref/contrib/contenttypes/#generic-relations

Constants
=========

.. automodule:: maykin_common.csp.constants
    :members:
    :undoc-members:

Caching
=======

.. automodule:: maykin_common.csp.cache
    :members:
    :undoc-members:
