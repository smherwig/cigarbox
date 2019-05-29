"""
Non-Blocking Buffered Socket

All operations are non-blocking (though there are a few convience APIs for
synchronous reads/writes).  Writes are not buffered, but the API (namely, the
NBBSocketError) makes it a bit easier for the caller to maintain state for a
write buffer (e.g., the current byte position) in the event of partial writes.
"""

import errno
import socket
import time

BUF_SIZE = 8192
STEP_SIZE = 8192
DEFAULT_SLEEP = 0.001

class NBBSocketError(socket.error):
    def __init__(self, sockerr, sent=0, received=0):
        socket.error.__init__(self, sockerr.errno, sockerr.strerror)
        self.sent = sent
        self.received = received

class NBBSocket:
    def __init__(self, sock):
        self.sock = sock
        self.sock.setblocking(False)
        self.rbuf = bytearray() 

    def have(self):
        return len(self.rbuf)

    def give(self, data):
        """
        put back into front of buffer
        """
        self.rbuf = bytearray(data) + self.rbuf

    def take(self, count):
        """
        take from front of buffer
        """
        n = min(count, self.have())
        ret = self.rbuf[:n]
        self.rbuf = self.rbuf[n:]
        return ret

    def recv(self, count, flags=0):
        """
        Either throws an NBBSocketError, returns exactly count,
        or returns less than count, in which case the connection was
        closed.
        """
        need = count - self.have()
        print '> recv: have=%d, count=%d, need=%d' % (self.have(), count, need)
        got = 0
        while got < need:
            try:
                data = self.sock.recv(BUF_SIZE)
            except socket.error as e:
                if e.errno == errno.EINTR:
                    continue
                else:
                    raise NBBSocketError(e, received=got)
            if not data:
                break
            self.rbuf.extend(data) 
            got += len(data)
            print 'got (%d bytes): %s' % (len(data), data)
        ret = self.take(count)
        print '< recv: (%d bytes): %s' % (len(ret), ret)
        return ret

    def recv_all(self):
        ret = bytearray()
        while True:
            try:
                data = self.recv(BUF_SIZE)
            except NBBSocketError as e:
                self.give(ret)
                raise
            if data == '':
                break
            else:
                ret.extend(data)

    def recv_delim(self, delim):
        ret = bytearray()
        while True:
            try:
                data = self.recv(BUF_SIZE)
            except NBBSocketError as e:
                if e.errno == errno.EAGAIN:
                    self.give(ret)
                    raise
            if data == '':
                break
            else:
                i = data.index(delim)
                if i == -1:
                    ret.extend(data)
                else:
                    a = data[:i]
                    b = data[i+len(delim):]
                    ret.extend(a)
                    self.give(b)
                    break
        return ret

    def recv_line(self):
        ret = self.recv_delim('\n')
        if ret.endswith('\r'):
           ret.pop()
        return ret

    def recv_all_sync(self):
        ret = bytearray()
        while True:
            try:
                data = self.recv(BUF_SIZE)
            except NBBSocketError as e:
                if e.errno == errno.EAGAIN:
                    time.sleep(DEFAULT_SLEEP)
                    continue
                else:
                    raise
            if data == '':
                break
            else:
                ret.extend(data)
        return ret

    def recv_delim_sync(self, delim):
        ret = bytearray()
        while True:
            try:
                data = self.recv(BUF_SIZE)
            except NBBSocketError as e:
                if e.errno == errno.EAGAIN:
                    if e.received > 0:
                        data = self.take(e.received)
                        pass
                    else:
                        time.sleep(DEFAULT_SLEEP)
                        continue
                else:
                    raise
            if data == '':
                break
            else:
                i = data.index(delim)
                if i == -1:
                    ret.extend(data)
                else:
                    a = data[:i]
                    b = data[i+len(delim):]
                    ret.extend(a)
                    self.give(b)
                    break
        return ret

    def recv_line_sync(self):
        ret = self.recv_delim_sync('\n')
        if ret.endswith('\r'):
           ret.pop()
        return ret

    def _send_raw(self, data, flags=0):
        """Either sends exactly len(data) (and returns len(data)) or throws an
        error.  If partial data was sent, the error contains the amount sent.
        """
        tot = 0
        count = len(data)
        while tot < count:
            step = count - tot if count - tot <= STEP_SIZE else STEP_SIZE
            part = data[tot:tot+step]
            try:
                nsent = self.sock.send(part, flags)
            except socket.error as e:
                if e.errno == errno.EINTR:
                    continue
                else:
                    raise NBBSocketError(e, sent=tot)
            tot += nsent
        return tot

    def send_all_sync(self, data, flags=0):
        count = len(data)
        put = 0
        mv = memoryview(data)
        while put < count:
            try:
                put += self._send_raw(mv[put:], flags)
            except NBBSocketError as e:
                if e.errno == errno.EAGAIN:
                    put += e.sent
                else:
                    raise

    def send(self, data, flags=0):
        return self._send_raw(data, flags)

    def close(self):
        self.sock.setblocking(True)
        self.sock.close()

    # TODO: make non-blocking
    def connect(self):
        self.sock.connect()

    # cheap inheritance; used to pass all other attribute
    # references ot the underlying socket object
    def __getattr__(self, attr):
        try:
            retattr = getattr(self.sock, attr)
        except AttributeError:
            raise AttributeError("%s instance has no attribute '%s'"
                                 %(self.__class__.__name__, attr))
        else:
            return retattr


def wrap_nbb(sock):
    return NBBSocket(sock)

if __name__ == '__main__':
    try:
        buf = sock.send(data[n:])
    except NBBSocketError as e:
        if e.error == errno.EAGAIN:
            n = e.sent
        else:
            pass

    try:
        buf = sock.recv_line(n)
    except NBBSocketError as e:
        if e.error == errno.EAGIN:
            pass

