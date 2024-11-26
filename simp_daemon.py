import socket
from Datagram import Datagram
from typing import List, Tuple

class Daemon:
    def __init__(self, daemon_ip:str, daemon_port:int = 7777, client_port:int = 7778):
        self.daemon_ip = daemon_ip
        self.demon_port = daemon_port
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_port = client_port
        self.active_chat = None
        self.udp_socket.bind((self.ip, self.port))
        self.operations = {
            0x01: {
                0x01: "ERR",
                0x02: "SYN",
                0x04: "ACK",
                0x08: "FIN",
            },
            0x02: {
                0x01: "CHAT"
            }
        }
        print(f"Daemon init at {self.ip}:{self.port}")
        
    def start(self) -> None:
        """Must start the daemon"""
        print("Daemon started")
        pass
    
    
    # another daemon -> daemon
    def handle_request(self, sender_address:Tuple[int, int], datagram:Datagram) -> None:
        """Must handle the request, input is tuple of sender adress(port and ip) and datagram"""
        
        if datagram.type == 0x01:  #Control datagram
            if datagram.operation == 0x02:  #SYN
                self.handle_syn(sender_address, datagram)
            elif datagram.operation == 0x04:  #ACK
                self.handle_ack(sender_address, datagram)
            elif datagram.operation == 0x08:  #FIN
                self.handle_fin(sender_address, datagram)
            elif datagram.operation == 0x01:  #ERR
                self.handle_err(sender_address, datagram)
        elif datagram.type == 0x02:  #Chat datagram
            self.handle_chat(sender_address, datagram)
    
    # daemon -> another daemon
    def send_datagram(self, datagram:Datagram, receiver_address: Tuple[int, int]) -> None:
        """Must send the datagram, input is datagram and tuple of address (port and ip)"""
        pass
    
    # another daemon -> daemon
    def receive_datagram(self) -> Tuple[Datagram, Tuple[int, int]]:
        """Must receive the datagram in form of tuple of Datagram and sender address(tuple of port and ip)"""
        pass
    
    # daemon -> another daemon
    def three_way_handshake(self, sender_address:Tuple[int, int], sender_username: str) -> bool:
        """Must establish a connection, input is the sender address with port and the usernamea as tuple and also second input is the username"""
        pass
    
    # daemon -> another daemon
    def stop_and_wait(self, datagram:Datagram, receiver_address:Tuple[int, int]) -> None | Datagram:
        """Must implement stop and wait protocol, input is datagram and sender address as tuple"""
        pass
    
    def end(self):
        """Must end the daemon session(daemon must be active non stop and listen for requests)"""
        pass
        