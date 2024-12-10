import socket
import sys
from logger import logger

class Client:
    def __init__(self, daemon_ip: str, daemon_port=7778):
        self.daemon_ip = daemon_ip
        self.daemon_port = daemon_port
        self.username = None
        self.connected = False
        self.in_chat = False
        self.is_sender = False
        self.daemon_tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.logger = logger

    def connect_to_daemon(self):
        """Connect to the daemon."""
        try:
            self.daemon_tcp_socket.connect((self.daemon_ip, self.daemon_port))
            self.connected = True
            print(f"Connected to Daemon at {self.daemon_ip}:{self.daemon_port}")
        except Exception as e:
            logger.error(f"Failed to connect to daemon: {e}")
            sys.exit(1)

    def send_username(self):
        """Send the username to the daemon."""
        try:
            self.username = input("Enter your username: ").strip()
            if not self.username:
                print("Username cannot be empty. Please restart the client.")
                sys.exit(1)
            self.daemon_tcp_socket.sendall(f"1 {self.username}".encode("utf-8"))
            logger.info(f"Username '{self.username}' sent to the daemon.")
            print("Username sent successfully.")
        except Exception as e:
            logger.error(f"Error sending username to daemon: {e}")
            sys.exit(1)

    def menu(self):
        """Main menu for client interaction."""
        while True:
            print("\nMain Menu:")
            print("1. Start Chat")
            print("2. Wait for Chat")
            print("q. Quit")
            choice = input("Enter your choice: ").strip()

            if choice == "1":
                self.start_chat()
            elif choice == "2":
                self.handle_incoming_chat_request()
            elif choice.lower() == "q":
                self.quit()
            else:
                print("Invalid choice. Please try again.")


    def start_chat(self):
        """Start a chat by providing the target daemon's IP."""
        try:
            target_ip = input("Enter the IP address of the target daemon: ").strip()
            if not target_ip:
                print("Target IP cannot be empty.")
                return

            self.daemon_tcp_socket.sendall(f"2 {target_ip}".encode("utf-8"))
            logger.info(f"Sent start_chat command to daemon for target IP {target_ip}.")

            response = self.daemon_tcp_socket.recv(1024).decode("utf-8")
            if response == "ACCEPTED":
                self.in_chat = True
                self.is_sender = True
                print(f"Chat accepted. Chat started with {target_ip}.")
                self.chat_session()
            elif response == "DECLINED":
                print(f"Chat request declined by {target_ip}.")
            else:
                print("Failed to start chat.")
        except Exception as e:
            logger.error(f"Error starting chat: {e}")


    def wait_for_chat(self):
        """Wait for an incoming chat request."""
        try:
            print("Waiting for an incoming chat request...")
            while True:
                response = self.daemon_tcp_socket.recv(1024).decode("utf-8")
                if response.startswith("Chat request from"):
                    requester = response.split(":")[1].strip()
                    print(f"\nIncoming chat request from {requester}.")
                    accept = input("Do you want to accept the chat? (y/n): ").strip().lower()
                    if accept == "y":
                        self.daemon_tcp_socket.sendall("ACCEPT".encode("utf-8"))
                        print("Chat accepted. Waiting for their message...")
                        self.in_chat = True
                        self.is_sender = False
                        self.chat_session()
                    else:
                        self.daemon_tcp_socket.sendall("DECLINE".encode("utf-8"))
                        print("Chat declined.")
                else:
                    print(response)
        except Exception as e:
            logger.error(f"Error waiting for chat: {e}")
        
    def chat_session(self):
        """Seamless chat session loop."""
        try:
            print("\nChat session started. Type your messages or wait for one.")
            while self.in_chat:
                if self.is_sender:
                    self.send_message()
                else:
                    self.wait_for_message()
        except KeyboardInterrupt:
            print("\nExiting chat...")
            self.quit_chat()
        except Exception as e:
            logger.error(f"Error during chat session: {e}")

    def handle_incoming_chat_request(self):
        """Wait for a chat request and prompt the user to accept or decline."""
        try:
            print("Waiting for an incoming chat request...")
            message = self.daemon_tcp_socket.recv(1024).decode("utf-8").strip()
            print(f"\n{message}")
            response = input("Enter 'ACCEPT' to join or 'DECLINE' to reject: ").strip().upper()
            self.daemon_tcp_socket.sendall(response.encode("utf-8"))
            if response == "ACCEPT":
                print("Chat request accepted. Waiting for the first message...")
            elif response == "DECLINE":
                print("Chat request declined.")
        except Exception as e:
            logger.error(f"Error handling incoming chat request: {e}")


    def quit(self):
        """Quit the client."""
        try:
            self.daemon_tcp_socket.sendall("0".encode("utf-8"))
            logger.info("Sent quit command to daemon.")
            self.daemon_tcp_socket.close()
            sys.exit(0)
        except Exception as e:
            logger.error(f"Error quitting client: {e}")
            sys.exit(1)

    def run(self):
        """Run the client."""
        self.connect_to_daemon()
        self.send_username()
        self.menu()


if __name__ == "__main__":
    daemon_ip = input("Enter the IP address of the daemon: ").strip()
    client = Client(daemon_ip)
    client.run()
