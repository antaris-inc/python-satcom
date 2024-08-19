### Imports ###
import struct
import binascii
from crc import Calculator, Configuration, TableBasedRegister, Register
from pydantic import BaseModel, ConfigDict

### Global Variables ###

SPACE_PACKET_PREAMBLE = [0xAA] * 4
SPACE_PACKET_ASM = [0xD3, 0x91] * 2
SPACE_PACKET_HEADER_LENGTH = 6
SPACE_PACKET_FOOTER_LENGTH = 4
PORT_IDS = [0,1]

def pack_uint16(u):
    'Helper to pack uint16 into packet header'
    return bytearray(struct.pack('<H', u)) # little endian, unsigned short

def unpack_uint16(b):
    'Helper to extract uint16 from header bytearray'
    return struct.unpack('<H', bytes(b))[0] # little endian, unsigned short

def crc16_maxim(bs: bytearray):
    'Helper to calculate a checksum using CRC16 MAXIM-DOW from a bytearray'
    # Construct calculator for CRC16 (MAXIM-DOW)
    # Source: https://reveng.sourceforge.io/crc-catalogue/all.htm
    config = Configuration(
        width=16,
        polynomial=0x8005,
        init_value=0x0000,
        final_xor_value=0xFFFF,
        reverse_input=True,
        reverse_output=True
    )

    register = Register(config)

    inp = bs[1:len(bs)-2]
    register.init()
    register.update(inp)
    
    return pack_uint16(register.digest())

class SpacePacketHeader(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

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
        
        try:
            bs[0] = self.length
            bs[1] = self.port
            bs[2:4] = pack_uint16(self.sequence_number)
            bs[4] = self.destination
            bs[5] = self.command_number

            return bs
        except ValueError:
            self.err()
    
    @classmethod
    def from_bytes(cls, bs: bytearray):
        'Unpacks space packet header metadata from bytes'
        if len(bs) != SPACE_PACKET_HEADER_LENGTH:
            raise ValueError('ERROR: Unexpected header length!')
        
        try:
            obj = cls(
                length = bs[0],
                port = bs[1],
                sequence_number = unpack_uint16(bs[2:4]),
                destination = bs[4],
                command_number = bs[5]
            )

            return obj
        except ValueError:
            cls.err(cls)

class SpacePacketFooter(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

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
        
        try:
            bs[0:2] = pack_uint16(self.hardware_id)
            if len(self.crc16_checksum) == 0:
                self.crc16_checksum = bytearray([0x00, 0x00])
            else:
                bs[2] = self.crc16_checksum[1]
                bs[3] = self.crc16_checksum[0]

            return bs
        except ValueError:
            self.err()
    
    @classmethod
    def from_bytes(cls, bs: bytearray):
        'Unpack space packet footer from a bytearray'
        if len(bs) != SPACE_PACKET_FOOTER_LENGTH:
            return ValueError('ERROR: Unexpected footer length')
        
        try:
            crc16_checksum = bytearray(2)
            crc16_checksum[0] = bs[3]
            crc16_checksum[1] = bs[2]

            obj = cls(
                hardware_id = unpack_uint16(bs[0:2]),
                crc16_checksum = crc16_checksum
            )

            return obj
        except ValueError:
            cls.err(cls)

class SpacePacket():
    def __init__(self, data: bytearray, header=None, footer=None):
        self.header = header or SpacePacketHeader()
        self.header.length = SPACE_PACKET_HEADER_LENGTH + len(data) + SPACE_PACKET_FOOTER_LENGTH
        self._data = data
        self.footer = footer or SpacePacketFooter()
        self.footer.crc16_checksum = crc16_maxim(self.to_bytes())
        
    @property
    def data(self):
        'Protects data from being modified after instance call'
        return self._data

    def verify_crc16(self):
        'Compares expected CRC of packet to computed CRC'
        got = self.footer.crc16_checksum
        #got = crc16_maxim(self.data)
        #got = crc16_maxim(self.header.to_bytes()+self.data) + crc16_maxim(self.footer.to_bytes()[0:2])
        #got = self.footer.crc16_checksum
        got = crc16_maxim(self.header.to_bytes()+self.data+self.footer.to_bytes())
        want = crc16_maxim(self.to_bytes())

        if got[0] != want[0] or got[1] != want[1]:
            return TypeError(f'ERROR: Checksum mismatch! got={got}, want = {want}')

    def err(self):
        'Throws an error if any parameters are out of bounds'
        if self.header.err() is not None:
            return self.header.err()
        if self.footer.err() is not None:
            return self.footer.err()
        if self.header.length != SPACE_PACKET_HEADER_LENGTH + len(self.data) + SPACE_PACKET_FOOTER_LENGTH:
            return ValueError('ERROR: Packet length unequal to header length!')
        if self.verify_crc16() is not None:
            return self.verify_crc16()
        return None
    
    def to_bytes(self):
        'Encodes space packet to byte slice, including header, data, and footer'
        buf = bytearray(self.header.length)

        try:
            buf = self.header.to_bytes()
            buf[SPACE_PACKET_HEADER_LENGTH:] = self.data
            buf[SPACE_PACKET_HEADER_LENGTH+len(self.data):] = self.footer.to_bytes()
            return buf
        except ValueError:
            self.err()
    
    def from_bytes(self, bs: bytearray):
        'Hydrates the space packet from provided byte array, returning non-nil if errors are present'
        if len(bs) < SPACE_PACKET_HEADER_LENGTH:
            return ValueError('ERROR: Insufficient data!')
        
        try:
            hdr = self.header.from_bytes(bs[0:SPACE_PACKET_HEADER_LENGTH])
            ftr = self.footer.from_bytes(bs[len(bs)-SPACE_PACKET_FOOTER_LENGTH:])
            
            return SpacePacket(data=bs[SPACE_PACKET_HEADER_LENGTH : len(bs)-SPACE_PACKET_FOOTER_LENGTH], header=hdr, footer=ftr)
        except ValueError:
            self.err()