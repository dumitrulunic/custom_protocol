import socket
from datagram import Datagram
import sys
from typing import Tuple

class Client:
    MESSAGE_CODES = {
        # Connection related
        1: "connect",
        2: "quit",

        # Chat related
        4: "chat_request",
        5: "chat_accept",
        6: "chat_reject",
        7: "chat_started",
        8: "chat_request_rejected",
        9: "chat_closed",
        
        # Message related
        10: "send_message",
        11: "message_sent",
        12: "message_received"
    }

    def __init__(self, daemon_ip: str, daemon_port=7778):
        self.daemon_ip = daemon_ip
        self.daemon_port = daemon_port
        self.username = None
        self.daemon_tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)