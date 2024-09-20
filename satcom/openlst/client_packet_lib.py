from pydantic import BaseModel
from satcom.utils import utils

CLIENT_PACKET_ASM = [0x22, 0x69]
CLIENT_PACKET_HEADER_LENGTH = 7

class ClientPacketHeader(BaseModel):
    length: int = 0
    hardware_id: int = 0
    sequence_number: int = 0
    destination: int = 0
    command_number: int = 0

    def err(self):
        """Throws an error if any params are out of bounds"""
        if self.length < 6 or self.length > 251:
            return ValueError('length must be 6-251')
        if self.hardware_id < 0 or self.hardware_id > 65535:
            return ValueError('hardware_id must be 0-65535')
        if self.sequence_number < 0 or self.sequence_number > 65535:
            return ValueError('sequence_number must be 0-65535')
        if self.destination < 0 or self.destination > 255:
            return ValueError('destination must be 0-255')
        if self.command_number < 0 or self.command_number > 255:
            return ValueError('command_number must be 0-255')
        return None

    def to_bytes(self):
        """Packs client packet header metadata into a bytearray"""
        bs = bytearray(CLIENT_PACKET_HEADER_LENGTH) # Create empty bytearray of header length  

        bs[0] = self.length
        bs[1:3] = utils.pack_ushort_little_endian(self.hardware_id)
        bs[3:5] = utils.pack_ushort_little_endian(self.sequence_number)
        bs[5] = self.destination
        bs[6] = self.command_number

        return bs

    @classmethod
    def from_bytes(cls, bs: bytearray):
        """Hydrates the client packet header metadata from a bytearray"""
        if len(bs) != CLIENT_PACKET_HEADER_LENGTH:
            raise ValueError('unexpected header length')
        
        obj = cls(
            length = bs[0],
            hardware_id = utils.unpack_ushort_little_endian(bs[1:3]),
            sequence_number = utils.unpack_ushort_little_endian(bs[3:5]),
            destination = bs[5],
            command_number = bs[6]
        )

        return obj

class ClientPacket():
    def __init__(self, data: bytearray, header=None):
        self.header = header or ClientPacketHeader()
        self.header.length = CLIENT_PACKET_HEADER_LENGTH + len(data) - 1
        self._data = data

    @property
    def data(self):
        """Protects data from being modified after instantiation"""
        return self._data

    def err(self):
        """Throws an error if any params are out of bounds"""
        if self.header.err() is not None:
            return self.header.err()
        if self.header.length != CLIENT_PACKET_HEADER_LENGTH + len(self.data) - 1:
            return ValueError('packet length unequal to header length')
        return None

    def to_bytes(self):
        """Encodes client packet and data into bytes"""
        buf = bytearray(CLIENT_PACKET_HEADER_LENGTH)
        buf[:CLIENT_PACKET_HEADER_LENGTH] = self.header.to_bytes()
        buf[0] += 1
        buf[CLIENT_PACKET_HEADER_LENGTH:] = self.data

        return buf

    @classmethod
    def from_bytes(cls, bs: bytearray):
        """Hydrates the client packet object from provided byte array"""
        if len(bs) < CLIENT_PACKET_HEADER_LENGTH:
            raise ValueError('insufficient data')

        hdr = ClientPacketHeader.from_bytes(bs[0:CLIENT_PACKET_HEADER_LENGTH])

        obj = cls(
            data = bs[CLIENT_PACKET_HEADER_LENGTH:],
            header = hdr
        )

        return obj
