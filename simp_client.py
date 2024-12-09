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
            print("\n0. Quit")
            choice = input("Enter your choice: ")
            if choice == "0":
                self.quit()
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
            
    def quit(self):
        """Quit the client."""
        try:
            self.daemon_tcp_socket.sendall("0".encode("utf-8"))  # Send quit command
            self.logger.info("Sent quit command to the daemon.")
            
            # Wait for the socket to close (detect EOF)
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
