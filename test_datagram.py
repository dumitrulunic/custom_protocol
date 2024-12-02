from Datagram import Datagram

def test_serialise_and_deserialise():
    
    payload = b'Hello, world!'
    length_payload = len(payload).to_bytes(4, byteorder='big')
    datagram = Datagram(type=b'\x01', operation=b'\x01', sequence=b'\x01', user=b'\x00'*32, length=length_payload, payload=payload)
    serialised = datagram.to_bytes()
    deserialised = Datagram.from_bytes(serialised)
    
    assert datagram.type == deserialised.type
    assert datagram.operation == deserialised.operation
    assert datagram.sequence == deserialised.sequence
    assert datagram.user == deserialised.user
    assert datagram.length == deserialised.length
    assert datagram.payload == deserialised.payload
    
if __name__ == "__main__":
    test_serialise_and_deserialise()
    print("All tests passed")