import socket
import threading
from Datagram import Datagram

class Daemon:
    def __init__(self, ip:str) -> None:
        self.port = 7777
        self.ip_address = ip
        self.running = True
        
        # Daemon - Daemon TCP socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.ip_address, self.port))
        self.socket.settimeout(5)
        
        # Daemon - Daemon connections
        self.active_connections = {}
        
        self.lock = threading.Lock()
        
    def listen_to_daemons(self):
        while self.running:
            data, address = self.socket.recvfrom(1024)
            if data:
                self.handle_datagram(data, address)
                
    def handle_datagram(self, datagram:Datagram, address:tuple):
        try:
            datagram = Datagram.from_bytes(datagram)
        except ValueError:
            print("Invalid datagram received")
            return
        
        if datagram.type == b'\x01':  # Control Datagram
            self.handle_control_message(datagram, address)
        elif datagram.type == b'\x02':  # Chat Datagram
            #! TODO: Implement chat message handling
            self.handle_chat_message(datagram, address)
        else:
            print(f"Unsupported datagram type from {address}")
            
    def handle_control_message(self, datagram:Datagram, address:tuple):
        operation = datagram.operation
        if operation == b'\x02':  # SYN
            self.handle_syn(datagram, address)
        elif operation == b'\x06':  # SYN+ACK
            self.handle_syn_ack(datagram, address)
        elif operation == b'\x04':  # ACK
            self.handle_ack(datagram, address)
        else:
            print(f"Unsupported control operation from {address}")

    def handle_syn(self, datagram:Datagram, address:tuple):
        print(f"[{self.ip_address}:{self.port}] Received SYN from {address}")
        with self.lock:
            if address in self.active_connections:
                print(f"Connection already exists with {address}, ignoring SYN")
                return

            # Send SYN+ACK
            syn_ack = Datagram(
                type=b'\x01',
                operation=b'\x06',  # SYN+ACK b'\x02' | b'\x04'
                sequence=b'\x00',
                user=b'Daemon'.ljust(32, b'\x00'),
                length=(0).to_bytes(4, 'big'),
                payload=b''
            )
            self.send_datagram(syn_ack, address)
            self.active_connections[address] = "SYN_SENT"
            
    def handle_syn_ack(self, datagram:Datagram, address:tuple):
        print(f"[{self.ip_address}:{self.port}] Received SYN+ACK from {address}")
        with self.lock:
            if address not in self.active_connections:
                print(f"Connection does not exist with {address}, ignoring SYN+ACK")
                return

            if self.active_connections[address] != "SYN_SENT":
                print(f"Connection with {address} is not in SYN_SENT state, ignoring SYN+ACK")
                return

            # Send ACK
            ack = Datagram(
                type=b'\x01',
                operation=b'\x04',
                sequence=b'\x00',
                user=b'Daemon'.ljust(32, b'\x00'),
                length=(0).to_bytes(4, 'big'),
                payload=b''
            )
            self.send_datagram(ack, address)
            self.active_connections[address] = "CONNECTED"
            
    def handle_ack(self, datagram:Datagram, address:tuple):
        print(f"[{self.ip_address}:{self.port}] Received ACK from {address}")
        with self.lock:
            if address not in self.active_connections:
                print(f"Connection does not exist with {address}, ignoring ACK")
                return

            if self.active_connections[address] != "SYN_SENT":
                print(f"Connection with {address} is not in SYN_SENT state, ignoring ACK")
                return

            self.active_connections[address] = "CONNECTED"
            
    def send_datagram(self, datagram, address):
        serialized = datagram.to_bytes()
        self.socket.sendto(serialized, address)

    def initiate_connection(self, target_ip, target_port):
        syn = Datagram(
            type=b'\x01',
            operation=b'\x02',  # SYN
            sequence=b'\x00',
            user=b'Daemon'.ljust(32, b'\x00'),
            length=(0).to_bytes(4, 'big'),
            payload=b''
        )
        self.send_datagram(syn, (target_ip, target_port))
        print(f"SYN sent to {target_ip}:{target_port}")
        with self.lock:
            self.active_connections[(target_ip, target_port)] = "SYN_SENT"
            
    def three_way_handshake_init(self, target_ip, target_port=7777):
        print(f"[{self.ip_address}:{self.port}] Initiating 3-way handshake with {target_ip}:{target_port}")
        
        syn = Datagram(
            type=b'\x01',
            operation=b'\x02',  # SYN
            sequence=b'\x00',
            user=b'Daemon'.ljust(32, b'\x00'),
            length=(0).to_bytes(4, 'big'),
            payload=b''
        )
        self.send_datagram(syn, (target_ip, target_port))
        self.active_connections[(target_ip, target_port)] = "SYN_SENT"
        
        # Wait for SYN+ACK
        try:
            while True:  # Allow handling multiple incoming messages during the timeout
                data, address = self.socket.recvfrom(1024)
                datagram = Datagram.from_bytes(data)
                if datagram.operation == b'\x06' and address == (target_ip, target_port):  # SYN+ACK
                    print(f"[{self.ip_address}:{self.port}] Received SYN+ACK from {address}")
                    ack = Datagram(
                        type=b'\x01',
                        operation=b'\x04',  # ACK
                        sequence=b'\x00',
                        user=b'Daemon'.ljust(32, b'\x00'),
                        length=(0).to_bytes(4, 'big'),
                        payload=b''
                    )
                    self.send_datagram(ack, address)
                    self.active_connections[address] = "CONNECTED"
                    print(f"[{self.ip_address}:{self.port}] Handshake successful with {address}")
                    return True
        except socket.timeout:
            print(f"[{self.ip_address}:{self.port}] Handshake failed: Timeout waiting for SYN+ACK")
            return False

    
    def three_way_handshake_receive(self, datagram:Datagram, address:tuple):
        print(f"[{self.ip_address}:{self.port}] Received SYN from {address}")
        with self.lock:
            if address in self.active_connections:
                print(f"[{self.ip_address}:{self.port}] Connection already exists with {address}, ignoring SYN")
                return

            # Step 1: Respond with SYN+ACK
            syn_ack = Datagram(
                type=b'\x01',
                operation=b'\x06',  # SYN+ACK
                sequence=b'\x00',
                user=b'Daemon'.ljust(32, b'\x00'),
                length=(0).to_bytes(4, 'big'),
                payload=b''
            )
            self.send_datagram(syn_ack, address)
            self.active_connections[address] = "SYN_RECEIVED"

        # Step 2: Wait for ACK
        try:
            while True:  # Allow handling multiple incoming messages during the timeout
                data, sender_address = self.socket.recvfrom(1024)
                if sender_address != address:
                    continue  # Ignore messages from other addresses

                ack_datagram = Datagram.from_bytes(data)
                if ack_datagram.operation == b'\x04':  # ACK
                    print(f"[{self.ip_address}:{self.port}] Received ACK from {address}")
                    with self.lock:
                        self.active_connections[address] = "CONNECTED"
                        print(f"[{self.ip_address}:{self.port}] Handshake successful with {address}")
                        return True
        except socket.timeout:
            print(f"[{self.ip_address}:{self.port}] Handshake failed: Timeout waiting for ACK")
        return False
