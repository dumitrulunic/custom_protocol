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
            
    def handle_chat_request_from_client(self, client_conn, client_addr, target_ip, target_port):
        try:
            print(f"Client requested chat with daemon at {target_ip}:{target_port}...")

            # Create chat request datagram
            chat_request_datagram = Datagram(
                type=0x01,
                operation=0x03,  # Chat request
                sequence=0,
                user=self.daemon_ip,
                payload=f"{self.daemon_ip}:{self.daemon_port}",
                length=len(f"{self.daemon_ip}:{self.daemon_port}")
            )
            self.daemon_udp_socket.sendto(chat_request_datagram.to_bytes(), (target_ip, target_port))
            print(f"Chat request sent to daemon at {target_ip}:{target_port}.")

            # Wait for a response
            response, addr = self.daemon_udp_socket.recvfrom(1024)
            response_datagram = Datagram.from_bytes(response)

            if response_datagram.operation == 0x07:  # Chat accepted
                print(f"Chat accepted by daemon at {addr}. Notifying client.")
                client_conn.sendall("7".encode("utf-8"))  # Notify client
            elif response_datagram.operation == 0x08:  # Chat rejected
                print(f"Chat rejected by daemon at {addr}. Notifying client.")
                client_conn.sendall("8".encode("utf-8"))  # Notify client
            else:
                print(f"Unexpected response from target daemon: {response_datagram}")
                client_conn.sendall("9".encode("utf-8"))  # No response
        except socket.timeout:
            print("Timeout waiting for target daemon response.")
            client_conn.sendall("9".encode("utf-8"))  # Notify client of timeout
        except Exception as e:
            print(f"Error handling chat request: {e}")
            client_conn.sendall("9".encode("utf-8"))  # Notify client of error


            
    def handle_chat_request_from_daemon(self, datagram: Datagram, source_addr: Tuple[str, int]):
        try:
            print(f"Received chat request from daemon at {source_addr}. Forwarding to client.")

            if not self.connected_to_client:
                print("No connected client to handle the chat request.")
                response_datagram = Datagram(
                    type=0x01,
                    operation=0x08,  # Chat rejected
                    sequence=datagram.sequence + 1,
                    user="chat-reject",
                    payload="No client available",
                    length=len("No client available")
                )
                self.daemon_udp_socket.sendto(response_datagram.to_bytes(), source_addr)
                return

            # Notify client
            self.client_conn.sendall(f"4 {datagram.payload}".encode("utf-8"))

            # Await client's response
            client_response = self.client_conn.recv(1024).decode("utf-8").strip()
            if client_response == "5":  # Chat accepted
                response_datagram = Datagram(
                    type=0x01,
                    operation=0x07,  # Chat accepted
                    sequence=datagram.sequence + 1,
                    user="chat-accept",
                    payload="Chat accepted",
                    length=len("Chat accepted")
                )
                self.daemon_udp_socket.sendto(response_datagram.to_bytes(), source_addr)
                print("Client accepted chat request.")
            elif client_response == "6":  # Chat rejected
                response_datagram = Datagram(
                    type=0x01,
                    operation=0x08,  # Chat rejected
                    sequence=datagram.sequence + 1,
                    user="chat-reject",
                    payload="Chat rejected",
                    length=len("Chat rejected")
                )
                self.daemon_udp_socket.sendto(response_datagram.to_bytes(), source_addr)
                print("Client rejected chat request.")
        except Exception as e:
            print(f"Error processing chat request: {e}")





    def connect_and_listen_daemon(self):
        try:
            self.daemon_udp_socket.bind((self.daemon_ip, self.daemon_port))
            print(f"Listening for daemons on {self.daemon_ip}:{self.daemon_port}")
            while self.process:
                try:
                    data, addr = self.daemon_udp_socket.recvfrom(1024)
                    deserialized_datagram = Datagram.from_bytes(data)
                    print(f"Message received from daemon {addr}: {deserialized_datagram}")

                    if deserialized_datagram.operation == 0x03:  # Chat request
                        self.handle_chat_request_from_daemon(deserialized_datagram, addr)
                    else:
                        print(f"Unknown operation received: {deserialized_datagram.operation}")
                except socket.timeout:
                    continue
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

        # Mark shutdown state
        self.shutdown = True
        self.process = False
        print(f"Initiating shutdown for daemon at {self.daemon_ip}:{self.daemon_port}...")

        # Join threads before closing sockets
        try:
            if hasattr(self, "client_thread") and self.client_thread.is_alive():
                self.client_thread.join(timeout=2)
                print(f"Client thread joined for {self.daemon_ip}:{self.daemon_port}.")
            if hasattr(self, "daemon_thread") and self.daemon_thread.is_alive():
                self.daemon_thread.join(timeout=2)
                print(f"Daemon thread joined for {self.daemon_ip}:{self.daemon_port}.")
        except Exception as e:
            print(f"Error joining threads for {self.daemon_ip}:{self.daemon_port}: {e}")

        # Close sockets
        try:
            if hasattr(self, "daemon_udp_socket") and self.daemon_udp_socket:
                self.daemon_udp_socket.close()
                print(f"UDP socket closed for {self.daemon_ip}:{self.daemon_port}.")
            if hasattr(self, "client_tcp_socket") and self.client_tcp_socket:
                self.client_tcp_socket.close()
                print(f"TCP socket closed for {self.daemon_ip}:{self.daemon_port}.")
        except Exception as e:
            print(f"Error closing sockets for {self.daemon_ip}:{self.daemon_port}: {e}")

        # Final log
        print(f"Daemon at {self.daemon_ip}:{self.daemon_port} successfully stopped.")

        
        
