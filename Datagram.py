class Datagram:
    def __init__(self, type:int, operation:int, sequence:int, user:str, payload:str, length:int):
        self.type = type
        self.operation = operation
        self.sequence = sequence
        self.user = user
        self.payload = payload
        self.length = length
        self.operations = {
            0x01: {
                0x01: "ERR",
                0x02: "SYN",
                0x04: "ACK",
                0x08: "FIN",
            },
            0x02: {
                0x01: "CHAT"
            }
        }
        
    def to_bytes(self) -> bytes:
        pass
    
    @staticmethod
    def from_bytes(data:bytes) -> "Datagram":
        pass
    
    def __str__(self) -> str:
        return f"{self.operations[self.operation]} {self.user} {self.payload}"
    
    def get_operation_name(self) -> str:
        if self.operation in self.operations:
            if self.operation in self.operations[self.operation]:
                return self.operations[self.operation][self.operation]
            else:
                return "UNKNOWN"