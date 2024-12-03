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
            
        
    def handle_incoming_packet_from_daemon(self, data, addr):
        pass