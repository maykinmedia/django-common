from unittest.mock import patch

import requests
from typer.testing import CliRunner

from maykin_common.cli import app

runner = CliRunner()


def test_health_check_defaults():
    with patch("maykin_common.cli.requests.get") as mock_get:
        result = runner.invoke(app, ["health-check"])

    assert result.exit_code == 0
    mock_get.assert_called_once_with("http://localhost:8000/_healthz/livez/", timeout=3)


def test_health_check_host_without_protocol():
    with patch("maykin_common.cli.requests.get") as mock_get:
        result = runner.invoke(app, ["health-check", "--endpoint=localhost:9000/ht/"])

    assert result.exit_code == 0
    mock_get.assert_called_once_with("http://localhost:9000/ht/", timeout=3)


def test_health_check_with_empty_endpoint():
    with patch("maykin_common.cli.requests.get") as mock_get:
        result = runner.invoke(app, ["health-check", "--endpoint="])

    assert result.exit_code == 0
    mock_get.assert_called_once_with("http://localhost:8000/_healthz/livez/", timeout=3)


def test_health_check_with_fully_qualified_endpoint():
    with patch("maykin_common.cli.requests.get") as mock_get:
        result = runner.invoke(app, ["health-check", "--endpoint=https://example.com/"])

    assert result.exit_code == 0
    mock_get.assert_called_once_with("https://example.com/", timeout=3)


def test_health_check_with_custom_timeout():
    with patch("maykin_common.cli.requests.get") as mock_get:
        result = runner.invoke(app, ["health-check", "--timeout=1"])

    assert result.exit_code == 0
    mock_get.assert_called_once_with("http://localhost:8000/_healthz/livez/", timeout=1)


def test_failing_health_check_exits_with_exit_code_1():
    with patch(
        "maykin_common.cli.requests.get",
        side_effect=requests.RequestException,
    ):
        result = runner.invoke(app, ["health-check", "--timeout=1"])

    assert result.exit_code == 1


def test_failing_health_check_exits_with_exit_code_1_bad_response_status_code():
    bad_response = requests.Response()
    bad_response.status_code = 503
    with patch(
        "maykin_common.cli.requests.get",
        return_value=bad_response,
    ):
        result = runner.invoke(app, ["health-check", "--timeout=1"])

    assert result.exit_code == 1
