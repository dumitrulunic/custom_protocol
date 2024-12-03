import socket
import threading
from Datagram import Datagram
from logger import logger
import time

class Daemon:
    def __init__(self, ip:str, port:int = 7777) -> None:
        self.port = port
        self.ip_address = ip
        self.running = True
        
        self.socket_daemon = None
        self.socket_client = None
        
        # Daemon - Daemon connections, by ip and port
        self.active_connections = {}
        
        self.lock = threading.Lock()
        
        self.logger = logger

    def start(self):
        self.logger.info(f'Daemon started on {self.ip_address}:{self.port}')
        daemon_thread = threading.Thread(target=self.listen_to_daemon_packets, daemon=True)
        daemon_thread.start()

        client_thread = threading.Thread(target=self.listen_to_client_packets, daemon=True)
        client_thread.start()
        
        try:
            while self.running:
                pass
        except KeyboardInterrupt:
            self.logger.info("Daemon shutting down via KeyboardInterrupt.")
            self.stop()

        
    def stop(self):
        self.running = False
        self.socket_daemon.close()
        self.socket_client.close()
        self.logger.info("Daemon stopped.")
        
    def listen_to_daemon_packets(self):
        try:
            self.socket_daemon = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket_daemon.bind((self.ip_address, 7777))
            self.socket_daemon.settimeout(5)

            while self.running:
                try:
                    data, addr = self.socket_daemon.recvfrom(1024)
                    self.logger.info(f"Received packet from daemon {addr}")
                    self.handle_incoming_datagram_from_daemon(data, addr)
                except socket.timeout:
                    continue
        except Exception as e:
            self.logger.error(f"Daemon packet listener encountered an error: {e}")
        finally:
            self.socket_daemon.close()
            
            
    def listen_to_client_packets(self):
        try:
            self.socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_client.bind((self.ip_address, 7778))
            self.socket_client.settimeout(5)
            self.socket_client.listen(5)
            
            while self.running:
                try:
                    conn, addr = self.socket_client.accept()
                    self.logger.info(f"Received packet from client {addr}")
                    self.handle_incoming_packet_from_client(conn, addr)
                except socket.timeout:
                    continue
                
        except Exception as e:
            self.logger.error(f"Client packet listener encountered an error: {e}")
        finally:
            self.socket_client.close()
            
    def send_datagram_to_daemon(self, datagram:Datagram, ip:str, port:int=7777):
        try:
            serialized_datagram = datagram.to_bytes()
            self.socket_daemon.sendto(serialized_datagram, (ip, port))
            self.logger.info(f"Sent datagram to daemon {ip}:{port}")
        except Exception as e:
            self.logger.error(f"Failed to send datagram to daemon {ip}:{port}: {e}")
            
        
    def handle_incoming_datagram_from_daemon(self, data: bytes, address: tuple):
        try:
            datagram = Datagram.from_bytes(data)
            self.logger.info(f"Received datagram from daemon {address}")
            self.logger.info(f"Datagram: {datagram}")
            type = datagram.type[0]
            logger.info(f"Type of received datagam: {type}")
            
            if type == 0x01: #control datagram
                self.handle_control_datagram(datagram)
            # elif type == 0x02: # chat datagram #! TODO
                # self.handle_chat_datagram(datagram)
            else:
                self.logger.error(f"Invalid type of datagram: {type}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle incoming datagram from daemon {addr}: {e}")
            
    def handle_control_datagram(self, datagram: Datagram, address: tuple):
        try:
            operation = datagram.operation[0]
            self.logger.info(f"Operation of received control datagram: {operation}")
            if operation == 0x01:  # ERR
                self.logger.error(f"Error received from {address}: {datagram.payload.decode('ascii')}")
            elif operation == 0x02:  # SYN
                self.logger.info(f"Received SYN from {address}, starting handshake.")
                self.handshake_init(target_ip=address[0], target_port=address[1], is_initiator=False, incoming_datagram=datagram)
            elif operation == 0x04:  # ACK
                self.logger.info(f"Received ACK from {address}")
                self.handle_ack(datagram, address)
            elif operation == 0x08:  # FIN
                self.logger.info(f"Received FIN from {address}")
                self.handle_fin(datagram, address)
            else:
                self.logger.error(f"Invalid operation of control datagram: {operation}")
        except Exception as e:
            self.logger.error(f"Failed to handle control datagram: {e}")
            
    def handle_syn(self, datagram: Datagram, address: tuple):
        try:
            with self.lock:
                if address in self.active_connections:
                    self.logger.error(f"Connection already exists with {address}")
                    # send error datagram because connection already exists
                    error_datagram = Datagram(
                        type_field=b'\x01',
                        operation=b'\x01',  # ERR
                        sequence=datagram.sequence,
                        user="Daemon",
                        payload=b"Connection already exists")
                    self.send_datagram_to_daemon(error_datagram, address[0])

                    # send FIN datagram to close connection
                    fin_datagram = Datagram(b'\x01', b'\x08', 0, b"Connection already exists")
                    self.send_datagram_to_daemon(fin_datagram, address[0])
                else:
                    # send SYN + ACK datagram
                    self.logger.info(f"Accepting SYN from {address}.")
                    syn_ack_datagram = Datagram(
                    type_field=b'\x01',
                    operation=b'\x06',  # SYN + ACK, logical OR
                    sequence=datagram.sequence,
                    user="Daemon",
                    payload=b"")
                    self.send_datagram_to_daemon(syn_ack_datagram, address[0])
                        
        except Exception as e:
            self.logger.error(f"Failed to handle SYN: {e}")
    
    def handle_ack(self, datagram: Datagram, address: tuple):
        try:
            with self.lock:
                if address not in self.active_connections:
                    self.active_connections[address] = {
                    "state": "connected",
                    "sequence": 0
                }
                else:
                    self.logger.info(f"ACK received from {address}, updating stop-and-wait state.")
                    self.active_connections[address]["sequence"] = 1 - self.active_connections[address]["sequence"]
                    #! TODO update stop and wait
        except Exception as e:
            self.logger.error(f"Failed to handle ACK: {e}")
    
    def handle_fin(self, datagram: Datagram, address: tuple):
        try:
            with self.lock:
                if address in self.active_connections:
                    self.logger.info(f"FIN received from {address}, terminating connection.")
                    # Send ACK to confirm
                    ack_datagram = Datagram(
                        type_field=b'\x01',
                        operation=b'\x04',
                        sequence=datagram.sequence,
                        user="Daemon",
                        payload=b""
                    )
                    self.send_datagram_to_daemon(ack_datagram, address[0], address[1])

                    # Remove the connection
                    del self.active_connections[address]
                else:
                    self.logger.warning(f"FIN received from unknown address {address}, ignoring.")
        except Exception as e:
            self.logger.error(f"Failed to handle FIN: {e}")
            
    def handle_err(self, datagram: Datagram, address: tuple):
        try:
            self.logger.error(f"Error received from {address}: {datagram.payload.decode('ascii')}")
        except Exception as e:
            self.logger.error(f"Failed to handle ERR: {e}")
    
    def handshake_init(self, target_ip: str, target_port: int, is_initiator: bool = True, incoming_datagram=None):
        try:
            sequence = 0

            if is_initiator:
                # Step 1: Send SYN
                self.logger.info(f"Initiating handshake with {target_ip}:{target_port}. Sending SYN.")
                syn_datagram = Datagram(
                    type_field=b'\x01',
                    operation=b'\x02',
                    sequence=sequence,
                    user="Daemon",
                    payload=b""
                )
                self.send_datagram_to_daemon(syn_datagram, target_ip, target_port)

                # Wait for SYN+ACK
                for _ in range(3):  # 3 tryes
                    if self.wait_for_syn_ack(sequence, target_ip, target_port):
                        self.logger.info(f"Handshake successful with {target_ip}:{target_port}")
                        break
                    self.logger.info(f"Retrying SYN to {target_ip}:{target_port}")
                    self.send_datagram_to_daemon(syn_datagram, target_ip, target_port)
                else:
                    self.logger.error(f"Failed to complete handshake with {target_ip}:{target_port}")
                    return False

                # Step 3: Send ACK
                ack_datagram = Datagram(
                    type_field=b'\x01',
                    operation=b'\x04',
                    sequence=sequence,
                    user="Daemon",
                    payload=b""
                )
                self.send_datagram_to_daemon(ack_datagram, target_ip, target_port)

            else:
                # Responding to an incoming SYN
                self.logger.info(f"Responding to SYN from {target_ip}:{target_port}. Sending SYN+ACK.")
                syn_ack_datagram = Datagram(
                    type_field=b'\x01',
                    operation=b'\x06',
                    sequence=incoming_datagram.sequence,
                    user="Daemon",
                    payload=b""
                )
                self.send_datagram_to_daemon(syn_ack_datagram, target_ip, target_port)

                # Wait for ACK
                for _ in range(3):  # 3 times
                    if self.wait_for_ack(incoming_datagram.sequence, target_ip, target_port):
                        self.logger.info(f"Handshake successful with {target_ip}:{target_port}")
                        break
                else:
                    self.logger.error(f"Handshake failed with {target_ip}:{target_port}")
                    return False

            # Mark connection as active
            with self.lock:
                self.active_connections[(target_ip, target_port)] = {
                    "state": "connected",
                    "sequence": sequence
                }
            return True
        except Exception as e:
            self.logger.error(f"Handshake error with {target_ip}:{target_port}: {e}")
            return False

        
    def wait_for_ack(self, sequence: int, target_ip: str, target_port: int, timeout=5):
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                data, addr = self.socket_daemon.recvfrom(1024)
                if addr == (target_ip, target_port):
                    datagram = Datagram.from_bytes(data)
                    if datagram.type[0] == 0x01 and datagram.operation[0] == 0x04 and datagram.sequence == sequence:
                        return True
            except socket.timeout:
                continue
        return False

