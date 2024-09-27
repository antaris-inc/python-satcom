from io import BytesIO
from pydantic import BaseModel
from satcom.utils import utils

HEADER_LENGTH_BYTES = 4
# field lengths (# bits)
FLEN_PRIO  = 2
FLEN_ADDR  = 5
FLEN_PORT  = 6
FLEN_FLAGS = 8

class CSPPacketHeader(BaseModel):
    # 2 bits, conventionally
    # 0 (cricical), 1 (high), 2 (norm), 3 (low)
    priority: int = 0

    # 5 bits: 0 - 31
    destination: int = 0
    source: int = 0

    # 6 bits: 0 - 63
    destination_port: int = 0
    source_port: int = 0

    #flags: int = 0

    def err(self):
        """Throws an error if any params are out of bounds"""
        if self.priority < 0 or self.priority > 3:
            return ValueError('PacketHeader.priority must be 0-3')
        if self.destination < 0 or self.destination > 31:
            return ValueError('PacketHeader.destination must be 0-31')
        if self.source < 0 or self.source > 31:
            return ValueError('PacketHeader.source must be 0-31')
        if self.destination_port < 0 or self.destination_port > 63:
            return ValueError('PacketHeader.destination_port must be 0-63')
        if self.source_port < 0 or self.source_port > 63:
            return ValueError('PacketHeader.source_port must be 0-63')
        return None

    def to_bytes(self):
        """Packs CSP packet header metadata into a bytearray"""
        header = 0
        cursor = 0
        bitmask32 = 0xFFFFFFFF

        cursor += FLEN_PRIO
        header |= (self.priority << (32 - cursor)) & bitmask32

        cursor += FLEN_ADDR
        header |= (self.source << (32 - cursor)) & bitmask32

        cursor += FLEN_ADDR
        header |= (self.destination << (32 - cursor)) & bitmask32

        cursor += FLEN_PORT
        header |= (self.destination_port << (32 - cursor)) & bitmask32

        cursor += FLEN_PORT
        header |= (self.source_port << (32 - cursor)) & bitmask32

        cursor += FLEN_FLAGS
        header |= (0 << (32 - cursor)) & bitmask32

        bs = bytearray(HEADER_LENGTH_BYTES)
        bs = utils.pack_uint_big_endian(header)

        return bs

    @classmethod
    def from_bytes(cls, bs: bytearray):
        """Hydrates the CSP packet header metadata from a bytearray"""
        if len(bs) != HEADER_LENGTH_BYTES:
            raise ValueError('unexpected header length')

        hdr = utils.unpack_uint_big_endian(bs)
        offset = 0
        bitmask32 = 0xFFFFFFFF

        val = (hdr << offset) & bitmask32
        cls.priority = val >> (32 - FLEN_PRIO)
        offset += FLEN_PRIO

        val = (hdr << offset) & bitmask32
        cls.source = val >> (32 - FLEN_ADDR)
        offset += FLEN_ADDR

        val = (hdr << offset) & bitmask32
        cls.destination = val >> (32 - FLEN_ADDR)
        offset += FLEN_ADDR

        val = (hdr << offset) & bitmask32
        cls.destination_port = val >> (32 - FLEN_PORT)
        offset += FLEN_PORT

        val = (hdr << offset) & bitmask32
        cls.source_port = val >> (32 - FLEN_PORT)
        offset += FLEN_PORT

        # not implemented, so ignored
        val = (hdr << offset) & bitmask32
        _ = val >> (32 - FLEN_FLAGS)
        offset += FLEN_FLAGS

        obj = cls(
            priority = cls.priority,
            source = cls.source,
            destination = cls.destination,
            destination_port = cls.destination_port,
            source_port = cls.source_port
        )

        return obj
    
class CSPPacket():
    def __init__(self, data: bytearray, header=None):
        self.header = header or CSPPacketHeader()
        self._data = data

    @property
    def data(self):
        """Protects data from being modified after instantiation"""
        return self._data

    def err(self):
        """Throws an error if any params are out of bounds"""
        if self.header.err() is not None:
            return self.header.err()
        return None

    def _max_packet_length(self, max_data_size: int):
        """Returns the maximum possible packet size based on provided max data size"""
        return HEADER_LENGTH_BYTES + max_data_size

    def _make_buffer(self, max_data_size: int):
        """Initializes a new byte slice appropriate for a full CSP packet"""
        return bytearray(self._max_packet_length(max_data_size))

    def to_bytes(self):
        """Encodes CSP packet and data into bytes"""
        buf = self._make_buffer(len(self.data))
        buf[:HEADER_LENGTH_BYTES] = self.header.to_bytes()
        buf[HEADER_LENGTH_BYTES:] = self.data

        return buf

    @classmethod
    def from_bytes(cls, bs: bytearray):
        """Hydrates the CSP packet object from provided byte array"""
        if len(bs) < HEADER_LENGTH_BYTES:
            raise ValueError('insufficient data')

        hbs, dbs = bs[0:HEADER_LENGTH_BYTES], bs[HEADER_LENGTH_BYTES:]
        hdr = CSPPacketHeader.from_bytes(hbs)

        obj = cls(
            header = hdr,
            data = dbs
        )

        return obj

    def write_packet(self):
        """Writes n bytes to CSP packet"""
        enc = self.to_bytes()
        enc_len = len(enc)
        dst = BytesIO()

        n, err = dst.write(enc)

        if err is not None:
            return self.err()

        if n != enc_len:
            return ValueError(f'CSP wrote failed: want {enc_len} bytes, got {n}')

        return None

    def read_packet(self, buf: bytearray):
        """Reads CSP packet using supplied buffer"""
        src = BytesIO(buf)
        n, err = src.getvalue()

        if err is not None:
            return self.err()
        buf = buf[:n]

        return self.from_bytes(buf)