import unittest
import satcom.openlst.space_packet_lib as space_pkt_lib

class TestSpacePacket(unittest.TestCase):

    def test_space_packet_header_encode(self):
        """Verifies ClientPacketHeader conversion to bytes"""
        ph = space_pkt_lib.SpacePacketHeader(
            length=27,
            port=0,
            sequence_number=1134,
            destination=23,
            command_number=132
        )
        want = bytes([0x1B, 0x00, 0x6E, 0x04, 0x17, 0x84])
        got = ph.to_bytes()

        self.assertIsNone(ph.err())
        self.assertEqual(got, want, f'unexpected result: want={want} got={got}')

    def test_space_packet_header_decode(self):
        """Verifies SpacePacketHeader byte decode"""
        hdr = bytes([0x0D, 0x01, 0x04, 0x00, 0xFD, 0x38])

        want = space_pkt_lib.SpacePacketHeader(
            length=13,
            port=1,
            sequence_number=4,
            destination=253,
            command_number=56
        )
        got = space_pkt_lib.SpacePacketHeader.from_bytes(hdr)

        self.assertIsNone(got.err(), msg=got.err())
        self.assertEqual(got, want, f'unexpected result: want={want} got={got}')

    def test_space_packet_footer_encode(self):
        """Verifies SpacePacketFooter conversion to bytes"""
        pf = space_pkt_lib.SpacePacketFooter(
            hardware_id=2047,
            crc16_checksum=bytes([0x01, 0x02])
        )
        want = bytes([0xFF, 0x07, 0x02, 0x01])
        got = pf.to_bytes()

        self.assertIsNone(pf.err(), msg=pf.err())
        self.assertEqual(got, want, f'unexpected result: want={want} got={got}')

    def test_space_packet_footer_decode(self):
        """Verifies SpacePacketFooter byte decode"""
        ftr = bytes([0x0E, 0x01, 0x0B, 0x0A])

        want = space_pkt_lib.SpacePacketFooter(
            hardware_id=270,
            crc16_checksum=bytes([0x0A,0x0B])
        )
        got = space_pkt_lib.SpacePacketFooter.from_bytes(ftr)

        self.assertIsNone(got.err(), msg=got.err())
        self.assertEqual(got, want, f'unexpected result: want={want} got={got}')

    def test_new_space_packet_from_bytes_too_much_data(self):
        """Tests if new space packet is rejected due to too much data"""
        dat = bytes(1024)
        hdr = space_pkt_lib.SpacePacketHeader(
            port=1,
            sequence_number=4000,
            destination=253,
            command_number=56
        )
        ftr = space_pkt_lib.SpacePacketFooter(hardware_id=12)

        # Tests if a ValueError is raised when assembling the packet
        with self.assertRaises(ValueError):
            space_pkt_lib.SpacePacket(dat, hdr, ftr)

    def test_new_space_packet_to_bytes_success(self):
        """Verifies successful space packet creation"""
        dat = bytes([0x11, 0x22, 0x33])
        hdr = space_pkt_lib.SpacePacketHeader(
            port=1,
            sequence_number=4000,
            destination=253,
            command_number=56
        )
        ftr = space_pkt_lib.SpacePacketFooter(hardware_id=12)
        pkt = space_pkt_lib.SpacePacket(dat, hdr, ftr)

        want = bytes([
            0x0C, 0x01, 0xA0, 0x0F, 0xFD, 0x38, # packet header
            0x11, 0x22, 0x33, # original message
            0x0C, 0x00, 0xFA, 0x45 # packet footer
        ])
        got = pkt.to_bytes()

        self.assertIsNone(pkt.err(), msg=pkt.err())
        self.assertEqual(got, want, f'unexpected result: want={want} got={got}')

    def test_new_space_packet_from_bytes(self):
        """Validates succesful space frame encoding"""
        val = bytes([0x0D, 0xC0, 0x04, 0x00, 0xFD, 0x38, 0x01, 0x02, 0x03, 0xFF, 0x03, 0xBF, 0x04])
        p = space_pkt_lib.SpacePacket(val)
        pkt = p.from_bytes(val)

        want = bytes([0x01, 0x02, 0x03])
        got = pkt.data

        self.assertIsNone(pkt.err(), msg=pkt.err())
        self.assertEqual(got, want, f'unexpected result: want={want} got={got}')
