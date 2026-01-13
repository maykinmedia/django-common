"""
Command line companion to the ``maykin-common`` Django utilities.

The command line script is deliberately written in pure Python without loading Django
at all (for performance), as opposed to providing Django management commands. Large
Django projects may see slow startup times in the order of 2-10s due to (expensive)
imports when loading all the code. This pairs very badly with health checks machinery
which tend to have timeouts of a couple of seconds.
"""

import importlib.metadata
import time
from pathlib import Path
from typing import Annotated
from urllib.parse import urlparse, urlunparse

import requests
import typer

app = typer.Typer()


@app.command()
def version():
    version = importlib.metadata.version("maykin_common")
    typer.echo(f"maykin-common v{version}")


@app.command(name="health-check")
def health_check(
    endpoint: Annotated[
        str,
        typer.Option(help="Endpoint/path to test for connection and status code."),
    ] = "/_healthz/livez/",
    timeout: Annotated[
        int,
        typer.Option(help="Timeout for the GET request (in seconds)."),
    ] = 3,
):
    """
    Execute an HTTP health check call against the provided endpoint.

    If no host or domain is provided with the ``endpoint`` option, a default of
    ``http://localhost:8000`` will be used.
    """

    # URLs must start with a scheme, otherwise urlparse chokes :-)
    if not (endpoint.startswith("http://") or endpoint.startswith("https://")):
        endpoint = f"http://{endpoint}"

    parsed = urlparse(endpoint)
    normalized_url = urlunparse(
        (
            parsed.scheme,
            parsed.netloc or "localhost:8000",
            parsed.path or "/_healthz/livez/",
            parsed.params,
            parsed.query,
            parsed.fragment,
        )
    )

    try:
        response = requests.get(normalized_url, timeout=timeout)
    except requests.RequestException as exc:
        typer.secho(f"DOWN ({exc.__class__.__name__})", fg=typer.colors.RED, err=True)
        exit(1)

    if up := response.ok:
        typer.secho(
            f"UP, response status code: {response.status_code}",
            fg=typer.colors.GREEN,
        )
    else:
        typer.secho(
            f"DOWN, response status code: {response.status_code}",
            fg=typer.colors.RED,
            err=True,
        )

    exit_code = 0 if up else 1
    exit(exit_code)


@app.command(name="beat-health-check")
def beat_health_check(
    file: Annotated[
        Path,
        typer.Option(
            help="The liveness file, created and updated by the Beat health check "
            "machinery."
        ),
    ] = Path("/tmp") / "celery_beat_live",
    max_age: Annotated[
        int,
        typer.Option(
            help="How long ago the last update of liveness file is allowed to be, in "
            "seconds. You should tune this to the beat schedule of your application."
        ),
    ] = 3600,
):
    """
    Check the last modified timestamp of the Beat liveness file.

    If it's older than ``max-age``, Beat is considered unhealthy.
    """
    file = file.resolve()
    if not file.exists() or not file.is_file():
        typer.secho(
            f"File '{file}' does not exist or is not a file.",
            fg=typer.colors.RED,
            err=True,
        )
        exit(1)

    # check the file age
    now = time.time()
    last_modified = file.stat().st_mtime
    age_in_seconds = int(now - last_modified)
    if age_in_seconds > max_age:
        typer.secho(
            f"File '{file}' is older than max-age.",
            fg=typer.colors.RED,
            err=True,
        )
        exit(1)
    else:
        human_readable_age: str = f"{age_in_seconds}s"
        if 60 < age_in_seconds < 3600:
            age_in_minutes = round(age_in_seconds / 60, 1)
            human_readable_age = f"{age_in_minutes:.1f}m".replace(".0", "")
        elif age_in_seconds >= 3600:
            age_in_hours = round(age_in_seconds / 3600, 1)
            human_readable_age = f"{age_in_hours:.1f}h".replace(".0", "")

        typer.secho(
            f"Last scheduled task: {human_readable_age} ago.",
            fg=typer.colors.GREEN,
        )
        exit(0)


if __name__ == "__main__":  # pragma: no cover
    app()
