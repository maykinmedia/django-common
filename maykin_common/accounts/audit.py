"""
Provide audit logging hooks for account/authentication related events.

Audit events are emitted for the following (optional) libraries when they're available:

* django-axes: lock out events
* django-hijack: hijack start and end events

We always emit events for successful user log ins, log outs and login failures.

.. note::

    Installing the audit hooks requires structlog to be set up.
"""

from typing import Literal

from django.apps import apps
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.http import HttpRequest

from ..logging.audit import audit_logger

try:
    from axes.helpers import get_client_ip_address
except ImportError:
    # fallback, in reverse-proxy setups this will report the proxy IP address and is
    # not very useful
    def get_client_ip_address(request: HttpRequest) -> str | None:
        return request.META.get("REMOTE_ADDR", None)


#
# CORE DJANGO
#


def on_user_logged_in(
    *,
    sender: type[AbstractBaseUser],
    request: HttpRequest,
    user: AbstractBaseUser,
    **kwargs,
) -> None:
    """
    Audit log a successful user login.
    """
    audit_logger.info(
        "user_logged_in",
        username=user.get_username(),
        login_path=request.path,
        ip_address=get_client_ip_address(request),
    )


def on_user_logged_out(
    *,
    sender: type[AbstractBaseUser],
    request: HttpRequest,
    user: AbstractBaseUser | None,
    **kwargs,
) -> None:
    """
    Audit log a successful user logout.
    """
    if user is None:
        return
    audit_logger.info(
        "user_logged_out",
        username=user.get_username(),
        logout_path=request.path,
        ip_address=get_client_ip_address(request),
    )


def on_user_login_failed(
    *,
    sender: str,
    request: HttpRequest | None,
    credentials: object,
    **kwargs,
) -> None:
    """
    Audit log a failed user login.
    """
    audit_log = audit_logger
    if request is not None:
        audit_log = audit_log.bind(
            login_path=request.path,
            ip_address=get_client_ip_address(request),
        )

    # axes has some complicated logic to extract the username from the credentials dict
    # that's passed to the auth backends. Since we only target username/password brute
    # forcing with a derivation of the built-in model backend, we can rely on a
    # hardcoded `username` field in the credentials for the logging purposes.
    if isinstance(credentials, dict) and (username := credentials.get("username")):
        audit_log = audit_log.bind(username=username)

    audit_log.warning("user_login_failed")


#
# DJANGO-AXES
#


def on_user_locked_out(
    *,
    sender: Literal["axes"],
    request: HttpRequest | None,
    username: str,
    ip_address: str | None,
    **kwargs,
) -> None:
    """
    Audit log when a user is locked out by axes.
    """
    audit_logger.warning("user_locked_out", username=username, ip_address=ip_address)


#
# DJANGO-HIJACK
#
def on_hijack_started(
    *,
    sender: None,
    request: HttpRequest,
    hijacker: AbstractBaseUser,
    hijacked: AbstractBaseUser,
    **kwargs,
) -> None:
    """
    Audit log when a user hijacks another user.
    """
    audit_logger.info(
        "hijack_started",
        hijacker=hijacker.get_username(),
        hijacked=hijacked.get_username(),
    )


def on_hijack_ended(
    *,
    sender: None,
    request: HttpRequest,
    hijacker: AbstractBaseUser,
    hijacked: AbstractBaseUser,
    **kwargs,
) -> None:
    """
    Audit log when a user releases another user's hijack.
    """
    audit_logger.info(
        "hijack_ended",
        hijacker=hijacker.get_username(),
        hijacked=hijacked.get_username(),
    )


#
# ENTRYPOINT
#


def connect_signals() -> None:
    # core django signals can always be connected
    user_logged_in.connect(
        on_user_logged_in,
        dispatch_uid="maykin_common.accounts.audit.on_user_logged_in",
    )
    user_logged_out.connect(
        on_user_logged_out,
        dispatch_uid="maykin_common.accounts.audit.on_user_logged_out",
    )
    user_login_failed.connect(
        on_user_login_failed,
        dispatch_uid="maykin_common.accounts.audit.on_user_login_failed",
    )

    if apps.is_installed("axes"):
        from axes.signals import user_locked_out

        user_locked_out.connect(
            on_user_locked_out,
            dispatch_uid="maykin_common.accounts.audit.on_user_locked_out",
        )

    if apps.is_installed("hijack"):
        from hijack.signals import hijack_ended, hijack_started

        hijack_started.connect(
            on_hijack_started,
            dispatch_uid="maykin_common.accounts.audit.on_hijack_started",
        )
        hijack_ended.connect(
            on_hijack_ended,
            dispatch_uid="maykin_common.accounts.audit.on_hijack_ended",
        )
