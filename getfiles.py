from __future__ import print_function
import sys, os, glob, io, codecs, contextlib

_PY3 = sys.version_info[0] >= 3

ERRORS = 'replace'

PROGNAME = os.path.basename(sys.argv[0] or sys.executable)

def printerr(msg='{prog}: {error}', *args, **kwargs):
##    import traceback
##    traceback.print_exc()
    etype, error, tb = sys.exc_info()
    kws = dict(prog=PROGNAME, error=error, etype=etype and etype.__name__)
    kws.update(kwargs)
    print(msg.format(*args, **kws), file=sys.stderr)

@contextlib.contextmanager
def safeclose(file):
    yield file
    try:
        if not file.closed and file.fileno() > 2:
            file.close()
        elif hasattr(file, '_changed_encoding') and file.buffer:
            file.detach()
    except io.UnsupportedOperation:
        pass  # fileno doesn't work on idle std streams

@contextlib.contextmanager
def maybeclose(file, close=True):
    yield file
    if close:
        file.close()

def chars(file):
    return chunk(file, 1)

def chunk(file, blocksize=8192):
    s = file.read(blocksize)
    while s:
        yield s
        s = file.read(blocksize)

def getfiles(paths=None, mode='r', encoding=None, errors=ERRORS,
             default='-', stdio=True, recursive=True):
    """Return an iterator yielding file objects matching glob patterns."""
    openf = stdopen if stdio else guess_open
    if not stdio and default == '-':
        default = None
    if paths is None:
        paths = sys.argv[1:]
    if not paths and default:
        paths = [default]
    for path in paths:
        if not isinstance(path, str):
            yield path
            continue
        for file in expandpaths([path], recursive):
            try:
                f = openf(file, mode, encoding=encoding, errors=errors)
                with safeclose(f):
                    yield f
            except IOError:
                printerr()

def expandpaths(paths, recursive=True):
    """Return a list of paths expanded from glob patterns."""
    if sys.version_info >= (3, 5):
        return [file for path in paths for file in
                glob.glob(path, recursive=recursive) or (path,)]
    return [file for path in paths for file in glob.glob(path) or (path,)]

def stdopen(file, mode='r', encoding=None, errors=ERRORS):
    """Open a file, or return stdin or stdout for '-'"""
    if file == '-':
        mode2 = mode.strip('btU')
        if mode2 == 'r':
            file = sys.stdin
        elif mode2 in ('w', 'a'):
            file = sys.stdout
        else:
            raise ValueError("mode '{}' not allowed for '-'".format(mode))
        if _PY3:
            encoding = encoding if encoding != '-' else None
            if 'b' in mode:
                file = file.buffer
            elif encoding or errors:
                try:
                    file = change_encoding(file, encoding, errors)
                except AttributeError:
                    pass
        return file
    else:
        return guess_open(file, mode, encoding=encoding, errors=errors)

def guess_open(file, mode='r', encoding=None, errors=ERRORS):
    if not _PY3:
        return open(file, mode)
    if (not encoding and 'b' not in mode and ('r' in mode or 'a' in mode)
        and os.path.isfile(file)):
        with open(file, 'rb') as f:
            if f.seekable() and not f.isatty():
                encoding = detect_enc(f)
    elif encoding == '-':
        encoding = None
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

def change_encoding(file, encoding=None, errors=ERRORS):
    encoding = encoding or file.encoding
    errors = errors or file.errors
    codecs.lookup_error(errors)
    newfile = io.TextIOWrapper(file.buffer, encoding, errors,
                               line_buffering=file.line_buffering)
    newfile.mode = file.mode
    newfile._changed_encoding = True
    return newfile

def set_encoding(encoding=None, errors=ERRORS):
    stdout = sys.stdout
    try:
        sys.stdout = change_encoding(stdout, encoding, errors)
    except AttributeError:
        pass
    return stdout

def reset_encoding(stdout=None):
    stdout = stdout or sys.__stdout__
    if stdout and sys.stdout is not stdout:
        sys.stdout.detach()
        sys.stdout = stdout

@contextlib.contextmanager
def stdout_encoding(encoding=None, errors=ERRORS):
    stdout = set_encoding(encoding, errors)
    yield
    reset_encoding(stdout)
