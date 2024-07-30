### Imports ###

import openlst
import struct
import copy

### Global Variables ###
CLIENT_PACKET_ASM = [0x22, 0x69]
CLIENT_PACKET_HEADER_LENGTH = 7

### Create ClientPackerError Object ###

class ClientPacketError

### Create ClientPacketHeader Object ###

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
            return Exception('ERROR: Length must be 7-251')
        if self.hardware_id < 0 or self.hardware_id > 65535:
            return Exception('ERROR: HardwareID must be 0-65535')
        if self.sequence_number < 0 or self.sequence_number > 65535:
            return Exception('ERROR: SequenceNumber must be 0-65535')
        if self.destination < 0 or self.destination > 255:
            return Exception('ERROR: Destination must be 0-255')
        if self.command_number < 0 or self.command_number > 255:
            return Exception('ERROR: CommandNumber must be 0-255')
        return None
    
    def to_bytes(self):
        'Packs client packet header metadata into bytes'
        bs = [None]*CLIENT_PACKET_HEADER_LENGTH
        
        bs[0] = bytes(self.length)
        bs[1:3] = struct.pack('<H',self.hardware_id) # little endian, unsigned short
        bs[3:5] = struct.pack('<H',self.sequence_number)
        bs[5] = bytes(self.destination)
        bs[6] = bytes(self.command_number)

        return bs
    
    def from_bytes(self, bs):
        'Unpacks client packet header metadata from bytes'
        if len(bs) != CLIENT_PACKET_HEADER_LENGTH:
            return Exception('Unexpected header length!')
        
        self.length = int(bs[0])
        self.hardware_id = struct.unpack('<H',bs[1:3])
        self.sequence_number = struct.unpack('<H',bs[3:5])
        self.destination = int(bs[5])
        self.command_number = int(bs[6])

        return None
    
### Create ClientPacket Object ###

class ClientPacket:
    def __init__(self, data):
        ClientPacketHeader
        self.data = data

    def err(self):
        ''
        if self.ClientPacketHeader.err() != None:
            return Exception
        if self.ClientPacketHeader.length != CLIENT_PACKET_HEADER_LENGTH + len(self.data):
            return Exception('Packet length unequal to header length!')
        return None
    
    def to_bytes(self):
        'Packs client packet header and data into bytes'
        buf = [None]*CLIENT_PACKET_HEADER_LENGTH
        # Copy packed header bytes into buffer
        copy.copy(buf, self.ClientPacketHeader.to_bytes())
        # Copy data into buffer after header bytes
        copy.copy(buf[CLIENT_PACKET_HEADER_LENGTH:], self.data)

        return buf
    
    def from_bytes(self, bs):
        if len(bs) < CLIENT_PACKET_HEADER_LENGTH:
            return Exception('Insufficient data!')
        
        ph = ClientPacketHeader
        if ph.FromBytes(bs[0:CLIENT_PACKET_HEADER_LENGTH]) != None:
            return Exception
        
        self.ClientPacketHeader = ph
        self.data = bs[CLIENT_PACKET_HEADER_LENGTH:]

        return None
    
def NewClientPacket(hdr, dat):
    pkt = ClientPacket(hdr,dat)
    pkt.ClientPacketHeader.length = CLIENT_PACKET_HEADER_LENGTH + len(dat)
        

        

        
        
        
