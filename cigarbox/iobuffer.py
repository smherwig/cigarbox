#!/usr/bin/env python

import struct 

_EOF_READ_FMT = "can't read %d bytes from IOBuffer; buffer only has %d bytes left"

_EOF_WRITE_FMT = "can't write %d bytes to bounded (maxsize=%d) IOBuffer; buffer only has %d bytes available"

class IOBuffer:
    def __init__(self, data=None, maxsize=-1):
        if data:
            self._a = bytearray(data)
        else:
            self._a = bytearray()
        self._i = 0
        self.maxsize = maxsize

    def __len__(self):
        return len(self._a)

    def clear(self):
        self._a = bytearray()
        self._i = 0

    def tell(self):
        return self._i

    def left(self):
        return len(self._a) - self._i

    def rewind(self):
        self._i = 0

    def seek(self, offset, whence=0):
        pass

    def truncate(self, size=None):
        pass

    def read(self, n):
        z = len(self._a)
        have = z - self._i
        m = min(n, have)
        newi = self._i + m
        s = self._a[self._i:newi]
        self._i = newi
        return s

    def read_u8(self):
        size = 1
        z = len(self._a)
        have = z - self._i
        if have < size:
            raise EOFError(_EOF_READ_FMT, size, have)
        newi = self._i + size
        s = self._a[self._i:newi]
        num = struct.unpack('>B', s)[0]
        self._i = newi
        return num

    def read_u16be(self):
        size = 2
        z = len(self._a)
        have = z - self._i
        if have < size:
            raise EOFError(_EOF_READ_FMT, size, have)
        newi = self._i + size
        s = self._a[self._i:newi]
        num = struct.unpack('>H', s)[0]
        self._i = newi
        return num

    def read_u32be(self):
        size = 4
        z = len(self._a)
        have = z - self._i
        if have < size:
            raise EOFError(_EOF_READ_FMT, size, have)
        newi = self._i + size
        s = self._a[self._i:newi]
        num = struct.unpack('>I', s)[0]
        self._i = newi
        return num

    def read_u64be(self):
        size = 8
        z = len(self._a)
        have = z - self._i
        if have < size:
            raise EOFError(_EOF_READ_FMT, size, have)
        newi = self._i + size
        s = self._a[self._i:newi]
        num = struct.unpack('>Q', s)[0]
        self._i = newi
        return num

    def read_u16le(self):
        size = 2
        z = len(self._a)
        have = z - self._i
        if have < size:
            raise EOFError(_EOF_READ_FMT, size, have)
        newi = self._i + size
        s = self._a[self._i:newi]
        num = struct.unpack('<H', s)[0]
        self._i = newi
        return num

    def read_u32le(self):
        size = 4
        z = len(self._a)
        have = z - self._i
        if have < size:
            raise EOFError(_EOF_READ_FMT, size, have)
        newi = self._i + size
        s = self._a[self._i:newi]
        num = struct.unpack('<I', s)[0]
        self._i = newi
        return num

    def read_u64le(self):
        size = 8
        z = len(self._a)
        have = z - self._i
        if have < size:
            raise EOFError(_EOF_READ_FMT, size, have)
        newi = self._i + size
        s = self._a[self._i:newi]
        num = struct.unpack('<Q', s)[0]
        self._i = newi
        return num

    def read_line(self):
        newi = self._a.find('\n', self._i)
        if newi == -1:
            raise
        s = self._a[self._i:newi]
        self._i = newi
        return s

    def write(self, s):
        size = len(s)
        newi = self._i + size
        if self.maxsize != -1 and newi > self.maxsize:
            raise EOFError(_EOF_WRITE_FMT, size, self.maxsize,
                    self.maxsize - self._i)
        self._a[self._i:newi] = s
        self._i = newi
        return size

    def write_u8(self):
        size = 1
        newi = self._i + size
        if self.maxsize != -1 and newi > self.maxsize:
            raise EOFError(_EOF_WRITE_FMT, size, self.maxsize,
                    self.maxsize - self._i)
        self._a[self._i:newi] = struct.pack('>B', i)
        self._i = newi
        return size

    def write_u16be(self, i):
        size = 2
        newi = self._i + size
        if self.maxsize != -1 and newi > self.maxsize:
            raise EOFError(_EOF_WRITE_FMT, size, self.maxsize,
                    self.maxsize - self._i)
        self._a[self._i:newi] = struct.pack('>H', i)
        self._i = newi
        return size

    def write_u32be(self, i):
        size = 4
        newi = self._i + size
        if self.maxsize != -1 and newi > self.maxsize:
            raise EOFError(_EOF_WRITE_FMT, size, self.maxsize,
                    self.maxsize - self._i)
        self._a[self._i:newi] = struct.pack('>I', i)
        self._i = newi
        return size

    def write_u64be(self, i):
        size = 8
        newi = self._i + size
        if self.maxsize != -1 and newi > self.maxsize:
            raise EOFError(_EOF_WRITE_FMT, size, self.maxsize,
                    self.maxsize - self._i)
        self._a[self._i:newi] = struct.pack('>Q', i)
        self._i = newi
        return size

    def write_u16le(self, i):
        size = 2
        newi = self._i + size
        if self.maxsize != -1 and newi > self.maxsize:
            raise EOFError(_EOF_WRITE_FMT, size, self.maxsize,
                    self.maxsize - self._i)
        self._a[self._i:newi] = struct.pack('<H', i)
        self._i = newi
        return size

    def write_u32le(self, i):
        size = 4
        newi = self._i + size
        if self.maxsize != -1 and newi > self.maxsize:
            raise EOFError(_EOF_WRITE_FMT, size, self.maxsize,
                    self.maxsize - self._i)
        self._a[self._i:newi] = struct.pack('<I', i)
        self._i = newi
        return size

    def write_u64le(self, i):
        size = 8
        newi = self._i + size
        if self.maxsize != -1 and newi > self.maxsize:
            raise EOFError(_EOF_WRITE_FMT, size, self.maxsize,
                    self.maxsize - self._i)
        self._a[self._i:newi] = struct.pack('<Q', i)
        self._i = newi
        return size

    def printf(self, fmt, *args):
        s = fmt % args
        size = len(s)
        newi = self._i + size
        if self.maxsize != -1 and newi > self.maxsize:
            raise EOFError(_EOF_WRITE_FMT, size, self.maxsize,
                    self.maxsize - self._i)
        self._a[self._i:newi] = s
        self._i = newi
        return size

    def write_pack(self, fmt, *args):
        s = struct.pack(fmt, *args)
        size = len(s)
        newi = self._i + size
        if self.maxsize != -1 and newi > self.maxsize:
            raise EOFError(_EOF_WRITE_FMT, size, self.maxsize,
                    self.maxsize - self._i)
        self._a[self._i:newi] = s
        self._i = newi
        return size

if __name__ == '__main__':
    b = IOBuffer()
    b.write_u32be(54)
    b.write('Hello, World!')
    b.write_u16be(76)
    b.rewind()
    print b.read_u32be()
    print b.read(13)
    print b.read_u16be()
