import socket
from Datagram import Datagram
from typing import List, Tuple
import threading

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
        self.connected_to_client = False
        self.client_tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected_to_daemon = False
        self.client_port = client_port
        self.active_chat = None
        self.pending_chat_request = None
        self.process = True  # This is a flag to stop the daemon
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