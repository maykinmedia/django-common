import os

import pytest
import structlog
from structlog.testing import LogCapture

os.environ.setdefault("AUDIT_LOGGER_NAME", "tests_audit")


@pytest.fixture(name="log_output")
def fixture_log_output():
    return LogCapture()


@pytest.fixture(autouse=True)
def fixture_configure_structlog(log_output: LogCapture):
    structlog.configure(processors=[log_output])


@pytest.fixture(scope="session", autouse=True)
def connect_account_audit_signals():
    from maykin_common.accounts.audit import connect_signals

    connect_signals()
