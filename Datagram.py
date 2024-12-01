

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
            if self.operation not in [b"\x01", b"\x02", b"\x04", b"\x08"]:
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
            
        return True