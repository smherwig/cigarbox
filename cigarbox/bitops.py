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

_INDEX_ERR_FMT = 'invalid bit index (%d) for BitMap(nbits=%d, resizeable=%s)'

class Bitmap(object):
    def __init__(self, nbits=64, resizeable=True):
        x = nbits / 8 
        y = nbits % 8 
        if y:
            x += 1
        self._nbits = nbits
        self._resizeable = resizeable
        self._a = array.array('B', [0 for i in xrange(x)])

    def _resize(self, nbits):
        self._nbits = nbits
        x = nbits / 8 
        y = nbits % 8 
        if y:
            x += 1
        need = x - len(self._a)
        if need > 0:
            self._a.extend([0 for i in xrange(need)])

    def _check_arg(self, i):
        if i < 0:
            raise IndexError(_INDEX_ERR_FMT %
                    (i, self._nbits, self._resizeable))

        if i >= self._nbits:
            if not self._resizeable:
                raise IndexError(_INDEX_ERR_FMT %
                        (i, self._nbits, self._resizeable))
            else:
                self._resize(i+1)

    def _is_set(self, i):
        x = i >> 3  
        y = 0x80 >> (i & 7)
        return bool(self._a[x] & y)

    def is_set(self, i):
        if i >= self._nbits or i < 0:
            raise IndexError(_INDEX_ERR_FMT % (i, self._nbits))
        return self._is_set(i)

    def set(self, i):
        self._check_arg(i)
        x = i >> 3  
        y = 0x80 >> (i & 7)
        self._a[x] |= y

    def clr(self, i):
        self._check_arg(i)
        x = i >> 3  
        y = ~(0x80 >> (i & 7))
        self._a[x] &= y

    def zero(self):
        for i in len(xrange(self._a)):
            self._a[i] = 0

    def ffs(self):
        for i in xrange(0, self._nbits):
            if self._is_set(i):
                return i
        return -1

    def fls(self):
        for i in xrange(self._nbits-1, -1, -1):
            if self._is_set(i):
                return i
        return -1

    def ffc(self):
        for i in xrange(0, self._nbits):
            if not self._is_set(i):
                return i
        if self._resizeable:
            self._resize(self._nbits + 1)
            return self._nbits - 1
        else:
            return -1

    def flc(self):
        for i in xrange(self._nbits-1, -1, -1):
            if not self._is_set(i):
                return i
        if self._resizeable:
            self._resize(self._nbits + 1)
            return self._nbits - 1
        else:
            return -1
