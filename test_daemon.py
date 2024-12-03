import threading
import time
from simp_daemon import Daemon
from Datagram import Datagram

daemon1 = None
daemon2 = None
daemon1_thread = None
daemon2_thread = None

def setup_daemons():
    """Start two daemons for testing."""
    global daemon1, daemon2, daemon1_thread, daemon2_thread
    daemon1 = Daemon(ip="127.0.0.1", port=7777)
    daemon2 = Daemon(ip="127.0.0.2", port=7777)

    daemon1_thread = threading.Thread(target=daemon1.start, daemon=True)
    daemon2_thread = threading.Thread(target=daemon2.start, daemon=True)

    daemon1_thread.start()
    daemon2_thread.start()

    time.sleep(1)

def teardown_daemons():
    """Stop the daemons and clean up."""
    global daemon1, daemon2, daemon1_thread, daemon2_thread
    daemon1.stop()
    daemon2.stop()
    daemon1_thread.join()
    daemon2_thread.join()

def test_send_datagram():
    """Test sending a datagram from Daemon1 to Daemon2."""
    print("Running test_send_datagram...")
    datagram = Datagram(
        type=b'\x01',
        operation=b'\x02',  # SYN
        sequence=b'\x00',
        user=b"TestUser",
        length=(0).to_bytes(4, 'big'),
        payload=b""
    )
    
    # Send datagram from Daemon1 to Daemon2
    daemon1.send_datagram_to_daemon(datagram, "127.0.0.2", 7777)
    
    time.sleep(1)
    
    # Check if Daemon2 received the datagram
    active_connections = daemon2.active_connections
    assert ("127.0.0.1", 7777) in active_connections, "Daemon2 should have a connection to Daemon1"
    assert active_connections[("127.0.0.1", 7777)]["state"] == "connected", "Connection state should be 'connected'"
    print("test_send_datagram passed!")

def test_handshake():
    """Test the handshake process between Daemon1 and Daemon2."""
    print("Running test_handshake...")
    result = daemon1.handshake_init("127.0.0.2", 7777)
    assert result, "Handshake should complete successfully"
    
    # Check active connections on both sides
    assert ("127.0.0.2", 7777) in daemon1.active_connections, "Daemon1 should have a connection to Daemon2"
    assert ("127.0.0.1", 7777) in daemon2.active_connections, "Daemon2 should have a connection to Daemon1"
    assert daemon1.active_connections[("127.0.0.1", 7778)]["state"] == "connected", "Daemon1 connection state should be 'connected'"
    assert daemon2.active_connections[("127.0.0.1", 7777)]["state"] == "connected", "Daemon2 connection state should be 'connected'"
    print("test_handshake passed!")

def test_invalid_datagram():
    """Test handling of invalid datagrams."""
    print("Running test_invalid_datagram...")
    invalid_datagram = Datagram(
        type=b'\x03',  # Invalid type
        operation=b'\x00',
        sequence=b'\x00',
        user=b"InvalidUser",
        length=(0).to_bytes(4, 'big'),
        payload=b""
    )
    
    try:
        invalid_datagram.to_bytes()
        assert False, "Invalid datagram should raise ValueError"
    except ValueError:
        print("Invalid datagram correctly raised ValueError")
    print("test_invalid_datagram passed!")

def test_fin_termination():
    """Test connection termination using FIN."""
    print("Running test_fin_termination...")
    # Establish a connection first
    daemon1.handshake_init("127.0.0.2", 7777)
    
    fin_datagram = Datagram(
        type=b'\x01',
        operation=b'\x08',  # FIN
        sequence=b'\x00',
        user=b"TestUser",
        length=(0).to_bytes(4, 'big'),
        payload=b""
    )
    daemon1.send_datagram_to_daemon(fin_datagram, "127.0.0.2", 7777)
    
    time.sleep(1)
    
    assert ("127.0.0.2", 7777) not in daemon1.active_connections, "Connection should be removed from Daemon1"
    assert ("127.0.0.1", 7777) not in daemon2.active_connections, "Connection should be removed from Daemon2"
    print("test_fin_termination passed!")

if __name__ == "__main__":
    try:
        setup_daemons()
        test_send_datagram()
        test_handshake()
        test_invalid_datagram()
        test_fin_termination()
    finally:
        teardown_daemons()
