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


def test_handshake():
    """Test the handshake process between Daemon1 and Daemon2."""
    print("Running test_handshake...")
    
    # Initiating handshake
    daemon1.handshake("127.0.0.2", 7777, is_initiator=True)
    
    # Check active connections on both sides
    assert ("127.0.0.2", 7777) in daemon1.active_connections, "Daemon1 should have a connection to Daemon2"
    assert ("127.0.0.1", 7777) in daemon2.active_connections, "Daemon2 should have a connection to Daemon1"
    assert daemon1.active_connections[("127.0.0.2", 7777)]["state"] == "connected", "Daemon1 connection state should be 'connected'"
    assert daemon2.active_connections[("127.0.0.1", 7777)]["state"] == "connected", "Daemon2 connection state should be 'connected'"
    print("test_handshake passed!")

def test_invalid_datagram():
    """Test handling of invalid datagrams."""
    print("Running test_invalid_datagram...")
    
    invalid_datagram = Datagram(
        datagram_type=3, 
        operation=0,
        sequence=0,
        user="InvalidUser",
        length=0,
        payload=""
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
    daemon1.handshake("127.0.0.2", 7777, is_initiator=True)
    
    # Send FIN to terminate the connection
    fin_datagram = Datagram(
        datagram_type=1,
        operation=8,  # FIN
        sequence=0,
        user="TestUser",
        length=0,
        payload=""
    )
    daemon1.send_datagram_to_daemon(fin_datagram, "127.0.0.2", 7777)
    
    time.sleep(1)
    
    # Check if the connection was removed on both sides
    assert ("127.0.0.2", 7777) not in daemon1.active_connections, "Daemon1 should have removed the connection"
    assert ("127.0.0.1", 7777) not in daemon2.active_connections, "Daemon2 should have removed the connection"
    print("test_fin_termination passed!")

if __name__ == "__main__":
    try:
        setup_daemons()
        test_handshake()
        test_invalid_datagram()
        test_fin_termination()
    finally:
        teardown_daemons()
