import utils
import unittest

class TestUtils(unittest.TestCase):

    def test_pack_little_endian(self):
        """Verifies that an int is packed into a bytearray with little endian mapping"""
        val = 4213

        want = bytearray([0x075, 0x10])
        got = utils.pack_uint16_little_endian(val)

        self.assertEqual(got, want, f'unexpected result: want={want} got={got}')

    def test_unpack_little_endian(self):
        """Verifies that a bytearray is correctly unpacked with little endian mapping"""
        bs = bytearray([0xFB, 0xCC])

        want = 52475
        got = utils.unpack_uint16_little_endian(bs)

        self.assertEqual(got, want, f'unexpected result: want={want} got={got}')

    def test_pack_big_endian(self):
        """Verifies that an int is packed into a bytearray with big endian mapping"""
        val = 8642

        want = bytearray([0x21, 0xC2])
        got = utils.pack_uint16_big_endian(val)

        self.assertEqual(got, want, f'unexpected result: want={want} got={got}')