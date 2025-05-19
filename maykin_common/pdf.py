"""
Utilities for PDF rendering from HTML using WeasyPrint.

Note that you need to add https://pypi.org/project/weasyprint/ to your dependencies
if you want to make use of HTML-to-PDF rendering. This is not included by default as
it's quite heavy and requires OS-level dependencies.

This module exposes the public function :func:`render_to_pdf` which renders a template
with a context into a PDF document (bytes output). You can use "external" stylesheets
in these templates, and they will be resolved through django's staticfiles machinery
by the custom :class:`UrlFetcher`.
"""

import logging
import mimetypes
from io import BytesIO
from pathlib import PurePosixPath
from typing import NotRequired, TypedDict
from urllib.parse import ParseResult, urljoin, urlparse

from django.conf import settings
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.files.storage import FileSystemStorage, default_storage
from django.core.files.storage.base import Storage
from django.template.loader import render_to_string
from django.utils.module_loading import import_string

import weasyprint

from maykin_common.settings import get_setting

logger = logging.getLogger(__name__)

__all__ = ["render_to_pdf"]


def get_base_url(*args, **kwargs) -> str:
    """
    Get the base URL where the project is served.
    """

    if pdf_base_url_function := get_setting("PDF_BASE_URL_FUNCTION"):
        return import_string(pdf_base_url_function)(*args, **kwargs)

    raise NotImplementedError("You must implement 'get_base_url'.")


class UrlFetcherResult(TypedDict):
    mime_type: str | None
    encoding: str | None
    redirected_url: str
    filename: str
    file_obj: NotRequired[BytesIO]
    string: NotRequired[bytes]


class UrlFetcher:
    """
    URL fetcher that skips the network for /static/* files.
    """

    def __init__(self):
        self.static_url = self._get_fully_qualified_url(settings.STATIC_URL)
        is_static_local_storage = issubclass(
            staticfiles_storage.__class__, FileSystemStorage
        )

        self.media_url = self._get_fully_qualified_url(settings.MEDIA_URL)
        is_media_local_storage = issubclass(
            default_storage.__class__, FileSystemStorage
        )

        self.candidates = (
            (self.static_url, staticfiles_storage, is_static_local_storage),
            (self.media_url, default_storage, is_media_local_storage),
        )

    @staticmethod
    def _get_fully_qualified_url(setting: str):
        fully_qualified_url = setting
        if not urlparse(setting).netloc:
            fully_qualified_url = urljoin(get_base_url(), setting)
        return urlparse(fully_qualified_url)

    def __call__(self, url: str) -> UrlFetcherResult:
        orig_url = url
        parsed_url = urlparse(url)

        candidate = self.get_match_candidate(parsed_url)
        if candidate is not None:
            base_url, storage = candidate
            path = PurePosixPath(parsed_url.path).relative_to(base_url.path)

            absolute_path = None
            if storage.exists(str(path)):
                absolute_path = storage.path(str(path))
            elif settings.DEBUG and storage is staticfiles_storage:
                # use finders so that it works in dev too, we already check that it's
                # using filesystem storage earlier
                absolute_path = finders.find(str(path))

            if absolute_path is None:
                logger.error("Could not resolve path '%s'", path)
                return weasyprint.default_url_fetcher(orig_url)  # pyright:ignore[reportReturnType]

            content_type, encoding = mimetypes.guess_type(absolute_path)
            result: UrlFetcherResult = {
                "mime_type": content_type,
                "encoding": encoding,
                "redirected_url": orig_url,
                "filename": path.parts[-1],
            }
            with open(absolute_path, "rb") as f:
                result["file_obj"] = BytesIO(f.read())
            return result
        return weasyprint.default_url_fetcher(orig_url)  # pyright:ignore[reportReturnType]

    def get_match_candidate(
        self, url: ParseResult
    ) -> tuple[ParseResult, Storage] | None:
        for parsed_base_url, storage, is_local_storage in self.candidates:
            if not is_local_storage:
                continue
            same_base = (parsed_base_url.scheme, parsed_base_url.netloc) == (
                url.scheme,
                url.netloc,
            )
            if not same_base:
                continue
            if not url.path.startswith(parsed_base_url.path):
                continue
            return (parsed_base_url, storage)
        return None


def render_to_pdf(template_name: str, context: dict) -> tuple[str, bytes]:
    """
    Render a (HTML) template to PDF with the given context.
    """
    rendered_html = render_to_string(template_name, context=context)
    html_object = weasyprint.HTML(
        string=rendered_html,
        url_fetcher=UrlFetcher(),
        base_url=get_base_url(),
    )
    pdf = html_object.write_pdf()
    assert isinstance(pdf, bytes)
    return rendered_html, pdf
