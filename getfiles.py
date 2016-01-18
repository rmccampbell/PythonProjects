from __future__ import print_function
import sys, os, glob, io, codecs, contextlib

PY3 = sys.version_info[0] >= 3

ERRORS = 'replace'

def printerr(msg, *args):
    print(msg.format(*args), file=sys.stderr)

@contextlib.contextmanager
def autoclose(file):
    yield file
    if file not in {sys.stdin, sys.stdout, sys.stderr,
                    sys.stdin.buffer, sys.stdout.buffer, sys.stderr.buffer}:
        file.close()

def getfiles(paths, mode='r', encoding=None, errors=ERRORS,
             default=None, stdio=True):
    """Return an iterator yielding file objects matching glob patterns."""
    openf = stdopen if stdio else guess_open
    if paths:
        for path in paths:
            if not isinstance(path, str):
                yield path
                continue
            files = glob.glob(path)
            if files:
                for file in files:
                    #if os.path.isfile(file):
                    try:
                        yield openf(file, mode, encoding=encoding, errors=errors)
                    except IOError as e:
                        printerr("error: {}", e)
            else:
                try:
                    yield openf(path, mode, encoding=encoding, errors=errors)
                except IOError as e:
                    printerr("error: '{}' does not match any files.", path)
                    #printerr("error: {}", e)
    elif default:
        if isinstance(default, str):
            yield openf(default, mode, encoding=encoding, errors=errors)
        else:
            yield default

def expandpaths(paths):
    """Return a list of paths expanded from glob patterns."""
    return [file for path in paths for file in glob.glob(path) or (path,)]

def stdopen(file, mode='r', encoding=None, errors=ERRORS):
    """Open a file, or return stdin or stdout for '-'"""
    if file == '-':
        md = mode.strip('bt')
        if md == 'r':
            file = sys.stdin
        elif md in ('w', 'a'):
            file = sys.stdout
        else:
            raise ValueError("mode '{}' not allowed for '-'".format(mode))
        if 'b' in mode and PY3:
            return file.buffer
        return file
    else:
        return guess_open(file, mode, encoding=encoding, errors=errors)

def guess_open(file, mode='r', encoding=None, errors=ERRORS):
    if not PY3:
        return open(file, mode)
    if (not encoding and 'r' in mode and 'b' not in mode
        and os.path.exists(file)):
        f = open(file, 'rb')
        if f.seekable() and not f.isatty():
            encoding = detect_enc(f)
        f.close()
    if 'b' in mode:
        errors = None
    return open(file, mode, encoding=encoding, errors=errors)

def detect_enc(file):
    bts = file.read(3)
    file.seek(0)
    if bts[:2] in (codecs.BOM_LE, codecs.BOM_BE):
        return 'utf-16'
    if bts == codecs.BOM_UTF8:
        return 'utf-8-sig'
    return None

def set_errorhandler(errors=ERRORS):
    stdout = sys.stdout
    codecs.lookup_error(errors)
    try:
        sys.stdout = io.TextIOWrapper(stdout.buffer, stdout.encoding, errors,
                                      line_buffering=stdout.line_buffering)
        sys.stdout.mode = stdout.mode
    except AttributeError:
        pass
    return stdout

def reset_errorhandler(stdout=None):
    stdout = stdout or sys.__stdout__
    if stdout and sys.stdout is not stdout:
        sys.stdout.detach()
        sys.stdout = stdout

@contextlib.contextmanager
def errorhandler(errors=ERRORS):
    stdout = set_errorhandler(errors)
    yield
    reset_errorhandler(stdout)
