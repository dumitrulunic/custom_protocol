import socket
from Message import Message

class Daemon:
    def __init__(self, ip:str, port:int = 7777):
        self.ip = ip
        self.port = port
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
        