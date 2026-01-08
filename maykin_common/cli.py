import importlib.metadata
from urllib.parse import urlparse, urlunparse

import requests
import typer

app = typer.Typer()


@app.command()
def version():
    version = importlib.metadata.version("maykin_common")
    typer.echo(f"maykin-common v{version}")


@app.command(
    name="health-check",
    help=(
        "Execute an HTTP health check call against the provided endpoint. If no "
        "host or domain is provided in the endpoint, this will default to "
        "'http://localhost:8000'."
    ),
)
def health_check(endpoint: str = "/_healthz/livez/", timeout: int = 3):
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


if __name__ == "__main__":  # pragma: no cover
    app()
