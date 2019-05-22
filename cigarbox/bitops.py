import array

#
#   i >> 3 is the same as i / 8
#   i & 7 is the same as i % 8
# 
#   1000000
# 
#
#                       1 1 1 1 1 1   1 1 1 1 2 2 2 2
# 0 1 2 3 4 5 6 7 | 8 9 0 1 2 3 4 5 | 6 7 8 9 0 1 2 3
#
#
#   isset(9)

_INDEX_ERR_FMT = 'invalid bit index (%d) for BitMap(nbits=%d)'

class Bitmap:
    def __init__(self, nbits):
        x = nbits / 8 
        y = nbits % 8 
        if y != 0:
            x = x +1
        self._nbits = nbits
        self._a = array.array('B', [0 for i in xrange(x)])

    def isset(self, i):
        if i >= self._nbits or i < 0:
            raise IndexError(_INDEX_ERR_FMT % (i, self._nbits))
        x = i >> 3  
        y = 0x80 >> (i & 7)
        return bool(self._a[x] & y)

    def set(self, i):
        if i >= self._nbits or i < 0:
            raise IndexError(_INDEX_ERR_FMT % (i, self._nbits))
        x = i >> 3  
        y = 0x80 >> (i & 7)
        self._a[x] |= y

    def clr(self, i):
        if i >= self._nbits or i < 0:
            raise IndexError(_INDEX_ERR_FMT % (i, self._nbits))
        x = i >> 3  
        y = ~(0x80 >> (i & 7))
        self._a[x] &= y

    def nset(self, start, stop):
        if start < 0 or start >= self._nbits or stop < 0 or stop >= self._nbits:
            raise IndexError(_INDEX_ERR_FMT % (i, self._nbits))
        if start > stop:
            raise ValueError('start bit index (%d) greater than stop index (%d)' %
                    (start, stop))
        for i in xrange(start, stop+1):
            x = i >> 3  
            y = 0x80 >> (i & 7)
            self._a[x] |= y

    def nclr(self, start, stop):
        if start < 0 or start >= self._nbits or stop < 0 or stop >= self._nbits:
            raise IndexError(_INDEX_ERR_FMT % (i, self._nbits))
        if start > stop:
            raise ValueError('start bit index (%d) greater than stop index (%d)' %
                    (start, stop))
        for i in xrange(start, stop+1):
            x = i >> 3  
            y = ~(0x80 >> (i & 7))
            self._a[x] &= y

    def zero(self):
        for i in len(xrange(self._a)):
            self._a[i] = 0

    def ffs(self):
        pass

    def fls(self):
        pass

    def ffc(self):
        pass

    def flc(self):
        pass

def isset(n, i):
    pass

def ffs_u32(n):
    pass

def fls_u32(n):
    pass

def ffc_u32(n):
    pass

def flc_u32(n):
    pass

def ffs_u64(n):
    pass

def fls_u32(n):
    pass

def ffc_u64(n):
    pass

def flc_u64(n):
    pass
