import socket
from Datagram import Datagram

class Client:
    def __init__(self, daemon_ip,  username: str, daemon_port=7778):
        self.daemon_ip = daemon_ip
        self.daemon_port = daemon_port
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
    def connect_to_daemon(self) -> bool:
        """Must connect to the daemon"""
        pass
        
    def send_chat_request(self, receiver_ip: str) -> None:
        """Must send the chat request"""
        pass
    
    def handle_incoming_request(self) -> None:
        """waint to requests and ask user about accept/reject"""
        pass
    
    def start_chat(self, receiver_ip: str) -> None:
        """Handle the chat session by sending and receiving mesages with the daemon."""