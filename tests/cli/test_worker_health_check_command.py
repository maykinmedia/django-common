import subprocess
import time
from collections.abc import Callable
from pathlib import Path

import pytest
from celery import Celery
from typer.testing import CliRunner

from maykin_common.cli import (
    _WORKER_EXIT_CODE_EVENT_LOOP_BROKEN,
    _WORKER_EXIT_CODE_NOT_READY,
    _WORKER_EXIT_CODE_PING_FAILURE,
    app,
)

ROOT_DIR = Path(__file__).parent.parent.parent.resolve()

runner = CliRunner()

celery_app = Celery("maykin-common-tests", broker="redis://localhost:6379/0")


@pytest.fixture
def start_worker_process():
    """
    Start a subprocess running worker and stop it when the test exits.
    """
    cmd = [
        "celery",
        "--workdir",
        str(ROOT_DIR),
        "--app",
        f"{__name__}:celery_app",
        "worker",
        "--hostname",
        "celery@test",
        "--loglevel",
        "DEBUG",
        "-c",
        "1",
    ]

    # start the process and let it run in the background - it should not exit by itself.
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        yield proc
    finally:
        is_running = proc.poll() is None
        if not is_running:
            return  # noqa: B012
        proc.terminate()
        # allow sufficient shutdown time, as workers have hot/cold shutdowns
        proc.wait(timeout=10)


def _wait_until(
    predicate: Callable[[], bool], *, timeout: float, interval: float = 0.1
):
    """
    Poll predicate() until it returns True or timeout expires.
    Returns True if condition met, False if timed out.
    """
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)

    raise AssertionError("Predicate was never satisfied")


def test_health_check_all_parts_disabled():
    result = runner.invoke(
        app,
        [
            "worker-health-check",
            "--skip-event-loop-liveness",
            "--skip-ping",
            "--skip-readiness",
        ],
    )

    assert result.exit_code == 0


#
# EVENT LOOP LIVENESS
#


def test_event_loop_liveness_is_not_a_file():
    result = runner.invoke(
        app,
        [
            "worker-health-check",
            "--liveness-file",
            "/",
            "--skip-ping",
            "--skip-readiness",
        ],
    )

    assert result.exit_code == _WORKER_EXIT_CODE_EVENT_LOOP_BROKEN


def test_event_loop_liveness_is_a_file_but_too_old(tmp_path: Path):
    test_file = tmp_path / "test"
    test_file.touch()

    result = runner.invoke(
        app,
        [
            "worker-health-check",
            "--liveness-file",
            str(test_file),
            "--max-age",
            "-1",  # abuse the fact that negative integers can be specified
            "--skip-ping",
            "--skip-readiness",
        ],
    )

    assert result.exit_code == _WORKER_EXIT_CODE_EVENT_LOOP_BROKEN


def test_event_loop_liveness_is_a_file_and_young_enough(tmp_path: Path):
    test_file = tmp_path / "test"
    test_file.touch()

    result = runner.invoke(
        app,
        [
            "worker-health-check",
            "--liveness-file",
            str(test_file),
            "--max-age",
            "10",
            "--skip-ping",
            "--skip-readiness",
        ],
    )

    assert result.exit_code == 0


#
# PING
#


def _ping_ready():
    replies = celery_app.control.ping(destination=["celery@test"], timeout=1)
    return bool(replies)


def test_ping_fails_no_worker_running():
    result = runner.invoke(
        app,
        [
            "worker-health-check",
            "--no-skip-ping",
            "--ping-timeout",
            "1",
            "--skip-event-loop-liveness",
            "--skip-readiness",
        ],
    )

    assert result.exit_code == _WORKER_EXIT_CODE_PING_FAILURE


def test_ping_running_worker(start_worker_process: subprocess.Popen):
    _wait_until(_ping_ready, timeout=10)

    result = runner.invoke(
        app,
        [
            "worker-health-check",
            "--no-skip-ping",
            "--worker-name",
            "celery@test",
            "--broker",
            "redis://localhost:6379/0",
            "--ping-timeout",
            "5",
            "--skip-event-loop-liveness",
            "--skip-readiness",
        ],
    )

    assert result.exit_code == 0


def test_ping_fails_wrong_worker_name(start_worker_process: subprocess.Popen):
    _wait_until(_ping_ready, timeout=10)

    result = runner.invoke(
        app,
        [
            "worker-health-check",
            "--no-skip-ping",
            "--worker-name",
            "WRONG@ALSOWRONG",
            "--broker",
            "redis://localhost:6379/0",
            "--ping-timeout",
            "5",
            "--skip-event-loop-liveness",
            "--skip-readiness",
        ],
    )

    assert result.exit_code == _WORKER_EXIT_CODE_PING_FAILURE


def test_ping_fails_wrong_broker(start_worker_process: subprocess.Popen):
    _wait_until(_ping_ready, timeout=10)

    result = runner.invoke(
        app,
        [
            "worker-health-check",
            "--no-skip-ping",
            "--worker-name",
            "celery@test",
            "--broker",
            "redis://127.0.0.1:9999/0",
            "--ping-timeout",
            "5",
            "--skip-event-loop-liveness",
            "--skip-readiness",
        ],
    )

    assert result.exit_code != 0


#
# READINESS
#
def test_readiness_is_not_a_file():
    result = runner.invoke(
        app,
        [
            "worker-health-check",
            "--no-skip-readiness",
            "--readiness-file",
            "/",
            "--skip-event-loop-liveness",
            "--skip-ping",
        ],
    )

    assert result.exit_code == _WORKER_EXIT_CODE_NOT_READY


def test_readiness_exists(tmp_path: Path):
    test_file = tmp_path / "test"
    test_file.touch()

    result = runner.invoke(
        app,
        [
            "worker-health-check",
            "--no-skip-readiness",
            "--readiness-file",
            str(test_file),
            "--skip-event-loop-liveness",
            "--skip-ping",
        ],
    )

    assert result.exit_code == 0
