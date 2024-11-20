def from_bytes_to_string(data:bytes) -> str:
    return data.decode('utf-8')

def from_string_to_bytes(data:str) -> bytes:
    return data.encode('utf-8')

def from_int_to_bytes(data:int) -> bytes:
    return data.to_bytes(4, 'little')

def from_bytes_to_int(data:bytes) -> int:
    return int.from_bytes(data, 'little')