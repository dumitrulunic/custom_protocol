import sys
from simp_client import Client

def main():
    if len(sys.argv) > 1:
        daemon_ip = sys.argv[1]

    client = Client(daemon_ip)
    print(f"Connecting to Daemon on {client.daemon_ip}:{client.daemon_port}...")
    try:
        client.connect_to_daemon()
    except KeyboardInterrupt:
        print("\nClient interrupted. Exiting...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
