#!/usr/bin/env python

import unittest

from cigarbox import bitops

class TestBitopsBitmap(unittest.TestCase):
    def setUp(self):
        self._map = bitops.Bitmap(100)

    def test_bitmap_isset(self):
        i = 10
        self._map.set(i)
        self.assertTrue(self._map.isset(i))

        i = 50
        self._map.set(i)
        self.assertTrue(self._map.isset(i))

        self.assertRaises(IndexError, self._map.isset, 100)
        self.assertRaises(IndexError, self._map.isset, 101)
        self.assertRaises(IndexError, self._map.isset, -1)

    def test_bitmap_set(self):
        i = 60
        self._map.set(i)
        self.assertTrue(self._map.isset(i))

        i = 99
        self._map.set(i)
        self.assertTrue(self._map.isset(i))

        self.assertRaises(IndexError, self._map.set, 100)
        self.assertRaises(IndexError, self._map.set, 101)
        self.assertRaises(IndexError, self._map.set, -1)

    def test_bitmap_clr(self):
        i = 14
        self._map.set(i)
        self.assertTrue(self._map.isset(i))
        self._map.clr(i)
        self.assertFalse(self._map.isset(i))

        i = 75
        self._map.set(i)
        self.assertTrue(self._map.isset(i))
        self._map.clr(i)
        self.assertFalse(self._map.isset(i))

        i = 89
        self._map.clr(i)
        self.assertFalse(self._map.isset(i))

        self.assertRaises(IndexError, self._map.clr, 100)
        self.assertRaises(IndexError, self._map.clr, 101)
        self.assertRaises(IndexError, self._map.clr, -1)


    def test_bitmap_nset(self):
        pass

    def test_bitmap_nclr(self):
        pass

    def test_bitmap_zero(self):
        pass

def suite():
    return unittest.TestLoader().loadTestsFromTestCase(TestBitopsBitmap)

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
