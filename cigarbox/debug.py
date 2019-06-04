import inspect
import os
import sys

DEBUG = False

def _make_line(frame, tag, msg='', self=None):
    filename = os.path.basename(frame[1])
    filename, _ = os.path.splitext(filename)
    lineno = frame[2]
    funcname = frame[3]
    if self:
        funcname = '%s.%s' % (self.__class__.__name__, funcname)
    msg.rstrip()
    if msg:
        line = '%s %s:%d:%s: %s\n' % (tag, filename, lineno, funcname, msg)
    else:
        line = '%s %s:%d:%s\n' % (tag, filename, lineno, funcname)
    return line

def debug(msg, self=None):
    if not DEBUG:
        return
    frames = inspect.stack()
    caller = frames[1]
    line = _make_line(caller, '[debug]', msg, self)
    sys.stderr.write(line)

def warn(msg, self=None):
    frames = inspect.stack()
    caller = frames[1]
    line = _make_line(caller, '[warn]', msg, self)
    sys.stderr.write(line)

def die(msg, self=None):
    frames = inspect.stack()
    caller = frames[1]
    line = _make_line(caller, '[die]', msg, self)
    sys.stderr.write(line)
    sys.exit(1)

def trace_enter(msg='', self=None):
    if not DEBUG:
        return
    frames = inspect.stack()
    caller = frames[1]
    line = _make_line(caller, '[trace >]', msg, self)
    sys.stderr.write(line)

def trace_exit(msg='', self=None):
    if not DEBUG:
        return
    frames = inspect.stack()
    caller = frames[1]
    line = _make_line(caller, '[trace <]', msg, self)
    sys.stderr.write(line)
