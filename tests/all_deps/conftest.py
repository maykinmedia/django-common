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
