from Datagram import Datagram

def test_datagram_initialization():
    datagram = Datagram(type=0x01, operation=0x02, sequence=0, user="test_user", payload="hello", length=5)
    
    assert datagram.type == 0x01
    assert datagram.operation == 0x02
    assert datagram.sequence == 0
    assert datagram.user.strip('\x00') == "test_user"
    assert datagram.payload == "hello"
    assert datagram.length == 5
    print("Datagram initialization test passed.")
    
def test_datagram_serialization():
    datagram = Datagram(type=0x01, operation=0x02, sequence=0, user="test_user", payload="hello", length=5)
    serialized = datagram.to_bytes()

    assert isinstance(serialized, bytes)
    assert serialized[:1] == b'\x01'
    assert serialized[1:2] == b'\x02'
    assert serialized[2:3] == b'\x00'
    assert serialized[3:35].decode("ascii").strip('\x00') == "test_user"
    assert serialized[35:39] == (5).to_bytes(4, "little")
    assert serialized[39:] == b"hello"
    print("Datagram serialization test passed.")
    
def test_datagram_deserialization():
    data = b'\x01\x02\x00' + b'test_user'.ljust(32, b'\x00') + (5).to_bytes(4, "little") + b"hello"
    datagram = Datagram.from_bytes(data)

    assert datagram.type == 0x01
    assert datagram.operation == 0x02
    assert datagram.sequence == 0
    assert datagram.user.strip('\x00') == "test_user"
    assert datagram.payload == "hello"
    assert datagram.length == 5
    print("Datagram deserialization test passed.")
    
def test_datagram_round_trip_serialization():
    original = Datagram(type=0x01, operation=0x02, sequence=0, user="test_user", payload="hello", length=5)
    serialized = original.to_bytes()
    deserialized = Datagram.from_bytes(serialized)

    assert deserialized.type == original.type
    assert deserialized.operation == original.operation
    assert deserialized.sequence == original.sequence
    assert deserialized.user == original.user
    assert deserialized.payload == original.payload
    assert deserialized.length == original.length
    print("Datagram round trip serialization test passed.")
    
def test_get_operation_name():
    datagram = Datagram(type=0x01, operation=0x02, sequence=0, user="test_user", payload="hello", length=5)
    assert datagram.get_operation_name() == "SYN"

    unknown_datagram = Datagram(type=0x03, operation=0x99, sequence=0, user="test_user", payload="hello", length=5)
    assert unknown_datagram.get_operation_name() == "UNKNOWN"
    print("Datagram get operation name test passed.")
    
def test_empty_datagram_initialization():
    datagram = Datagram(type=0x01, operation=0x02, sequence=0, user="", payload="", length=0)
    
    assert datagram.type == 0x01
    assert datagram.operation == 0x02
    assert datagram.sequence == 0
    assert datagram.user.strip('\x00') == ""
    assert datagram.payload == ""
    assert datagram.length == 0
    print("Empty datagram initialization test passed.")
    
def test_empty_datagram_serialization():
    datagram = Datagram(type=0x01, operation=0x02, sequence=0, user="", payload="", length=0)
    serialized = datagram.to_bytes()

    assert serialized[:1] == b'\x01'
    assert serialized[1:2] == b'\x02'
    assert serialized[2:3] == b'\x00'
    assert serialized[3:35] == b'\x00' * 32
    assert serialized[35:39] == (0).to_bytes(4, "little")
    assert serialized[39:] == b""
    print("Empty datagram serialization test passed.")
    
def test_empty_datagram_deserialization():
    data = b'\x01\x02\x00' + b'\x00' * 32 + (0).to_bytes(4, "little")
    datagram = Datagram.from_bytes(data)

    assert datagram.type == 0x01
    assert datagram.operation == 0x02
    assert datagram.sequence == 0
    assert datagram.user.strip('\x00') == ""
    assert datagram.payload == ""
    assert datagram.length == 0
    print("Empty datagram deserialization test passed.")
    
def test_empty_datagram_round_trip_serialization():
    original = Datagram(type=0x01, operation=0x02, sequence=0, user="", payload="", length=0)
    serialized = original.to_bytes()
    deserialized = Datagram.from_bytes(serialized)

    assert deserialized.type == original.type
    assert deserialized.operation == original.operation
    assert deserialized.sequence == original.sequence
    assert deserialized.user == original.user
    assert deserialized.payload == original.payload
    assert deserialized.length == original.length
    print("Empty datagram round trip serialization test passed.")
    
def test_empty_datagram_for_three_way_handshake():
    # SYN datagram
    syn_datagram = Datagram(type=0x01, operation=0x02, sequence=0, user="", payload="", length=0)
    serialized_syn = syn_datagram.to_bytes()
    deserialized_syn = Datagram.from_bytes(serialized_syn)

    assert deserialized_syn.type == 0x01
    assert deserialized_syn.operation == 0x02
    assert deserialized_syn.sequence == 0
    assert deserialized_syn.user.strip('\x00') == ""
    assert deserialized_syn.payload == ""
    assert deserialized_syn.length == 0

    # ACK datagram
    ack_datagram = Datagram(type=0x01, operation=0x04, sequence=1, user="", payload="", length=0)
    serialized_ack = ack_datagram.to_bytes()
    deserialized_ack = Datagram.from_bytes(serialized_ack)

    assert deserialized_ack.type == 0x01
    assert deserialized_ack.operation == 0x04
    assert deserialized_ack.sequence == 1
    assert deserialized_ack.user.strip('\x00') == ""
    assert deserialized_ack.payload == ""
    assert deserialized_ack.length == 0

    # SYN+ACK datagram
    syn_ack_operation = 0x02 | 0x04 # logical or
    syn_ack_datagram = Datagram(type=0x01, operation=syn_ack_operation, sequence=1, user="", payload="", length=0)
    serialized_syn_ack = syn_ack_datagram.to_bytes()
    deserialized_syn_ack = Datagram.from_bytes(serialized_syn_ack)

    assert deserialized_syn_ack.type == 0x01
    assert deserialized_syn_ack.operation == syn_ack_operation
    assert deserialized_syn_ack.sequence == 1
    assert deserialized_syn.user.strip('\x00') == ""
    assert deserialized_syn_ack.payload == ""
    assert deserialized_syn_ack.length == 0
    print("Empty datagram for three-way handshake test passed.")
    
if __name__ == "__main__":
    test_datagram_initialization()
    test_datagram_serialization()
    test_datagram_deserialization()
    test_datagram_round_trip_serialization()
    test_get_operation_name()
    test_empty_datagram_initialization()
    test_empty_datagram_serialization()
    test_empty_datagram_deserialization()
    test_empty_datagram_round_trip_serialization()
    test_empty_datagram_for_three_way_handshake()