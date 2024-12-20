## SIMP: Simple IMC Messaging Protocol

### Project Overview

A lightweight chat protocol built on UDP with reliable messaging using stop-and-wait and a three-way handshake.

### Authors:

- [Andrei-Flavius Văcaru](https://github.com/VakaruGIT)
- [Dumitru Lunic](https://github.com/dumitrulunic)

### Running the Project

1. Dependencies:

   - We only used sockets library from Python, so no additional dependencies are required.
   - We used built-in custom logger (logger.py), to display comprehensive messages on the daemon console. Very useful during development and debugging.

2. We will need a total of 4 terminals to run the project:

   - 2 terminals for the server
   - 2 terminals for the client

3. Running the daemons:
   - First terminal:
     `python run_daemon.py`
     - We input the ip address eg. 127.0.0.1 - by default available on all machines windows/macOS/linux
   - Second terminal:
     `python run_daemon.py`
     - We input the ip address eg. 127.0.0.2 - available on windows, on macOS must configure with:
     
       `
       sudo ifconfig lo0 alias 127.0.0.2
       `

> Note: If ports are not available, check if the ports 7777 and 7778 are busy with:
> `lsof -i :7777` and `lsof -i :7778`

4. Running the clients:

   - First terminal:
     `     python run_client.py`
     - We input the ip address of the daemon we want to connect to: `127.0.0.1`
     - We input the name of the user: user1
   - Second terminal:
     `     python run_client.py`
     - We input the ip address of the daemon we want to connect to: `127.0.0.2`
     - We input the name of the user: user2

5. After everything is set, we can start sending messages between the clients.

   - One client waits for chat requests, while the other client sends a chat request.
   - The client that receives the chat request can accept or decline it.
   - If the chat request is accepted, the clients can start sending messages to each other.
   - If the chat request is declined, the clients can send chat requests to other clients.
   - The clients can also disconnect from the chat at any time. Write 'quit' to disconnect from the chat.
   - The server will keep track of all the active clients and their connections.
   - The server will also keep track of all the active chats and their connections.

#### Handling Sequence Numbers

We use sequence numbers to ensure the correct order of messages. Each datagram includes a sequence number, which alternates between 0 and 1. This allows us to detect and handle duplicate or out-of-order messages.

#### Handling Retransmissions

Our protocol uses a stop-and-wait mechanism for reliable messaging. After sending a datagram, the sender waits for an acknowledgment (ACK) from the receiver before sending the next datagram. If an ACK is not received within a certain timeout period, the sender retransmits the datagram.

#### Code Organization

- `Datagram.py`: Defines the `Datagram` class, which represents the structure of a datagram and includes methods for serialization and deserialization based on the project requirements.
- `logger.py`: Configures the logging for the project.
- `run_client.py`: Entry point for running the client.
- `run_daemon.py`: Entry point for running the daemon.
- `simp_client.py`: Defines the `Client` class, which handles client-side operations(chat menu, sending ).
- `simp_daemon.py`: Defines the `Daemon` class, which handles daemon-side operations.

### Testing

We have included tests in the `tests/` directory to verify the functionality of the client, daemon, and datagram. You can run these tests to ensure that everything is working correctly.

6. To stop the daemons, we can press `Ctrl+C` in the terminal where the daemon is running.

7. To stop the clients, we can press `Ctrl+C` in the terminal where the client is running.

8. That is all. Enjoy the SIMP chat protocol!

