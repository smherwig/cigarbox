#!/usr/bin/env python

import errno
import select
import time

from cigarbox import bitops
from cigarbox import debug

READ    = 1
WRITE   = 2
TIMEOUT = 4
PERSIST = 8
ALL_MASK = READ | WRITE | TIMEOUT | PERSIST

DEFAULT_MIN_TIMEOUT_MS = 5000

def _mask_to_str(mask):
    a = []
    if mask & READ:    a.append('READ')
    if mask & WRITE:   a.append('WRITE')
    if mask & TIMEOUT: a.append('TIMEOUT')
    if mask & PERSIST: a.append('PERSIST')
    return '|'.join(a)

def _poll_flags_to_str(flags):
    a = []
    if flags & select.POLLERR:  a.append('POLLERR')
    if flags & select.POLLHUP:  a.append('POLLHUP')
    if flags & select.POLLIN:   a.append('POLLIN')
    if flags & select.POLLNVAL: a.append('POLLNVAL')
    if flags & select.POLLOUT:  a.append('POLLOUT')
    if flags & select.POLLPRI:  a.append('POLLPRI')
    return '|'.join(a)

def _poll_flags_to_mask(flags):
        what = 0
        if flags & (select.POLLIN | select.POLLERR | select.POLLHUP):
            what |= READ
        if flags & (select.POLLOUT |select.POLLHUP | select.POLLERR):
            what |= WRITE
        assert what, 'poll flags=0x%08x' % flags
        return what

class _Event(object):
    def __init__(self, fd, fn, mask, timeout=0):
        self.fd = fd
        self.fn = fn
        self.mask = mask
        self.timeout = timeout
        self.dispatchable = True
        if timeout > 0:
            self.reset_expires()
        else:
            self.expires = 0

    def has_timeout(self):
        return self.timeout > 0

    def has_expired(self):
        assert self.timeout > 0 and self.expires > 0
        return time.time() >  self.expires

    def reset_expires(self):
        assert self.timeout > 0
        t = time.time()
        ms = self.timeout / 1000.0
        self.expires = t + ms

