import requests

from maykin_common.vcr import VCRTestCase


def get(url: str) -> Exception | requests.Response:
    try:
        return requests.get(url)
    except Exception as e:
        return e


class VCRTests(VCRTestCase):
    def test_vcr_raises_default(self):
        with self.vcr_raises():
            response = get("https://example.com")

        assert isinstance(response, requests.exceptions.RequestException)

    def test_vcr_raises_exception(self):
        class MyException(Exception):
            pass

        with self.vcr_raises(MyException):
            response = get("https://example.com")

        assert isinstance(response, MyException)

    def test_vcr_raises_specific_instance(self):
        my_exception = Exception("With arguments")

        with self.vcr_raises(lambda: my_exception):
            response = get("https://example.com")

        assert response is my_exception
