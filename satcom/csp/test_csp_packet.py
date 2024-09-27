import unittest
from satcom.csp import csp_packet

class TestCSPPacket(unittest.TestCase):

    def test_packet_header_encode(self):
        """Verifies CSP PacketHeader conversion to bytes"""
        ph = csp_packet.CSPPacketHeader(
            priority=2,
            destination=24,
            destination_port=1,
            source=10,
            source_port=63
        )
        want = bytearray([0x95, 0x80, 0x7F, 0x00])
        got = ph.to_bytes()

        self.assertIsNone(ph.err(), msg = ph.err())
        self.assertEqual(got, want, f'unexpected result: want={want} got={got}')

    def test_packet_header_decode(self):
        """Verifies CSP PacktHeader byte decode"""
        hdr = bytearray([0x95, 0x80, 0x5C, 0x00])

        want = csp_packet.CSPPacketHeader(
            priority=2,
            destination=24,
            destination_port=1,
            source=10,
            source_port=28
        )
        got = csp_packet.CSPPacketHeader.from_bytes(hdr)

        self.assertIsNone(got.err(), msg=got.err())
        self.assertEqual(got, want, f'unexpected result: want={want} got={got}')

    def test_packet_decode_and_encode(self):
        """Verifies CSP packet encode and decode"""

        bs = bytearray([0x48, 0x20, 0xC5, 0x00, 0x66, 0x6F, 0x6F, 0x62, 0x61, 0x72])
        pkt = csp_packet.CSPPacket.from_bytes(bs)

        got = pkt.to_bytes()

        want = bytearray(b'H \xc5\x00foobar')

        self.assertIsNone(pkt.err(), msg=pkt.err())
        self.assertEqual(got, want, f'unexpected result: want={want} got={got}')