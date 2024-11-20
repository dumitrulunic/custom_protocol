import socket
from Message import Message

class Client:
    def __init__(self, daemon_ip, daemon_port=7778):
        self.daemon_ip = daemon_ip
        self.daemon_port = daemon_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
    def connect(self, username):
        message = Message(type=0x01, operation=0x02, sequence=0x00, user=username, payload="")
        self.sock.sendto(message.to_bytes(), (self.daemon_ip, self.daemon_port))
        
    def chat(self, target_ip):
        pass