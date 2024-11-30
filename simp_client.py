import socket
from Datagram import Datagram
import sys
from typing import Tuple

class Client:
    MESSAGE_CODES = {
        1: "connect",
        2: "check_pending",
        3: "chat_request",
        4: "chat_request_pending",
        5: "chat_accept",
        6: "chat_reject",
        7: "chat_started",
        8: "chat_request_rejected",
        9: "no_pending_chat_request",
        10: "quit"
    }

    def __init__(self, daemon_ip: str, daemon_port=7778):
        self.daemon_ip = daemon_ip
        self.daemon_port = daemon_port
        self.username = None
        self.connected = False
        self.daemon_tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect_to_daemon(self):
        try:
            self.daemon_tcp_socket.connect((self.daemon_ip, self.daemon_port))
            self.connected = True
            print(f"Connected to Daemon on {self.daemon_ip}:{self.daemon_port}")
            
            self.username = input("Enter your username: ").strip()
            self.daemon_tcp_socket.sendall(f"1 {self.username}".encode("utf-8"))  # "connect"
            
            self.check_pending_requests()
        except Exception as e:
            print(f"Error connecting to Daemon: {e}")
            sys.exit(1)

    def check_pending_requests(self):
        try:
            self.daemon_tcp_socket.sendall("2".encode("utf-8"))  # "check_pending"
            response = self.daemon_tcp_socket.recv(1024).decode("utf-8")
            if response.startswith("4"):  # "chat_request_pending"
                pending_user = response.split()[1]
                print(f"Chat request pending from {pending_user}.")
                choice = input("Do you want to accept the chat request? (y/n): ").strip().lower()
                if choice == "y":
                    self.daemon_tcp_socket.sendall(f"5 {pending_user}".encode("utf-8"))  # "chat_accept"
                    self.run_chat_session()
                else:
                    self.daemon_tcp_socket.sendall(f"6 {pending_user}".encode("utf-8"))  # "chat_reject"
                    self.main_menu()
            else:
                self.main_menu()
        except Exception as e:
            print(f"Error checking pending requests: {e}")

    def main_menu(self):
        while True:
            print("\nOptions:")
            print("1. Wait for chat requests")
            print("2. Start a new chat")
            print("q. Quit")
            choice = input("Select an option (1/2/q): ").strip()
            if choice == "1":
                self.wait_for_requests()
            elif choice == "2":
                self.initiate_chat()
            elif choice.lower() == "q":
                self.quit()
            else:
                print("Invalid option. Please try again.")

    def wait_for_requests(self):
        print("Waiting for chat requests...")
        while True:
            response = self.daemon_tcp_socket.recv(1024).decode("utf-8")
            if response.startswith("4"):
                pending_user = response.split()[1]
                print(f"Chat request pending from {pending_user}.")
                choice = input("Do you want to accept the chat request? (y/n): ").strip().lower()
                if choice == "y":
                    self.daemon_tcp_socket.sendall(f"5 {pending_user}".encode("utf-8"))
                    self.run_chat_session()
                else:
                    self.daemon_tcp_socket.sendall(f"6 {pending_user}".encode("utf-8"))

    def initiate_chat(self):
        target_ip = input("Enter the IP address of the user to chat with: ").strip()
        self.daemon_tcp_socket.sendall(f"3 {target_ip}".encode("utf-8"))  # "chat_request"
        response = self.daemon_tcp_socket.recv(1024).decode("utf-8")
        if response.startswith("7"):  # "chat_started"
            print(f"Chat request accepted by {target_ip}. Starting chat...")
            self.run_chat_session()
        else:
            print(f"Chat request declined by {target_ip}.")

    def run_chat_session(self):
        try:
            while True:
                message = input("Enter a message (type 'q' to disconnect): ").strip()
                if not message:
                    continue
                self.daemon_tcp_socket.sendall(message.encode("utf-8"))
                if message.lower() == "q":
                    print("Disconnecting from daemon...")
                    break
        except Exception as e:
            print(f"Error during chat session: {e}")
        finally:
            self.daemon_tcp_socket.close()
            self.connected = False
            print("Disconnected from daemon.")

    def quit(self):
        self.daemon_tcp_socket.sendall("10".encode("utf-8"))
        self.daemon_tcp_socket.close()
        print("Disconnected from the daemon. Goodbye!")
        sys.exit(0)

    def run(self):
        self.connect_to_daemon()
        self.main_menu()