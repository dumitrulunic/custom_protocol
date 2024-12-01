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

    for i in range(5, 0, -1):
        print(f"starting test in {i}")
        time.sleep(1)

    try:
         test_datagram = Datagram(type=0x01, operation=0x02, sequence=0, user="daemon1", payload="test datagram", length=4) # send syn datagram
         print(f"{daemon1_ip}:{daemon_port} - Sending datagram: {test_datagram} to {daemon2_ip}:{daemon_port}")
         result = daemon1.stop_and_wait(test_datagram, (daemon2_ip, daemon_port))
         assert result, "Daemon1 failed to complete stop-and-wait with Daemon2."
         print("Daemon1 completed stop-and-wait with Daemon2.")
    finally:
        daemon1.end()
        daemon2.end()

        daemon1_thread.join()
        daemon2_thread.join()
        
def test_three_way_handshake():
    sender_ip = "127.0.0.1"
    receiver_ip = "127.0.0.2"
    daemon_port = 7777

    sender_daemon = Daemon(sender_ip, daemon_port)
    receiver_daemon = Daemon(receiver_ip, daemon_port)

    sender_thread = threading.Thread(target=sender_daemon.start)
    receiver_thread = threading.Thread(target=receiver_daemon.start)

    sender_thread.start()
    receiver_thread.start()

    time.sleep(2)

    try:
        print("Testing custom three-way handshake")
        result = sender_daemon.three_way_handshake_init((receiver_ip, daemon_port))
        assert result, "Three-way handshake failed!"
        print("Three-way handshake successful")

        # Validate handshake state
        # Add any daemon-specific state validation here if needed
        print("Handshake validation complete.")

    finally:
        sender_daemon.end()
        receiver_daemon.end()
        sender_thread.join()
        receiver_thread.join()
        print("Daemons shut down.")

        
def test_stop_and_wait():
    sender_ip = "127.0.0.1"
    receiver_ip = "127.0.0.2"
    daemon_port = 7777

    sender_daemon = Daemon(sender_ip, daemon_port)
    receiver_daemon = Daemon(receiver_ip, daemon_port)

    sender_thread = threading.Thread(target=sender_daemon.start)
    receiver_thread = threading.Thread(target=receiver_daemon.start)

    sender_thread.start()
    receiver_thread.start()

    time.sleep(2)  # Allow daemons to start up

    try:
        # Test Case 1: Sending SYN
        syn_datagram = Datagram(type=0x01, operation=0x02, sequence=1, user="sender", payload="SYN", length=3)
        print(f"Test Case 1: Sending SYN from {sender_ip} to {receiver_ip}")
        result = sender_daemon.stop_and_wait(syn_datagram, (receiver_ip, daemon_port))
        assert result, "Failed to handle SYN and receive ACK"
        print("Test Case 1 Passed")

        # Test Case 2: Sending SYN+ACK
        syn_ack_datagram = Datagram(type=0x01, operation=0x02 | 0x04, sequence=2, user="receiver", payload="SYN+ACK", length=7)
        print(f"Test Case 2: Sending SYN+ACK from {receiver_ip} to {sender_ip}")
        result = receiver_daemon.stop_and_wait(syn_ack_datagram, (sender_ip, daemon_port))
        assert result, "Failed to handle SYN+ACK and receive ACK"
        print("Test Case 2 Passed")

        # Test Case 3: Sending ACK (Expecting no response)
        ack_datagram = Datagram(type=0x01, operation=0x04, sequence=3, user="sender", payload="ACK", length=3)
        print(f"Test Case 3: Sending ACK from {sender_ip} to {receiver_ip}")
        result = sender_daemon.stop_and_wait(ack_datagram, (receiver_ip, daemon_port))
        assert result, "Failed to handle ACK"
        print("Test Case 3 Passed")

        # Test Case 4: Unexpected Response
        unexpected_datagram = Datagram(type=0x01, operation=0x01, sequence=4, user="sender", payload="ERR", length=3)
        print(f"Test Case 4: Sending Unexpected Datagram from {sender_ip} to {receiver_ip}")
        result = sender_daemon.stop_and_wait(unexpected_datagram, (receiver_ip, daemon_port))
        assert not result, "Unexpected response incorrectly handled as success"
        print("Test Case 4 Passed")

    finally:
        sender_daemon.end()
        receiver_daemon.end()
        sender_thread.join()
        receiver_thread.join()
        print("Daemons shut down.")
        
def test_daemon_interprets_syn_ack():
    sender_ip = "127.0.0.1"
    receiver_ip = "127.0.0.2"
    daemon_port = 7777

    # Initialize sender and receiver daemons
    sender_daemon = Daemon(sender_ip, daemon_port)
    receiver_daemon = Daemon(receiver_ip, daemon_port)

    sender_thread = threading.Thread(target=sender_daemon.start)
    receiver_thread = threading.Thread(target=receiver_daemon.start)

    sender_thread.start()
    receiver_thread.start()

    time.sleep(2)  # Give daemons time to initialize

    try:
        # Manually craft and send SYN+ACK from sender to receiver
        syn_ack_datagram = Datagram(type=0x01, operation=0x06, sequence=1, user="Sender", payload="SYN+ACK", length=7)
        print(f"{sender_ip}:{daemon_port} - Sending SYN+ACK to {receiver_ip}:{daemon_port}")
        sender_daemon.send_datagram(sender_daemon.daemon_udp_socket, syn_ack_datagram, (receiver_ip, daemon_port))

        # Wait for receiver's response
        response, addr = receiver_daemon.receive_datagram(receiver_daemon.daemon_udp_socket)
        if response:
            print(f"Response received by receiver: {response}")
            assert response.operation == 0x04, "Expected ACK from receiver, but got something else."
            print("Receiver successfully interpreted SYN+ACK and sent ACK.")
        else:
            print("Receiver did not respond to SYN+ACK.")
            assert False, "Receiver failed to respond to SYN+ACK."
    finally:
        # Shutdown daemons
        sender_daemon.end()
        receiver_daemon.end()
        sender_thread.join()
        receiver_thread.join()


if __name__ == "__main__":
    # test_daemon_communication()
    test_three_way_handshake()
    # test_stop_and_wait()
    # test_daemon_interprets_syn_ack()