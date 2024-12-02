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
            print(f"Welcome, {self.username}!")
            self.check_pending_requests()
        except Exception as e:
            print(f"Error connecting to Daemon: {e}")
            sys.exit(1)

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
                
    def check_pending_requests(self):
        try:
            self.daemon_tcp_socket.sendall("2".encode("utf-8"))  # "check_pending"
            response = self.daemon_tcp_socket.recv(1024).decode("utf-8")
            if response.startswith("4"):  # "chat_request_pending"
                _, ip, username = response.split()
                print(f"Chat request pending from {username} at {ip}.")
                choice = input("Do you want to accept the chat request? (y/n): ").strip().lower()
                if choice == "y":
                    self.daemon_tcp_socket.sendall(f"5 {ip}".encode("utf-8"))  # "chat_accept"
                    self.run_chat_session()
                else:
                    self.daemon_tcp_socket.sendall(f"6 {ip}".encode("utf-8"))  # "chat_reject"
                    print(f"Chat request from {username} rejected.")
            else:
                self.main_menu()
        except Exception as e:
            print(f"Error checking pending requests: {e}")

    def wait_for_requests(self):
        print("Waiting for chat requests...")
        try:
            while True:
                response = self.daemon_tcp_socket.recv(1024).decode("utf-8")
                if response.startswith("4"):  # "chat_request_pending"
                    _, ip, username = response.split()
                    print(f"Chat request pending from {username} at {ip}.")
                    choice = input("Do you want to accept the chat request? (y/n): ").strip().lower()
                    if choice == "y":
                        self.daemon_tcp_socket.sendall(f"5 {ip}".encode("utf-8"))  # "chat_accept"
                        self.run_chat_session()
                        break
                    else:
                        self.daemon_tcp_socket.sendall(f"6 {ip}".encode("utf-8"))  # "chat_reject"
                        print(f"Chat request from {username} rejected.")
        except Exception as e:
            print(f"Error while waiting for requests: {e}")

    def initiate_chat(self):
        while True:
            try:
                target_input = input("Enter the target IP and port (e.g., 127.0.0.1:7778): ").strip()
                if ":" not in target_input:
                    print("Invalid format. Please use IP:PORT.")
                    continue

                target_ip, target_port = target_input.split(":")
                target_port = int(target_port)

                self.daemon_tcp_socket.sendall(f"3 {target_ip}:{target_port}".encode("utf-8"))  # "chat_request"

                response = self.daemon_tcp_socket.recv(1024).decode("utf-8")
                if response.startswith("7"):  # Chat started
                    print(f"Chat request accepted by {target_ip}:{target_port}. Starting chat...")
                    self.run_chat_session()
                    break
                elif response.startswith("8"):  # Chat rejected
                    print(f"Chat request rejected by {target_ip}:{target_port}.")
                    break
                elif response == "9":  # No pending chat requests
                    print("No pending chat requests.")
                    break
            except ValueError:
                print("Invalid port. Please ensure the port is a number.")
            except Exception as e:
                print(f"Error initiating chat: {e}")
                break



                
    def run_chat_session(self):
        print("Chat session started. Type 'q' to quit.")
        try:
            while True:
                message = input("You: ").strip()
                if message.lower() == "q":
                    print("Exiting chat...")
                    self.daemon_tcp_socket.sendall("10".encode("utf-8"))  # "quit"
                    break
                self.daemon_tcp_socket.sendall(message.encode("utf-8"))
                response = self.daemon_tcp_socket.recv(1024).decode("utf-8")
                if response:
                    print(f"Friend: {response}")
        except Exception as e:
            print(f"Error during chat session: {e}")

    def quit(self):
        try:
            self.daemon_tcp_socket.sendall("10".encode("utf-8"))  # "quit"
            self.daemon_tcp_socket.close()
        except Exception as e:
            print(f"Error while quitting: {e}")
        finally:
            print("Disconnected from daemon. Goodbye!")
            sys.exit(0)

    def run(self):
        self.connect_to_daemon()
        self.main_menu()