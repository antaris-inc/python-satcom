import unittest
import satcom.openlst.whitening as whitening

class TestWhitening(unittest.TestCase):

    def test_whitening(self):
        """Validates data whitening"""
        bs = bytes(b'foobar')
        gen = whitening.pn9()

        got = whitening.whiten(bs, gen)
        want = b'\x99\x8er\xf8\x8c\xf7'

        self.assertEqual(got, want, f'unexpected result: want={want} got={got}')