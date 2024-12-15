## SIMP: Simple IMC Messaging Protocol

### Project Overview
A lightweight chat protocol built on UDP with reliable messaging using stop-and-wait and a three-way handshake.

### Authors:
- [Andrei-Flavius Văcaru](https://github.com/VakaruGIT)
- [Dumitru Lunic](https://github.com/dumitrulunic)

### Running the Project
1. Dependencies:
   - We only used sockets library from Python, so no additional dependencies are required.

2. We will need a total of 4 terminals to run the project:
   - 2 terminals for the server
   - 2 terminals for the client

3. Running the daemons:
    - First terminal:
            ```
            python run_daemon.py
            ```
        - We input the ip address eg. 127.0.0.1        
        
    - Second terminal:
            ```
            python run_daemon.py
            ```
        - We input the ip address eg. 127.0.0.2

4. Running the clients:
    - First terminal:
            ```
            python run_client.py
            ```
        - We input the ip address of the daemon we want to connect to: 127.0.0.1
        - We input the name of the user: user1
    - Second terminal:
            ```
            python run_client.py
            ```
        - We input the ip address of the daemon we want to connect to: 127.0.0.2
        - We input the name of the user: user2

5. After everything is set, we can start sending messages between the clients.
    - One client waits for chat requests, while the other client sends a chat request.
    - The client that receives the chat request can accept or decline it.
    - If the chat request is accepted, the clients can start sending messages to each other.
    - If the chat request is declined, the clients can send chat requests to other clients.
    - The clients can also disconnect from the chat at any time.
    - The server will keep track of all the active clients and their connections.
    - The server will also keep track of all the active chats and their connections.

6. To stop the daemons, we can press `Ctrl+C` in the terminal where the daemon is running.

7. To stop the clients, we can press `Ctrl+C` in the terminal where the client is running.

8. That is all. Enjoy the SIMP chat protocol!