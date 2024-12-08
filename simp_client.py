import socket
from Datagram import Datagram
import sys
from typing import Tuple
from logger import logger
from threading import Thread

class Client:
    MESSAGE_CODES = {
        # CONNECTION TO DAEMON OPERATIONS
        1: "connect",
        2: "disconnect",
        
        # MESSAGE OPERATIONS
        3: "send_message",
        4: "receive_message",
        
        # CHAT OPERATIONS
        5: "wait_chat",
        6: "start_chat", 
        7: "accept_chat",
        8: "decline_chat",
        9: "end_chat"
    }

    def __init__(self, daemon_ip: str, daemon_port=7778):
        self.daemon_ip = daemon_ip
        self.daemon_port = daemon_port
        self.username = None
        self.connected = False
        self.in_chat = False
        self.daemon_tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.logger = logger

    def connect_to_daemon(self):
        try:
            self.daemon_tcp_socket.connect((self.daemon_ip, self.daemon_port))
            self.connected = True
            print(f"Connected to Daemon at {self.daemon_ip}:{self.daemon_port}")
            self.username = input("Enter your username: ").strip()
            self.daemon_tcp_socket.sendall(f"1 {self.username}".encode("utf-8"))  # "connect"
        except ConnectionRefusedError:
            logger.error(f"Connection to Daemon at {self.daemon_ip}:{self.daemon_port} refused.")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error connecting to Daemon: {e}")
            sys.exit(1)

    def main_menu(self):
        while True:
            if self.in_chat:
                print("\nChat Menu:")
                print("1. Send a message")
                print("2. End chat")
            else:
                print("\nMain Menu:")
                print("1. Wait for a chat")
                print("2. Start a chat")
            print("3. Quit")
            
            choice = input("Enter your choice: ")
            if self.in_chat:
                if choice == "1":
                    self.send_message()
                elif choice == "2":
                    self.end_chat()
                elif choice == "3":
                    self.quit()
                else:
                    print("Invalid choice. Please try again.")
            else:
                if choice == "1":
                    self.wait_for_chat()
                elif choice == "2":
                    self.start_chat()
                elif choice == "3":
                    self.quit()
                else:
                    print("Invalid choice. Please try again.")

    def disconnect_from_daemon(self):
        try:
            if self.connected:
                self.daemon_tcp_socket.sendall("2".encode("utf-8"))  # "disconnect"
            self.daemon_tcp_socket.close()  # Close the TCP socket
            self.connected = False
            self.logger.info("Disconnected from Daemon")
        except Exception as e:
            self.logger.error(f"Error disconnecting from Daemon: {e}")


    def send_name_to_daemon(self, name: str):
        """Send the client's name to the daemon."""
        try:
            # Assuming the protocol for sending the name is '1 {name}'
            message = f"1 {name}"  # "1" indicates a connection with the name
            self.daemon_tcp_socket.sendall(message.encode("utf-8"))
            print(f"Sent name '{name}' to the daemon.")
        except Exception as e:
            self.logger.error(f"Error sending name to Daemon: {e}")

    def check_pending_requests(self):
        try:
            self.daemon_tcp_socket.sendall("3".encode("utf-8"))  # "check_pending_requests"
            response = self.daemon_tcp_socket.recv(1024).decode("utf-8")
            print(f"Pending requests: {response}")
        except Exception as e:
            self.logger.error(f"Error checking pending requests: {e}")
        finally:
            self.main_menu()  # Go back to main menu

    def wait_for_chat(self):
        try:
            self.daemon_tcp_socket.sendall("5".encode("utf-8"))  # Notify daemon of waiting status
            print("Waiting for a chat request...")
            
            response = self.daemon_tcp_socket.recv(1024).decode("utf-8")
            if response.startswith("Chat started"):
                print("Chat initiated by another user.")
                self.in_chat = True
                self.chat_loop()
            else:
                print(response)
        except Exception as e:
            self.logger.error(f"Error waiting for chat: {e}")




    # THIS SHOULD INPUT THE CLIENT WE WANT TO CONNECT TO
    def start_chat(self):
        try:
            other_client_ip = input("Enter the IP address of the client you want to connect to: ").strip()
            self.daemon_tcp_socket.sendall(f"6 {other_client_ip}".encode("utf-8"))
            response = self.daemon_tcp_socket.recv(1024).decode("utf-8")
            if response.startswith("Chat started"):
                self.in_chat = True
                self.chat_loop()
            else:
                print(f"Failed to start chat: {response}")
        except Exception as e:
            self.logger.error(f"Error starting chat: {e}")


    def accept_chat(self):
        try:
            self.daemon_tcp_socket.sendall("7".encode("utf-8"))  # "accept_chat"
            response = self.daemon_tcp_socket.recv(1024).decode("utf-8")
            print(f"Accepted a chat: {response}")
        except Exception as e:
            self.logger.error(f"Error accepting chat: {e}")
        finally:
            self.main_menu()

    def decline_chat(self):
        try:
            self.daemon_tcp_socket.sendall("8".encode("utf-8"))  # "decline_chat"
            response = self.daemon_tcp_socket.recv(1024).decode("utf-8")
            print(f"Declined a chat: {response}")
        except Exception as e:
            self.logger.error(f"Error declining chat: {e}")
        finally:
            self.main_menu()

    def end_chat(self):
        try:
            self.daemon_tcp_socket.sendall("9".encode("utf-8"))  # "end_chat"
            response = self.daemon_tcp_socket.recv(1024).decode("utf-8")
            print(f"Ended the chat: {response}")
        except Exception as e:
            self.logger.error(f"Error ending chat: {e}")
        finally:
            self.main_menu()
            
    def chat_loop(self):
        print("Chat started! Type 'q' to leave.")

        # Thread for receiving messages
        def receive_messages():
            while self.in_chat:
                try:
                    response = self.daemon_tcp_socket.recv(1024).decode("utf-8")
                    if response:
                        print(f"Them: {response}")
                except Exception as e:
                    self.logger.error(f"Error receiving messages: {e}")
                    break

        Thread(target=receive_messages, daemon=True).start()

        while self.in_chat:
            message = input("You: ")
            if message.lower() == 'q':
                self.end_chat()
                break
            self.daemon_tcp_socket.sendall(f"3 {message}".encode("utf-8"))




    def quit(self):
        self.daemon_tcp_socket.sendall("2".encode("utf-8"))
        self.daemon_tcp_socket.close()
        print("Disconnected from the daemon. Goodbye!")
        sys.exit(0)

    def run(self):
        self.connect_to_daemon()
        self.main_menu()