class Loop(object):
    def __init__(self, min_timeout=None):
        self._active = {} 
        self._pending = {}
        self._neg_idents = bitops.Bitmap()
        self._neg_idents.set(0)
        self.min_timeout = DEFAULT_MIN_TIMEOUT_MS
        self.min_timeout_stale = False

    def _get_poll_fn(self):
        if hasattr(select, 'poll'):
            debug.debug('using poll')
            return self._poll
        else:
            debug.debug('using select')
            return self._select

    def _reset_min_timeout(self):
        self.min_timeout = DEFAULT_MIN_TIMEOUT_MS
        for ident, event in self._pending.iteritems():
            if event.has_timeout() and event.timeout < self.min_timeout:
                self._min_timeout = event.timeout
        self.min_timeout_stale = False

    def _dispatch(self, ident, event, what):
        debug.debug('ident=%d, what=%s' % (ident, _mask_to_str(what)))
        event.fn(what, self)
        if not event.mask & PERSIST:
            event.dispatchable = False
            if event.timeout == self.min_timeout:
                self.min_timeout_stale = True
        else:
            if what & TIMEOUT:
                assert event.timeout > 0
                event.reset_expires()

    def _make_select_args(self):
        r = []; w = []; e = []
        for ident, event in self._active.iteritems():
            if event.fd >= 0:
                if event.mask & READ:
                    r.append(event.fd)
                if event.mask & WRITE:
                    w.append(event.fd)
                if event.mask & WRITE or event.mask & READ:
                    e.append(event.fd)
        return r, w, e

    def _select(self):
        r, w, e = self._make_select_args()
        try:
            r, w, e = select.select(r, w, e, self.min_timeout / 1000.0)
        except select.error as e:
            if e.errno != errno.EINTR:
                raise
            else:
                return

        for fd in r:
            what = 0
            event = self._active.get(fd)
            assert event.fd == fd
            what |= READ
            if event.has_timeout() and event.has_expired():
                what |= TIMEOUT
            self._dispatch(fd, event, what)

        for fd in w:
            what = 0
            event = self._active.get(fd)
            assert event.fd == fd
            what |= WRITE 
            if event.has_timeout() and event.has_expired():
                what |= TIMEOUT
            self._dispatch(fd, event, what)

        for fd in e:
            what = 0
            event = self._active.get(fd)
            assert event.fd == fd
            what |= WRITE | READ
            if event.has_timeout() and event.has_expired():
                what |= TIMEOUT
            self._dispatch(fd, event, what)

        for ident, event in self._active.iteritems(): 
            if event.has_timeout() and event.has_expired():
                self._dispatch(ident, event, TIMEOUT)

        if self.min_timeout_stale:
            self._reset_min_timeout()

    def _make_pollster(self):
        pollster = select.poll()
        for ident, event in self._active.iteritems():
            flags = 0
            if event.fd >= 0:
                if event.mask & READ:
                    flags |= select.POLLIN
                if event.mask & WRITE:
                    flags |= select.POLLOUT
                if flags:
                    debug.debug('register fd=%d %s' %
                            (event.fd, _poll_flags_to_str(flags)))
                    pollster.register(event.fd, flags)
        return pollster

    def _merge_pending(self):
        for ident, event in self._active.items():
            if not event.dispatchable:
                del self._active[ident] 
        self._active.update(self._pending)
        self._pending = {}

    def _poll(self):
        self._merge_pending()
        pollster = self._make_pollster()

        while True:
            try:
                r = pollster.poll(self.min_timeout)
            except select.error as e:
                if e.errno == errno.EINTR:
                    continue
                else:
                    raise
            break

        for fd, flags in r:
            event = self._active.get(fd)
            if not event.dispatchable:
                continue
            assert event.fd == fd
            what = _poll_flags_to_mask(flags)
            if event.has_timeout() and event.has_expired():
                what |= TIMEOUT
            self._dispatch(fd, event, what)

        for ident, event in self._active.iteritems(): 
            if not event.dispatchable:
                continue
            if event.has_timeout() and event.has_expired():
                self._dispatch(ident, event, TIMEOUT)

        if self.min_timeout_stale:
            self._reset_min_timeout()

    def run(self):
        """Start the run loop.

        The loop terminates when there are no more events to process
        """
        poll_fn = self._get_poll_fn()
        while self._pending or self._active:
            poll_fn()

    def add(self, fd, fn, mask, timeout=0):
        """Add an event to the run loop.

        The event is added to the next cycle of the loop.

        Args:
            fd (int): file descriptor (e.g. sock.fileno()).  For timeout
                events, pass -1.

            fn (func): callback function.  When the fd is readable/writeable
                or a timer has expired, func is called with two arguments:
                what, and loop.  what is a mask of the events that triggered
                (READ, WRITE, and/or TIMEOUT), and loop is the run loop.

            mask (int): The events to listen for.  Must be READ, WRITE, and/or
                TIMEOUT.

            timeout (int, optional): If mask includes TIMEOUT, the timeout
                value in milliseconds.

        Returns:
            int: the event indentifer.  For file descriptors, the identifer
                is just the descriptor number.  For pure timeouts (fd=-1),
                the identifier is a negative number.

        Raises:
            ValuError: mask is invalid, or mask specifies TIMEOUT and timeout
                <= 0.
        """
        if not (mask & ALL_MASK) or (mask & ~ALL_MASK):
            raise ValueError('invalid mask %08x' % mask) 
        if mask & TIMEOUT and timeout <= 0:
            raise ValueError('timeout (%d) must be positive', timeout)

        debug.trace_enter('fd=%d, mask=%s (0x%08x), timeout=%d' % 
                (fd, _mask_to_str(mask), mask, timeout))

        if fd >= 0:
            ident = fd
        else:
            ident = self._neg_idents.ffc()
            self._neg_idents.set(ident)
            ident *= -1
        event = _Event(fd, fn, mask, timeout)
        if event.has_timeout() and (event.timeout < self.min_timeout):
            self.min_timeout = event.timeout
        self._pending[ident] = event

        debug.trace_exit('ident=%d' % ident)
        return ident

    def remove(self, ident):
        """"Remove an event from the run loop.

        The ident is searched for in both the current cycle 
        and the next (pending) cycle, and removed from both.

        Args:
            ident (int): identifier of the event to remove

        Raises:
            ValueError: the event does not exist
        """
        debug.trace_enter('ident=%d'% ident)
        if ident not in self._active and ident not in self._pending:
            raise ValueError('ident %d is not in run loop' % ident)
        if ident < 0:
            assert self._neg_idents.is_set(-1 * ident)
            self._neg_idents.clr(-1 * ident)
        if ident in self._active:
            event = self._active[ident]
            event.dispatchable = False
            if event.timeout == self.min_timeout:
                self.min_timeout_stale = True
        if ident in self._pending:
            event = self._pending[ident]
            if event.timeout == self.min_timeout:
                self.min_timeout_stale = True
            del self._pending[ident]

        debug.trace_exit()

    def once(self, fn, ms):
        """Add a timer event.

        The callback will be called ms milliseconds in the future

        Args:
            fn (func): callback function.  Receives two parameters: the
            event that fired (here, TIMEOUT), and the run loop.

            ms (int): timeout in milliseconds
        """
        return self.add(-1, fn, TIMEOUT, ms) 

    def periodic(self, fn, ms):
        """Add a periodic event.

        The callback is called every ms milliseconds.

        Args:
            fn (func): callback function.  Receives two parameters: the
            event that fired (here, TIMEOUT), and the run loop.

            ms (int): timeout in milliseconds
        """
        return self.add(-1, fn, TIMEOUT|PERSIST, ms) 
