import unittest
import satcom.openlst.fec as fec

class TestFEC(unittest.TestCase):

    def test_fec_chunk_encode(self):
        """Verifies FEC byte chunk encoding"""
        bs = bytearray(b'ihgfedcba')

        got = fec.encode_fec(bs)
        want = b'\xe2\xde\x8b\xdc\xa6\x9a3\x10\xe2V\x00 j\xde\xff#N2|\xd3\x04\x03\x04\x0e'

        self.assertEqual(got, want, f'unexpected result: want={want} got={got}')

    def test_fec_chunk_decode(self):
        """Verifies FEC byte chunk decoding"""
        bs = bytearray(b'*j\x03\x00J=L\xe2\x04\x03\x04\x0e')
        # create decoder
        gen = fec.decode_fec_chunk()
        gen.send(None)

        # decode 4 byte chunks
        chunk0 = gen.send(bs[0:4])
        chunk1 = gen.send(bs[4:8])
        chunk2 = gen.send(bs[8:12])

        got = chunk0 + chunk1 + chunk2
        want = bytearray(b'fec')
        self.assertEqual(got, want, f'unexpected result: want={want} got={got}')