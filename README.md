## SIMP: Simple IMC Messaging Protocol

### Project Overview
A lightweight chat protocol built on UDP with reliable messaging using stop-and-wait and a three-way handshake.

### Authors:
- [Andrei-Flavius Văcaru](https://github.com/VakaruGIT)
- [Dumitru Lunic](https://github.com/dumitrulunic)

### Running the Project
1. Install dependencies:
    ```
    pip install -r requirements.txt
    ```

2. Start the daemon:
    ```
    python simp_daemon.py 
    ```

3. Start the client:
    ```
    python simp_client.py
    ```