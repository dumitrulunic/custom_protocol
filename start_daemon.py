import sys
from simp_daemon import Daemon

def main():
    if len(sys.argv) > 1:
        daemon_ip = sys.argv[1]

    daemon = Daemon(daemon_ip)
    try:
        daemon.start()
    except KeyboardInterrupt:
        print("\nDaemon interrupted. Shutting down...")
    finally:
        daemon.end()

if __name__ == "__main__":
    main()
