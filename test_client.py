import threading
import time
from simp_daemon import Daemon
from simp_client import Client

daemon = None
client = None
daemon_thread = None

def setup_daemon_and_client():
    """Start a daemon and a client for testing."""
    global daemon, client, daemon_thread
    daemon = Daemon(ip="127.0.0.1", port=7777)
    client = Client(daemon_ip="127.0.0.1", daemon_port=7778)

    daemon_thread = threading.Thread(target=daemon.start, daemon=True)
    daemon_thread.start()

    time.sleep(1)

def teardown_daemon_and_client():
    """Stop the daemon and clean up."""
    global daemon, daemon_thread
    if daemon:
        daemon.stop()
    if daemon_thread:
        daemon_thread.join()

def test_client_connection_and_send_name():
    """Test the client connection to the daemon and sending its name."""
    print("Running test_client_connection_and_send_name...")
    
    client.connect_to_daemon()
    assert client.connected, "Client should be connected to the daemon"
    
    client.send_name_to_daemon("andrusha_dimusha")
    
    time.sleep(1)
    
    
    print("test_client_connection_and_send_name passed!")

if __name__ == "__main__":
    try:
        setup_daemon_and_client()
        test_client_connection_and_send_name()
    finally:
        teardown_daemon_and_client()