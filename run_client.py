from simp_client import Client

def main():
    daemon_ip = input("Enter the IP address of the daemon: ")

    client = Client(daemon_ip=daemon_ip)
    client.run()

if __name__ == "__main__":
    main()
