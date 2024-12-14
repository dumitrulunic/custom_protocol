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

    def connect_to_daemon(self):
        try:
            self.daemon_tcp_socket.connect((self.daemon_ip, self.daemon_port))
            self.connected = True
            print(f"Connected to Daemon at {self.daemon_ip}:{self.daemon_port}")
        except Exception as e:
            logger.error(f"Failed to connect to daemon: {e}")
            sys.exit(1)

    def send_username(self):
        self.username = input("Enter your username: ").strip()
        if not self.username:
            print("Username cannot be empty. Please restart the client.")
            sys.exit(1)
        self.daemon_tcp_socket.sendall(f"1 {self.username}".encode("utf-8"))
        response = self.daemon_tcp_socket.recv(1024).decode("utf-8")
        if response == "SUCCESS":
            print("Username sent successfully.")
        else:
            print("Failed to set username.")
            sys.exit(1)

    def menu(self):
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
        target_ip = input("Enter the IP address of the target daemon: ").strip()
        if not target_ip:
            print("Target IP cannot be empty.")
            return

        self.daemon_tcp_socket.sendall(f"2 {target_ip}".encode("utf-8"))

        # We now wait for either a SUCCESS (chat accepted) or a message from daemon
        # indicating we must wait for request acceptance.
        # The daemon will send us a "Chat request from..." if it needs acceptance,
        # or "User already in another chat" or "DECLINED" if failed.
        while True:
            response = self.daemon_tcp_socket.recv(1024).decode("utf-8")
            if response == "SUCCESS":
                print(f"Chat started with {target_ip}.")
                self.in_chat = True
                self.is_sender = True
                self.chat_session()
                break
            elif response == "User already in another chat":
                print(response)
                break
            elif response.startswith("Chat request from"):
                # This would happen if remote needs acceptance, 
                # but we initiated the chat, so presumably we've done the handshake already.
                # If this happens, handle similarly as wait_for_chat scenario.
                self.handle_incoming_chat_request(response)
                break
            elif response == "DECLINED":
                print("Chat request declined.")
                break
            elif response.startswith("Message from"):
                # Received first message from other side
                print(response)
                self.is_sender = True
                self.in_chat = True
                self.chat_session()
                break
            else:
                # Continue waiting for a meaningful response
                if response:
                    print(response)
                else:
                    # no meaningful response
                    break

    def wait_for_chat(self):
        print("Waiting for an incoming chat request...")
        while True:
            response = self.daemon_tcp_socket.recv(1024).decode("utf-8")
            if response.startswith("Chat request from"):
                self.handle_incoming_chat_request(response)
                break
            elif response.startswith("Message from"):
                # We've received a message while waiting for a chat request.
                # This implies a chat is already in progress.
                print(response)
                # Set the chat state and start a chat session immediately.
                self.in_chat = True
                self.is_sender = True
                self.chat_session()
                break
            else:
                if response:
                    print(response)
                else:
                    # No data, maybe connection closed?
                    break



    def handle_incoming_chat_request(self, response):
        requester_ip = response.split(":")[1].strip()
        accept = input(f"Do you want to accept the chat request from {requester_ip}? (y/n): ").strip().lower()
        if accept == "y":
            self.daemon_tcp_socket.sendall("3 ACCEPT".encode("utf-8"))
            self.in_chat = True
            self.is_sender = False  # Start by waiting for the other side's message
        else:
            self.daemon_tcp_socket.sendall("3 DECLINE".encode("utf-8"))
            self.in_chat = False

        final_response = self.daemon_tcp_socket.recv(1024).decode("utf-8")
        if final_response == "SUCCESS":
            print("Chat accepted. Chat started.")
            self.chat_session()
        elif final_response == "DECLINED":
            print("Chat declined.")
            self.in_chat = False
        else:
            print("Unexpected response from daemon:", final_response)

    def chat_session(self):
        print("\nChat session started. Type your messages or wait for one.")
        try:
            while self.in_chat:
                if self.is_sender:
                    self.send_message()
                    continue
                else:
                    self.wait_for_message()
                    # print(f"is_sender: {self.is_sender}")
        except KeyboardInterrupt:
            print("\nExiting chat...")
            self.quit_chat()

    def wait_for_message(self):
        print("Waiting for a reply...", flush=True)
        try:
            response = self.daemon_tcp_socket.recv(1024).decode("utf-8", errors="replace")
            if response.startswith("Message from"):
                print(response, flush=True)
                self.is_sender = True
                # print("You can now reply:", flush=True)
            elif not response:
                print("Chat ended.", flush=True)
                self.in_chat = False
            else:
                print(f"Unexpected response: {response}", flush=True)
        except Exception as e:
            print(f"Error receiving message: {e}", flush=True)
            self.in_chat = False





    def send_message(self):
        message = input("Enter your message: ").strip()
        if message.lower() == "quit":
            self.quit_chat()
            return
        if message:
            self.daemon_tcp_socket.sendall(f"4 {message}".encode("utf-8"))
        self.is_sender = False  # Set to False after sending the message


    def quit_chat(self):
        # For simplicity, just send a quit
        self.in_chat = False
        self.daemon_tcp_socket.sendall("0".encode("utf-8"))
        self.daemon_tcp_socket.close()
        sys.exit(0)

    def quit(self):
        self.daemon_tcp_socket.sendall("0".encode("utf-8"))
        self.daemon_tcp_socket.close()
        sys.exit(0)

    def run(self):
        self.connect_to_daemon()
        self.send_username()
        self.menu()
