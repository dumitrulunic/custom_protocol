import struct

class Datagram:
    def __init__(self, type:bytes, operation:bytes, sequence:bytes, user:bytes, length:bytes, payload:bytes) -> None:
        self.type = type
        self.operation = operation
        self.sequence = sequence
        self.user = user
        self.length = length
        self.payload = payload
        
        self.types = {
            "control_datagram": b'\x01',
            "chat_datagram": b'\x02',
        }
        
        self.operations = {
            "ERR": b'\x01',
            "SYN": b'\x02',
            "ACK": b'\x04',
            "FIN": b'\x08',
        }
    
    def check_datagram(self):
        if len(self.type) != 1:
            print("Type is not 1 byte long")
            return False
        if len(self.operation) != 1:
            print("Operation is not 1 byte long")
            return False
        if len(self.sequence) != 1:
            print("Sequence is not 1 byte long")
            return False
        if len(self.user) != 32:
            print("User is not 32 bytes long")
            return False
        if len(self.length) != 4:
            print("Length is not 4 bytes long")
            return False
        
        if self.type == b"\x01":
            if self.operation not in [b"\x01", b"\x02", b"\x04", b"\x08", b"\x06"]:
                print("Invalid operation")
                return False
        elif self.type == b"\x02":
            if self.operation != b"\x02":
                print("Invalid operation")
                return False

        if self.type == b"\x01" and self.operation == b"\x01":
            try:
                self.payload.decode('ascii')
            except UnicodeDecodeError:
                print("Payload is not a valid ASCII string for error message")
                return False
        if self.type == b"\x02":
            try:
                self.payload.decode('ascii')
            except UnicodeDecodeError:
                print("Payload is not a valid ASCII string for chat message")
                return False
            
        if int.from_bytes(self.length, 'big') != len(self.payload):
            print("Length field does not match payload size")
            return False
            
        return True

    def to_bytes(self):
        if not self.check_datagram():
            raise ValueError("Invalid datagram")
        user_fixed = self.user.ljust(32, b'\x00')[:32]
         
        header = struct.pack(
        "!BBB32sI",
        self.type[0],
        self.operation[0],
        self.sequence[0],
        user_fixed,
        int.from_bytes(self.length, 'big')
    )
        return header + self.payload
    
    def from_bytes(data:bytes):
        if len(data) < 38:
            raise ValueError("Datagram is too short")
        type = bytes([data[0]])
        operation = bytes([data[1]])
        sequence = bytes([data[2]])
        user = data[3:35]
        length = data[35:39]
        payload = data[39:]
        
        return Datagram(type, operation, sequence, user, length, payload)