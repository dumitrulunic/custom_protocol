import struct
from logger import logger

class Datagram:
    def __init__(self, type:bytes, operation:bytes, sequence:bytes, user:bytes, length:bytes, payload:bytes) -> None:
        self.type = type
        self.operation = operation
        self.sequence = sequence
        self.user = user.ljust(32)[:32] # fixed 32 bytes length
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
        
        if self.type not in (b'\x01', b'\x02'):
            logger.error(f"Invalid type: {self.type}")
            return False

        if self.type == b'\x01':  # control datagram
            if self.operation not in (b'\x01', b'\x02', b'\x04', b'\x08'):
                logger.error(f"Invalid operation for control datagram: {self.operation}")
                return False
            
        elif self.type == b'\x02':  # chat datagram
            if self.operation != b'\x01':
                logger.error(f"Invalid operation for chat datagram: {self.operation}")
                return False
            
        if self.sequence not in (b'\x00', b'\x01'):
            logger.error(f"Invalid sequence: {self.sequence}")
            return False
        
        if int.from_bytes(self.length, 'big') != len(self.payload):
            logger.error(f"Invalid length, must be length of payload: {self.length}")
            return False

        try:
            self.user.decode('ascii')
        except UnicodeDecodeError:
            logger.error(f"Invalid user, cannot decode 'ascii': {self.user}")
            return False
        
        return True


    def to_bytes(self):
        if not self.check_datagram():
            logger.error("Invalid datagram")
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
        logger.info(f"Datagram created: {header} {self.payload}")
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
        
        logger.info(f"Datagram parsed: {type} {operation} {sequence} {user} {length} {payload}")
        
        datagram = Datagram(type, operation, sequence, user, length, payload)
        if not datagram.check_datagram():
            raise ValueError("Invalid datagram")
        
        return datagram