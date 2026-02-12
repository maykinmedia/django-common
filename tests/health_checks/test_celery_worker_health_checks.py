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
    EventLoopProbe,
    connect_worker_signals,
)

ROOT_DIR = Path(__file__).parent.parent.parent.resolve()

app = Celery("maykin-common-tests", broker="redis://localhost:6379/0")
# signals must be connected in the process that runs worker - this module is imported
# again via the start_worker_process fixture which starts a subprocess
connect_worker_signals()
assert app.steps is not None
app.steps["worker"].add(EventLoopProbe)


@pytest.fixture(autouse=True)
def install_celery_health_checks(settings):
    settings.INSTALLED_APPS = [
        *settings.INSTALLED_APPS,
        "maykin_common.health_checks.celery",
    ]


@pytest.fixture
def worker_event_loop_liveness_file(request, tmp_path: Path) -> Path:
    marker = request.node.get_closest_marker("worker_event_loop_liveness_file")
    subpath = marker.kwargs.get("subpath") if marker else ""
    dir_path = tmp_path
    if subpath:
        dir_path /= subpath
    return dir_path / "worker_live"


@pytest.fixture
def worker_readiness_file(request, tmp_path: Path) -> Path:
    marker = request.node.get_closest_marker("worker_readiness_file")
    subpath = marker.kwargs.get("subpath") if marker else ""
    dir_path = tmp_path
    if subpath:
        dir_path /= subpath
    return dir_path / "worker_ready"


@pytest.fixture
def start_worker_process(
    worker_event_loop_liveness_file: Path, worker_readiness_file: Path
):
    """
    Start a subprocess running worker and stop it when the test exits.
    """
    assert not worker_event_loop_liveness_file.exists(), (
        "worker liveness file should not yet exist"
    )
    assert not worker_readiness_file.exists(), (
        "worker readiness file should not yet exist"
    )

    cmd = [
        "celery",
        "--workdir",
        str(ROOT_DIR),
        "--app",
        __name__,
        "worker",
        "--loglevel",
        "CRITICAL",
    ]
    env = os.environ.copy()
    env["MKN_HEALTH_CHECKS_WORKER_EVENT_LOOP_PROBE_FREQUENCY_SECONDS"] = "1"
    env["MKN_HEALTH_CHECKS_WORKER_EVENT_LOOP_LIVENESS_FILE"] = str(
        worker_event_loop_liveness_file
    )
    env["MKN_HEALTH_CHECKS_WORKER_READINESS_FILE"] = str(worker_readiness_file)

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


def test_worker_hooks_create_probe_files(
    start_worker_process: subprocess.Popen[bytes],
    worker_event_loop_liveness_file: Path,
    worker_readiness_file: Path,
):
    """
    Check that when worker is running and scheduling tasks, it touches a heartheat file.
    """
    _wait_until(
        lambda: (
            worker_event_loop_liveness_file.exists() and worker_readiness_file.exists()
        ),
        timeout=5,
    )

    assert worker_event_loop_liveness_file.is_file()
    assert worker_readiness_file.is_file()


def test_worker_updates_file_stat(
    start_worker_process: subprocess.Popen[bytes],
    worker_event_loop_liveness_file: Path,
):
    # start up worker and wait until the liveness file is initially created
    _wait_until(worker_event_loop_liveness_file.exists, timeout=5)
    initial_modified = worker_event_loop_liveness_file.stat().st_mtime

    # check that the modified at timestamp is updated because of hour every-second
    # timer frequency
    _wait_until(
        lambda: worker_event_loop_liveness_file.stat().st_mtime - initial_modified > 1,
        timeout=3,
    )


def test_worker_removes_probe_files_on_exit(
    start_worker_process: subprocess.Popen[bytes],
    worker_event_loop_liveness_file: Path,
    worker_readiness_file: Path,
):
    _wait_until(
        lambda: (
            worker_event_loop_liveness_file.exists() and worker_readiness_file.exists()
        ),
        timeout=5,
    )

    start_worker_process.terminate()
    # allow sufficient shutdown time, as workers have hot/cold shutdowns
    start_worker_process.wait(timeout=10)
    assert start_worker_process.poll() is not None  # check that it's exited

    assert not worker_readiness_file.exists()
    assert not worker_event_loop_liveness_file.exists()


@pytest.mark.worker_event_loop_liveness_file(subpath="subpath-to-create")
@pytest.mark.worker_readiness_file(subpath="other-subpath-to-create")
def test_intermediate_directories_are_created(
    start_worker_process: subprocess.Popen[bytes],
    tmp_path: Path,
    worker_event_loop_liveness_file: Path,
    worker_readiness_file: Path,
):
    _wait_until(
        lambda: (
            worker_event_loop_liveness_file.exists() and worker_readiness_file.exists()
        ),
        timeout=5,
    )

    assert worker_event_loop_liveness_file.relative_to(tmp_path) == Path(
        "subpath-to-create/worker_live"
    )
    assert worker_event_loop_liveness_file.is_file()

    assert worker_readiness_file.relative_to(tmp_path) == Path(
        "other-subpath-to-create/worker_ready"
    )
    assert worker_readiness_file.is_file()
