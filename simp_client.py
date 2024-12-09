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
            print("\nq. Quit")
            print("1. Start Chat")
            print("2. Wait for Chat")
            choice = input("Enter your choice: ")
            if choice == "q":
                self.quit()
            elif choice == "1":
                self.start_chat()
            elif choice == "2":
                self.wait_chat()
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
        try:
            target_ip = input("Enter the IP address of the target daemon to start a chat: ").strip()
            if not target_ip:
                print("Target IP cannot be empty. Aborting start chat operation.")
                return

            message = f"2 {target_ip}"  # Command with target IP
            self.daemon_tcp_socket.sendall(message.encode("utf-8"))  # Send start_chat command
            self.logger.info(f"Sent start_chat command to the daemon with target IP {target_ip}.")

            if not self.wait_for_ack_from_daemon():
                print("Failed to start chat.")
                return

            print(f"Handshake with daemon at {target_ip} completed successfully.")
        except Exception as e:
            self.logger.error(f"Error starting chat: {e}")
            print("An error occurred while starting the chat.")

    def wait_chat(self):
        try:
            self.daemon_tcp_socket.sendall("3".encode("utf-8"))  # Command for wait_chat
            self.logger.info("Sent wait_chat command to the daemon.")
            
            if not self.wait_for_ack_from_daemon():
                print("Failed to wait for chat.")
                return

            print("Handshake completed successfully. Waiting for messages...")
        except Exception as e:
            self.logger.error(f"Error waiting for chat: {e}")
            print("An error occurred while waiting for the chat.")


            
            
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
