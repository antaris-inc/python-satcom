from pydantic import BaseModel

from satcom.utils import utils


SPACE_PACKET_PREAMBLE = bytes([0xAA, 0xAA, 0xAA, 0xAA])
SPACE_PACKET_ASM = bytes([0xD3, 0x91, 0xD3, 0x91])

SPACE_PACKET_HEADER_LENGTH = 6
SPACE_PACKET_FOOTER_LENGTH = 4


class SpacePacketHeader(BaseModel):
    length: int = 0
    port: int = 0
    sequence_number:  int = 0
    destination:  int = 0
    command_number: int = 0

    def err(self):
        """Throws an error if any params are out of bounds"""
        if self.length < 10 or self.length > 254:
            return ValueError('length must be 10-254')
        if self.sequence_number < 0 or self.sequence_number > 65535:
            return ValueError('sequence_number must be 0-65535')
        if self.destination < 0 or self.destination > 255:
            return ValueError('destination must be 0-255')
        if self.command_number < 0 or self.command_number > 255:
            return ValueError('command_number must be 0-255')
        return None

    def to_bytes(self) -> bytes:
        """Packs space packet header metadata into bytes"""
        bs = bytearray(SPACE_PACKET_HEADER_LENGTH)

        bs[0] = self.length
        bs[1] = self.port
        bs[2:4] = utils.pack_ushort_little_endian(self.sequence_number)
        bs[4] = self.destination
        bs[5] = self.command_number

        return bytes(bs)

    @classmethod
    def from_bytes(cls, bs: bytes):
        """Unpacks space packet header metadata from bytes"""
        if len(bs) != SPACE_PACKET_HEADER_LENGTH:
            raise ValueError('unexpected header length')

        obj = cls(
            length = bs[0],
            port = bs[1],
            sequence_number = utils.unpack_ushort_little_endian(bs[2:4]),
            destination = bs[4],
            command_number = bs[5]
        )

        return obj

class SpacePacketFooter(BaseModel):
    hardware_id: int = 0
    crc16_checksum: bytes = []

    def err(self):
        """Throws an error if any fields are out of bounds"""
        if self.hardware_id < 0 or self.hardware_id > 65535:
            return ValueError('hardware_id must be 0-65535')
        if len(self.crc16_checksum) != 2:
            return ValueError('crc16_checksum set incorrectly.')
        return None

    def to_bytes(self) -> bytes:
        """Packs space packet footer metadata into bytes"""
        bs = bytearray(SPACE_PACKET_FOOTER_LENGTH)

        bs[0:2] = utils.pack_ushort_little_endian(self.hardware_id)

        if len(self.crc16_checksum) != 0:
            # big to little endian mapping
            bs[2] = self.crc16_checksum[1]
            bs[3] = self.crc16_checksum[0]

        return bytes(bs)

    @classmethod
    def from_bytes(cls, bs: bytes):
        """Unpack space packet footer from bytes"""
        if len(bs) != SPACE_PACKET_FOOTER_LENGTH:
            return ValueError('unexpected footer length')

        crc16_checksum = bytearray(2)
        # little to big endian mapping
        crc16_checksum[0] = bs[3]
        crc16_checksum[1] = bs[2]

        obj = cls(
            hardware_id = utils.unpack_ushort_little_endian(bs[0:2]),
            crc16_checksum = bytes(crc16_checksum)
        )

        return obj

class SpacePacket():
    def __init__(self, data: bytes, header=None, footer=None):
        self.header = header or SpacePacketHeader()
        self.header.length = SPACE_PACKET_HEADER_LENGTH + len(data) + SPACE_PACKET_FOOTER_LENGTH - 1
        self._data = data
        self.footer = footer or SpacePacketFooter()
        self.footer.crc16_checksum = self._make_packet_checksum()

    @property
    def data(self):
        """Protects data from being modified after instantiation"""
        return self._data

    def _verify_crc16(self):
        """Compares expected CRC of packet to computed CRC"""
        got = self.footer.crc16_checksum
        want = self._make_packet_checksum()

        if got[0] != want[0] or got[1] != want[1]:
            return ValueError(f'checksum mismatch: got={got} want={want}')

    def _make_packet_checksum(self) -> bytes:
        """Creates checksum of packet from candidate bytes"""
        bs = self.to_bytes()
        inp = bs[0:len(bs)-2]

        # Evaluate checksum
        ck = 0xFFFF
        for b in inp:
            for _ in range(0,8):
                if (((ck & 0x8000) >> 8) ^ (b & 0x80)) > 0:
                    ck = (ck << 1) ^ 0x8005
                else:
                    ck = ck << 1
                b = b << 1
        ck = ck & 0xFFFF

        ckb = bytes(utils.pack_ushort_big_endian(ck))

        return ckb

    def err(self):
        """Throws an error if any parameters are out of bounds"""
        if self.header.err() is not None:
            return self.header.err()
        if self.footer.err() is not None:
            return self.footer.err()
        if self.header.length != SPACE_PACKET_HEADER_LENGTH + len(self.data) + SPACE_PACKET_FOOTER_LENGTH - 1:
            return ValueError('packet length unequal to header length')
        if self._verify_crc16() is not None:
            return self._verify_crc16()
        return None

    def to_bytes(self) -> bytes:
        """Encodes space packet to byte slice, including header, data, and footer"""
        buf = bytearray(self.header.length)

        buf[:SPACE_PACKET_HEADER_LENGTH] = self.header.to_bytes()
        buf[SPACE_PACKET_HEADER_LENGTH:] = self.data
        buf[SPACE_PACKET_HEADER_LENGTH+len(self.data):] = self.footer.to_bytes()
        return bytes(buf)

    @classmethod
    def from_bytes(cls, bs: bytes):
        """Hydrates the space packet from provided byte array, returning non-nil if errors are present"""
        if len(bs) < SPACE_PACKET_HEADER_LENGTH:
            return ValueError('insufficient data')

        hdr = SpacePacketHeader.from_bytes(bs[0:SPACE_PACKET_HEADER_LENGTH])
        ftr = SpacePacketFooter.from_bytes(bs[len(bs)-SPACE_PACKET_FOOTER_LENGTH:])

        obj = cls(
            data=bs[SPACE_PACKET_HEADER_LENGTH : len(bs)-SPACE_PACKET_FOOTER_LENGTH],
            header=hdr,
            footer=ftr
        )

        return obj
