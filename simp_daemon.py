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
        self.active_client_connection = False # { address, username }
        self.active_chat = None #{ target_ip, target_port }
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
            
    def handle_chat_datagram(self, datagram: Datagram, address: tuple):
        message = datagram.payload.decode("utf-8")
        self.logger.info(f"Received chat message from {address}: {message}")

        # Relay to the connected client
        if self.active_client_connection:
            client_address = self.active_client_connection["address"]
            try:
                client_socket = socket.create_connection(client_address)
                client_socket.sendall(message.encode("utf-8"))
                client_socket.close()
            except Exception as e:
                self.logger.error(f"Failed to forward message to client: {e}")
            
    def relay_message_to_other_daemon(self, message: str):
        if not self.active_chat:
            self.logger.error("No active chat session.")
            return

        target_ip, target_port = self.active_chat["target_ip"], self.active_chat["target_port"]
        datagram = Datagram(
            datagram_type=2,
            operation=1,  # Chat message operation
            sequence=self.expected_sequence,
            user=self.active_client_connection["username"],
            length=len(message),
            payload=message.encode("utf-8"),
        )
        self.send_datagram_to_daemon(datagram, target_ip, target_port)
        self.logger.info(f"Relayed message to {target_ip}:{target_port}")

            
            

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
            
    def mark_chat_as_active(self, target_ip, target_port):
        self.active_chat = {"target_ip": target_ip, "target_port": target_port}
        self.send_control_datagram(
            operation=9,  # Custom operation for chat session sync
            sequence=self.expected_sequence,
            target_ip=target_ip,
            target_port=target_port,
            payload="Chat session active".encode("utf-8"),
        )

            
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
    

    def handle_incoming_packet_from_client(self, client_conn, client_addr):
        try:
            data = client_conn.recv(1024).decode("utf-8")
            if not data:
                return

            message_code, *args = data.split()
            if int(message_code) == 6:  # Start Chat
                other_client_ip = args[0]
                self.logger.info(f"Client {client_addr} requested chat with {other_client_ip}")
                self.active_chat = {"target_ip": other_client_ip, "target_port": 7777}
                self.handshake(other_client_ip, 7777, is_initiator=True)
                
                # Notify target daemon of the chat session
                self.send_control_datagram(
                    operation=9,  # Synchronization operation
                    sequence=0,
                    target_ip=other_client_ip,
                    target_port=7777,
                    payload=f"chat_with:{self.ip_address}".encode("utf-8"),
                )
                client_conn.sendall("Chat started.".encode("utf-8"))

            elif int(message_code) == 3:  # Send Message
                chat_message = " ".join(args)
                self.relay_message_to_other_daemon(chat_message)
                client_conn.sendall("Message sent.".encode("utf-8"))
        except Exception as e:
            self.logger.error(f"Error handling client packet: {e}")



    def handle_client_message(self, message: str, client_conn, client_addr):
        try:
            if not self.active_client_connection or self.active_client_connection.get("state") != "connected":
                self.logger.warning(f"Client {client_addr} attempted to send a message without connecting.")
                client_conn.sendall("Please connect before sending messages.".encode("utf-8"))
                return

            message_code, *args = message.split()
            message_code = int(message_code)

            if message_code == 3:  # Send message
                chat_message = " ".join(args)
                self.logger.info(f"Message from {client_addr}: {chat_message}")

                # Check if there is an active chat session to relay the message
                if self.active_chat:
                    self.relay_message_to_other_daemon(chat_message)
                else:
                    self.logger.warning(f"No active chat session for client {client_addr}.")
                    client_conn.sendall("No active chat session. Start a chat first.".encode("utf-8"))
                client_conn.sendall(f"Message received: {chat_message}".encode("utf-8"))
            elif message_code == 4:  # receive message
                self.logger.info(f"Client {client_addr} requested to receive messages (not implemented).")
                client_conn.sendall("Feature not implemented yet.".encode("utf-8"))
            elif message_code == 5:  # wait chat
                self.logger.info(f"Client {client_addr} requested to wait for chat.")
                client_conn.sendall("Waiting for a chat request...".encode("utf-8"))
            elif message_code == 6:  # start chat
                self.logger.info(f"Client {client_addr} requested to start a chat.")
                if len(args) != 1:
                    self.logger.error(f"Invalid IP format received from client {client_addr}.")
                    client_conn.sendall("Invalid IP format. Please try again.".encode("utf-8"))
                    return
                client_ip = args[0]
                self.logger.info(f"Client {client_addr} wants to chat with {client_ip}.")
                self.handshake(client_ip, 7777, is_initiator=True)
                client_conn.sendall("Chat started.".encode("utf-8"))
            elif message_code == 7:  # accept chat
                self.logger.info(f"Client {client_addr} accepted a chat.")
                client_conn.sendall("Chat accepted.".encode("utf-8"))
            elif message_code == 8:  # decline chat
                self.logger.info(f"Client {client_addr} declined a chat.")
                client_conn.sendall("Chat declined.".encode("utf-8"))
            elif message_code == 9:  # Chat Synchronization
                self.logger.info(f"Chat synchronized with {client_addr}.")
                if self.active_client_connection:
                    client_conn = self.active_client_connection["connection"]
                    client_conn.sendall("Chat started.".encode("utf-8"))
                    self.active_chat = {"target_ip": client_addr[0], "target_port": client_addr[1]}

            else:
                self.logger.warning(f"Unknown message code {message_code} from client {client_addr}.")
                client_conn.sendall("Unknown message code.".encode("utf-8"))
        except Exception as e:
            self.logger.error(f"Error processing message from client {client_addr}: {e}")
            client_conn.sendall(f"Error processing message: {e}".encode("utf-8"))
        