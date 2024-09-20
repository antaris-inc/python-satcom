import struct

def pack_ushort_little_endian(i: input) -> bytearray:
    """Helper to pack uint16 into a bytearray with little endian mapping"""
    return bytearray(struct.pack('<H', i)) # little endian, unsigned short

def pack_ushort_big_endian(i: int) -> bytearray:
    """Helper to pack uint16 into a bytearray using big endian mapping"""
    return bytearray(struct.pack('>H', i)) # big endian, unsigned short

def unpack_ushort_little_endian(bs: bytearray) -> int:
    """Helper to extract uint16 from bytearray using little endian mapping"""
    return struct.unpack('<H', bs)[0] # little endian, unsigned short

def pack_uint_big_endian(i: int) -> bytearray:
    """Helper to pack uint32 into a bytearray using big endian mapping"""
    return bytearray(struct.pack('>I', i)) # big endian, unsigned int

def unpack_uint_big_endian(bs: bytearray) -> int:
    """Helper to extract uint32 from a bytearray using big endian mapping"""
    return struct.unpack('>I', bs)[0] # big endian, unsigned int