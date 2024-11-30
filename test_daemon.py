import threading
import time
from simp_daemon import Daemon
from simp_client import Client
from Datagram import Datagram

def run_daemon(daemon):
    daemon.start()


def test_daemon_communication():
    daemon1_ip = "127.0.0.1"
    daemon2_ip = "127.0.0.2"
    daemon_port = 7777

    daemon1 = Daemon(daemon1_ip, daemon_port)
    daemon2 = Daemon(daemon2_ip, daemon_port)

    daemon1_thread = threading.Thread(target=run_daemon, args=(daemon1,))
    daemon2_thread = threading.Thread(target=run_daemon, args=(daemon2,))

    daemon1_thread.start()
    daemon2_thread.start()

    time.sleep(2)

    # Send a test datagram from daemon1 to daemon2
    test_datagram = Datagram(type=0x01, operation=0x02, sequence=0, user="daemon1", payload="test", length=4)
    daemon1.send_datagram(daemon1.daemon_udp_socket, test_datagram, (daemon2_ip, daemon_port))

    # Wait for the datagram to be received by daemon2
    received_datagram, address = None, None
    for _ in range(3):  # Retry up to 3 times
        received_datagram, address = daemon2.receive_datagram(daemon2.daemon_udp_socket)
        if received_datagram is not None:
            break
        time.sleep(1)

    daemon1.end()
    daemon2.end()
    daemon1_thread.join()
    daemon2_thread.join()

    assert received_datagram is not None, "Datagram was not received"
    assert received_datagram.payload == "test", f"Unexpected payload: {received_datagram.payload}"
    assert address == (daemon1_ip, daemon_port), f"Unexpected address: {address}"
    print("Daemon communication test passed.")

# def test_daemon_start_and_stop():
#     daemon_ip = "127.0.0.1"
#     daemon_port = 7777
#     daemon = Daemon(daemon_ip, daemon_port)

#     daemon_thread = threading.Thread(target=run_daemon, args=(daemon,))
#     daemon_thread.start()

#     time.sleep(2)

#     daemon.end()
#     daemon_thread.join()

#     assert not daemon.process
#     print("Daemon start and stop test passed.")

# def test_three_way_handshake():
#     daemon1_ip = "127.0.0.1"
#     daemon2_ip = "127.0.0.2"
#     daemon_port = 7777
#     daemon1 = Daemon(daemon1_ip, daemon_port)
#     daemon2 = Daemon(daemon2_ip, daemon_port)

#     daemon1_thread = threading.Thread(target=run_daemon, args=(daemon1,))
#     daemon2_thread = threading.Thread(target=run_daemon, args=(daemon2,))

#     daemon1_thread.start()
#     daemon2_thread.start()

#     time.sleep(2)

#     result = daemon1.three_way_handshake_init((daemon2_ip, daemon_port))

#     daemon1.end()
#     daemon2.end()
#     daemon1_thread.join()
#     daemon2_thread.join()

#     assert result
#     print("Three-way handshake test passed.")

# def test_stop_and_wait():
#     daemon_ip = "127.0.0.1"
#     daemon_port = 7777
#     daemon = Daemon(daemon_ip, daemon_port)

#     daemon_thread = threading.Thread(target=run_daemon, args=(daemon,))
#     daemon_thread.start()

#     time.sleep(2)

#     datagram = Datagram(type=0x01, operation=0x02, sequence=0, user="testuser", payload="")
#     receiver_address = ("127.0.0.1", 8888)
#     result = daemon.stop_and_wait(datagram, receiver_address)

#     daemon.end()
#     daemon_thread.join()

#     assert result is not None
#     print("Stop and wait test passed.")

# def test_client_connect_to_daemon():
#     daemon_ip = "127.0.0.1"
#     daemon_port = 7777
#     daemon = Daemon(daemon_ip, daemon_port)

#     daemon_thread = threading.Thread(target=run_daemon, args=(daemon,))
#     daemon_thread.start()

#     time.sleep(2)

#     client = Client(daemon_ip)
#     result = client.connect_to_daemon()

#     daemon.end()
#     daemon_thread.join()

#     assert result
#     print("Client connect to daemon test passed.")

if __name__ == "__main__":
    #test_daemon_start_and_stop()
    # test_three_way_handshake()
    #test_stop_and_wait()
    #test_client_connect_to_daemon()
    test_daemon_communication()