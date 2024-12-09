import threading
import time
from simp_daemon import Daemon

def main():
    daemon_ip = input("Enter the IP address of the daemon: ")
    daemon = Daemon(ip=daemon_ip)

    daemon_thread = threading.Thread(target=daemon.start, daemon=True)
    daemon_thread.start()
    print(f"Daemon is running on {daemon.ip_address}:{daemon.port}. Press Ctrl+C to stop.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down the daemon...")
        daemon.stop()
        daemon_thread.join()

if __name__ == "__main__":
    main()
