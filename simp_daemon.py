import socket
from Datagram import Datagram
from typing import List, Tuple
import threading
import time

class Daemon:
    MESSAGE_CODES = {
        1: "connect",
        2: "check_pending",
        3: "chat_request",
        4: "chat_request_pending",
        5: "chat_accept",
        6: "chat_reject",
        7: "chat_started",
        8: "chat_request_rejected",
        9: "no_pending_chat_request",
        10: "quit"
    }

    def __init__(self, daemon_ip: str, daemon_port: int = 7777, client_port: int = 7778):
        self.daemon_ip = daemon_ip
        self.daemon_port = daemon_port
        self.daemon_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.daemon_udp_socket.settimeout(5)
        self.connected_to_client = False
        self.client_tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected_to_daemon = False
        self.client_port = client_port
        self.active_chat = None
        self.pending_chat_request = None
        self.process = True  # This is a flag to stop the daemon
        self.shutdown = False
        self.timeout = 5
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

    
    ###################HANDLING CLIENTS#########################
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
                if message_code == 10:  # "quit"
                    print(f"Client {client_addr} disconnected.")
                    break
                elif message_code == 1:  # "connect"
                    username = args[0]
                    print(f"Client {client_addr} connected with username: {username}")
                elif message_code == 2:  # "check_pending"
                    if self.pending_chat_request:
                        client_conn.sendall(f"4 {self.pending_chat_request}".encode("utf-8"))  # "chat_request_pending"
                    else:
                        client_conn.sendall("9".encode("utf-8"))  # "no_pending_chat_request"
                elif message_code == 3:  # "chat_request"
                    self.pending_chat_request = args[0]
                    client_conn.sendall(f"4 {self.pending_chat_request}".encode("utf-8"))  # "chat_request_pending"
                elif message_code == 5:  # "chat_accept"
                    if self.pending_chat_request:
                        self.active_chat = self.pending_chat_request
                        client_conn.sendall(f"7 {self.active_chat}".encode("utf-8"))  # "chat_started"
                        self.pending_chat_request = None
                    else:
                        client_conn.sendall("9".encode("utf-8"))  # "no_pending_chat_request"
                elif message_code == 6:  # "chat_reject"
                    if self.pending_chat_request:
                        client_conn.sendall(f"8 {self.pending_chat_request}".encode("utf-8"))  # "chat_request_rejected"
                        self.pending_chat_request = None
                    else:
                        client_conn.sendall("9".encode("utf-8"))  # "no_pending_chat_request"
                else:
                    print(f"Unknown message from client {client_addr}: {message}")
        except Exception as e:
            print(f"Error with client {client_addr}: {e}")
        finally:
            client_conn.close()
            print(f"Connection with client {client_addr} closed.")

    def connect_and_listen_daemon(self):
        try:
            self.daemon_udp_socket.bind((self.daemon_ip, self.daemon_port))
            print(f"Listening for daemons on {self.daemon_ip}:{self.daemon_port}")
            while self.process:
                try:
                    data, addr = self.daemon_udp_socket.recvfrom(1024)
                    deserialized_datagram = Datagram.from_bytes(data)
                    print(f"Message received from daemon {addr}: {deserialized_datagram}")

                    # Handle SYN and respond with ACK
                    if deserialized_datagram.operation == 0x02:  # SYN
                        print(f"Received SYN from {addr}. Sending ACK...")
                        ack_datagram = Datagram(
                            type=0x01,
                            operation=0x04,
                            sequence=deserialized_datagram.sequence + 1,
                            user="daemon2",
                            payload="",
                            length=0
                        )
                        self.send_datagram(self.daemon_udp_socket, ack_datagram, addr)
                        print(f"Sent ACK to {addr}: {ack_datagram}")

                except socket.timeout:
                    print("Timeout waiting for datagram.")
                except Exception as e:
                    print(f"Error receiving datagram: {e}")
        except Exception as e:
            print(f"Error in daemon listener: {e}")
        finally:
            self.daemon_udp_socket.close()
            print("Stopped listening for daemons.")
    def start(self):
        self.client_thread = threading.Thread(target=self.connect_and_listen_client, daemon=False)
        self.daemon_thread = threading.Thread(target=self.connect_and_listen_daemon, daemon=False)

        self.client_thread.start()
        self.daemon_thread.start()

        print("Daemon is running...")
        try:
            while self.process:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nDaemon shutting down...")
        finally:
            self.end()

    def end(self):
        if self.shutdown:
            print(f"Daemon at {self.daemon_ip}:{self.daemon_port} already shut down.")
            return

        self.shutdown = True
        self.process = False

        try:
            self.daemon_udp_socket.close()
            self.client_tcp_socket.close()
            print(f"Sockets closed for {self.daemon_ip}:{self.daemon_port}.")
        except Exception as e:
            print(f"Error closing sockets: {e}")

        try:
            if hasattr(self, "client_thread"):
                self.client_thread.join(timeout=2)
            if hasattr(self, "daemon_thread"):
                self.daemon_thread.join(timeout=2)
            print(f"Threads joined for {self.daemon_ip}:{self.daemon_port}.")
        except Exception as e:
            print(f"Error joining threads: {e}")
        print(f"Daemon at {self.daemon_ip}:{self.daemon_port} stopped.")
        
        
