import socket
from Datagram import Datagram
import sys
from typing import Tuple

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
        self.daemon_tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect_to_daemon(self):
        try:
            self.daemon_tcp_socket.connect((self.daemon_ip, self.daemon_port))
            self.connected = True
        except ConnectionRefusedError:
            print("Connection refused")
            sys.exit(1)

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
        

    # def main_menu(self):
    #     while True:
    #         print("\nOptions:")
    #         print("1. Wait for chat requests")
    #         print("2. Start a new chat")
    #         print("q. Quit")
    #         choice = input("Select an option (1/2/q): ").strip()
    #         if choice == "1":
    #             self.wait_for_requests()
    #         elif choice.lower() == "q":
    #             self.quit()
    #         else:
    #             print("Invalid option. Please try again.")


    def quit(self):
        self.daemon_tcp_socket.sendall("2".encode("utf-8"))
        self.daemon_tcp_socket.close()
        print("Disconnected from the daemon. Goodbye!")
        sys.exit(0)

    def run(self):
        self.connect_to_daemon()
        # self.main_menu()