import socket
import sys
from logger import logger

class Client:
    def __init__(self, daemon_ip: str, daemon_port=7778):
        self.daemon_ip = daemon_ip
        self.daemon_port = daemon_port
        
        # track client username
        self.username = None
        
        # track connection status
        self.connected = False
        
        # track chat status if in chat or not
        self.in_chat = False
        
        # flag used to determine if the client is the sender or receiver
        self.is_sender = False
        
        self.daemon_tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect_to_daemon(self):
        '''
        Connect to the daemon server, using tcp
        '''
        try:
            self.daemon_tcp_socket.connect((self.daemon_ip, self.daemon_port))
            self.connected = True
            print(f"Connected to Daemon at {self.daemon_ip}:{self.daemon_port}")
        except Exception as e:
            logger.error(f"Failed to connect to daemon: {e}")
            sys.exit(1)


    def send_username(self):
        '''
        Send the username to the daemon, using '1 <username>' format. Wait for response
        '''
        self.username = input("Enter your username: ").strip()
        if not self.username:
            print("Username cannot be empty. Please restart the client.")
            sys.exit(1)
        self.daemon_tcp_socket.sendall(f"1 {self.username}".encode("utf-8"))
        response = self.daemon_tcp_socket.recv(1024).decode("utf-8")
        if response == "SUCCESS":
            print("Username sent successfully.")
        else:
            print("Failed to set username.")
            sys.exit(1)


    def menu(self):
        '''
        Main menu for the client.
        '''
        while True:
            print("\nMain Menu:")
            print("1. Start Chat")
            print("2. Wait for Chat")
            print("q. Quit")
            choice = input("Enter your choice: ").strip()

            if choice == "1":
                self.start_chat()
            elif choice == "2":
                self.wait_for_chat()
            elif choice.lower() == "q":
                self.quit()
            else:
                print("Invalid choice. Please try again.")

    
    def start_chat(self):
        '''
        Start a chat with another user, wait response from daemon i nformat: 'DECLINED' | 'SUCCESS'
        '''
        target_ip = input("Enter the IP address of the target daemon: ").strip()
        if not target_ip:
            print("Target IP cannot be empty.")
            return

        self.daemon_tcp_socket.sendall(f"2 {target_ip}".encode("utf-8"))

        while True:
            response = self.daemon_tcp_socket.recv(1024).decode("utf-8")

            if response.startswith("DECLINED"):
                print("Chat declined or request timed out. Returning to main menu.")
                break
            elif response.startswith("SUCCESS"):
                print("Chat started successfully!")
                self.in_chat = True
                # self.is_sender = True
                self.chat_session()
                break

            elif response == "User already in another chat":
                print(response)
                break
            elif response.startswith("Chat request from"):
                self.handle_incoming_chat_request(response)
                break
            elif response.startswith("Message from"):
                print(response)
                self.in_chat = True
                self.is_sender = True
                self.chat_session()
                break
            else:
                if response:
                    print(response)
                else:
                    break
                
                
    def wait_for_chat(self):
        '''
            Function to start a chat (send request to other user)
        '''
        print("Waiting for an incoming chat request...")
        while True:
            response = self.daemon_tcp_socket.recv(1024).decode("utf-8")
            if response.startswith("DECLINED"):
                print("Chat declined or request timed out. Returning to main menu.")
                break
            elif response.startswith("SUCCESS"):
                print("Chat started successfully!")
                self.in_chat = True
                self.is_sender = False
                self.chat_session()
                break
            elif response.startswith("Chat request from"):
                self.handle_incoming_chat_request(response)
                break
            else:
                if response:
                    print(response)
                else:
                    break


    def handle_incoming_chat_request(self, response):
        '''
        Handle incoming chat request for other user. Can decline using "y" | 'n"
        '''
        requester_ip = response.split(":")[1].strip()

        accept = input(f"Do you want to accept the chat request from {requester_ip} ? (y/n): ").strip().lower()
        if accept == "y":
            self.daemon_tcp_socket.sendall("3 ACCEPT".encode("utf-8"))
            self.in_chat = True
            self.is_sender = False 
        else:
            self.daemon_tcp_socket.sendall("3 DECLINE".encode("utf-8"))
            self.in_chat = False

        final_response = self.daemon_tcp_socket.recv(1024).decode("utf-8")

        if final_response.startswith("SUCCESS"):
            print("Chat accepted. Chat started.")
            self.in_chat = True
            self.chat_session()
        elif final_response.startswith("DECLINED"):
            print("Chat declined.")
            self.in_chat = False
        else:
            print("Unexpected response from daemon:", final_response)


    def chat_session(self):
        '''
        Chat session between two users, is running inifinetelly, use ctr+c to stop it, daemons will disconnect automatically
        '''
        try:
            while self.in_chat:
                if self.is_sender:
                    self.send_message()
                    continue
                else:
                    self.wait_for_message()
        except KeyboardInterrupt:
            self.daemon_tcp_socket.sendall("0".encode("utf-8"))
            self.in_chat = False


    def wait_for_message(self):
        '''
        Function to wait for a message from other user. If other user ends chat, will be notified.
        '''
        print("Waiting for a reply...", flush=True)
        try:
            response = self.daemon_tcp_socket.recv(1024).decode("utf-8", errors="replace")
            if not response or response.startswith("CHAT_ENDED"):
                print("Other user ended the chat. Returning to main menu.")
                self.in_chat = False
            elif response.startswith("Message from"):
                print(response, flush=True)
                self.is_sender = True
            else:
                print(f"Unexpected response: {response}", flush=True)
        except Exception as e:
            print(f"Error receiving message: {e}", flush=True)
            self.in_chat = False


    def send_message(self):
        '''
            Function to send a message, if you send "quit", you will exit the chat and other user will be notified.
        '''
        message = input("Enter your message (or 'quit' to end chat): ").strip()
        if message.lower() == "quit":
            self.daemon_tcp_socket.sendall("0".encode("utf-8"))
            print("Exiting chat...")
            self.in_chat = False
            return
        if message:
            self.daemon_tcp_socket.sendall(f"4 {message}".encode("utf-8"))
            self.is_sender = False
        self.is_sender = False


    def quit(self):
        '''
        Quit the client
        '''
        self.daemon_tcp_socket.sendall("0".encode("utf-8"))
        self.daemon_tcp_socket.close()
        sys.exit(0)


    def run(self):
        '''
        Run the client
        '''
        self.connect_to_daemon()
        self.send_username()
        self.menu()