####################HANDLING DAEMONS######################
    # daemon -> daemon
    def three_way_handshake_init(self, responder_address: Tuple[str, int]) -> bool:
        try:
            print(f"Starting three-way handshake with {responder_address}")

            # Step 1: Send SYN
            syn_datagram = Datagram(type=0x01, operation=0x02, sequence=0, user="Daemon1", payload="SYN", length=3)
            self.send_datagram(self.daemon_udp_socket, syn_datagram, responder_address)
            print(f"SYN sent to {responder_address}")

            # Step 2: Wait for SYN+ACK
            response, address = self.receive_datagram(self.daemon_udp_socket)
            if response and response.operation == 0x06:  # SYN+ACK
                print(f"SYN+ACK received from {address}")

                # Step 3: Send ACK
                ack_datagram = Datagram(type=0x01, operation=0x04, sequence=response.sequence + 1, user="Daemon1", payload="ACK", length=3)
                self.send_datagram(self.daemon_udp_socket, ack_datagram, responder_address)
                print(f"ACK sent to {responder_address}")

                print(f"Three-way handshake completed with {responder_address}")
                return True
            else:
                print(f"Unexpected response: {response}")
                return False

        except Exception as e:  # Ensure proper exception handling
            print(f"Error during handshake as initiator: {e}")
            return False



    def three_way_handshake_receive(self) -> bool:
        try:
            print("Waiting for SYN...")
            
            # Step 1: Wait for SYN
            syn_datagram, address = self.receive_datagram(self.daemon_udp_socket)
            if syn_datagram and syn_datagram.operation == 0x02:  # SYN
                print(f"SYN received from {address}")

                # Step 2: Send SYN+ACK
                syn_ack_datagram = Datagram(type=0x01, operation=0x06, sequence=syn_datagram.sequence + 1, user="Daemon2", payload="SYN+ACK", length=7)
                self.send_datagram(self.daemon_udp_socket, syn_ack_datagram, address)
                print(f"SYN+ACK sent to {address}")

                # Step 3: Wait for ACK
                ack_datagram, ack_address = self.receive_datagram(self.daemon_udp_socket)
                if ack_datagram and ack_datagram.operation == 0x04:  # ACK
                    print(f"ACK received from {ack_address}")
                    print(f"Three-way handshake completed with {ack_address}")
                    return True
                else:
                    print(f"Unexpected response: {ack_datagram}")
                    return False
            else:
                print(f"Unexpected datagram received: {syn_datagram}")
                return False

        except Exception as e:
            print(f"Error during handshake as responder: {e}")
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
            for attempt in range(3):
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
