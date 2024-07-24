import unittest

import satcom.example


class TestExample(unittest.TestCase):

    def test_sample_func(self):
        self.assertTrue(satcom.example.sample_func())
