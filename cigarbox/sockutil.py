"""
Non-Blocking Buffered Socket

All operations are non-blocking (though there are a few convience APIs for
synchronous reads/writes).  Writes are not buffered.  Reads are buffered
in order to support operations like recv_line.  All recvs and sends
handle EINTR by re-trying the syscall (the caller doesn't have to handle
the EINTR error condition).
"""

import errno
import socket
import time

BUF_SIZE = 8192
STEP_SIZE = 8192
DEFAULT_SLEEP = 0.001

class NBBSocket(object):
    def __init__(self, sock):
        self.sock = sock
        self.sock.setblocking(False)
        self.rbuf = bytearray() 

    def have(self):
        """Return the number of bytes in the recv buffer."""
        return len(self.rbuf)

    def give(self, data):
        """Put back into front of recv buffer."""
        if data:
            self.rbuf = bytearray(data) + self.rbuf

    def take(self, count=None):
        """Take up to count bytes from front of recv buffer.
        
        If count is omitted, take all bytes from the recv buffer. 
        """
        if count is None:
            ret = self.rbuf[:]
            self.rbuf= bytearray()
        else:
            n = min(count, self.have())
            ret = self.rbuf[:n]
            self.rbuf = self.rbuf[n:]
        return ret

    def recv(self, count, flags=0):
        """Receive up to count bytes.

        If any data is available return the data (this may be less than count).
        A return of '' means the peer closed the connection.  If no data is
        available raise EAGAIN.  If an error occurs, re-raise the error.
        """
        need = count - self.have()
        while self.have() < need:
            try:
                data = self.sock.recv(BUF_SIZE)
            except socket.error as e:
                if e.errno == errno.EINTR:
                    continue
                if e.errno == errno.EAGAIN and self.have():
                    return self.take()
                else:
                    raise
            if not data:
                break
            self.rbuf.extend(data) 
        ret = self.take(count)
        return ret

    def recv_n(self, count, flags=0):
        """Receive count bytes.
        
        Returns data when count bytes are available, or the peer closed the
        connection (in which case less than count bytes may be returned).
        Otherwise, raises an NBBSocketError, which indiciates how many bytes
        have been received (e.received).
        """
        need = count - self.have()
        while self.have() < need:
            try:
                data = self.sock.recv(BUF_SIZE)
            except socket.error as e:
                if e.errno == errno.EINTR:
                    continue
                else:
                    raise
            if not data:
                break
            self.rbuf.extend(data) 
        ret = self.take(count)
        return ret

    def recv_all(self):
        """Receive until the peer closes the connection.  

        The function returns the data when it is available, and
        otherwise throws a socket.error.
        """
        ret = self.take()
        while True:
            try:
                data = self.recv(BUF_SIZE)
            except socket.error as e:
                self.give(ret)
                raise
            else:
                if not data:
                    break
                else:
                    ret.extend(data)

    def recv_delim(self, delim):
        """Receive until a delimator byte sequence is encountered.
        
        Also returns the data henceforth read if the peer closes the
        connection.  The returned data includes the delim.  (The
        caller can see if the returned data ends with delim to determine
        whether the connection has been closed.)
        """
        ret = bytearray()
        while True:
            e = None
            try:
                data = self.recv(BUF_SIZE)
            except socket.error as e:
                if e.errno == errno.EAGAIN and self.have():
                    data = self.take()
                else:
                    self.give(ret)
                    raise

            if not data:
                break

            i = data.index(delim)
            if i == -1:
                if e:
                    self.give(ret)
                    raise e
                else:
                    ret.extend(data)
            else:
                a = data[:i+1]
                b = data[i+1:]
                ret.extend(a)
                self.give(b)
                break

        return ret

    def recv_line(self):
        """Receive a line."""
        return self.recv_delim('\n')

    def recv_all_sync(self):
        ret = bytearray()
        while True:
            try:
                data = self.recv(BUF_SIZE)
            except socket.error as e:
                if e.errno == errno.EAGAIN:
                    time.sleep(DEFAULT_SLEEP)
                    continue
                else:
                    raise
            else:
                if not data:
                    break
                else:
                    ret.extend(data)
        return ret

    def recv_delim_sync(self, delim):
        ret = bytearray()
        while True:
            try:
                data = self.recv(BUF_SIZE)
            except socket.error as e:
                if e.errno == errno.EAGAIN:
                    if self.have():
                        data = self.take()
                    else:
                        time.sleep(DEFAULT_SLEEP)
                        continue
                else:
                    self.give(ret)
                    raise

            if not data:
                break
            else:
                i = data.index(delim)
                if i == -1:
                    ret.extend(data)
                else:
                    a = data[:i+1]
                    b = data[i+1:]
                    ret.extend(a)
                    self.give(b)
                    break
        return ret

    def recv_line_sync(self):
        return self.recv_delim_sync('\n')

    def send(self, data, flags=0):
        while True:
            try:
                put = self.sock.send(data, flags)
            except socket.error as e:
                if e.errno == errno.EINTR:
                    continue
                else:
                    raise
            else:
                break
        return put

    def send_all_sync(self, data, flags=0):
        count = len(data)
        put = 0
        mv = memoryview(data)
        while put < count:
            try:
                put += self.send(mv[put:], flags)
            except socket.error as e:
                if e.errno == errno.EAGAIN:
                    put += e.sent
                    time.sleep(DEFAULT_SLEEP)
                else:
                    raise 

    def close(self):
        self.sock.setblocking(True)
        self.sock.close()

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
