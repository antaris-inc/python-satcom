### Imports ###
## how do I do this ##
from fastcrc import crc16
import struct

### Global Variables ###

SPACE_PACKET_PREAMBLE = [0xAA] * 4
SPACE_PACKET_ASM = [0xD3, 0x91] * 2
SPACE_PACKET_HEADER_LENGTH = 6
SPACE_PACKET_FOOTER_LENGTH = 4
PORT_IDS = [0,1]

### Create Space Packet Header Class ###

class SpacePacketHeader:
    def __init__(self, length, port, sequence_number, destination, command_number):
        self.length = length
        self.port = port
        self.sequence_number = sequence_number
        self.destination = destination
        self.command_number = command_number

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
        bs[2:4] = [i for i in struct.pack('<H',self.sequence_number)] # little endian, unsigned short
        bs[4] = self.destination
        bs[5] = self.command_number

        return bs
    
    def from_bytes(self, bs: bytearray):
        'Unpacks space packet header metadata from bytes'
        if len(bs) != SPACE_PACKET_HEADER_LENGTH:
            return ValueError('ERROR: Unexpected header length!')
        
        self.length = bs[0]
        self.port = [1]
        self.sequence_number = struct.unpack('<H',bytes(bs[2:4]))[0]
        self.destination = bs[4]
        self.command_number = bs[5]

        return None

### Create Space Packet Footer Class ###

class SpacePacketFooter:
    def __init__(self, hardware_id: int, crc16: bytes):
        self.hardware_id = hardware_id
        self.crc16 = crc16

    def err(self):
        'Throws an error if any fields are out of bounds'
        if self.hardware_id < 0 or self.hardware_id > 65535:
            return ValueError('ERROR: HardwareID must be 0-65535')
        if len(self.crc16) != 2:
            return ValueError('ERROR: CRC16 set incorrectly')
        return None
    
    def to_bytes(self):
        'Packs space packet footer metadata into bytes'
        bs = bytearray(SPACE_PACKET_FOOTER_LENGTH)
        
        bs[0:2] = [i for i in struct.pack('<H', self.hardware_id)]

        if self.crc16 is not None:
            bs[2] = self.crc16[1]
            bs[3] = self.crc16[0]

        return bs
    
    def from_bytes(self, bs: bytearray):
        'Unpack space packet footer from a bytearray'
        if len(bs) != SPACE_PACKET_FOOTER_LENGTH:
            return ValueError('ERROR: Unexpected footer length')
        
        self.hardware_id = struct.unpack('<H', bytes(bs[0:2]))[0]
        self.crc16 = bytearray(2)
        self.crc16[0] = bs[3]
        self.crc16[1] = bs[2]

        return None
    
### Create Space Packet Class ###
class SpacePacket(SpacePacketHeader, SpacePacketFooter):
    def __init__(self, length, port, sequence_number, destination, command_number, data: bytearray, hardware_id, crc16):
        SpacePacketHeader.__init__(self, length, port, sequence_number, destination, command_number)
        self.data = data
        SpacePacketFooter.__init__(self, hardware_id, crc16)


    def make_space_packet_crc16(self):
        'Encodes the body of the space packet using CRC16 (xmodem)'
        bs = SpacePacket.to_bytes(self)
        inp = bs[1:len(bs-2)]
        return crc16.xmodem(inp)

    def verify_crc16(self):
        'Compares expected CRC of packet to computed CRC'
        got = self.crc16
        want = self.make_space_packet_crc16()

        if got[0] != want[0] or got[1] != want[1]:
            return TypeError('ERROR: Checksum mismatch!')

    def err(self):
        'Throws an error if any parameters are out of bounds'
        if SpacePacketHeader.err(self) is not None:
            return SpacePacketHeader.err(self)
        if SpacePacketFooter.err(self) is not None:
            return SpacePacketFooter.err(self)
        if self.length != SPACE_PACKET_HEADER_LENGTH + len(self.data) + SPACE_PACKET_FOOTER_LENGTH:
            return ValueError('ERROR: Packet length unequal to header length!')
        if self.verify_crc16() is not None:
            return self.verify_crc16()
        return None
    
    def to_bytes(self):
        'Encodes space packet to byte slice, including header, data, and footer'
        buf = bytearray(self.length)

        buf = SpacePacketHeader.to_bytes(self).copy()
        buf[SPACE_PACKET_HEADER_LENGTH:] = self.data.copy()
        buf[SPACE_PACKET_HEADER_LENGTH+len(self.data):] = SpacePacketFooter.to_bytes(self).copy

        return buf
    
    def from_bytes(self, bs: bytearray):
        'Hydrates the space packet from provided byte array, returning non-nil if errors are present'
        if len(bs) < SPACE_PACKET_HEADER_LENGTH:
            return ValueError('ERROR: Insufficient data!')
        
        if SpacePacketHeader.from_bytes(self, bs[0:SPACE_PACKET_HEADER_LENGTH]) is not None:
            return ValueError
        
        if SpacePacketFooter.from_bytes(self, bs[len(bs)-SPACE_PACKET_FOOTER_LENGTH:]) is not None:
            return ValueError
        
        self.SpacePacketHeader = SpacePacketHeader()
        self.data = bs[SPACE_PACKET_HEADER_LENGTH : len(bs)-SPACE_PACKET_FOOTER_LENGTH]
        self.SpacePacketFooter = SpacePacketFooter()

        return None
    
def new_space_packet(port, seq_num, dest, cmd_num, dat: bytearray, hardware_id):
    'Constructs a new SpacePacket object using provided header and data inputs'
    pkt = SpacePacket(None, port, seq_num, dest, cmd_num, dat, hardware_id, None)

    pkt.SpacePacketHeader.length = SPACE_PACKET_HEADER_LENGTH + len(dat) + SPACE_PACKET_FOOTER_LENGTH
    pkt.SpacePacketFooter.crc16 = pkt.make_space_packet_crc()