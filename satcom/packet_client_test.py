### Imports ###
from packet_client_lib import *

### Test Functions ###

def test_client_packet_header_encode():
    'Verifies ClientPacketHeader conversion to bytes'
    ph = ClientPacketHeader(length=10, hardware_id=755, sequence_number=12, destination=212, command_number=57)
    
    if ph.err() is not None:
        return ph.err()
    want = bytearray([0x0A, 0xF3, 0x02, 0x0C, 0x00, 0xD4, 0x39])
    got = ph.to_bytes()

    if want != got:
        raise TypeError(f"ERROR: Unexpected result: want={want}, got{got}")
    
def test_client_packet_header_decode():
    'Verifies ClientPacktHeader byte decode'
    hdr = bytearray([0x0D, 0x01, 0x04, 0x00, 0xFD, 0x38])
    want = ClientPacketHeader(length=13, hardware_id=1023, sequence_number=4, destination=253, command_number=56)
    got = ClientPacketHeader() # is hdr passed through here?

    if got.from_bytes(hdr) is not None:
        return got.from_bytes(hdr)
    
    if want != got:
        raise TypeError(f"ERROR: Unexpected result: want={want}, got{got}")
    
def test_new_client_packet_to_bytes_small_frame():
    'Test new client packet creation with a small dataframe'
    dat = bytearray([0x0A, 0x0B, 0x0C, 0x0D])
    pkt = new_client_packet(hardware_id=1023, sequence_number=1, destination=253, command_number=56, dat=dat)
    
    if pkt.err() is not None:
        return pkt.err()
    
    want = bytearray([0x0B, 0xFF, 0x03, 0x01, 0x00, 0xFD, 0x38, 0x0A, 0x0B, 0x0C, 0x0D])
    got = pkt.to_bytes()

    if want != got:
        raise TypeError(f"ERROR: Unexpected result: want={want}, got{got}")
    
def test_new_client_packet_from_bytes_too_much_data():
    'Tests if new client packet is rejected due to too much data'
    dat = bytearray(1024)
    pkt = new_client_packet(hardware_id=1023, sequence_number=1, destination=253, command_number=56, dat=dat)

    if pkt.err() is None:
        raise Exception('ERROR: Expected an error, but did not manifest!')
    
def test_client_packet_from_bytes_small_frame():
    'Verifies that client packet structure is preserved when passing a small frame'
    val = bytearray([0x0A, 0xFF, 0x03, 0x04, 0x00, 0xFD, 0x38, 0x01, 0x02, 0x03])
    pkt = ClientPacket()

    if pkt.from_bytes(val) is not None:
        return pkt.from_bytes
    if pkt.err() is not None:
        return pkt.err()
    
    want_data = bytearray([0x01, 0x02, 0x03])
    if want_data != pkt.data:
        raise TypeError(f"ERROR: Unexpected result: want={want_data}, got{pkt.data}")
    
def test_client_packet_from_bytes_empty_frame():
    'Verifies expected client packet behavior for no data'
    val = bytearray([0x0A, 0xFF, 0x03, 0x04, 0x00, 0xFD, 0x38])
    pkt = ClientPacket()

    if pkt.from_bytes(val) is not None:
        return pkt.from_bytes
    if pkt.err() is not None:
        return pkt.err()
    
    if len(pkt.data) != 0:
        raise Exception(f"ERROR: Expected empty result, got {pkt.data}")

