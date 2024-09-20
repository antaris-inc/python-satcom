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

    def test_packet_encode_and_decode(self):
        """Verifies CSP packet encode and decode"""
        ph = csp_packet.CSPPacketHeader(
            priority=1,
            destination=2,
            destination_port=3,
            source=4,
            source_port=5
        )

        arg = csp_packet.CSPPacket(
            header = ph,
            data = bytearray(b'foobar')
        )

        got_bytes = arg.to_bytes()
        pkt = csp_packet.CSPPacket(got_bytes)

        got = pkt.from_bytes(got_bytes)
        want = arg

        self.assertIsNone(got.err(), msg=f'got={got.header.destination}, error:{got.err()}')
        self.assertEqual(got, want, f'unexpected result: want={want} got={got}')
