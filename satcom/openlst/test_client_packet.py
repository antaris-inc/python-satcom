import unittest
import satcom.openlst.client_packet_lib as client_pkt_lib

class TestClientPacket(unittest.TestCase):

    def test_client_packet_header_encode(self):
        """Verifies ClientPacketHeader conversion to bytes"""
        ph = client_pkt_lib.ClientPacketHeader(
            length=10,
            hardware_id=755,
            sequence_number=12,
            destination=212,
            command_number=57
        )
        want = bytearray([0x0A, 0xF3, 0x02, 0x0C, 0x00, 0xD4, 0x39])
        got = ph.to_bytes()

        self.assertIsNone(ph.err(), msg = ph.err())
        self.assertEqual(got, want, f'unexpected result: want={want} got={got}')

    def test_client_packet_header_decode(self):
        """Verifies ClientPacktHeader byte decode"""
        hdr = bytearray([0x0D, 0xFF, 0x03, 0x04, 0x00, 0xFD, 0x38])

        want = client_pkt_lib.ClientPacketHeader(
            length=13,
            hardware_id=1023,
            sequence_number=4,
            destination=253,
            command_number=56
        )
        got = client_pkt_lib.ClientPacketHeader.from_bytes(hdr)

        self.assertIsNone(got.err(), msg=got.err())
        self.assertEqual(got, want, f'unexpected result: want={want} got={got}')

    def test_new_client_packet_to_bytes_small_frame(self):
        """Test new client packet creation with a small dataframe"""
        dat = bytearray([0x0A, 0x0B, 0x0C, 0x0D])
        hdr = client_pkt_lib.ClientPacketHeader(
            hardware_id=1023,
            sequence_number=1,
            destination=253,
            command_number=56
        )
        pkt = client_pkt_lib.ClientPacket(dat, hdr)

        want = bytearray([0x0B, 0xFF, 0x03, 0x01, 0x00, 0xFD, 0x38, 0x0A, 0x0B, 0x0C, 0x0D])
        got = pkt.to_bytes()

        self.assertIsNone(pkt.err(), msg=pkt.err())
        self.assertEqual(got, want, f'unexpected result: want={want} got={got}')

    def test_new_client_packet_from_bytes_too_much_data(self):
        """Tests if new client packet is rejected due to too much data"""
        dat = bytearray(1024)
        hdr = client_pkt_lib.ClientPacketHeader(
            hardware_id=1023,
            sequence_number=1,
            destination=253,
            command_number=56
        )
        pkt = client_pkt_lib.ClientPacket(dat, hdr)

        self.assertIsNotNone(pkt.err(), 'expected an error, but did not manifest')

    def test_client_packet_from_bytes_small_frame(self):
        """Verifies that client packet structure is preserved when passing a small frame"""
        val = bytearray([0x0A, 0xFF, 0x03, 0x04, 0x00, 0xFD, 0x38, 0x01, 0x02, 0x03])
        p = client_pkt_lib.ClientPacket(val)
        pkt = p.from_bytes(val)

        want = bytearray([0x01, 0x02, 0x03])
        got = pkt.data

        self.assertIsNone(pkt.err(), msg=pkt.err())
        self.assertEqual(got, want, f'unexpected result: want={want} got={got}')

    def test_client_packet_from_bytes_empty_frame(self):
        """Verifies expected client packet behavior for no data"""
        val = bytearray([0x0A, 0xFF, 0x03, 0x04, 0x00, 0xFD, 0x38])
        p = client_pkt_lib.ClientPacket(val)
        pkt = p.from_bytes(val)

        #self.assertIsNone(pkt.err(), msg=pkt.err())
        self.assertIsNone(pkt.err(), msg=f'{pkt.header.length}')
        self.assertEqual(len(pkt.data), 0, f'expected empty result, got {pkt.data}')
