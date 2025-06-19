import inspect
import os
from collections.abc import Callable
from contextlib import AbstractContextManager
from pathlib import Path
from typing import (
    Any,
    NotRequired,
    Protocol,
    TypedDict,
    override,
)

from django.test import (
    SimpleTestCase as _SimpleTestCase,
    TestCase as _TestCase,
    TransactionTestCase as _TransactionTestCase,
    tag,
)

import requests.exceptions
from vcr.cassette import Cassette
from vcr.config import RecordMode
from vcr.request import Request
from vcr.unittest import VCR, VCRMixin as _VCRMixin

__all__ = [
    "SimpleTestCase",
    "TestCase",
    "TransactionTestCase",
    "VCRMixin",
]
type _VCRBRRHook = Callable[[Request], Request | None]
"""VCR before_record_request hook
May mutate Request and return it, or cancel recording by returning None"""


class _VCRTestCase(Protocol):
    "The interface VCRMixin depends on"

    _testMethodName: str

    def _get_cassette_name(self) -> str: ...
    def _get_vcr(self, **kwargs) -> VCR: ...
    # TypedDict is almost as cursed as Protocol :(
    def _get_vcr_kwargs(self, **kwargs) -> dict[str, Any]: ...


class VCRMixin(_VCRMixin):
    """
    Mixin to use VCR cassettes to record HTTP requests/responses.
    """

    VCR_RECORD_MODE: RecordMode = RecordMode(
        os.environ.get("VCR_RECORD_MODE", RecordMode.NONE)
    )
    """
    Defaults to `VCR_RECORD_MODE` env variable or `RecordMode.NONE`
    to (re-)record throw away the cassettes and set to `RecordMode.ONCE`
    """

    VCR_TEST_FILES: Path | None = None
    """
    Cassettes will be stored in `VCR_TEST_FILES` / "vcr_cassettes" / {classname}
    Defaults to Path(__file__).parent / "files" of your class.
    """

    @override
    def _get_cassette_library_dir(self):
        test_files = (
            self.VCR_TEST_FILES
            or Path(inspect.getfile(self.__class__)).parent / "files"
        )
        return str(test_files / "vcr_cassettes" / self.__class__.__qualname__)

    @override
    def _get_cassette_name(self: _VCRTestCase):
        """Return the filename for cassette

        Default VCR behaviour puts class name in the cassettename
        we put them in a directory.
        """
        return f"{self._testMethodName}.yaml"

    @override
    def _get_vcr_kwargs(self, **kwargs):
        return {
            "record_mode": self.VCR_RECORD_MODE,
            # Decompress for human readable cassette diffs when re-recoding
            "decode_compressed_response": True,
        } | super()._get_vcr_kwargs(**kwargs)

    def vcr_raises(
        self: _VCRTestCase,
        exception: Callable[[], Exception] = requests.exceptions.RequestException,
    ) -> AbstractContextManager[Cassette]:
        """Simulate an error occuring during.

        Instead of performing and recording a request, raises an exception.
        So there will be no request or cassette!

        :Example:

        .. code-block: python
        from requests.exceptions import SSLError, Timeout

        # sometimes certificates expire
        with self.raises(SSLError):
            response = function_under_test_that_uses_requests()

        # or services/connections are down
        with self.raises(Timeout):
            response = function_under_test_that_uses_requests()
        """
        # TODO: decouple exception from requests with generic Timeout/SSLError/etc that
        # inherit from all semantically equal exceptions thrown by better libraries
        # than requests. A client can then change its implementation without a need to
        # change the tests (iff it doesn't do anything with the Error arguments).

        kwargs = self._get_vcr_kwargs()
        hook: _VCRBRRHook = kwargs.get("before_record_request") or (lambda _: None)

        def raise_exception(request):
            # perform configured hook first
            hook(request)
            raise exception()

        clean_vcr = self._get_vcr(**kwargs | {"before_record_request": raise_exception})
        return clean_vcr.use_cassette(self._get_cassette_name())


@tag("vcr")
class SimpleTestCase(VCRMixin, _SimpleTestCase):
    pass


@tag("vcr")
class TestCase(VCRMixin, _TestCase):
    pass


@tag("vcr")
class TransactionTestCase(VCRMixin, _TransactionTestCase):
    pass
