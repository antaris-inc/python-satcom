import utils
from pydantic import BaseModel, ConfigDict

SPACE_PACKET_PREAMBLE = [0xAA, 0xAA, 0xAA, 0xAA]
SPACE_PACKET_ASM = [0xD3, 0x91, 0xD3, 0x91]
SPACE_PACKET_HEADER_LENGTH = 6
SPACE_PACKET_FOOTER_LENGTH = 4
PORT_IDS = (0,1)

def crc16(data: bytes) -> int:
    """Calculate the CRC-16 (in the manner of the CC1110) of data"""
    crc = 0xFFFF
    for i in data:
        for _ in range(0, 8):
            if ((crc & 0x8000) >> 8) ^ (i & 0x80):
                crc =(crc << 1) ^ 0x8005
            else:
                crc = crc << 1
            i = i << 1
    return crc & 0xFFFF

class SpacePacketHeader(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    length: int = 0
    port: int = 0
    sequence_number:  int = 0
    destination:  int = 0
    command_number: int = 0

    def err(self):
        """Throws an error if any params are out of bounds"""
        if self.length < 10 or self.length > 251:
            return ValueError('length must be 10-251')
        if self.port not in PORT_IDS:
            return ValueError('port must be 0 or 1')
        if self.sequence_number < 0 or self.sequence_number > 65535:
            return ValueError('sequence_number must be 0-65535')
        if self.destination < 0 or self.destination > 255:
            return ValueError('destination must be 0-255')
        if self.command_number < 0 or self.command_number > 255:
            return ValueError('command_number must be 0-255')
        return None

    def to_bytes(self) -> bytearray:
        """Packs space packet header metadata into a bytearray"""
        bs = bytearray(SPACE_PACKET_HEADER_LENGTH)

        bs[0] = self.length
        bs[1] = self.port
        bs[2:4] = utils.pack_uint16(self.sequence_number)
        bs[4] = self.destination
        bs[5] = self.command_number

        return bs

    @classmethod
    def from_bytes(cls, bs: bytearray):
        """Unpacks space packet header metadata from bytes"""
        if len(bs) != SPACE_PACKET_HEADER_LENGTH:
            raise ValueError('unexpected header length')

        obj = cls(
            length = bs[0],
            port = bs[1],
            sequence_number = utils.unpack_uint16(bs[2:4]),
            destination = bs[4],
            command_number = bs[5]
        )

        return obj

class SpacePacketFooter(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    hardware_id: int = 0
    crc16_checksum: bytearray = []

    def err(self):
        """Throws an error if any fields are out of bounds"""
        if self.hardware_id < 0 or self.hardware_id > 65535:
            return ValueError('hardware_id must be 0-65535')
        if len(self.crc16_checksum) != 2:
            return ValueError('crc16_checksum set incorrectly')
        return None

    def to_bytes(self) -> bytearray:
        """Packs space packet footer metadata into bytes"""
        bs = bytearray(SPACE_PACKET_FOOTER_LENGTH)

        bs[0:2] = utils.pack_uint16(self.hardware_id)
        self.crc16_checksum = bytearray(self.crc16_checksum)
        if len(self.crc16_checksum) == 0:
            self.crc16_checksum = bytearray([0x00, 0x00])
        else:
            bs[2] = self.crc16_checksum[1]
            bs[3] = self.crc16_checksum[0]

        return bs

    @classmethod
    def from_bytes(cls, bs: bytearray):
        """Unpack space packet footer from a bytearray"""
        if len(bs) != SPACE_PACKET_FOOTER_LENGTH:
            return ValueError('unexpected footer length')

        crc16_checksum = bytearray(2)
        crc16_checksum[0] = bs[3]
        crc16_checksum[1] = bs[2]

        obj = cls(
            hardware_id = utils.unpack_uint16(bs[0:2]),
            crc16_checksum = crc16_checksum
        )

        return obj

class SpacePacket():
    def __init__(self, data: bytearray, header=None, footer=None):
        self.header = header or SpacePacketHeader()
        self.header.length = SPACE_PACKET_HEADER_LENGTH + len(data) + SPACE_PACKET_FOOTER_LENGTH
        self._data = data
        self.footer = footer or SpacePacketFooter()
        self.footer.crc16_checksum = self.make_packet_checksum()

    @property
    def data(self):
        """Protects data from being modified after instance call"""
        return self._data

    def verify_crc16(self):
        """Compares expected CRC of packet to computed CRC"""
        #got = self.footer.crc16_checksum
        got = utils.pack_uint16(crc16(self.header.to_bytes() + self.data + bytes(12)))
        #want = crc16(self.to_bytes()) # this is evaluating with a crc placeholder of [0x00, 0x00]
        #want = self.to_bytes()[-2:]
        want = bytearray([0x3D, 0x7E])

        if got != want or got != want:
            return TypeError(f'checksum mismatch! got={got}, want={want}')
        
    def make_packet_checksum(self) -> int:
        """Creates checksum of packet from candidate bytes"""
        bs = self.to_bytes()
        inp = bs[1:len(bs)-2]
        
        return crc16(inp)

    def err(self):
        """Throws an error if any parameters are out of bounds"""
        if self.header.err() is not None:
            return self.header.err()
        if self.footer.err() is not None:
            return self.footer.err()
        if self.header.length != SPACE_PACKET_HEADER_LENGTH + len(self.data) + SPACE_PACKET_FOOTER_LENGTH:
            return ValueError('packet length unequal to header length')
        if self.verify_crc16() is not None:
            return self.verify_crc16()
        return None

    def to_bytes(self) -> bytearray:
        """Encodes space packet to byte slice, including header, data, and footer"""
        buf = bytearray(self.header.length)

        buf = self.header.to_bytes()
        buf[SPACE_PACKET_HEADER_LENGTH:] = self.data
        buf[SPACE_PACKET_HEADER_LENGTH+len(self.data):] = self.footer.to_bytes()

        return buf

    def from_bytes(self, bs: bytearray):
        """Hydrates the space packet from provided byte array, returning non-nil if errors are present"""
        if len(bs) < SPACE_PACKET_HEADER_LENGTH:
            return ValueError('insufficient data')

        hdr = self.header.from_bytes(bs[0:SPACE_PACKET_HEADER_LENGTH])
        ftr = self.footer.from_bytes(bs[len(bs)-SPACE_PACKET_FOOTER_LENGTH:])

        return SpacePacket(
            data=bs[SPACE_PACKET_HEADER_LENGTH : len(bs)-SPACE_PACKET_FOOTER_LENGTH],
            header=hdr,
            footer=ftr
        )