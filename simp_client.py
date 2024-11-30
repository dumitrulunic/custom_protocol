import socket
from Datagram import Datagram
import sys
from typing import Tuple

class Client:
    def __init__(self, daemon_ip:str, daemon_port=7778):
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
            
            self.run_chat_session()
        except Exception as e:
            print(f"Error connecting to Daemon: {e}")
            sys.exit(1)
            
    def run_chat_session(self):
        try:
            while True:
                message = input("Enter a message (type 'QUIT' to disconnect): ").strip()
                if not message:
                    continue
                self.daemon_tcp_socket.sendall(message.encode("utf-8"))
                if message.upper() == "QUIT":
                    print("Disconnecting from daemon...")
                    break
        except Exception as e:
            print(f"Error during chat session: {e}")
        finally:
            self.daemon_tcp_socket.close()
            self.connected = False
            print("Disconnected from daemon.")
            
    def run(self):
        self.connect_to_daemon()
        self.send_message()
            

    def request_chat():
        pass