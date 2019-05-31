import inspect
import os
import sys

DEBUG = False

def debug(s, self=None):
    if not DEBUG:
        return
    frames = inspect.stack()
    caller = frames[1]
    filename = os.path.basename(caller[1])
    filename, _ = os.path.splitext(filename)
    lineno = caller[2]
    funcname = caller[3]
    if self:
        funcname = '%s.%s' % (self.__class__.__name__, funcname)
    s.rstrip()
    line = '[debug] %s:%d:%s: %s\n' % (filename, lineno, funcname, s)
    sys.stderr.write(line)

def trace_enter(s='', self=None):
    if not DEBUG:
        return
    frames = inspect.stack()
    caller = frames[1]
    filename = os.path.basename(caller[1])
    filename, _ = os.path.splitext(filename)
    lineno = caller[2]
    funcname = caller[3]
    if self:
        funcname = '%s.%s' % (self.__class__.__name__, funcname)
    line = '[trace] > %s:%d:%s' % (filename, lineno, funcname)
    if s:
        s.strip()
        line += ' %s' % s
    line += '\n'
    sys.stderr.write(line)

def trace_exit(s='', self=None):
    if not DEBUG:
        return
    frames = inspect.stack()
    caller = frames[1]
    filename = os.path.basename(caller[1])
    filename, _ = os.path.splitext(filename)
    lineno = caller[2]
    funcname = caller[3]
    if self:
        funcname = '%s.%s' % (self.__class__.__name__, funcname)
    line = '[trace] < %s:%d:%s' % (filename, lineno, funcname)
    if s:
        s.strip()
        line += ' %s' % s
    line += '\n'
    sys.stderr.write(line)
