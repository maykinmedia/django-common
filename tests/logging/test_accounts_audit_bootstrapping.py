from maykin_common.accounts.audit import connect_signals


def test_can_connect_audit_signals():
    connect_signals()  # optional dependencies may not cause crashes
