import fcntl
import os
from io import StringIO
from multiprocessing import Process
from pathlib import Path

from django.core.management import call_command

import pytest
from django_yubin.models import Message
from filelock import FileLock
from freezegun import freeze_time
from pytest_django import DjangoCaptureOnCommitCallbacks

from .utils import create_message

pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture(autouse=True)
def install_django_yubin_settings(settings):
    settings.INSTALLED_APPS = [
        *settings.INSTALLED_APPS,
        "maykin_common.yubin",
    ]
    settings.EMAIL_BACKEND = "maykin_common.yubin.backends.QueuedEmailBackend"


@pytest.fixture()
def lock_file(settings, tmp_path: Path) -> Path:
    lock_path = tmp_path / "test.lock"
    settings.YUBIN_LOCK_PATH = lock_path
    return lock_path


def test_retry_output():
    Message.objects.create(
        to_address="test1@example.com",
        subject="Test Subject 1",
        message_data="<p>Test message 1</p>",
        status=Message.STATUS_FAILED,
    )
    Message.objects.create(
        to_address="test2@example.com",
        subject="Test Subject 2",
        message_data="<p>Test message 2</p>",
        status=Message.STATUS_IN_PROCESS,
    )
    assert Message.objects.count() == 2
    out = StringIO()

    call_command("retry_emails", stdout=out)

    output = out.getvalue()
    assert "Retried emails" in output
    assert "enqueued=1" in output
    assert "failed=0" in output


def test_delete_old_output():
    with freeze_time("2026-02-04"):
        Message.objects.create(
            to_address="test1@example.com",
            subject="Test Subject 1",
            message_data="<p>Test message 1</p>",
            status=Message.STATUS_SENT,
        )

    out = StringIO()
    assert Message.objects.count() == 1

    with freeze_time("2026-06-01"):
        call_command("delete_old_emails", stdout=out)

    output = out.getvalue()

    assert "Deleted old emails" in output
    assert "deleted=1" in output
    assert "cutoff_date=2026-03-03" in output


def test_delete_old_output_days_param():
    with freeze_time("2026-02-04"):
        Message.objects.create(
            to_address="test1@example.com",
            subject="Test Subject 1",
            message_data="<p>Test message 1</p>",
            status=Message.STATUS_SENT,
        )

    out = StringIO()
    assert Message.objects.count() == 1

    # keep for a year
    with freeze_time("2026-06-01"):
        call_command("delete_old_emails", "--days=365", stdout=out)

    output = out.getvalue()
    assert "deleted=0" in output
    assert "Deleted old emails" in output
    assert "cutoff_date=2025-06-01" in output


def test_send_all_mails(
    django_capture_on_commit_callbacks: DjangoCaptureOnCommitCallbacks,
):

    create_message(
        to_address="test1@example.com",
        subject="Test Subject 1",
        body="<p>Test message 1</p>",
        status=Message.STATUS_QUEUED,
    )
    create_message(
        to_address="test2@example.com",
        subject="Test Subject 2",
        body="<p>Test message 2</p>",
        status=Message.STATUS_CREATED,
    )
    create_message(
        to_address="test3@example.com",
        subject="Test Subject 3",
        body="<p>Test message 3</p>",
        status=Message.STATUS_SENT,
    )

    assert Message.objects.filter(status=Message.STATUS_SENT).count() == 1
    assert Message.objects.filter(status=Message.STATUS_QUEUED).count() == 1

    with django_capture_on_commit_callbacks(execute=True):
        call_command("send_all_mail")

    assert Message.objects.filter(status=Message.STATUS_QUEUED).count() == 0
    assert Message.objects.filter(status=Message.STATUS_SENT).count() == 2


def test_send_all_mails_lockfile(
    django_capture_on_commit_callbacks: DjangoCaptureOnCommitCallbacks,
    lock_file: Path,
):

    message = create_message(
        to_address="test1@example.com",
        subject="Test Subject 1",
        body="<p>Test message 1</p>",
        status=Message.STATUS_QUEUED,
    )

    lock = FileLock(lock_file)
    lock.acquire()

    with lock:
        assert lock.is_locked
        assert Message.objects.filter(status=Message.STATUS_QUEUED).count() == 1

        with django_capture_on_commit_callbacks(execute=True):
            # should fail to acquire the lock and get deadlock detection
            call_command("send_all_mail")

        message.refresh_from_db()
        assert message.status == Message.STATUS_QUEUED


def test_send_all_mails_lockfile_stale(
    django_capture_on_commit_callbacks: DjangoCaptureOnCommitCallbacks, lock_file: Path
):
    message = create_message(
        to_address="test1@example.com",
        subject="Test Subject 1",
        body="<p>Test message 1</p>",
        status=Message.STATUS_QUEUED,
    )
    lock_file.touch()

    def create_lock_file(lock_file_path: Path) -> None:
        """
        Create a lock file without releasing.
        """
        fd = os.open(lock_file_path, os.O_RDWR | os.O_TRUNC)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

    p = Process(target=create_lock_file, args=(lock_file,))
    p.start()
    assert os.getpid() != p.pid
    p.join()

    with django_capture_on_commit_callbacks(execute=True):
        call_command("send_all_mail")

    message.refresh_from_db()
    assert message.status == Message.STATUS_SENT
