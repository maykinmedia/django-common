from django.test import RequestFactory

from maykin_common.accounts.audit import connect_signals, get_client_ip_address


def test_can_connect_audit_signals():
    connect_signals()  # optional dependencies may not cause crashes


def test_get_client_ip_fallback(rf: RequestFactory):
    request = rf.get("/irrelvant", REMOTE_ADDR="8.8.4.4")

    ip_address = get_client_ip_address(request)

    assert ip_address == "8.8.4.4"
