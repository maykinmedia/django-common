# Celery is specified in the test dependencies already for the otel instrumentation, so
# we can rely on it being available for health-check tests.

import os
import subprocess
import time
from collections.abc import Callable
from pathlib import Path

import pytest
from celery import Celery

from maykin_common.health_checks.celery.probes import (
    connect_beat_signals,
    on_beat_task_published,
)

ROOT_DIR = Path(__file__).parent.parent.parent.resolve()

app = Celery("maykin-common-tests", broker="redis://localhost:6379/0")
# signals must be connected in the process that runs beat - this module is imported
# again via the start_beat_process fixture which starts a subprocess
connect_beat_signals()

app.conf.beat_schedule = {
    "dummy": {
        "task": "tests.health_checks.test_celery_beat_health_checks.dummy",
        "schedule": 1.0,  # every second, for sufficiently fast tests.
    }
}


@app.task()
def dummy():
    """
    Dummy task for beat schedule.
    """
    return "ok"


@pytest.fixture(autouse=True)
def install_celery_health_checks(settings):
    settings.INSTALLED_APPS = [
        *settings.INSTALLED_APPS,
        "maykin_common.health_checks.celery",
    ]


@pytest.fixture
def beat_liveness_file(request, tmp_path: Path) -> Path:
    marker = request.node.get_closest_marker("beat_liveness_file")
    subpath = marker.kwargs.get("subpath") if marker else ""
    dir_path = tmp_path
    if subpath:
        dir_path /= subpath
    return dir_path / "beat_live"


@pytest.fixture
def start_beat_process(beat_liveness_file):
    """
    Start a subprocess running beat and stop it when the test exits.
    """
    assert not beat_liveness_file.exists(), "beat liveness file should not yet exist"

    cmd = [
        "celery",
        "--workdir",
        str(ROOT_DIR),
        "--app",
        __name__,
        "beat",
        "--loglevel",
        "CRITICAL",
    ]
    env = os.environ.copy()
    env["MKN_HEALTH_CHECKS_BEAT_LIVENESS_FILE"] = str(beat_liveness_file)

    # start the process and let it run in the background - it should not exit by itself.
    proc = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        yield proc
    finally:
        is_running = proc.poll() is None
        if not is_running:
            return  # noqa: B012
        proc.terminate()
        proc.wait(timeout=5)


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


def test_beat_hooks_create_heartbeat_file(
    start_beat_process: subprocess.Popen[bytes],
    beat_liveness_file: Path,
):
    """
    Check that when beat is running and scheduling tasks, it touches a heartheat file.
    """
    _wait_until(beat_liveness_file.exists, timeout=5)

    assert beat_liveness_file.is_file()


def test_beat_updates_file_stat(
    start_beat_process: subprocess.Popen[bytes],
    beat_liveness_file: Path,
):
    # start up beat and wait until the liveness file is initially created
    _wait_until(beat_liveness_file.exists, timeout=5)
    initial_modified = beat_liveness_file.stat().st_mtime

    # check that the modified at timestamp is updated because of hour every-second
    # task
    _wait_until(
        lambda: beat_liveness_file.stat().st_mtime - initial_modified > 1, timeout=3
    )


def test_beat_removes_liveness_file_on_exit(
    start_beat_process: subprocess.Popen[bytes],
    beat_liveness_file: Path,
):
    _wait_until(beat_liveness_file.exists, timeout=5)

    start_beat_process.terminate()
    start_beat_process.wait(timeout=5)

    assert not beat_liveness_file.exists()


def test_no_liveness_file_created_when_not_running_in_beat(beat_liveness_file: Path):
    assert not beat_liveness_file.exists()

    on_beat_task_published(sender="mock", routing_key="mock")

    assert not beat_liveness_file.exists()


@pytest.mark.beat_liveness_file(subpath="subpath-to-create")
def test_intermediate_directories_are_created(
    start_beat_process: subprocess.Popen[bytes],
    tmp_path: Path,
    beat_liveness_file: Path,
):
    _wait_until(beat_liveness_file.exists, timeout=5)

    assert beat_liveness_file.relative_to(tmp_path) == Path(
        "subpath-to-create/beat_live"
    )
    assert beat_liveness_file.is_file()
