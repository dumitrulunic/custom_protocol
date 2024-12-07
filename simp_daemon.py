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
        self.active_connections = {} # KEY-(ip and port), VALUE-state(connected/disconnected)
        
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
                    data, address = self.socket_daemon.recvfrom(1024)
                    self.logger.info(f"Received packet from daemon {address}")
                    self.handle_incoming_datagram_from_daemon(data, address)
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
                    conn, address = self.socket_client.accept()
                    self.logger.info(f"Received packet from client {address}")
                    self.handle_incoming_packet_from_client(conn, address)
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
            datagram_type = datagram.datagram_type[0]
            logger.info(f"Type of received datagam: {type}")
            
            if datagram_type == 1: #control datagram
                self.handle_control_datagram(datagram, address)
            # elif type == 0x02: # chat datagram #! TODO
                # self.handle_chat_datagram(datagram)
            else:
                self.logger.error(f"Invalid type of datagram: {datagram_type}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle incoming datagram from daemon {address}: {e}")
            
    def handle_control_datagram(self, datagram: Datagram, address: tuple):
        try:
            operation = datagram.operation[0]
            sequence = datagram.sequence[0]
            operation = datagram.operation[0]
            self.logger.info(f"Operation of received control datagram: {operation}")
            if operation == 1:  # ERR
                self.logger.error(f"Error received from {address}: {datagram.payload.decode('ascii')}")
            elif operation == 2:  # SYN
                self.logger.info(f"Received SYN from {address}, starting handshake.")
                self.handshake(address[0], address[1], is_initiator=False, incoming_datagram=datagram)
            elif operation == 4:  # ACK
                self.logger.info(f"Received ACK from {address}")
                self.mark_connection_as_active(address, sequence)
            elif operation == 8:  # FIN
                self.logger.info(f"Received FIN from {address}")
                self.send_control_datagram(4, sequence, address[0], address[1])
                self.mark_connection_as_inactive(address)
                
            elif operation == 6:  # SYN + ACK
                self.logger.info(f"Received SYN + ACK from {address}")
                self.handshake(address[0], address[1], is_initiator=True, incoming_datagram=datagram, phase=3)
            else:
                self.logger.error(f"Invalid operation of control datagram: {operation}")
        except Exception as e:
            self.logger.error(f"Failed to handle control datagram: {e}")
            



    def mark_connection_as_active(self, address: tuple, sequence: int):
        with self.lock:
            self.active_connections[address] = {
                "state": "connected",
                "sequence": sequence
            }
            self.logger.info(f"Connection with {address} established.")
    
    def mark_connection_as_inactive(self, address: tuple):
        with self.lock:
            del self.active_connections[address]
            self.logger.info(f"Connection with {address} terminated.")
            
    def send_control_datagram(self, operation: int, sequence: int, target_ip: str, target_port: int, payload: str = ""):
        try:
            control_datagram = Datagram(
                datagram_type=1,
                operation=operation,
                sequence=sequence,
                user="Daemon",
                length=len(payload),
                payload=payload
            )
            self.send_datagram_to_daemon(control_datagram, target_ip, target_port)
        except Exception as e:
            self.logger.error(f"Failed to send control datagram: {e}")
            
    
    def handshake(self, target_ip: str, target_port: int, is_initiator: bool, incoming_datagram=None, phase=1):
        sequence = 0
        
        if is_initiator:
            if phase == 1:  # Send SYN
                    self.logger.info(f"Initiating handshake with {target_ip}:{target_port}. Sending SYN.")
                    self.send_control_datagram(2, sequence, target_ip, target_port)
                    if self.wait_for_syn_ack(sequence, target_ip, target_port):
                        self.logger.info(f"Received SYN+ACK from {target_ip}:{target_port}. Sending ACK.")
                        self.send_control_datagram(4, sequence, target_ip, target_port)  # Send ACK
                        self.mark_connection_as_active((target_ip, target_port), sequence)
            elif phase == 3:  # Send ACK (Final phase)
                self.send_control_datagram(4, incoming_datagram.sequence[0], target_ip, target_port)
                self.mark_connection_as_active((target_ip, target_port), incoming_datagram.sequence[0])
        
        else:
                # Respond to SYN with SYN+ACK
                self.logger.info(f"Responding to SYN from {target_ip}:{target_port}. Sending SYN+ACK.")
                self.send_control_datagram(6, incoming_datagram.sequence[0], target_ip, target_port)
                # if connection exists, reject additional SYN
                if (target_ip, target_port) in self.active_connections:
                    self.logger.info(f"Connection exists. Sending ERR + FIN to {target_ip}:{target_port}")
                    self.send_control_datagram(1, 0, target_ip, target_port, payload="User already in another chat")
                    self.send_control_datagram(8, 0, target_ip, target_port)
                    
    def wait_for_syn_ack(self, sequence: int, target_ip: str, target_port: int, timeout: int = 5):
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                data, address = self.socket_daemon.recvfrom(1024)
                if address == (target_ip, target_port):
                    datagram = Datagram.from_bytes(data)
                    if datagram.operation[0] == 6 and datagram.sequence[0] == sequence:  # SYN+ACK
                        self.logger.info(f"Received SYN+ACK from {address}")
                        return True
            except socket.timeout:
                continue
        self.logger.warning(f"Timed out waiting for SYN+ACK from {target_ip}:{target_port}")
        return False
            
            
            
            
            
            
    # def handle_syn(self, datagram: Datagram, address: tuple):
    #     try:
    #         with self.lock:
    #             if address in self.active_connections:
    #                 self.logger.error(f"Connection already exists with {address}")
    #                 # send error datagram because connection already exists
    #                 payload= "Connection already exists"
    #                 error_datagram = Datagram(
    #                     datagram_type=1,
    #                     operation=1,  # ERR
    #                     sequence=datagram.sequence,
    #                     user="Daemon",
    #                     length=len(payload),
    #                     payload=payload)
    #                 self.send_datagram_to_daemon(error_datagram, address[0])

    #                 # send FIN datagram to close connection
    #                 payload = b"Connection already exists"
    #                 fin_datagram = Datagram(
    #                     datagram_type=1,
    #                     operation=8,  # FIN
    #                     sequence=datagram.sequence,
    #                     user="Daemon",
    #                     length=len(payload),
    #                     payload=payload)
                    
    #                 self.send_datagram_to_daemon(fin_datagram, address[0])
    #             else:
    #                 # send SYN + ACK datagram
    #                 self.logger.info(f"Accepting SYN from {address}.")
    #                 syn_ack_datagram = Datagram(
    #                 datagram_type=1,
    #                 operation=6,  # SYN + ACK, logical OR
    #                 sequence=datagram.sequence,
    #                 user="Daemon",
    #                 length=0,
    #                 payload="")
    #                 self.send_datagram_to_daemon(syn_ack_datagram, address[0])
                        
    #     except Exception as e:
    #         self.logger.error(f"Failed to handle SYN: {e}")
    
    # def handle_ack(self, datagram: Datagram, address: tuple):
    #     try:
    #         with self.lock:
    #             if address not in self.active_connections:
    #                 self.active_connections[address] = {
    #                 "state": "connected",
    #                 "sequence": 0
    #             }
    #             else:
    #                 self.logger.info(f"ACK received from {address}, updating stop-and-wait state.")
    #                 self.active_connections[address]["sequence"] = 1 - self.active_connections[address]["sequence"]
    #                 #! TODO update stop and wait
    #     except Exception as e:
    #         self.logger.error(f"Failed to handle ACK: {e}")
    
    # def handle_fin(self, datagram: Datagram, address: tuple):
    #     try:
    #         with self.lock:
    #             if address in self.active_connections:
    #                 self.logger.info(f"FIN received from {address}, terminating connection.")
    #                 # Send ACK to confirm
    #                 ack_datagram = Datagram(
    #                     datagram_type=1,
    #                     operation=4,
    #                     sequence=datagram.sequence,
    #                     user="Daemon",
    #                     length=0,
    #                     payload=""
    #                 )
    #                 self.send_datagram_to_daemon(ack_datagram, address[0], address[1])

    #                 # Remove the connection
    #                 del self.active_connections[address]
    #             else:
    #                 self.logger.warning(f"FIN received from unknown address {address}, ignoring.")
    #     except Exception as e:
    #         self.logger.error(f"Failed to handle FIN: {e}")
            
    # def handle_err(self, datagram: Datagram, address: tuple):
    #     try:
    #         self.logger.error(f"Error received from {address}: {datagram.payload.decode('ascii')}")
    #     except Exception as e:
    #         self.logger.error(f"Failed to handle ERR: {e}")
    
    # def handshake_init(self, target_ip: str, target_port: int, is_initiator: bool = True, incoming_datagram=None):
    #     try:
    #         sequence = 0

    #         if is_initiator:
    #             # Step 1: Send SYN
    #             self.logger.info(f"Initiating handshake with {target_ip}:{target_port}. Sending SYN.")
    #             syn_datagram = Datagram(
    #                 datagram_type=1,
    #                 operation=2,
    #                 sequence=sequence,
    #                 user="Daemon",
    #                 length=0,
    #                 payload=""
    #             )
    #             self.send_datagram_to_daemon(syn_datagram, target_ip, target_port)

    #             # Wait for SYN+ACK
    #             for _ in range(3):  # 3 tryes
    #                 if self.wait_for_syn_ack(sequence, target_ip, target_port):
    #                     self.logger.info(f"Handshake successful with {target_ip}:{target_port}")
    #                     break
    #                 self.logger.info(f"Retrying SYN to {target_ip}:{target_port}")
    #                 self.send_datagram_to_daemon(syn_datagram, target_ip, target_port)
    #             else:
    #                 self.logger.error(f"Failed to complete handshake with {target_ip}:{target_port}")
    #                 return False

    #             # Step 3: Send ACK
    #             ack_datagram = Datagram(
    #                 datagram_type=1,
    #                 operation=4,
    #                 sequence=sequence,
    #                 user="Daemon",
    #                 length=0,
    #                 payload=""
    #             )
    #             self.send_datagram_to_daemon(ack_datagram, target_ip, target_port)

    #         else:
    #             # Responding to an incoming SYN
    #             self.logger.info(f"Responding to SYN from {target_ip}:{target_port}. Sending SYN+ACK.")
    #             syn_ack_datagram = Datagram(
    #                 datagram_type=1,
    #                 operation=6,
    #                 sequence=incoming_datagram.sequence,
    #                 user="Daemon",
    #                 length=0,
    #                 payload=""
    #             )
    #             self.send_datagram_to_daemon(syn_ack_datagram, target_ip, target_port)

    #             # Wait for ACK
    #             for _ in range(3):  # 3 times
    #                 if self.wait_for_ack(incoming_datagram.sequence, target_ip, target_port):
    #                     self.logger.info(f"Handshake successful with {target_ip}:{target_port}")
    #                     break
    #             else:
    #                 self.logger.error(f"Handshake failed with {target_ip}:{target_port}")
    #                 return False

    #         # Mark connection as active
    #         with self.lock:
    #             self.active_connections[(target_ip, target_port)] = {
    #                 "state": "connected",
    #                 "sequence": sequence
    #             }
    #         return True
    #     except Exception as e:
    #         self.logger.error(f"Handshake error with {target_ip}:{target_port}: {e}")
    #         return False
        
    
        
    # def wait_for_ack(self, sequence: int, target_ip: str, target_port: int, timeout=5):
    #     start_time = time.time()
    #     while time.time() - start_time < timeout:
    #         try:
    #             data, addr = self.socket_daemon.recvfrom(1024)
    #             if addr == (target_ip, target_port):
    #                 datagram = Datagram.from_bytes(data)
    #                 if datagram.datagram_type[0] == 0x01 and datagram.operation[0] == 0x04 and datagram.sequence == sequence:
    #                     return True
    #         except socket.timeout:
    #             continue
    #     return False

