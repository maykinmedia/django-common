"""
Expose an audit logger that can be imported by projects or (sub) packages.

The name of the audit logger is configured from the environment variables (not Django
settings), so that each project gets a unique but similarly structured audit logger
name. The convention is to use ``AUDIT_LOGGER_NAME=my_app_audit``.

Note that the audit logging has a hard requirement on ``structlog``, see the docs on
how to set it up.
"""

import warnings

import structlog

from ..config import config

__all__ = ["audit_logger"]

if not (logger_name := config("AUDIT_LOGGER_NAME", default="")):  # pragma: no cover
    logger_name = "maykin_common_audit"
    warnings.warn(
        "You should explicitly define 'AUDIT_LOGGER_NAME' to classify audit logs "
        "between different projects.",
        RuntimeWarning,
        stacklevel=1,
    )

audit_logger = structlog.stdlib.get_logger(logger_name)
