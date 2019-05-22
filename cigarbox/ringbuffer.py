#!/usr/bin/env python

_EOF_READ_FMT = "can't read %d bytes from RingBuffer; buffer only has %d unread bytes"
_EOF_WRITE_FMT = "can't write %d bytes to RingBuffer; buffer only has %d bytes available"

class RingBuffer:
    def __init__(self, size):
        self._size = size
        self._buf = bytearray('\x00' * size)
        self._w = 0  # index of next read
        self._r = 0  # index of next write
        self._u = 0  # number of unread bytes

    def _put(self, data):
        #print 'putting: %s' % binascii.hexlify(data)
        n = len(data)
        e = self._w  + n 
        if e <= self._size:
            self._buf[self._w:e] = data
        else:
            na = self._size - self._w
            nb = n - na
            self._buf[self._w:] = data[:na]
            self._buf[:nb] = data[na:]
        self._u += n
        self._w = e % self._size

    def avail_write(self):
        if self._w == self._r:
            if self._u == 0:
                n = self._size
            else:
                n = 0
        elif self._w > self._r:
            n = (self._size - self._w) +  self._r
        else:
            n = self._r - self._w
        return n

    def write(self, data):
        n = len(data)
        avail = self.avail_write()
        m = min(avail, n)
        if m > 0:
            self._put(data[:m])
        return m

    def write_u8(self, i):
        size = 1
        avail = self.avail_write()
        if avail < size:
            raise EOFError(EOF_WRITE_FMT, size, avail)
        s = struct.pack('>B', i)
        self._put(s)
        return size

    def write_u16be(self, i):
        size = 2
        avail = self.avail_write()
        if avail < size:
            raise EOFError(EOF_WRITE_FMT, size, avail)
        s = struct.pack('>H', i)
        self._put(s)
        return size

    def write_u32be(self, i):
        size = 4
        avail = self.avail_write()
        if avail < size:
            raise EOFError(EOF_WRITE_FMT, size, avail)
        s = struct.pack('>I', i)
        self._put(s)
        return size

    def write_u64be(self, i):
        size = 8
        avail = self.avail_write()
        if avail < size:
            raise EOFError(EOF_WRITE_FMT, size, avail)
        s = struct.pack('>Q', i)
        self._put(s)
        return size

    def write_u16le(self, i):
        size = 2
        avail = self.avail_write()
        if avail < size:
            raise EOFError(EOF_WRITE_FMT, size, avail)
        s = struct.pack('<H', i)
        self._put(s)
        return size

    def write_u32le(self, i):
        size = 4
        avail = self.avail_write()
        if avail < size:
            raise EOFError(EOF_WRITE_FMT, size, avail)
        s = struct.pack('<I', i)
        self._put(s)
        return size

    def write_u64le(self, i):
        size = 8
        avail = self.avail_write()
        if avail < size:
            raise EOFError(EOF_WRITE_FMT, size, avail)
        s = struct.pack('<Q', i)
        self._put(s)
        return size

    def _get(self, n, peek):
        #print 'getting %d' % n
        e = self._r + n
        if e <= self._size:
            data = self._buf[self._r:e]
        else:
            data = self._buf[self._r:]
            extra = n - (self._size - self._r)
            data += self._buf[:extra]
        if not peek:
            self._u -= n
            self._r = e % self._size
        return data

    def avail_read(self):
        if self._w == self._r:
            if self._u == 0:
                n = 0
            else:
                n = self._size
        elif self._w > self._r:
            n = self._w - self._r
        else:
            n = (self._size - self._r) + self._w
        return n

    def _read(self, n, peek=False):
        avail = self.avail_read()
        m = min(avail, n)
        data = ''
        if m > 0:
            data = self._get(m, peek)
        return data

    def read(self, n):
        return self._read(n)

    def peek(self, n):
        return self._read(n, peek=True)

    def read_u8(self):
        size = 1
        avail = self.avail_read()
        if avail < size:
            raise EOFError(_EOF_READ_FMT, size, have)
        s = self._read(size)
        num = struct.unpack('>B', s)[0]
        return num

    def read_u16be(self):
        size = 2
        avail = self.avail_read()
        if avail < size:
            raise EOFError(_EOF_READ_FMT, size, have)
        s = self._read(size)
        num = struct.unpack('>H', s)[0]
        return num

    def read_u32be(self):
        size = 4
        avail = self.avail_read()
        if avail < size:
            raise EOFError(_EOF_READ_FMT, size, have)
        s = self._read(size)
        num = struct.unpack('>I', s)[0]
        return num

    def read_u64be(self):
        size = 8
        avail = self.avail_read()
        if avail < size:
            raise EOFError(_EOF_READ_FMT, size, have)
        s = self._read(size)
        num = struct.unpack('>Q', s)[0]
        return num

    def read_u16le(self):
        size = 2
        avail = self.avail_read()
        if avail < size:
            raise EOFError(_EOF_READ_FMT, size, have)
        s = self._read(size)
        num = struct.unpack('<H', s)[0]
        return num

    def read_u32le(self):
        size = 4
        avail = self.avail_read()
        if avail < size:
            raise EOFError(_EOF_READ_FMT, size, have)
        s = self._read(size)
        num = struct.unpack('<I', s)[0]
        return num

    def read_u64le(self):
        size = 8
        avail = self.avail_read()
        if avail < size:
            raise EOFError(_EOF_READ_FMT, size, have)
        s = self._read(size)
        num = struct.unpack('<Q', s)[0]
        return num

    def has(self, s):
        n = self.avail_read()
        s = self.peek(n)
        return s in n

    def read_delim(self, sub, chomp=False):
        n = self.avail_read()
        s = self.peek(n)
        i = s.find(sub)
        if i == -1:
            raise
        data = self.read(i + len(sub))
        if chomp:
            data = data[:len(sub)]
        return data

if __name__ == '__main__':
    rb = RingBuffer(10)
    rb.write('abcde')
    print rb.read(5)
    rb.write('fghijkl')
    print rb.read(6) 
