### Imports ###
from packet_space_lib import *

### Test Functions ###

def test_space_packet_header_encode():
    'Verifies ClientPacketHeader conversion to bytes'
    ph = SpacePacketHeader(length=27, port=0, sequence_number=1134, destination=23, command_number=132)

    if ph.err() is not None:
        return ph.err()
    want = bytearray([0x1B, 0x00, 0x6E, 0x04, 0x17, 0x84])
    got = ph.to_bytes()

    if want != got:
        raise TypeError(f"ERROR: Unexpected result: want={want}, got{got}")
    
def test_space_packet_header_decode():
    'Verifies SpacePacketHeader byte decode'
    hdr = bytearray([0x0D, 0xFF, 0x03, 0x04, 0x00, 0xFD, 0x38])
    want = SpacePacketHeader(length=13, port=1, sequence_number=4, destination=253, command_number=56)
    got = SpacePacketHeader() # is hdr passed through here?

    if got.from_bytes(hdr) is not None:
        return got.from_bytes(hdr)
    
    if want != got:
        raise TypeError(f"ERROR: Unexpected result: want={want}, got{got}")
    
def test_space_packet_footer_encode():
    'Verifies SpacePacketFooter conversion to bytes'
    pf = SpacePacketFooter(hardware_id=2047, crc16=bytearray([0x01, 0x02]))

    if pf.err() is not None:
        return pf.err()
    want = bytearray([0xFF, 0x07, 0x02, 0x01])
    got = pf.to_bytes()

    if want != got:
        raise TypeError(f"ERROR: Unexpected result: want={want}, got{got}")
    
def test_space_packet_footer_decode():
    'Verifies SpacePacketFooter byte decode'
    ftr = bytearray([0x0E, 0x01, 0x0B, 0x0A])
    want = SpacePacketFooter(hardware_id=270, crc16=bytearray([0x0A,0x0B]))
    got = SpacePacketFooter() # is hdr passed through here?

    if got.from_bytes(ftr) is not None:
        return got.from_bytes(ftr)
    
    if want != got:
        raise TypeError(f"ERROR: Unexpected result: want={want}, got{got}")
    
def test_new_space_packet_from_bytes_too_much_data():
    'Tests if new space packet is rejected due to too much data'
    dat = bytearray(1024)
    pkt = new_space_packet(length=None, port=1, sequence_number=4000, destination=253, command_number=56, dat=dat, hardware_id=12, crc16=None)

    if pkt.err() is None:
        raise Exception('ERROR: Expected an error, but did not manifest!')
    
def test_new_space_packet_to_bytes_success():
    'Verifies successful space packet creation'
    dat = bytearray([0x11, 0x22, 0x33])
    pkt = new_space_packet(length=None, port=1, sequence_number=4000, destination=253, command_number=56, dat=dat, hardware_id=12, crc16=None)

    if pkt.err() is not None:
        return pkt.err()
    
    want = bytearray([
		0x0D, 0x01, 0xA0, 0x0F, 0xFD, 0x38, # packet header
		0x11, 0x22, 0x33, # original message
		0x0C, 0x00, 0x3D, 0x7E # packet footer
    ])

    got = pkt.to_bytes()

    if want != got:
        raise TypeError(f"ERROR: Unexpected result: want={want}, got{got}")