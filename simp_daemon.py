import socket
from Datagram import Datagram
from typing import List, Tuple
import threading

class Daemon:
    def __init__(self, daemon_ip:str, daemon_port:int = 7777, client_port:int = 7778):
        self.daemon_ip = daemon_ip
        self.daemon_port = daemon_port
        self.daemon_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.connected_to_client = False
        self.client_tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected_to_daemon = False
        self.client_port = client_port
        self.active_chat = None
        self.process = True # This is a flag to stop the daemon
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
        
    # daemon - client
    def connect_and_listen_client(self):
        try:
            self.client_tcp_socket.bind((self.daemon_ip, self.client_port))
            self.client_tcp_socket.listen(1)
            print(f"Listening for clients on {self.daemon_ip}:{self.client_port}")
            while self.process:
                client_conn, client_addr = self.client_tcp_socket.accept()
                print(f"Client connected: {client_addr}")
                self.handle_client(client_conn, client_addr)
        except Exception as e:
            print(f"Error in client connection: {e}")
        finally:
            self.client_tcp_socket.close()
            
            
    def connect_and_listen_daemon(self):
        try:
            self.daemon_udp_socket.bind((self.daemon_ip, self.daemon_port))
            print(f"Listening for daemons on {self.daemon_ip}:{self.daemon_port}")
            while self.process:
                try:
                    data, addr = self.daemon_udp_socket.recvfrom(1024)
                    print(f"Message received from daemon {addr}: {data.decode('utf-8')}")
                except socket.timeout:
                    pass
                except Exception as e:
                    print(f"Error receiving datagram: {e}")
        except Exception as e:
            print(f"Error in UDP listener: {e}")
        finally:
            self.daemon_udp_socket.close()
            
            
    def start(self):
        try:
            client_thread = threading.Thread(target=self.connect_and_listen_client, daemon=True)
            daemon_thread = threading.Thread(target=self.connect_and_listen_daemon, daemon=True)

            client_thread.start()
            daemon_thread.start()

            print("Daemon is running...")
            while self.process:
                pass
        except KeyboardInterrupt:
            print("\nDaemon shutting down...")
            self.process = False
        finally:
            self.daemon_udp_socket.close()
            self.client_tcp_socket.close()

    def end(self):
        self.process = False
        
        
    def handle_client(self, client_conn, client_addr):
        """Handle communication with a connected client."""
        try:
            while self.process:
                message = client_conn.recv(1024).decode("utf-8")
                if not message:
                    print(f"No message received from client {client_addr}.")
                    continue  # Continue the loop to keep the connection open
                print(f"Message from client {client_addr}: {message}")
                if message == "QUIT":
                    print(f"Client {client_addr} disconnected.")
                    break
        except Exception as e:
            print(f"Error with client {client_addr}: {e}")
        finally:
            client_conn.close()
            print(f"Connection with client {client_addr} closed.")
