import struct

def pack_uint16_little_endian(u) -> bytearray:
    """Helper to pack uint16 into a bytearray with little endian mapping"""
    return bytearray(struct.pack('<H', u)) # little endian, unsigned short

def pack_uint16_big_endian(u) -> bytearray:
    """Helper to pack uint16 into a bytearray using big endian mapping"""
    return bytearray(struct.pack('>H', u)) # big endian, unsigned short

def unpack_uint16_little_endian(b) -> int:
    """Helper to extract uint16 from bytearray using little endian mapping"""
    return struct.unpack('<H', bytearray(b))[0] # little endian, unsigned short