import threading
import time
from simp_daemon import Daemon

def run_daemon(daemon):
    daemon.start()

if __name__ == "__main__":
    daemon_ip = "127.0.0.1"  # Use localhost for testing
    daemon_port = 7777
    daemon = Daemon(daemon_ip, daemon_port)

    # Start the daemon in a separate thread
    """
    target is function to execute 
    args is tuple of arguments for the function
    """
    daemon_thread = threading.Thread(target=run_daemon, args=(daemon,)) 
    daemon_thread.start()

    # Allow the daemon to run for a short period
    time.sleep(5)

    # Stop the daemon
    daemon.end()

    # Wait for the daemon thread to finish
    daemon_thread.join()

    print("Daemon has been stopped.")