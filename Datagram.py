import struct
from logger import logger

# Used big endianess

class Datagram:
    def __init__(self, datagram_type:bytes, operation:bytes, sequence:bytes, user:bytes, payload:bytes, length:bytes) -> None:
        # can be bytes or regular data types(if yes convert to bytes)
        self.datagram_type = datagram_type if isinstance(datagram_type, bytes) else datagram_type.to_bytes(1, 'big')
        self.operation = operation if isinstance(operation, bytes) else operation.to_bytes(1, 'big')
        self.sequence = sequence if isinstance(sequence, bytes) else sequence.to_bytes(1, 'big')
        self.user = user.encode('ascii').ljust(32, b'\x00')[:32] if isinstance(user, str) else user.ljust(32)[:32]
        self.payload = payload.encode('ascii') if isinstance(payload, str) else payload
        
        if length is None:
            self.length = len(self.payload).to_bytes(4, 'big')
        else:
            self.length = length.to_bytes(4, 'big') if isinstance(length, int) else length
        
        self.types = {
            "control_datagram": b'\x01',
            "chat_datagram": b'\x02',
        }
        
        self.operations = {
            "ERR": b'\x01',
            "SYN": b'\x02',
            "ACK": b'\x04',
            "FIN_ACK": b'\x06',
            "FIN": b'\x08',
        }
        
        if not self.check_datagram():
            raise ValueError("Invalid datagram")

        
    def check_datagram(self):
        '''
        check validity of th datagram.
        '''
        if self.datagram_type not in (b'\x01', b'\x02'):
            logger.error(f"Invalid type: {self.datagram_type}")
            return False

        if self.datagram_type == b'\x01':  # control datagram
            if self.operation not in (b'\x01', b'\x02', b'\x04', b'\x08', b'\x06'):
                logger.error(f"Invalid operation for control datagram: {self.operation}")
                return False
            
        elif self.datagram_type == b'\x02':  # chat datagram
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
        '''
            convert to bytes
        '''
        user_fixed = self.user.ljust(32, b'\x00')[:32]
        header = struct.pack(
            "!BBB32sI",
            self.datagram_type[0],
            self.operation[0],
            self.sequence[0],
            user_fixed,
            int.from_bytes(self.length, 'big')
        )
        logger.info(f"Datagram created: {header} {self.payload}")
        return header + self.payload

    @classmethod
    def from_bytes(cls, data: bytes):
        '''
            convert from bytes
        '''
        if len(data) < 38:
            raise ValueError("Datagram is too short")
        
        datagram_type = data[0]
        operation = data[1]
        sequence = data[2]
        user = data[3:35].rstrip(b'\x00')
        length = int.from_bytes(data[35:39], 'big')
        payload = data[39:]

        # Check length matches payload
        if len(payload) != length:
            logger.error(f"Invalid datagram length: {length} (actual payload length: {len(payload)})")
            raise ValueError("Invalid datagram")

        logger.info(f"Datagram parsed: {datagram_type} {operation} {sequence} {user} {length} {payload}")
        
        return cls(datagram_type, operation, sequence, user, payload, length)