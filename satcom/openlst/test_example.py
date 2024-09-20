import unittest
import satcom.openlst.example


class TestExample(unittest.TestCase):

    def test_sample_func(self):
        self.assertTrue(satcom.openlst.example.sample_func())
