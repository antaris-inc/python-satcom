### Imports ###

import struct
import types

### Global Variables ###
CLIENT_PACKET_ASM = [0x22, 0x69]
CLIENT_PACKET_HEADER_LENGTH = 7

### Create ClientPacketHeader Class ###

class ClientPacketHeader:
    def __init__(self, length, hardware_id, sequence_number, destination, command_number):
        self.length = length
        self.hardware_id = hardware_id
        self.sequence_number = sequence_number
        self.destination = destination
        self.command_number = command_number

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
        
        bs[0] = self.length
        bs[1:3] = [i for i in struct.pack('<H', self.hardware_id)]
        bs[3:5] = [i for i in struct.pack('<H', self.sequence_number)]
        bs[5] = self.destination
        bs[6] = self.command_number

        return bs
    
    def from_bytes(self, bs: bytearray):
        'Hydrates the client packet header metadata from a bytearray'
        if len(bs) != CLIENT_PACKET_HEADER_LENGTH:
            return ValueError('Unexpected header length!')
        
        self.length = bs[0]
        self.hardware_id = struct.unpack('<H', bytes(bs[1:3]))[0] # convert int elements to bytes, then unpack
        self.sequence_number = struct.unpack('<H',bytes(bs[3:5]))[0]
        self.destination = bs[5]
        self.command_number = bs[6]

        return None
    
### Create ClientPacket Class ###

class ClientPacket(ClientPacketHeader):
    def __init__(self, length, hardware_id, sequence_number, destination, command_number, data: bytearray):
        ClientPacketHeader.__init__(self, length, hardware_id, sequence_number, destination, command_number)
        #self.header = ClientPacketHeader  
        self.data = data
        # super().__init__(length, hardware_id, sequence_number, destination, command_number)

    def err(self):
        'Throws an error if any params are out of bounds'
        if ClientPacketHeader.err(self) is not None:
            return ClientPacketHeader.err(self)
        if self.length != CLIENT_PACKET_HEADER_LENGTH + len(self.data):
            return ValueError('ERROR: Packet length unequal to header length!')
        return None
    
    def to_bytes(self):
        'Encodes client packet header and data into bytes'
        buf = bytearray(CLIENT_PACKET_HEADER_LENGTH)
        # Copy packed header bytes into buffer
        buf = ClientPacketHeader.to_bytes(self).copy()
        # Copy data into buffer after header bytes
        buf[CLIENT_PACKET_HEADER_LENGTH:] = self.data.copy()

        return buf
    
    def from_bytes(self, bs: bytearray):
        'Hydrates the client packet object from provided byte array'
        if len(bs) < CLIENT_PACKET_HEADER_LENGTH:
            return ValueError('ERROR: Insufficient data!')
        
        #cph = ClientPacketHeader()
        if ClientPacketHeader.from_bytes(self, bs[0:CLIENT_PACKET_HEADER_LENGTH]) is not None:
            return ValueError
        
        self.header = ClientPacketHeader
        self.data = bs[CLIENT_PACKET_HEADER_LENGTH:]

        return None
    
def new_client_packet(hardware_id, sequence_number, destination, command_number, dat: bytearray):
    '''Construct new ClientPacket using provided header and data inputs, and determines its length'''
    pkt = ClientPacket(None, hardware_id, sequence_number, destination, command_number, dat)

    pkt.length = CLIENT_PACKET_HEADER_LENGTH + len(dat)
    
    #consider deep copy?
    return pkt

        

        
        
        
