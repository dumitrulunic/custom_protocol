import threading
import time
from simp_daemon import Daemon

def run_daemon(ip):
    """
    Creates and runs a daemon instance on a separate thread.
    """
    daemon = Daemon(ip)
    threading.Thread(target=daemon.listen_to_daemons, daemon=True).start()
    return daemon

def test_successful_handshake():
    """
    Test a successful three-way handshake between two daemons.
    """
    # Setup
    daemon1 = run_daemon("127.0.0.1")
    daemon2 = run_daemon("127.0.0.2")

    # Allow some time for the daemons to start
    time.sleep(1)

    # Initiate handshake
    success = daemon1.three_way_handshake_init("127.0.0.2", 7777)

    # Assertions
    assert success, "Three-way handshake failed"
    assert daemon1.active_connections[("127.0.0.2", 7777)] == "CONNECTED", "Daemon1 did not reach CONNECTED state"
    assert daemon2.active_connections[("127.0.0.1", 7777)] == "CONNECTED", "Daemon2 did not reach CONNECTED state"

    print("[TEST PASSED] Successful handshake test")

def test_timeout_on_syn():
    """
    Test timeout when the target daemon does not respond to SYN.
    """
    # Setup
    daemon1 = run_daemon("127.0.0.1")

    # Initiate handshake (no daemon running on 127.0.0.2)
    success = daemon1.three_way_handshake_init("127.0.0.2", 7777)

    # Assertions
    assert not success, "Handshake should have failed due to timeout"
    assert ("127.0.0.2", 7777) in daemon1.active_connections, "Connection state should exist"
    assert daemon1.active_connections[("127.0.0.2", 7777)] == "SYN_SENT", "State should remain SYN_SENT after timeout"

    print("[TEST PASSED] Timeout on SYN test")

def test_timeout_on_ack():
    """
    Test timeout when the initiator fails to send ACK.
    """
    # Setup
    daemon1 = run_daemon("127.0.0.1")
    daemon2 = run_daemon("127.0.0.2")

    # Override daemon1 to fail after SYN+ACK
    def broken_three_way_handshake_receive(datagram, address):
        print(f"[BROKEN] {daemon1.ip_address}:{daemon1.port} refusing to send ACK to {address}")
        # Intentionally do nothing after receiving SYN+ACK
    daemon1.three_way_handshake_receive = broken_three_way_handshake_receive

    # Initiate handshake
    success = daemon2.three_way_handshake_init("127.0.0.1", 7777)

    # Assertions
    assert not success, "Handshake should have failed due to missing ACK"
    assert daemon2.active_connections[("127.0.0.1", 7777)] == "SYN_RECEIVED", "Daemon2 should remain in SYN_RECEIVED state"

    print("[TEST PASSED] Timeout on ACK test")

if __name__ == "__main__":
    # Run the tests
    test_successful_handshake()
    test_timeout_on_syn()
    test_timeout_on_ack()
