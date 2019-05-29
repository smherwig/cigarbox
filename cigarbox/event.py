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

DEFAULT_MIN_TIMEOUT_MS = 5000

class Loop:
    def __init__(self, min_timeout=None):
        self._active = {} 
        self._pending = {}
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
        for ident, event in self._pending.items():
            if event.has_timeout() and event.timeout < self.min_timeout:
                self._min_timeout = event.timeout
        self.min_timeout_stale = False

    def _dispatch(self, ident, event, what):
        print 'dispatch ident=%d, what=%08x' % (ident, what)
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
        for ident, event in self._active.items():
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

        for ident, event in self._active.items(): 
            if event.has_timeout() and event.has_expired():
                self._dispatch(ident, event, TIMEOUT)

        if self.min_timeout_stale:
            self._reset_min_timeout()

    def _make_pollster(self):
        pollster = select.poll()
        for ident, event in self._active.items():
            flags = 0
            if event.fd >= 0:
                if event.mask & READ:
                    flags |= select.POLLIN
                if event.mask & WRITE:
                    flags |= select.POLLOUT
                if flags:
                    pollster.register(event.fd, flags)
        return pollster

    def _poll2event(self, flags):
        what = 0
        if flags & (select.POLLIN | select.POLLERR | select.POLLHUP):
            what |= READ
        if flags & (select.POLLOUT |select.POLLHUP | select.POLLERR):
            what |= WRITE
        assert what, 'flags=0x%08x' % flags
        return what

    def _merge_pending(self):
        print 'pending: %s' % str(self._pending.keys())
        for ident, event in self._active.items():
            if not event.dispatchable:
                del self._active[ident] 
        self._active.update(self._pending)
        self._pending = {}
        print 'active: %s' % str(self._active.keys())

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

        print 'r=%s' % str(r)

        for fd, flags in r:
            event = self._active.get(fd)
            if not event.dispatchable:
                continue
            assert event.fd == fd
            what = self._poll2event(flags)
            if event.has_timeout() and event.has_expired():
                what |= TIMEOUT
            self._dispatch(fd, event, what)

        for ident, event in self._active.items(): 
            if not event.dispatchable:
                continue
            if event.has_timeout() and event.has_expired():
                self._dispatch(ident, event, TIMEOUT)

        if self.min_timeout_stale:
            self._reset_min_timeout()

    def run(self):
        poll_fn = self._get_poll_fn()
        while self._pending or self._active:
            poll_fn()

    def add(self, fd, fn, mask, timeout=0):
        print 'event: add(fd=%d, mask=%d, timeout=%d)' % (fd, mask, timeout)
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
        return ident

    def remove(self, ident):
        print 'event: remove(ident=%d)' % ident
        if ident not in self._active and ident not in self._pending:
            raise ValueError('ident %d is not in run loop' % ident)
        if ident < 0:
            assert self._neg_idents.is_set(-1 * ident)
            self._neg_idents.clr(-1 * ident)
        if ident in self._active:
            event = self._active[ident]
            event.dispatchable = False
        if ident in self._pending:
            del self._pending[ident]

    def once(self, fn, ms):
        return self.add(-1, fn, TIMEOUT, ms) 

    def periodic(self, fn, ms):
        return self.add(-1, fn, TIMEOUT|PERSIST, ms) 
