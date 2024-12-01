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

if __name__ == "__main__":
    test_daemon_communication()