import socket
import threading
import time
from simp_daemon import Daemon
from simp_client import Client

def setup_daemon():
    """Start the Daemon for testing."""
    daemon = Daemon(ip="127.0.0.1", port=7778)
    daemon_thread = threading.Thread(target=daemon.start, daemon=True)
    daemon_thread.start()
    time.sleep(1)  # Give the daemon some time to start
    return daemon, daemon_thread

def teardown_daemon(daemon, daemon_thread):
    """Stop the Daemon after testing."""
    daemon.stop()  # Stops the daemon and closes sockets
    daemon_thread.join(timeout=2)  # Ensures the thread has exited
    time.sleep(0.5)  # Small delay to allow ports to be released

def setup_client():
    """Initialize the Client."""
    return Client(daemon_ip="127.0.0.1", daemon_port=7778)

def test_connect_message_with_client():
    daemon, daemon_thread = setup_daemon()
    client = setup_client()
    try:
        print("Running test_connect_message_with_client...")
        username = "TestUser"
        client.username = username
        client.connect_to_daemon()
        response = client.daemon_tcp_socket.recv(1024).decode("utf-8")
        expected_response = f"Welcome, {username}! Connection established."
        assert response == expected_response, f"Expected '{expected_response}', but got '{response}'"
        print("test_connect_message_with_client passed!")
    finally:
        client.disconnect_from_daemon()
        teardown_daemon(daemon, daemon_thread)

def test_disconnect_message_with_client():
    daemon, daemon_thread = setup_daemon()
    client = setup_client()
    try:
        print("Running test_disconnect_message_with_client...")
        client.connect_to_daemon()
        client.daemon_tcp_socket.sendall("2".encode("utf-8"))  # Send disconnect message
        response = client.daemon_tcp_socket.recv(1024).decode("utf-8")
        expected_response = "Goodbye!"
        assert response == expected_response, f"Expected '{expected_response}', but got '{response}'"
        print("test_disconnect_message_with_client passed!")
    finally:
        client.disconnect_from_daemon()
        teardown_daemon(daemon, daemon_thread)

def test_send_message_with_client():
    daemon, daemon_thread = setup_daemon()
    client = setup_client()
    try:
        print("Running test_send_message_with_client...")
        client.connect_to_daemon()
        chat_message = "Hello, this is a test message!"
        client.daemon_tcp_socket.sendall(f"3 {chat_message}".encode("utf-8"))
        response = client.daemon_tcp_socket.recv(1024).decode("utf-8")
        expected_response = f"Message received: {chat_message}"
        assert response == expected_response, f"Expected '{expected_response}', but got '{response}'"
        print("test_send_message_with_client passed!")
    finally:
        client.disconnect_from_daemon()
        teardown_daemon(daemon, daemon_thread)

def test_wait_chat_with_client():
    daemon, daemon_thread = setup_daemon()
    client = setup_client()
    try:
        print("Running test_wait_chat_with_client...")
        client.connect_to_daemon()
        client.daemon_tcp_socket.sendall("5".encode("utf-8"))  # Send wait chat message
        response = client.daemon_tcp_socket.recv(1024).decode("utf-8")
        expected_response = "Waiting for a chat request..."
        assert response == expected_response, f"Expected '{expected_response}', but got '{response}'"
        print("test_wait_chat_with_client passed!")
    finally:
        client.disconnect_from_daemon()
        teardown_daemon(daemon, daemon_thread)

# Add other test functions following the same pattern...

if __name__ == "__main__":
    test_connect_message_with_client()
    time.sleep(0.5)  # Delay to allow cleanup
    test_disconnect_message_with_client()
    time.sleep(0.5)
    test_send_message_with_client()
    time.sleep(0.5)
    test_wait_chat_with_client()
