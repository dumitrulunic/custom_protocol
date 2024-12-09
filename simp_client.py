import socket
from Datagram import Datagram
import sys
from typing import Tuple
from logger import logger
from threading import Thread

class Client:
    MESSAGE_CODES = {
        # CONNECTION TO DAEMON OPERATIONS
        1: "send_username",
        0: "quit",
        2: "start_chat",
        3: "wait_chat",
        4: "send_message",
        5: "receive_message",
        
        # # MESSAGE OPERATIONS
        # 3: "send_message",
        # 4: "receive_message",
        
        # # CHAT OPERATIONS
        # 5: "wait_chat",
        # 6: "start_chat", 
        # 7: "accept_chat",
        # 8: "decline_chat",
        # 9: "end_chat"
    }

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
        try:
            self.daemon_tcp_socket.connect((self.daemon_ip, self.daemon_port))
            self.connected = True
            print(f"Connected to Daemon at {self.daemon_ip}:{self.daemon_port}")
        except ConnectionRefusedError:
            logger.error(f"Connection to Daemon at {self.daemon_ip}:{self.daemon_port} refused.")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error connecting to Daemon: {e}")
            sys.exit(1)
            
            
    def wait_for_ack_from_daemon(self):
        try:
            response = self.daemon_tcp_socket.recv(1024).decode("utf-8")
            if response == "SUCCESS":
                self.logger.info("Received acknowledgement from Daemon.")
                return True
            else:
                self.logger.error(f"Failed to receive acknowledgement from Daemon: {response}")
                return False
        except Exception as e:
            self.logger.error(f"Error waiting for acknowledgement from Daemon: {e}")
            
    def menu(self):
        """Main menu for client interaction."""
        while True:
            print("\nMain Menu:")
            print("q. Quit")
            print("1. Start Chat")
            choice = input("Enter your choice: ").strip()
            if choice == "q":
                self.quit()
            elif choice == "1":
                self.start_chat()
            else:
                print("Invalid choice. Please try again.")



            
    def send_username(self):
        """Send the username to the daemon."""
        try:
            self.username = input("Enter your username: ").strip()
            if not self.username:
                print("Username cannot be empty. Please restart the client.")
                sys.exit(1)
            message = f"1 {self.username}"
            self.daemon_tcp_socket.sendall(message.encode("utf-8"))
            self.logger.info(f"Username '{self.username}' sent to the daemon.")
        except Exception as e:
            self.logger.error(f"Error sending username to Daemon: {e}")
            
            
    def start_chat(self):
        """Start a chat session by initiating a handshake."""
        try:
            target_ip = input("Enter the IP address of the target daemon to start a chat: ").strip()
            if not target_ip:
                print("Target IP cannot be empty.")
                return

            self.daemon_tcp_socket.sendall(f"2 {target_ip}".encode("utf-8"))  # Start chat command
            self.logger.info(f"Sent start_chat command to the daemon with target IP {target_ip}.")

            response = self.daemon_tcp_socket.recv(1024).decode("utf-8")
            if response != "SUCCESS":
                print("Failed to start chat.")
                return

            self.in_chat = True  # Chat is active
            self.is_sender = True  # Initiator sends the first message
            print(f"Handshake with daemon at {target_ip} completed successfully.")
            self.chat_menu()
        except Exception as e:
            self.logger.error(f"Error starting chat: {e}")
            print("An error occurred while starting the chat.")
            
    def chat_menu(self):
        """Chat menu to send or wait for messages."""
        while self.in_chat:
            if self.is_sender:
                print("\nChat Menu:")
                print("1. Send Message")
                print("2. Quit Chat")
            else:
                print("\nChat Menu:")
                print("1. Wait for Message")
                print("2. Quit Chat")

            choice = input("Enter your choice: ").strip()
            if choice == "1":
                if self.is_sender:
                    self.send_message()
                else:
                    self.wait_for_message()
            elif choice == "2":
                self.quit_chat()
            else:
                print("Invalid choice. Please try again.")
            
            
    def send_message(self):
        """Send a message during the chat."""
        try:
            message = input("Enter your message: ").strip()
            if not message:
                print("Message cannot be empty.")
                return

            self.daemon_tcp_socket.sendall(f"4 {message}".encode("utf-8"))
            self.logger.info(f"Sent message: {message}")

            # Wait for acknowledgment
            response = self.daemon_tcp_socket.recv(1024).decode("utf-8")
            if response != "SUCCESS":
                print("Failed to send the message.")
                return

            print("Message sent successfully.")
            self.is_sender = False  # Switch to waiting mode
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            print("An error occurred while sending the message.")

    def wait_for_message(self):
        """Wait for a message during the chat."""
        try:
            print("Waiting for a message...")
            response = self.daemon_tcp_socket.recv(1024).decode("utf-8")
            if response:
                print(f"\nMessage received: {response}\n")
                self.is_sender = True  # Switch to sending mode
            else:
                print("No message received.")
        except Exception as e:
            self.logger.error(f"Error waiting for message: {e}")
            print("An error occurred while waiting for a message.")

    def quit_chat(self):
        """Quit the active chat."""
        try:
            self.daemon_tcp_socket.sendall("0".encode("utf-8"))
            self.logger.info("Quit chat command sent to the daemon.")
            self.in_chat = False
        except Exception as e:
            self.logger.error(f"Error quitting chat: {e}")

            
            
    def quit(self):
        """Quit the client."""
        try:
            self.daemon_tcp_socket.sendall("0".encode("utf-8")) # quit
            self.logger.info("Sent quit command to the daemon.")
            
            try:
                data = self.daemon_tcp_socket.recv(1024)
                if not data:
                    self.logger.info("Daemon closed connection. Disconnect successful.")
            except ConnectionResetError:
                self.logger.info("Daemon forcibly closed the connection. Disconnect successful.")
            except Exception as e:
                self.logger.warning(f"Unexpected issue waiting for disconnect: {e}")
            finally:
                self.daemon_tcp_socket.close()
                sys.exit(0)
        except Exception as e:
            self.logger.error(f"Error quitting: {e}")
            sys.exit(1)

    def run(self):
        """Run the client."""
        self.connect_to_daemon()
        if not self.connected:
            print("Failed to connect to the daemon.")
            return
        self.send_username()
        print("Username sent successfully.")
        self.menu()