####################HANDLING DAEMONS######################
    # daemon -> daemon
    def three_way_handshake_init(self, other_daemon_address: Tuple[str, int], retries: int = 3) -> bool:
        for attempt in range(retries):
            try:
                print(f"Attempt {attempt + 1}: Starting 3-way handshake with {other_daemon_address}")
                
                # Send SYN
                syn_datagram = Datagram(type=0x01, operation=0x02, sequence=0, user="daemon1", payload="", length=0)
                self.send_datagram(self.daemon_udp_socket, syn_datagram, other_daemon_address)
                print(f"SYN sent to {other_daemon_address}")
                
                # Wait for SYN+ACK
                response = self.receive_datagram(self.daemon_udp_socket)
                if response is None:
                    print("Timeout waiting for SYN+ACK. Retrying...")
                    continue

                datagram, address = response
                if datagram.operation == (0x02 | 0x04):  # SYN+ACK
                    print(f"Received SYN+ACK from {address}")
                    
                    # Send ACK
                    ack_datagram = Datagram(type=0x01, operation=0x04, sequence=1, user="daemon1", payload="", length=0)
                    self.send_datagram(self.daemon_udp_socket, ack_datagram, other_daemon_address)
                    print(f"ACK sent to {other_daemon_address}")
                    print(f"3-way handshake completed with {other_daemon_address}")
                    return True
                else:
                    print(f"Unexpected response from {address}: {datagram}")
            except Exception as e:
                print(f"Error in 3-way handshake attempt {attempt + 1}: {e}")
        
        print("Failed to complete 3-way handshake after retries.")
        return False

    def three_way_handshake_receive(self) -> bool:
        
        try:
            print("Waiting for SYN...")
            datagram, address = self.receive_datagram(self.daemon_udp_socket)
            if datagram and datagram.operation == 0x02:  # SYN
                print(f"Received SYN from {address}")
                
                # Send SYN+ACK
                ack_syn_operation = 0x02 | 0x04
                syn_ack_datagram = Datagram(type=0x01, operation=ack_syn_operation, sequence=0, user="Daemon2", payload="", length=0)
                self.send_datagram(self.daemon_udp_socket, syn_ack_datagram, address)
                print(f"SYN+ACK sent to {address}")
                
                # Wait for ACK
                ack_response = self.receive_datagram(self.daemon_udp_socket)
                if ack_response is None:
                    print("Timeout waiting for ACK.")
                    return False
                
                ack_datagram, ack_address = ack_response
                if ack_datagram.operation == 0x04:  # ACK
                    print(f"Received ACK from {ack_address}")
                    print(f"3-way handshake completed with {ack_address}")
                    return True
                else:
                    print(f"Unexpected response from {ack_address}: {ack_datagram}")
            else:
                print(f"Unexpected datagram received: {datagram}")
        except Exception as e:
            print(f"Error in 3-way handshake receive: {e}")
        return False

    
    # daemon -> daemon
    def receive_datagram(self, socket: socket.socket) -> Tuple[Datagram, Tuple[str, int]]:
        try:
            data, address = socket.recvfrom(1024)
            datagram_received = Datagram.from_bytes(data)
            print(f"RECEIVED: {datagram_received} from {address}")
            return datagram_received, address
        except socket.timeout:
            print("Datagram receive timed out.")
            return None, None  # Explicitly return a tuple with None values
        except Exception as e:
            print(f"Error receiving datagram: {e}")
            raise  # Raise the error to let the caller decide how to handle it

            
    def send_datagram(self, socket: socket.socket, datagram: Datagram, target_address: Tuple[str, int]):
        try:
            socket.sendto(datagram.to_bytes(), target_address)
            print(f"SENT: {datagram} to {target_address}")
        except Exception as e:
            print(f"Error sending datagram: {e}")
            
    def stop_and_wait(self, datagram: Datagram, receiver_address: Tuple[str, int]) -> bool:
        try:
            for attempt in range(3):  # Retry 3 times if needed
                self.send_datagram(self.daemon_udp_socket, datagram, receiver_address)
                print(f"Datagram sent to {receiver_address}. Waiting for ACK...")

                response, addr = self.receive_datagram(self.daemon_udp_socket)
                if response is None:
                    print(f"Attempt {attempt + 1}: Timeout waiting for ACK. Retrying...")
                    continue

                if response.operation == 0x04:  # ACK
                    print(f"Received ACK from {addr}: {response}")
                    return True  # Successful stop-and-wait

            print("Failed to receive ACK after 3 attempts.")
            return False
        except Exception as e:
            print(f"Error in stop-and-wait: {e}")
            return False
