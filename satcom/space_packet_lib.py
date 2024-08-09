### Imports ###
import struct
from fastcrc import crc16
from pydantic import BaseModel

### Global Variables ###

SPACE_PACKET_PREAMBLE = [0xAA] * 4
SPACE_PACKET_ASM = [0xD3, 0x91] * 2
SPACE_PACKET_HEADER_LENGTH = 6
SPACE_PACKET_FOOTER_LENGTH = 4
PORT_IDS = [0,1]

def pack_uint16(u):
    'Helper to pack uint16 into packet header'
    return list(struct.pack('<H', u)) # little endian, unsigned short

def unpack_uint16(b):
    'Helper to extract uint16 from header bytearray'
    return struct.unpack('<H', bytes(b))[0] # little endian, unsigned short

class SpacePacketHeader(BaseModel):
    length: int = 0
    port: int = 0
    sequence_number:  int = 0
    destination:  int = 0
    command_number: int = 0

    def err(self):
        'Throws an error if any params are out of bounds'
        if self.length < 10 or self.length > 251:
            return ValueError('ERROR: Length must be 10-251')
        if self.port not in PORT_IDS:
            return ValueError('ERROR: Port must be 0 or 1')
        if self.sequence_number < 0 or self.sequence_number > 65535:
            return ValueError('ERROR: SequenceNumber must be 0-65535')
        if self.destination < 0 or self.destination > 255:
            return ValueError('ERROR: Destination must be 0-255')
        if self.command_number < 0 or self.command_number > 255:
            return ValueError('ERROR: CommandNumber must be 0-255')
        return None

    def to_bytes(self):
        'Packs space packet header metadata into a bytearray'
        bs = bytearray(SPACE_PACKET_HEADER_LENGTH)
        
        bs[0] = self.length
        bs[1] = self.port
        bs[2:4] = pack_uint16(self.sequence_number)
        bs[4] = self.destination
        bs[5] = self.command_number

        return bs
    
    def from_bytes(self, bs: bytearray):
        'Unpacks space packet header metadata from bytes'
        if len(bs) != SPACE_PACKET_HEADER_LENGTH:
            return ValueError('ERROR: Unexpected header length!')
        
        self.length = bs[0]
        self.port = [1]
        self.sequence_number = unpack_uint16(bs[2:4])
        self.destination = bs[4]
        self.command_number = bs[5]

        return None

class SpacePacketFooter(BaseModel):
    hardware_id: int = 0
    crc16_checksum: bytearray = []

    def err(self):
        'Throws an error if any fields are out of bounds'
        if self.hardware_id < 0 or self.hardware_id > 65535:
            return ValueError('ERROR: HardwareID must be 0-65535')
        if len(self.crc16_checksum) != 2:
            return ValueError('ERROR: CRC16 set incorrectly')
        return None
    
    def to_bytes(self):
        'Packs space packet footer metadata into bytes'
        bs = bytearray(SPACE_PACKET_FOOTER_LENGTH)
        
        bs[0:2] = pack_uint16(self.hardware_id)

        if self.crc16_checksum is not None:
            bs[2] = self.crc16_checksum[1]
            bs[3] = self.crc16_checksum[0]

        return bs
    
    @classmethod
    def from_bytes(cls, bs: bytearray):
        'Unpack space packet footer from a bytearray'
        if len(bs) != SPACE_PACKET_FOOTER_LENGTH:
            return ValueError('ERROR: Unexpected footer length')
        
        crc16_checksum = bytearray(2)
        crc16_checksum[0] = bs[3]
        crc16_checksum[1] = bs[2]

        obj = cls(
            hardware_id = unpack_uint16(bs[0:2]),
            crc16_checksum = crc16_checksum
        )
        return obj

class SpacePacket():
    def __init__(self ,data: bytearray, header=None, footer=None ):
        self.header = header or SpacePacketHeader()
        self.header.length = SPACE_PACKET_HEADER_LENGTH + len(data) + SPACE_PACKET_FOOTER_LENGTH
        self._data = data
        self.footer = footer or SpacePacketFooter()
        self.footer.crc16 = self.make_space_packet_crc16()

    @property
    def data(self):
        'Protects data from being modified after instance call'
        return self._data

    def make_space_packet_crc16(self):
        'Encodes the body of the space packet using CRC16 (xmodem)'
        bs = self.to_bytes()
        inp = bs[1:len(bs-2)]
        return crc16.xmodem(inp)

    def verify_crc16(self):
        'Compares expected CRC of packet to computed CRC'
        got = self.footer.crc16
        want = self.make_space_packet_crc16()

        if got[0] != want[0] or got[1] != want[1]:
            return TypeError('ERROR: Checksum mismatch!')

    def err(self):
        'Throws an error if any parameters are out of bounds'
        if SpacePacketHeader.err(self) is not None:
            return SpacePacketHeader.err(self)
        if SpacePacketFooter.err(self) is not None:
            return SpacePacketFooter.err(self)
        if self.header.length != SPACE_PACKET_HEADER_LENGTH + len(self.data) + SPACE_PACKET_FOOTER_LENGTH:
            return ValueError('ERROR: Packet length unequal to header length!')
        if self.verify_crc16() is not None:
            return self.verify_crc16()
        return None
    
    def to_bytes(self):
        'Encodes space packet to byte slice, including header, data, and footer'
        buf = bytearray(self.header.length)

        buf = self.header.to_bytes(self).copy()
        buf[SPACE_PACKET_HEADER_LENGTH:] = self.data.copy()
        buf[SPACE_PACKET_HEADER_LENGTH+len(self.data):] = self.footer.to_bytes(self).copy

        return buf
    
    def from_bytes(self, bs: bytearray):
        'Hydrates the space packet from provided byte array, returning non-nil if errors are present'
        if len(bs) < SPACE_PACKET_HEADER_LENGTH:
            return ValueError('ERROR: Insufficient data!')
        
        if self.header.from_bytes(self, bs[0:SPACE_PACKET_HEADER_LENGTH]) is not None:
            return ValueError
        
        if self.footer.from_bytes(bs[len(bs)-SPACE_PACKET_FOOTER_LENGTH:]) is not None:
            return ValueError
        
        self.header = self.header # this seems redundant
        self.data = bs[SPACE_PACKET_HEADER_LENGTH : len(bs)-SPACE_PACKET_FOOTER_LENGTH]
        self.footer = self.footer # this seems redundant
        return None