##################################### CLIENT FUNCTIONS                                                                              

    def connect_and_listen_client(self):
        try:
            self.client_tcp_socket.bind((self.daemon_ip, self.client_port))
            self.client_tcp_socket.listen(1)
            print(f"Listening for clients on {self.daemon_ip}:{self.client_port}")
            while self.process:
                try:
                    client_conn, client_addr = self.client_tcp_socket.accept()
                    print(f"Client connected: {client_addr}")
                    self.handle_client(client_conn, client_addr)
                except Exception as e:
                    if self.process:
                        print(f"Error accepting client connection: {e}")
        except Exception as e:
            print(f"Error in client listener: {e}")
        finally:
            self.client_tcp_socket.close()
            print(f"Stopped listening for clients on {self.daemon_ip}:{self.client_port}.")


    def handle_client(self, client_conn, client_addr):
        """Handle communication with a connected client."""
        try:
            while self.process:
                message = client_conn.recv(1024).decode("utf-8")
                if not message:
                    print(f"No message received from client {client_addr}.")
                    continue  # Continue the loop to keep the connection open
                print(f"Message from client {client_addr}: {message}")
                message_code, *args = message.split()
                message_code = int(message_code)
        #         if message_code == 10:  # "quit"
        #             print(f"Client {client_addr} disconnected.")
        #             break
        #         elif message_code == 1:  # "connect"
        #             username = args[0]
        #             print(f"Client {client_addr} connected with username: {username}")
        #         elif message_code == 2:  # "check_pending"
        #             if self.pending_chat_request:
        #                 client_conn.sendall(f"4 {self.pending_chat_request}".encode("utf-8"))  # "chat_request_pending"
        #             else:
        #                 client_conn.sendall("9".encode("utf-8"))  # "no_pending_chat_request"
        #         elif message_code == 3:  # "chat_request"
        #             self.pending_chat_request = args[0]
        #             client_conn.sendall(f"4 {self.pending_chat_request}".encode("utf-8"))  # "chat_request_pending"
        #         elif message_code == 5:  # "chat_accept"
        #             if self.pending_chat_request:
        #                 self.active_chat = self.pending_chat_request
        #                 client_conn.sendall(f"7 {self.active_chat}".encode("utf-8"))  # "chat_started"
        #                 self.pending_chat_request = None
        #             else:
        #                 client_conn.sendall("9".encode("utf-8"))  # "no_pending_chat_request"
        #         elif message_code == 6:  # "chat_reject"
        #             if self.pending_chat_request:
        #                 client_conn.sendall(f"8 {self.pending_chat_request}".encode("utf-8"))  # "chat_request_rejected"
        #                 self.pending_chat_request = None
        #             else:
        #                 client_conn.sendall("9".encode("utf-8"))  # "no_pending_chat_request"
        #         else:
        #             print(f"Unknown message from client {client_addr}: {message}")
        except Exception as e:
            print(f"Error with client {client_addr}: {e}")
        finally:
            client_conn.close()
            print(f"Connection with client {client_addr} closed.")

    # WITHOUT THIS FUNCTION THE CLIENT WILL NOT BE ABLE TO SEND MESSAGES TO THE DAEMON
    def handle_incoming_packet_from_client(self, client_conn, client_addr):
        try:
            while True:
                data = client_conn.recv(1024)
                if not data:
                    break
                message = data.decode("utf-8")
                print(f"Received message from client {client_addr}: {message}")
                # Handle the received message (e.g., store the client's name)
        except Exception as e:
            print(f"Error with client {client_addr}: {e}")
        finally:
            client_conn.close()
            print(f"Connection with client {client_addr} closed.")

