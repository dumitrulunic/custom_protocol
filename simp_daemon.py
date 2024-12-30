import socket
import threading
from Datagram import Datagram
from logger import logger
import time

class Daemon:
    def __init__(self, ip: str, port: int = 7777) -> None:
        self.ip_address = ip
        self.port = port
        self.running = True

        self.socket_daemon = None
        self.socket_client = None

        self.active_daemon_connection = {} # {"target_ip": ..., "target_port": ..., "state": ...}
        self.active_client_connection = {} # {"conn": ..., "username": ..., "address": ...}
        self.active_chat = {} # {"target_ip": ..., "target_port": ..., "state": ...}
        
        # track handshake status
        self.handshake_status = {}

        self.lock = threading.Lock()
        self.logger = logger
        self.expected_sequence = 0

    def start(self):
        '''
        Start the daemon and listen for incoming packets from the daemon and client.
        Used threading because, the dameon must listen for both it's client and other daemon/s, since any of them can start chat.
        '''
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
        '''
        Stop the daemon and close the sockets.
        '''
        self.running = False
        if self.socket_daemon:
            self.socket_daemon.close()
            self.logger.info("Daemon UDP socket closed.")
        if self.socket_client:
            self.socket_client.close()
            self.logger.info("Daemon TCP socket closed.")


    def listen_to_daemon_packets(self):
        '''
            Listen for other daemon, using custom SIMP UDP.
        '''
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
            self.logger.error(f"Daemon packet listener error: {e}")
        finally:
            if self.socket_daemon:
                self.socket_daemon.close()


    def listen_to_client_packets(self):
        '''
        Listen for incoming TCP connections from the client.
        '''
        try:
            self.socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_client.bind((self.ip_address, 7778))
            self.socket_client.settimeout(5)
            self.socket_client.listen(1)
            while self.running:
                try:
                    conn, address = self.socket_client.accept()
                    self.logger.info(f"Received connection from client {address}")
                    client_thread = threading.Thread(target=self.handle_incoming_command_from_client, args=(conn, address), daemon=True)
                    client_thread.start()
                except socket.timeout:
                    continue
        except Exception as e:
            self.logger.error(f"Client packet listener error: {e}")
        finally:
            if self.socket_client:
                self.socket_client.close()


    def handle_incoming_datagram_from_daemon(self, data: bytes, address: tuple):
        '''
        Handle incoming datagram from the daemon. Distinguish between control and chat datagram.
        '''
        try:
            logger.info(f"Active chat: {self.active_chat}")
            datagram = Datagram.from_bytes(data)
            datagram_type = datagram.datagram_type[0]
            self.logger.info(f"Received datagram from {address}: {datagram}")

            if datagram_type == 1:  # Control
                self.handle_control_datagram(datagram, address)
            elif datagram_type == 2:  # Chat
                self.handle_chat_datagram(datagram, address)
            else:
                self.logger.error(f"Invalid datagram type: {datagram_type}")
        except Exception as e:
            self.logger.error(f"Failed to handle incoming datagram from daemon {address}: {e}")


    def handle_control_datagram(self, datagram: Datagram, address: tuple):
        '''
        Handle incoming control datagram from the daemon. check its operation and proceed acordingly.
        '''
        logger.info(f"Active chat: {self.active_chat}")
        operation = datagram.operation[0]
        sequence = datagram.sequence[0]
        ip, port = address
        self.logger.info(f"Control datagram op: {operation} from {address}")

        if operation == 1:  # ERR
            self.logger.error(f"Error from {address}: {datagram.payload.decode('ascii')}")

        # there is incomming chat request
        elif operation == 2:  # SYN 
            self.logger.info(f"Received SYN from {address}.")
            # Check if we are already in a chat
            if self.is_already_in_chat():
                self.send_control_datagram(1, 0, ip, port, "User already in another chat")
                self.send_control_datagram(8, 0, ip, port)  # FIN
            else:
                self.send_control_datagram(6, 0, ip, port)  # SYN+ACK
                self.handshake_status[(ip, port)] = "SYN_ACK_SENT"

                self.active_chat = {"target_ip": ip, "target_port": port,
                                    "state": "pending_user_acceptance"}
                self.notify_client_chat_request(ip)


        elif operation == 4:  # ACK
            self.logger.info(f"Received ACK from {address}")
            # Mark connection with this daemon as active
            self.mark_connection_as_active(address, sequence)
            
            # additional check if target ip and port are set
            if self.active_chat.get("target_ip") is None:
                self.active_chat["target_ip"] = ip
                self.active_chat["target_port"] = port

            #If we were in 'handshake_complete' state and got ACK, that means handshake done
            if self.active_chat.get("state") == "handshake_complete":
                self.active_chat["state"] = "started"
                # Notify client that the chat starte
                if "conn" in self.active_client_connection:
                    self.active_client_connection["conn"].sendall(b"SUCCESS - Chat started.")
            #additional check and uppdate handshake_status if needed
            if (ip, port) in self.handshake_status and self.handshake_status[(ip, port)] == "SYN_ACK_RECEIVED":
                self.handshake_status[(ip, port)] = "handshake_complete"

        elif operation == 6:  # SYN+ACK
            self.logger.info(f"Received SYN+ACK from {address}")
            # If we sent SYN and now got SYN+ACK, we respond with ACK
            if (ip, port) in self.handshake_status and self.handshake_status[(ip, port)] == "SYN_SENT":
                self.send_control_datagram(4, sequence, ip, port)  # ACK
                self.handshake_status[(ip, port)] = "SYN_ACK_RECEIVED"

        elif operation == 8:  # FIN
            self.logger.info(f"Received FIN from {address}, sending ACK and closing.")
             # Acknowledge the FIN
            self.send_control_datagram(4, sequence, ip, port)
            self.mark_connection_as_inactive(address)

            # check FIN corresponds to our active chat, end the chat session
            if self.active_chat.get("target_ip") == ip and self.active_chat.get("target_port") == port:
                if "conn" in self.active_client_connection:
                    self.active_client_connection["conn"].sendall(b"CHAT_ENDED")

                # clean handhshake status
                with self.lock:
                    if (ip, port) in self.handshake_status:
                        del self.handshake_status[(ip, port)]
                # clean chat track dict
                self.active_chat.clear()


        else:
            self.logger.error(f"Unknown control operation: {operation}")


    def handle_chat_datagram(self, datagram: Datagram, address: tuple):
        logger.info(f"Active chat: {self.active_chat}")
        # check if chat started to continue to process chat datagrams
        if self.active_chat.get("state") == "waiting_for_first_message":
            self.logger.info("Received first chat from remote => remote user accepted!")
            self.active_chat["state"] = "started"
            # Let local client know that the chat is truly started
            if "conn" in self.active_client_connection:
                self.active_client_connection["conn"].sendall(b"SUCCESS - Chat started.\n")


        sender = datagram.user.decode("utf-8").strip()
        message = datagram.payload.decode("utf-8")
        sequence = datagram.sequence[0]
        
        # skip acceptance message
        if message.endswith(" accepted."):
            self.logger.info("Skipping display of acceptance message.")

        # check packet sequence to tarck order of messages
        if sequence != self.expected_sequence:
            self.logger.warning(f"Unexpected sequence. Expected: {self.expected_sequence}, got: {sequence}")
            return

        with self.lock:
            # reverse sequence for next expected package
            self.expected_sequence = (self.expected_sequence + 1) % 2

        self.logger.info(f"Received chat message from {sender}@{address}: {message}")

        # forward messafe to client
        if "conn" in self.active_client_connection:
            client_conn = self.active_client_connection["conn"]
            try:
                client_conn.sendall(f"Message from {sender}: {message}".encode("utf-8"))
            except Exception as e:
                self.logger.error(f"Failed to forward message to client: {e}")
                self.disconnect_client(client_conn)
        else:
            self.logger.warning("No client connected, dropping message.")
        #Send ACK back to the other daemon to confirm if it receivedthe  message
        self.send_control_datagram(4, sequence, address[0], address[1])


    def is_already_in_chat(self):
        '''
        Check if the user is already in a chat session.
        '''
        logger.info(f"Active chat: {self.active_chat}")
        return self.active_chat.get("state") in ["handshake_complete", "started"]


    def mark_connection_as_active(self, address: tuple, sequence: int):
        '''
        Mark the connection with the daemon as active.
        '''
        logger.info(f"Active chat: {self.active_chat}")
        with self.lock:
            self.active_daemon_connection[address] = {
                "state": "connected",
                "sequence": sequence
            }
            self.logger.info(f"Connection with {address} established.")


    def mark_connection_as_inactive(self, address: tuple):
        '''
        Mark the connection with the daemon as inactive.
        '''
        logger.info(f"Active chat: {self.active_chat}")
        with self.lock:
            if address in self.active_daemon_connection:
                del self.active_daemon_connection[address]
                self.logger.info(f"Connection with {address} terminated.")


    def send_control_datagram(self, operation: int, sequence: int, target_ip: str, target_port: int, payload: str = ""):
        ''''
        Send a control datagram to the daemon.
        '''
        logger.info(f"Active chat: {self.active_chat}")
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


    def send_datagram_to_daemon(self, datagram: Datagram, ip: str, port: int = 7777):
        '''
        Send a datagram to the daemon.
        '''
        logger.info(f"Active chat: {self.active_chat}")
        try:
            serialized = datagram.to_bytes()
            self.socket_daemon.sendto(serialized, (ip, port))
            self.logger.info(f"Sent datagram to daemon {ip}:{port}")
        except Exception as e:
            self.logger.error(f"Failed to send datagram to daemon {ip}:{port}: {e}")


    def notify_client_chat_request(self, requester_ip):
        logger.info(f"Active chat: {self.active_chat}")
        if "conn" in self.active_client_connection and self.active_client_connection.get("username"):
            client_conn = self.active_client_connection["conn"]
            message = f"Chat request from: {requester_ip}"
            client_conn.sendall(message.encode("utf-8"))
            self.logger.info("Notified client about incoming chat request.")
        else:
            self.logger.info("No client connected to handle chat request.")
            self.send_control_datagram(8, 0, requester_ip, 7777)  # FIN
            with self.lock:
                if (requester_ip, 7777) in self.handshake_status:
                    del self.handshake_status[(requester_ip, 7777)]
            self.active_chat.clear()


    def handle_incoming_command_from_client(self, client_conn, client_addr):
        '''
        Handle incoming commands from the client.
        '''
        logger.info(f"Active chat: {self.active_chat}")
        self.logger.info(f"Started handling commands from client {client_addr}.")
        self.active_client_connection["conn"] = client_conn
        try:
            while True:
                data = client_conn.recv(1024)
                if not data:
                    self.logger.info(f"Client {client_addr} disconnected.")
                    self.disconnect_client(client_conn)
                    break

                msg = data.decode("utf-8").strip()
                parts = msg.split(" ", 1)
                if len(parts) == 1:
                    message_code_str = parts[0]
                    args_str = ""
                else:
                    message_code_str, args_str = parts[0], parts[1]

                try:
                    message_code = int(message_code_str)
                except ValueError:
                    self.logger.warning(f"Invalid message code from client: {msg}")
                    continue

                if message_code == 1:
                    # Set username of client
                    username = args_str.strip()
                    self.handle_client_username(username, client_conn)

                elif message_code == 0:
                    # Client wants to end the chat or quit
                    if self.active_chat and self.active_chat.get("state") == "started":
                        target_ip = self.active_chat["target_ip"]
                        target_port = self.active_chat["target_port"]
                        self.send_control_datagram(8, 0, target_ip, target_port)  # FIN
                        self.active_chat.clear()

                    # disconnect client
                    self.disconnect_client(client_conn)
                    break

                elif message_code == 2:
                    # Start chat
                    target_ip = args_str.strip()
                    self.logger.info(f"Client requests to start chat with {target_ip}")
                    self.start_chat_with_daemon(target_ip, 7777, is_initiator=True)

                elif message_code == 3:
                    # Chat request response (ACCEPT/DECLINE)
                    decision = args_str.upper().strip()
                    self.handle_client_chat_decision(decision, client_conn)

                elif message_code == 4:
                    # Client wants to send a message to the other , retransmit to other daemon
                    self.retransmit_message_to_other_daemon(args_str)

                else:
                    self.logger.warning(f"Unknown message code {message_code} from client {client_addr}.")

        except Exception as e:
            self.logger.error(f"Error handling commands from client {client_addr}: {e}")
        finally:
            self.logger.info(f"Finished handling commands from client {client_addr}.")


    def handle_client_username(self, username: str, client_conn):
        '''
        Handle the username sent by the client.
        '''
        logger.info(f"Active chat: {self.active_chat}")
        self.active_client_connection["username"] = username
        self.active_client_connection["address"] = (self.ip_address, 7778)
        client_conn.sendall(b"SUCCESS")
        self.logger.info(f"Client username set to '{username}'.")


    def handle_client_chat_decision(self, decision, client_conn):
        logger.info(f"Active chat: {self.active_chat}")
        
        if not self.active_chat or self.active_chat.get("state") != "pending_user_acceptance":
            self.logger.warning("No pending chat request.")
            client_conn.sendall(b"No pending chat request.\n")
            return

        requester_ip = self.active_chat["target_ip"]
        requester_port = self.active_chat["target_port"]

        if decision == "ACCEPT":
            self.logger.info("Client accepted the chat request.")
            self.active_chat["state"] = "started"
            client_conn.sendall(b"SUCCESS - Chat started.\n")
            
            # send fake chat message to trigger chat start
            acceptance_message = f"{self.active_client_connection.get('username', '???')} accepted."
            self.retransmit_message_to_other_daemon(acceptance_message)

        else:
            self.logger.info("Client declined the chat request.")
            self.send_control_datagram(8, 0, requester_ip, requester_port)  # FIN
            
            client_conn.sendall(b"DECLINED - Back to menu.\n")
            
            self.active_chat.clear()
            with self.lock:
                if (requester_ip, requester_port) in self.handshake_status:
                    del self.handshake_status[(requester_ip, requester_port)]



    def disconnect_client(self, client_conn):
        '''
        Disconnect the client.
        '''
        logger.info(f"Active chat: {self.active_chat}")
        self.logger.info("Disconnecting client.")
        with self.lock:
            self.active_client_connection.clear()
        client_conn.close()
        self.logger.info("Client disconnected.")


    def start_chat_with_daemon(self, target_ip: str, target_port: int, is_initiator: bool = False):
        logger.info(f"Active chat: {self.active_chat}")
        if self.is_already_in_chat():
            self.logger.info("User already in another chat. Cannot start a new one.")
            if "conn" in self.active_client_connection:
                self.active_client_connection["conn"].sendall(b"User already in another chat")
            return

        if is_initiator:
            success = self.handshake_initiator(target_ip, target_port)
            if success:
                # Handshake succeeded, chat session started
                self.logger.info("Handshake complete, now waiting for remote acceptance.")
                if "conn" in self.active_client_connection:
                    self.active_client_connection["conn"].sendall(
                        b"Transport handshake OK. Waiting for remote user to accept...\n"
                    )
                self.active_chat["state"] = "waiting_for_first_message"
            else:
                self.logger.info("Handshake failed or timed out.")


    def handshake_initiator(self, target_ip: str, target_port: int, timeout=5):
        logger.info(f"Active chat: {self.active_chat}")
        self.handshake_status[(target_ip, target_port)] = "SYN_SENT"
        self.send_control_datagram(2, 0, target_ip, target_port)  # SYN

        start_time = time.time()
        # Wait up to 5 seconds for SYN+ACK
        while time.time() - start_time < timeout:
            with self.lock:
                state = self.handshake_status.get((target_ip, target_port))
                if state == "SYN_ACK_RECEIVED":
                    # Got SYN+ACK, send ACK and mark handshake complete
                    self.send_control_datagram(4, 0, target_ip, target_port)
                    self.handshake_status[(target_ip, target_port)] = "HANDSHAKE_COMPLETE"
                    self.active_chat = {
                        "target_ip": target_ip,
                        "target_port": target_port,
                        "state": "handshake_complete"
                    }
                    return True
            time.sleep(0.3)
        # If we reached here, handshake timed out
        self.logger.warning("Handshake timed out.")
        if "conn" in self.active_client_connection:
            self.active_client_connection["conn"].sendall(b"DECLINED - Handshake timed out, back to menu.")


        self.active_chat.clear()
        with self.lock:
            if (target_ip, target_port) in self.handshake_status:
                del self.handshake_status[(target_ip, target_port)]

        return False


    def retransmit_message_to_other_daemon(self, message: str):
        '''
        Retransmit the message to the other daemon.
        '''
        logger.info(f"Active chat: {self.active_chat}")
        logger.info(f"Retransmitting message to other daemon: {message}")
        logger.info(f"Active chat: {self.active_chat}")
        if not self.active_chat or self.active_chat["state"] != "started":
            self.logger.warning("No active chat session. Cannot send message.")
            # optionally also tell the local client:
            if "conn" in self.active_client_connection:
                self.active_client_connection["conn"].sendall(
                    b"Cannot send message: remote user has not accepted.\n"
                )
            return

        target_ip = self.active_chat["target_ip"]
        target_port = self.active_chat["target_port"]

        with self.lock:
             # neext sequence number
            seq = self.expected_sequence
            self.expected_sequence = (self.expected_sequence + 1) % 2

        username = self.active_client_connection.get("username", "Unknown")

        # make chat datagram to send to other daemon
        chat_datagram = Datagram(
            datagram_type=2,
            operation=1,
            sequence=seq,
            user=username,
            length=len(message),
            payload=message
        )
        self.send_datagram_to_daemon(chat_datagram, target_ip, target_port)
        
        
    def notify_client_chat_request(self, requester_ip):
        logger.info(f"Active chat: {self.active_chat}")
        if "conn" in self.active_client_connection and self.active_client_connection.get("username"):
            client_conn = self.active_client_connection["conn"]
            requester_username = self.active_client_connection.get("username", "Unknown")
            message = f"Chat request from: {requester_ip}, {requester_username}"
            client_conn.sendall(message.encode("utf-8"))
            self.logger.info("Notified client about incoming chat request.")
        else:
            self.logger.info("No client connected to handle chat request.")
            self.send_control_datagram(8, 0, requester_ip, 7777)  # FIN
            self.active_chat.clear()
