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
                self.wait_for_chat()
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
            if response == "SUCCESS":
                self.in_chat = True
                self.is_sender = True
                print(f"Chat request sent to {target_ip}. Enter your first message:")
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
                # Receive message from daemon
                response = self.daemon_tcp_socket.recv(1024).decode("utf-8").strip()
                if response.startswith("Chat request from"):
                    print(f"\n{response}")
                    
                    # Prompt user to accept or decline
                    while True:
                        choice = input("Do you want to accept the chat? (y/n): ").strip().lower()
                        if choice in ["y", "n"]:
                            break
                        print("Invalid input. Please type 'y' for accept or 'n' for decline.")
                    
                    # Send response to daemon
                    if choice == "y":
                        self.daemon_tcp_socket.sendall("ACCEPT".encode("utf-8"))
                        print("Chat accepted. Waiting for the first message...")
                        self.in_chat = True
                        self.is_sender = False
                        self.chat_session()  # Enter chat session
                        break
                    else:
                        self.daemon_tcp_socket.sendall("DECLINE".encode("utf-8"))
                        print("Chat declined. Returning to waiting state.")
                else:
                    print(response)
        except Exception as e:
            logger.error(f"Error while waiting for chat: {e}")
            
    def wait_for_message(self):
        """Wait for an incoming message from the daemon."""
        try:
            message = self.daemon_tcp_socket.recv(1024).decode("utf-8").strip()
            if message:
                print(f"\n{message}")
                self.logger.info(f"Message received from daemon: {message}")
                self.is_sender = True  # Switch the state to allow sending the next message
        except Exception as e:
            self.logger.error(f"Error receiving message from daemon: {e}")





        
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
            
    def send_message(self):
        """Send a message to the daemon."""
        try:
            message = input("Enter your message: ").strip()
            if not message:
                print("Message cannot be empty. Please try again.")
                return

            # Send the message to the daemon
            self.daemon_tcp_socket.sendall(f"4 {message}".encode("utf-8"))
            self.logger.info(f"Message sent to daemon: {message}")
            self.is_sender = False  # Toggle the sender state
        except Exception as e:
            self.logger.error(f"Error sending message to daemon: {e}")



    # def handle_incoming_chat_request(self):
    #     """Wait for a chat request and prompt the user to accept or decline."""
    #     try:
    #         print("Waiting for an incoming chat request...")
    #         message = self.daemon_tcp_socket.recv(1024).decode("utf-8").strip()
    #         print(f"\n{message}")
    #         response = input("Enter 'ACCEPT' to join or 'DECLINE' to reject: ").strip().upper()
    #         self.daemon_tcp_socket.sendall(response.encode("utf-8"))
    #         if response == "ACCEPT":
    #             print("Chat request accepted. Waiting for the first message...")
    #         elif response == "DECLINE":
    #             print("Chat request declined.")
    #     except Exception as e:
    #         logger.error(f"Error handling incoming chat request: {e}")


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

