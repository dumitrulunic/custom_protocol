import socket
from Datagram import Datagram
from typing import List, Tuple

class Daemon:
    def __init__(self, daemon_ip:str, daemon_port:int = 7777, client_port:int = 7778):
        self.daemon_ip = daemon_ip
        self.daemon_port = daemon_port
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_port = client_port
        self.active_chat = None
        self.process = True # This is a flag to stop the daemon
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
        print(f"Daemon init at {self.daemon_ip}:{self.daemon_port}")
        
    def start(self) -> None:
        """Must start the daemon"""
        print("Daemon started")
        try:
            # Binding the UDP socket to specified IP and port
            self.udp_socket.bind((self.daemon_ip,self.daemon_port))
            while self.process: # Daemon is active 
                try:
                    # Listen for data from incoming datagrams (UDP packets)
                    data, addr = self.udp_socket.recvfrom(1024)
                    # Parse datagram
                    datagram = Datagram(data)
                    # Handle datagram
                    self.handle_request(addr, datagram)
                except socket.error as e:
                    # Socket was closed, break out the loop
                    break
                print(f"Error handling datagram: {e}")
        except Exception as e:
            print(f"Error starting daemon: {e}")
        finally:
            self.udp_socket.close()
    
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
        # Convert datagram to bytes
        datagram_bytes = datagram.to_bytes()
        # Send datagram to receiver
        self.udp_socket.sendto(datagram_bytes, receiver_address)
    
    # another daemon -> daemon
    def receive_datagram(self) -> Tuple[Datagram, Tuple[int, int]]:
        """Must receive the datagram in form of tuple of Datagram and sender address(tuple of port and ip)"""
        data, sender_address = self.udp_socket.recvfrom(1024)
        datagram = Datagram.from_bytes(data)
        return datagram, sender_address
    
    # daemon -> another daemon
    def three_way_handshake(self, sender_address:Tuple[int, int], sender_username: str) -> bool:
        """Must establish a connection, input is the sender address with port and the usernamea as tuple and also second input is the username"""
        # We send the SYN
        syn_datagram = Datagram(type= 0x01, operation=0x02, sequence=0, user=sender_username, payload="", length=0)
        # Send the SYN datagram
        self.send_datagram(syn_datagram, sender_address)

        # We wait for SYN-ACK
        try:
            datagram, _ = self.receive_datagram() # Ignore the sender address
            if datagram.operation == 0x04: # SYN-ACK
                ack_datagram = Datagram(type=0x01, operation=0x04, sequence=0, user=sender_username, payload="", length=0)
                self.send_datagram(ack_datagram, sender_address)
                return True
        except Exception as e:
            print(f"Error receiving SYN-ACK: {e}")          
        return False
    
    # daemon -> another daemon
    def stop_and_wait(self, datagram:Datagram, receiver_address:Tuple[int, int]) -> None | Datagram:
        """Must implement stop and wait protocol, input is datagram and sender address as tuple"""
        pass
    
    def end(self):
        """Must end the daemon session(daemon must be active non stop and listen for requests)"""
        self.process = False
        try:
            self.udp_socket.close()
            print("Daemon stopped")
        except Exception as e:
            print(f"Error closing socket: {e}")
        