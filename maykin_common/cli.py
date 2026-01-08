# TODO: tests: https://typer.tiangolo.com/tutorial/testing/
import importlib.metadata
from urllib.parse import urlparse, urlunparse

import requests
import typer

app = typer.Typer()


@app.command()
def version():
    version = importlib.metadata.version("maykin_common")
    print(f"maykin-common v{version}")


@app.command(
    name="health-check",
    help=(
        "Execute an HTTP health check call against the provided endpoint. If no "
        "host or domain is provided in the endpoint, this will default to "
        "'http://localhost:8000'."
    ),
)
def health_check(endpoint: str = "/_healtz/livez/", timeout: int = 3):
    parsed = urlparse(endpoint)
    normalized_url = urlunparse(
        (
            parsed.scheme or "http",
            parsed.netloc or "localhost:8000",
            parsed.path or "/_healtz/livez/",
            parsed.params,
            parsed.query,
            parsed.fragment,
        )
    )

    response = requests.get(normalized_url, timeout=timeout)
    exit_code = 0 if response.ok else 1
    exit(exit_code)


if __name__ == "__main__":
    app()
