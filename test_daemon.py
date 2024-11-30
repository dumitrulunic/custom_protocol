import threading
import time
from simp_daemon import Daemon
from simp_client import Client
from Datagram import Datagram

def run_daemon(daemon):
    daemon.start()

def test_daemon_start_and_stop():
    daemon_ip = "127.0.0.1"
    daemon_port = 7777
    daemon = Daemon(daemon_ip, daemon_port)

    daemon_thread = threading.Thread(target=run_daemon, args=(daemon,))
    daemon_thread.start()

    time.sleep(2)

    daemon.end()
    daemon_thread.join()

    assert not daemon.process
    print("Daemon start and stop test passed.")

def test_three_way_handshake():
    daemon_ip = "127.0.0.1"
    daemon_port = 7777
    daemon = Daemon(daemon_ip, daemon_port)

    daemon_thread = threading.Thread(target=run_daemon, args=(daemon,))
    daemon_thread.start()

    time.sleep(2)

    sender_address = ("127.0.0.1", 8888)
    sender_username = "testuser"
    result = daemon.three_way_handshake(sender_address, sender_username)

    daemon.end()
    daemon_thread.join()

    assert result
    print("Three-way handshake test passed.")

def test_stop_and_wait():
    daemon_ip = "127.0.0.1"
    daemon_port = 7777
    daemon = Daemon(daemon_ip, daemon_port)

    daemon_thread = threading.Thread(target=run_daemon, args=(daemon,))
    daemon_thread.start()

    time.sleep(2)

    datagram = Datagram(type=0x01, operation=0x02, sequence=0, user="testuser", payload="")
    receiver_address = ("127.0.0.1", 8888)
    result = daemon.stop_and_wait(datagram, receiver_address)

    daemon.end()
    daemon_thread.join()

    assert result is not None
    print("Stop and wait test passed.")

def test_client_connect_to_daemon():
    daemon_ip = "127.0.0.1"
    daemon_port = 7777
    daemon = Daemon(daemon_ip, daemon_port)

    daemon_thread = threading.Thread(target=run_daemon, args=(daemon,))
    daemon_thread.start()

    time.sleep(2)

    client = Client(daemon_ip)
    result = client.connect_to_daemon()

    daemon.end()
    daemon_thread.join()

    assert result
    print("Client connect to daemon test passed.")

if __name__ == "__main__":
    test_daemon_start_and_stop()
    test_three_way_handshake()
    test_stop_and_wait()
    test_client_connect_to_daemon()