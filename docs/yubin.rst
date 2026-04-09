.. _yubin:

========================
De-celeried Django Yubin
========================

.. versionadded:: 0.19.0

    Added yubin celery cronjob bypass.

Re-writes parts of `Django Yubin`_ to bypass the need for celery tasks to queue and send emails.

Quickstart (tl;dr)
==================

Install the extra dependencies:

.. code-block:: bash

    uv pip install maykin-common[yubin]

Update your settings accordingly:

.. code-block:: python

    INSTALLED_APPS = [
        ...,
        "django_yubin",
        "maykin_common.yubin",
        ...
    ]

    # use this instead of django-yubins backend
     EMAIL_BACKEND = "maykin_common.yubin.backends.QueuedEmailBackend"
     MAILER_USE_BACKEND = "django.core.mail.backends.smtp.EmailBackend" # the same setting from Django-yubin

Now using django's ``send_mail`` will create and save a queued yubin ``Message`` without using the ``send_email`` task.
Then management commands and cronjobs can be used to send and retry emails without celery.


Management Commands
===================

Updates or deletes ``django-yubin`` ``Message`` emails bypassing the celery tasks.

delete_old_emails
-----------------

.. code-block:: bash

    ./manage.py delete_old_emails --days 90

Delete `Message` instances that are older than a certain number of days.
By default this is 90 days but can be changed using ``--days`` argument.

retry_emails
------------

.. code-block:: bash

    ./manage.py retry_emails --max-retries 0

Updates retryable `Messages` by changing their status back to queued. By default it will not allow retries
but this can be changed with the ``--max-retries`` or ``-m`` arguments

send_all_mail
-------------

.. code-block:: bash

    ./manage.py send_all_mail

Sends all queued `Messages`.

.. _Django Yubin: https://django-yubin.readthedocs.io/en/latest/
