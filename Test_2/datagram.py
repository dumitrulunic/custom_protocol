class Datagram:
    def __init__(self, type: int, operation: int, sequence: int, user: str, payload: str, length: int):
        self.type = type
        self.operation = operation
        self.sequence = sequence
        self.user = user.ljust(32, '\x00')[:32]
        self.payload = payload
        self.length = length
        self.operations = {
            0x01: {
                0x01: "ERR",
                0x02: "SYN",
                0x03: "ACK",
                0x04: "SYN+ACK",
                0x05: "FIN", # Daemon sends this to another daemon when they finish the chat
            },
            0x02: {
                0x01: "CHAT_REQUEST",
                0x02: "CHAT_ACCEPT",
                0x03: "CHAT_DECLINE",
                0x04: "CHAT_MESSAGE_SENT",
                0x05: "CHAT_MESSAGE_RECEIVED",
                0x06: "CHAT_CLOSE", 
            }
        }

    def to_bytes(self) -> bytes:
        # Convert datagram fields to bytes
        type_bytes = self.type.to_bytes(1, "little")
        operation_bytes = self.operation.to_bytes(1, "little")
        sequence_bytes = self.sequence.to_bytes(1, "little")
        user_bytes = self.user.encode("ascii").ljust(32, b'\x00')  # Ensure user is 32 bytes
        length_bytes = self.length.to_bytes(4, "little")
        payload_bytes = self.payload.encode("ascii")
        

        # Concatenate all byte fields
        return type_bytes + operation_bytes + sequence_bytes + user_bytes + length_bytes + payload_bytes

    @staticmethod
    def from_bytes(data: bytes) -> "Datagram":
        type = int.from_bytes(data[0:1], "little")
        operation = int.from_bytes(data[1:2], "little")
        sequence = int.from_bytes(data[2:3], "little")
        user = data[3:35].decode("ascii").strip('\x00')
        length = int.from_bytes(data[35:39], "little")
        payload = data[39:].decode("ascii")
        
        # Return a new instance of Datagram
        return Datagram(type, operation, sequence, user, payload, length)

    def __str__(self) -> str:
        operation_name = self.get_operation_name()
        return f"{operation_name} {self.user} {self.payload}"

    def get_operation_name(self) -> str:
        if self.type in self.operations and self.operation in self.operations[self.type]:
            return self.operations[self.type][self.operation]
        return f"UNKNOWN_OPERATION({self.operation})"