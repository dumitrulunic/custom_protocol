import socket
import threading
from Datagram import Datagram
from logger import logger

class Daemon:
    def __init__(self, ip:str, port:int = 7777) -> None:
        self.port = port
        self.ip_address = ip
        self.running = True
        
        # Daemon - Daemon connections, by ip and port
        self.active_connections = {}
        
        self.lock = threading.Lock()
        
        self.logger = logger()

    def start(self):
        self.logger.log(f'Daemon started on {self.ip_address}:{self.port}')
        daemon_thread = threading.Thread(target=self.listen_to_daemon_packets, daemon=True)
        daemon_thread.start()

        client_thread = threading.Thread(target=self.listen_to_client_packets, daemon=True)
        client_thread.start()
        
        try:
            while self.running:
                pass
        except KeyboardInterrupt:
            self.logger.log("Daemon shutting down via KeyboardInterrupt.")
            self.stop()

        
    def stop(self):
        self.running = False
        self.socket_daemon.close()
        self.socket_client.close()
        self.logger.log("Daemon stopped.")
        
    def listen_to_daemon_packets(self):
        try:
            self.socket_daemon = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket_daemon.bind((self.ip_address, 7777))
            self.socket_daemon.settimeout(5)

            while self.running:
                try:
                    data, addr = self.socket_daemon.recvfrom(1024)
                    self.logger.log(f"Received packet from daemon {addr}")
                    self.handle_incoming_packet_from_daemon(data, addr)
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
                    self.logger.log(f"Received packet from client {addr}")
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
            self.logger.log(f"Sent datagram to daemon {ip}:{port}")
        except Exception as e:
            self.logger.error(f"Failed to send datagram to daemon {ip}:{port}: {e}")
            
        
    def handle_incoming_datagram_from_daemon(self, data: bytes, address: tuple):
        try:
            datagram = Datagram.from_bytes(data)
            self.logger.log(f"Received datagram from daemon {address}")
            self.logger.log(f"Datagram: {datagram}")
            type = datagram.type[0]
            logger.log(f"Type of received datagam: {type}")
            
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
            self.logger.log(f"Operation of received control datagram: {operation}")
            if operation == 0x01:  # ERR
                self.logger.error(f"Error received from {address}: {datagram.payload.decode('ascii')}")
            elif operation == 0x02:  # SYN
                self.logger.log(f"Received SYN from {address}, starting handshake.")
                self.handle_syn(datagram, address)
            elif operation == 0x04:  # ACK
                self.logger.log(f"Received ACK from {address}")
                self.handle_ack(datagram, address)
            elif operation == 0x08:  # FIN
                self.logger.log(f"Received FIN from {address}")
                self.handle_fin(datagram, address)
            else:
                self.logger.error(f"Invalid operation of control datagram: {operation}")
        except Exception as e:
            self.logger.error(f"Failed to handle control datagram: {e}")
            
    def hanle_syn(self, datagram: Datagram, address: tuple):
        try:
            #! TODO
            pass
        except Exception as e:
            self.logger.error(f"Failed to handle SYN: {e}")
    
    def handle_ack(self, datagram: Datagram, address: tuple):
        try:
            #! TODO
            pass
        except Exception as e:
            self.logger.error(f"Failed to handle ACK: {e}")
    
    def handle_fin(self, datagram: Datagram, address: tuple):
        try:
            #! TODO
            pass
        except Exception as e:
            self.logger.error(f"Failed to handle FIN: {e}")
    
    