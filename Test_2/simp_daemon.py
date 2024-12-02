import socket
from datagram import Datagram
from typing import List, Tuple
import threading
import time

class Daemon:
    def __init__(self, daemon_ip: str, daemon_port: int = 7777, client_port: int =7778):
        
        # CONNECTION RELATED
        self.daemon_ip = daemon_ip
        self.daemon_port = daemon_port
        self.client_port = client_port
        self.daemon_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected_to_client = False
        self.conneted_to_daemon = False
        
        # CHAT RELATED
        self.active_chat = False
        self.pending_chat = False
        self.processing_chat = False
        self.chat_request = False
        self.chat_accepted = False
        self.chat_declined = False
        self.chat_closed = False

        # PROCESS RELATED
        self.shutdown = False
        self.process = True # Daemon will keep running until this is False
        
        # STOP AND WAIT
        self.timeout_for_stop_and_wait = 5

        # OPERATIONS BETWEEN DAEMONS AND CLIENTS
        self.operations = {
            0x01: {
                0x01: "ERR",
                0x02: "SYN",
                0x04: "ACK",
                0x08: "FIN",
            },
            0x02: {
                0x01: "CHAT_REQUEST",
                0x02: "CHAT_ACCEPT",
                0x03: "CHAT_DECLINE",
                0x04: "CHAT_MESSAGE",
                0x05: "CHAT_CLOSE", 
            }
        }
        print(f"Daemon init at {self.daemon_ip}:{self.daemon_port}")

    def start(self):
        self.client_thread = threading.Thread(target=self.client_handler, daemon=True)
        self.daemon_thread = threading.Thread(target=self.daemon_handler, daemon=True)

        self.client_thread.start()
        self.daemon_thread.start()
        
        print("Daemon started")
        try:
            while self.process:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nDaemon stopped")
        
        finally:
            self.end()

    def end(self):
        # If daemon is not already shutdown, shutdown
        if self.shutdown == True:
            print(f"Daemon at {self.daemon_ip}:{self.daemon_port} already shut down")
            # Why return with nothing? Because we want to exit the function
            return 
    
        self.shutdown = True
        self.process = False
        print(f"Shutting down daemon at {self.daemon_ip}:{self.daemon_port}")

        # Error Handling for closing sockets
        # First enter thrads and then close sockets
        try:
            if hasattr(self, "client_thread") and self.client_thread.is_alive():
                self.client_thread.join(timeout=2)
                print(f"Client thread joined for {self.daemon_ip}:{self.daemon_port}")
            if hasattr(self, "daemon_thread") and self.daemon_thread.is_alive():
                self.daemon_thread.join(timeout=2)
                print(f"Daemon thread joined for {self.daemon_ip}:{self.daemon_port}")
        except Exception as e:
            print(f"Error joining threads for: {self.daemon_ip}:{self.daemon_port}")

        # Now we close the sockets
        try:
            if hasattr(self, "daemon_udp_socket") and self.daemon_udp_socket:
                self.daemon_udp_socket.close()
                print(f"Daemon UDP socket closed for {self.daemon_ip}:{self.daemon_port}")
            if hasattr(self, "tcp_socket") and self.tcp_socket:
                self.tcp_socket.close()
                print(f"Daemon TCP socket closed for {self.daemon_ip}:{self.daemon_port}")
        except Exception as e:
            print(f"Error closing sockets for: {self.daemon_ip}:{self.daemon_port}")

        # FINAL LOG
        print(f"Daemon at {self.daemon_ip}:{self.daemon_port} shut down")
        
############# HANDLE CLIENT #############
    def listen_clients(self):
        try:
            self.client_tcp_socket.bind((self.daemon_ip, self.client_port))
            self.client_tcp_socket.listen(1)
            print(f"Listening for clients {self.daemon_ip}:{self.client_port}")
            
            # Assure that daemon is working
            while self.process:
                try:
                    client_conn, client_addr = self.client_tcp_socket.accept()
                    print(f"Client connected: {client_addr}")
                    self.handle_client(client_conn, client_addr)
                except Exception as e:
                    print(f"Error accepting client connection: {e}")
        
        # Catch exceptions and close the socket  
        except Exception as e:
            if self.process:
                print(f"Error in client listener: {e}")
        finally:
            self.client_tcp_socket.close()
            print(f"Stopped listening for clients on {self.daemon_ip}:{self.client_port}")

    def handle_client(self,client_conn, client_addr):
        # Handle communication with client based on operations
        try:
            while self.process:
                # Handle data from client
                message = client_conn.recv(1024).decode("utf-8")
                if not message:
                    # We wait for a message
                    print(f"No message from client {client_addr}")
                    continue
            
            print(f"Message from client {client_addr}: {message}")
            # Handle message
            message_code, *args = message.split()
            if message_code == 1: # Connect
                username = args[0]
                print(f"Client {client_addr} connected with username {username}")
            if message_code == 2: # Quit
                print(f"Client {client_addr} disconnected")
                break
            if message_code == 3: # Chat request
                print(f"Client {client_addr} requested chat")
                # We need after to either accept or decline
                # We need to send a response back to the client
            if message_code == 5: # Chat accept
                print(f"Client {client_addr} accepted chat")
                # We need to start chat]
                # FUNCTION TO START THE CHAT MEANING DAEMONS WILL COMMUNICATE THE MESSAGES
                

            
            
