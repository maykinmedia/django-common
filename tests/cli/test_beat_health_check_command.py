import os
import time
from pathlib import Path

import pytest
from typer.testing import CliRunner

from maykin_common.cli import app

runner = CliRunner()


def test_health_check_defaults():
    default_path_exists = (Path("/tmp") / "celery_beat_live").is_file()
    assert not default_path_exists  # establish pre-condition for test

    result = runner.invoke(app, ["beat-health-check"])

    assert result.exit_code == 1


def test_health_check_file_is_not_a_file():
    result = runner.invoke(
        app,
        [
            "beat-health-check",
            "--file",
            "/",
        ],
    )

    assert result.exit_code == 1


def test_health_check_file_is_a_file_but_too_old(tmp_path: Path):
    test_file = tmp_path / "test"
    test_file.touch()
    result = runner.invoke(
        app,
        [
            "beat-health-check",
            "--file",
            str(test_file),
            "--max-age",
            "-1",  # abuse the fact that negative integers can be specified
        ],
    )

    assert result.exit_code == 1


def test_health_check_file_is_a_file_and_young_enough(tmp_path: Path):
    test_file = tmp_path / "test"
    test_file.touch()
    result = runner.invoke(
        app,
        [
            "beat-health-check",
            "--file",
            str(test_file),
            "--max-age",
            "10",
        ],
    )

    assert result.exit_code == 0


@pytest.mark.parametrize(
    "age,expected",
    (
        (30, "30s ago"),
        (300, "5m ago"),
        (330, "5.5m ago"),
        (3600, "1h ago"),
        (3600 + 1799, "1.5h ago"),
        (3600 * 10, "10h ago"),
    ),
)
def test_output_formatting_of_file_age(tmp_path: Path, age: int, expected: str):
    test_file = tmp_path / "test"
    test_file.touch()  # create the file
    creation_time = mod_time = time.time() - age
    # modify the creation/modification timestamps
    os.utime(test_file, (creation_time, mod_time))

    result = runner.invoke(
        app,
        [
            "beat-health-check",
            "--file",
            str(test_file),
            "--max-age",
            str(age + 60),
        ],
    )

    assert result.exit_code == 0
    assert expected in result.stdout
