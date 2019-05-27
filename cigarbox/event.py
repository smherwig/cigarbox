#!/usr/bin/env python

import errno
import select
import time

from cigarbox import bitops


READ    = 1
WRITE   = 2
TIMEOUT = 4
PERSIST = 8

class _Event:
    def __init__(self, fd, fn, mask, timeout=0):
        self.fd = fd
        self.fn = fn
        self.mask = mask
        self.timeout = timeout
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

DEFAULT_MIN_TIMEOUT_MS = 5000

class Loop:
    def __init__(self, min_timeout=None):
        self._map = {} 
        self._neg_idents = bitops.Bitmap()
        self._neg_idents.set(0)
        self.min_timeout = DEFAULT_MIN_TIMEOUT_MS
        self.min_timeout_stale = False


    def _default_min_timeout(self):
        poll_fn = self._get_poll_fn()
        if poll_fn == self._poll:
            return DEFAULT_MIN_TIMEOUT_POLL
        elif poll_fn == self._select:
            return DEFAULT_MIN_TIMEOUT_SELECT
        else:
            assert False, 'no valid poll function'

    def _get_poll_fn(self):
        if hasattr(select, 'poll'):
            return self._poll
        else:
            return self._select

    def _reset_min_timeout(self):
        self.min_timeout = DEFAULT_MIN_TIMEOUT_MS
        for ident, event in self._map:
            if event.has_timeout() and event.timeout < self.min_timeout:
                self._min_timeout = event.timeout
        self.min_timeout_stale = False

    def _dispatch(self, ident, event, what):
        event.fn(what, self)
        if not event.mask & PERSIST:
            self.remove(ident)
            if what & TIMEOUT:
                assert event.timeout > 0
                if event.timeout == self.min_timeout:
                    self.min_timeout_stale = True
        else:
            if what & TIMEOUT:
                event.reset_expires()

    def _make_select_args(self):
        r = []; w = []; e = []
        for ident, event in self._map.items():
            if event.fd >= 0:
                if event.mask & READ:
                    r.append(fd)
                if event.mask & WRITE:
                    w.append(fd)
                if event.mask & WRITE or event.mask & READ:
                    e.append(fd)
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
            event = self._map.get(fd)
            assert event.fd == fd
            what |= READ
            if event.has_timeout() and event.has_expired():
                what |= TIMEOUT
            self._dispatch(fd, event, what)

        for fd in w:
            what = 0
            event = self._map.get(fd)
            assert event.fd == fd
            what |= WRITE 
            if event.has_timeout() and event.has_expired():
                what |= TIMEOUT
            self._dispatch(fd, event, what)

        for fd in e:
            what = 0
            event = self._map.get(fd)
            assert event.fd == fd
            what |= WRITE | READ
            if event.has_timeout() and event.has_expired():
                what |= TIMEOUT
            self._dispatch(fd, event, what)

        for ident, event in self._map.items(): 
            if event.has_timeout() and event.has_expired():
                self._dispatch(ident, event, TIMEOUT)

        if self.min_timeout_stale:
            self._reset_min_timeout()

    def _make_pollster(self):
        pollster = select.poll()
        for ident, event in self._map.items():
            flags = 0
            if event.fd >= 0:
                if event.mask & READ:
                    flags |= select.POLLIN
                if event.mask & WRITE:
                    flags |= select.POLLOUT
                if flags:
                    pollster.register(event.fd, flags)

    def _poll2event(flags):
        what = 0
        if flags & (select.POLLIN | select.POLLERR | select.POLLHUP):
            what |= READ
        if flags & (select.POLLOUT |select.POLLHUP | select.POLLERR):
            what |= WRITE
        assert what
        return what

    def _poll(self):
        pollster = self._make_pollster()
        try:
            r = pollster.poll(self.min_timeout)
        except select.error as e:
            if e.errno != errno.EINTR:
                raise
            r = []

        for fd, flags in r:
            event = self._map.get(fd)
            assert event.fd == fd
            what = self._poll2event(flags)
            if event.has_timeout() and event.has_expired():
                what |= TIMEOUT
            self._dispatch(fd, event, what)

        for ident, event in self._map: 
            if event.has_timeout() and event.has_expired():
                self._dispatch(ident, event, TIMEOUT)

        if self.min_timeout_stale:
            self._reset_min_timeout()

    def run(self):
        poll_fn = self._get_poll_fn()
        while self._map:
            poll_fn()

    def add(self, fd, fn, mask, timeout=0):
        if fd >= 0:
            ident = fd
        else:
            ident = self._neg_idents.ffc()
            self._neg_idents.set(ident)
            ident *= -1
        event = _Event(fd, fn, mask, timeout)
        if event.has_timeout() and (event.timeout < self.min_timeout):
                self.min_timeout = event.timeout
        self._map[ident] = event
        return ident

    def remove(self, ident):
        if not ident in self._map:
            raise ValueError('ident %d is not in run loop' % ident)
        if ident < 0:
            assert self._neg_idents.is_set(-1 * ident)
            self._neg_idents.clr(-1 * ident)
        del self._map[ident]
        self._reset_min_timeout()

    def once(self, fn, ms):
        return self.add(-1, fn, TIMEOUT, ms) 

    def periodic(self, fn, ms):
        return self.add(-1, fn, TIMEOUT|PERSIST, ms) 
