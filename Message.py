class Message:
    def __init__(self, type:int, operation:str, sequence:int, user:str, payload:bytes):
        self.type = type
        self.operation = operation
        self.sequence = sequence
        self.user = user
        self.payload = payload
        self.operations = {
            1:"ERR",
            2:"SYN",
            3:"ACK",
            4:"FIN",            
        }
        
    def to_bytes(self) -> bytes:
        pass
    
    @staticmethod
    def from_bytes(data:bytes) -> 'Message':
        pass