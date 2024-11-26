## Progress Overview

#### Core Components
- **Daemon** (`simp_daemon.py`):
  - [x] Define basic structure.
  - [x] Placeholders for all methods.
  - [ ] Implement `start` and `end` methods.
  - [ ] Implement `three_way_handshake`.
  - [ ] Implement `stop_and_wait`.
  - [ ] Handle `send_datagram` and `receive_datagram`.
  - [ ] Process incoming chat invitations and manage active chat status.

- **Client** (`simp_client.py`):
  - [x] Define basic structure.
  - [ ] Implement `connect_to_daemon`.
  - [ ] Implement `send_chat_request` and handle user input.
  - [ ] Implement `start_chat` to send/receive messages.

- **Datagram**:
  - [x] Define datagram format and fields.
  - [ ] Implement `to_bytes` and `from_bytes` for serialization/deserialization.

#### Supporting Functionality
- [x] Define utility functions for data conversion.
- [ ] Add error handling for edge cases (timeouts, busy users, etc.).

### Requirements
- The assignment is worth 50 points that will be given using the following criteria:
    - Correct implementation of the message (header + payload): 15 points.
    - Correct implementation of three-way handshake: 10 points.
    - Correct implementation of stop-and-wait: 10 points.
    - Correct implementation of the communication between daemon and client: 10 points.
    - Clean code and clear documentation: 5 points.
