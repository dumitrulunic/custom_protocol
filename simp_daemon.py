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
        self.active_daemon_connection = {} # KEY-(ip and port), VALUE-state(connected/disconnected)
        self.active_client_connection = {} # KEY-(ip and port), VALUE-state(connected/disconnected) or empty dict
        self.active_chat = {} # # KEY-(ip and port), VALUE-state(started/in_progress/ended/ or empty dict
        self.expected_sequence = 0
        
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
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Daemon shutting down via KeyboardInterrupt.")
            self.stop()

        
    def stop(self):
        """Stop the daemon and release resources."""
        self.running = False  # Stop the main loop
        try:
            if self.socket_daemon:
                self.socket_daemon.close()  # Close the UDP socket
                self.logger.info("Daemon UDP socket closed.")
        except Exception as e:
            self.logger.error(f"Error closing UDP socket: {e}")

        try:
            if self.socket_client:
                self.socket_client.close()  # Close the TCP socket
                self.logger.info("Daemon TCP socket closed.")
        except Exception as e:
            self.logger.error(f"Error closing TCP socket: {e}")

        
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
                self.socket_client.listen(1) # Listen for one connection only
                
                while self.running:
                    try:
                        conn, address = self.socket_client.accept()
                        self.logger.info(f"Received packet from client {address}")
                        self.handle_incoming_command_from_client(conn, address)
                    except socket.timeout:
                        continue
                    
            except Exception as e:
                self.logger.error(f"Client packet listener encountered an error: {e}")
            finally:
                if self.socket_client:
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
            elif datagram_type == 2: #chat datagram
                self.handle_chat_datagram(datagram, address)
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

            
    # def relay_message_to_other_daemon(self, message: str):
    #     if not self.active_chat:
    #         self.logger.error("No active chat session.")
    #         return
#
        # target_ip, target_port = self.active_chat["target_ip"], self.active_chat["target_port"]
        # datagram = Datagram(
        #     datagram_type=2,
        #     operation=1,  # Chat message operation
        #     sequence=self.expected_sequence,
        #     user=self.active_client_connection["username"],
        #     length=len(message),
        #     payload=message.encode("utf-8"),
        # )
        # self.send_datagram_to_daemon(datagram, target_ip, target_port)
        # self.logger.info(f"Relayed message to {target_ip}:{target_port}")

            
            

    def mark_connection_as_active(self, address: tuple, sequence: int):
        with self.lock:
            self.active_daemon_connection[address] = {
                "state": "connected",
                "sequence": sequence
            }
            self.logger.info(f"Connection with {address} established.")
    
    def mark_connection_as_inactive(self, address: tuple):
        with self.lock:
            del self.active_daemon_connection[address]
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
        
        if (target_ip, target_port) in self.active_daemon_connection:
            self.logger.warning(f"Handshake already completed with {target_ip}:{target_port}.")
            return
        
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
                if (target_ip, target_port) in self.active_daemon_connection:
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
    
    def send_chat_datagram(self, message: str, target_ip: str, target_port: int):
        try:
            chat_datagram = Datagram(
                datagram_type=2,
                operation=1,
                sequence=self.expected_sequence,
                user=self.active_client_connection["username"].encode("utf-8"),
                length=len(message),
                payload=message.encode("utf-8")
            )
            self.send_datagram_to_daemon(chat_datagram, target_ip, target_port)
        except Exception as e:
            self.logger.error(f"Failed to send chat datagram: {e}")
    
            
###########################CLIENT

    def handle_incoming_command_from_client(self, client_conn, client_addr):
        try:
            self.logger.info(f"Started handling commands from client {client_addr}.")
            
            while True:
                try:
                    data = client_conn.recv(1024).decode("utf-8")
                    if not data:
                        self.logger.info(f"Client {client_addr} closed the connection.")
                        break

                    self.logger.debug(f"Received data from client {client_addr}: {data}")
                    message_code, *args = data.split()
                    message_code = int(message_code)

                    if message_code == 1: # username
                        username = args[0]
                        self.handle_client_username(username, client_conn)
                        self.logger.info(f"Received username '{username}' from {client_addr}")
                        self.logger.info(f"Client connection dictionary: {self.active_client_connection}")

                    elif message_code == 0:  # quit
                        self.logger.info(f"Received quit command from {client_addr}")
                        self.disconnect_client(client_conn)
                        break 
                    
                    else:
                        self.logger.warning(f"Unknown message code {message_code} from client {client_addr}.")
                
                except Exception as e:
                    self.logger.error(f"Error processing command from {client_addr}: {e}")
                    break 
        except Exception as e:
            self.logger.error(f"Error handling commands from client {client_addr}: {e}")
        finally:
            self.logger.info(f"Finished handling commands from client {client_addr}.")
            

    
    def send_ack_to_client(self, client_conn):
        try:
            client_conn.sendall(f"SUCCESS".encode("utf-8"))
            self.logger.info("Sent ACK to client.")
        except Exception as e:
            self.logger.error(f"Failed to send ACK to client: {e}")
            

    def handle_client_username(self, username: str, client_conn):
        """Handle the client's username."""
        self.active_client_connection["username"] = username
        self.active_client_connection["address"] = (self.ip_address, 7778)
        self.logger.info(f"Client username set to '{username}'.")
        self.send_ack_to_client(client_conn)
        
    def disconnect_client(self, client_conn):
        try:
            self.logger.info(f"Disconnecting client. Current state before disconnection: {self.active_client_connection}")
            with self.lock:
                self.active_client_connection.clear()
                self.logger.info(f"Client state after disconnection: {self.active_client_connection}")
            client_conn.close()
            self.logger.info("Client connection closed successfully.")
        except Exception as e:
            self.logger.error(f"Error disconnecting client: {e}")

