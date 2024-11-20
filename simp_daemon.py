import socket
from Message import Message

class Daemon:
    def __init__(self, ip:str, daemon_port:int = 7777, client_port:int = 7778):
        self.ip = ip
        self.daemon_port = daemon_port
        self.client_port = client_port
        self.connections = {}
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.ip, self.port))
        
    def listen_to_client(self):
        data, address = self.sock.recvfrom(1024)
        self.handle_message(data, address)
        pass
        
    def handle_message(self, data, addr):
        message = Message.from_bytes(data)
        pass
        