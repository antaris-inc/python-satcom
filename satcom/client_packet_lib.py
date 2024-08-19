### Imports ###
import struct
from pydantic import BaseModel, ConfigDict

### Global Variables ###
CLIENT_PACKET_ASM = [0x22, 0x69]
CLIENT_PACKET_HEADER_LENGTH = 7

def pack_uint16(u):
    'Helper to pack uint16 into packet header'
    return bytearray(struct.pack('<H', u)) # little endian, unsigned short

def unpack_uint16(b):
    'Helper to extract uint16 from header bytearray'
    return struct.unpack('<H', bytes(b))[0] # little endian, unsigned short

class ClientPacketHeader(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    length: int = 0
    hardware_id: int = 0
    sequence_number: int = 0
    destination: int = 0
    command_number: int = 0

    def err(self):
        'Throws an error if any params are out of bounds'
        if self.length < 7 or self.length > 251:
            return ValueError('ERROR: Length must be 7-251')
        if self.hardware_id < 0 or self.hardware_id > 65535:
            return ValueError('ERROR: HardwareID must be 0-65535')
        if self.sequence_number < 0 or self.sequence_number > 65535:
            return ValueError('ERROR: SequenceNumber must be 0-65535')
        if self.destination < 0 or self.destination > 255:
            return ValueError('ERROR: Destination must be 0-255')
        if self.command_number < 0 or self.command_number > 255:
            return ValueError('ERROR: CommandNumber must be 0-255')
        return None
    
    def to_bytes(self):
        'Packs client packet header metadata into a bytearray'
        bs = bytearray(CLIENT_PACKET_HEADER_LENGTH) # Create empty bytearray of header length
        
        try:
            bs[0] = self.length
            bs[1:3] = pack_uint16(self.hardware_id)
            bs[3:5] = pack_uint16(self.sequence_number)
            bs[5] = self.destination
            bs[6] = self.command_number

            return bs
        except ValueError:
            self.err()
    
    @classmethod
    def from_bytes(cls, bs: bytearray):
        'Hydrates the client packet header metadata from a bytearray'
        if len(bs) != CLIENT_PACKET_HEADER_LENGTH:
            raise ValueError('Unexpected header length!')
        
        try:
            obj = cls(
                length = bs[0],
                hardware_id = unpack_uint16(bs[1:3]),
                sequence_number = unpack_uint16(bs[3:5]),
                destination = bs[5],
                command_number = bs[6]
            )

            return obj
        except ValueError:
            cls.err(cls)

class ClientPacket():
    def __init__(self, data: bytearray, header=None):
        self.header = header or ClientPacketHeader()
        self.header.length = CLIENT_PACKET_HEADER_LENGTH + len(data)
        self._data = data

    @property
    def data(self):
        'Protects data from being modified after instance call'
        return self._data

    def err(self):
        'Throws an error if any params are out of bounds'
        if self.header.err() is not None:
            return self.header.err()
        if self.header.length != CLIENT_PACKET_HEADER_LENGTH + len(self.data):
            return ValueError('ERROR: Packet length unequal to header length!')
        return None
    
    def to_bytes(self):
        'Encodes client packet header and data into bytes'
        try:
            buf = bytearray(CLIENT_PACKET_HEADER_LENGTH)
            buf = self.header.to_bytes()
            buf[CLIENT_PACKET_HEADER_LENGTH:] = self.data

            return buf
        except ValueError:
            self.err()  
    
    def from_bytes(self, bs: bytearray):
        'Hydrates the client packet object from provided byte array'
        if len(bs) < CLIENT_PACKET_HEADER_LENGTH:
            raise ValueError('ERROR: Insufficient data!')
        
        try:
            hdr = self.header.from_bytes(bs[0:CLIENT_PACKET_HEADER_LENGTH])
    
            return ClientPacket(data=bs[CLIENT_PACKET_HEADER_LENGTH:], header=hdr)
        except ValueError:
            self.err()
        

        
        
        
