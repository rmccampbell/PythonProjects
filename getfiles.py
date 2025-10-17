from __future__ import print_function
import sys, os, glob, io, codecs, contextlib

_PY3 = sys.version_info[0] >= 3

ERRORS = 'surrogateescape'

PROGNAME = os.path.basename(sys.argv[0] or sys.executable)

PATHTYPES = (str, bytes)
if sys.version_info >= (3,6):
    PATHTYPES += (os.PathLike,)

def printerr(msg='{prog}: {error}', *args, file=None, **kwargs):
##    import traceback
##    traceback.print_exc()
    etype, error, tb = sys.exc_info()
    kws = dict(prog=PROGNAME, error=error, etype=etype and etype.__name__)
    kws.update(kwargs)
    print(msg.format(*args, **kws), file=file or sys.stderr)

@contextlib.contextmanager
def safeclose(file):
    try:
        yield file
    finally:
        if file.closed:
            return
        try:
            isstdio = (file in (sys.stdin, sys.stdout, sys.stderr) or
                       file.fileno() <= 2)
        except (AttributeError, OSError):
            isstdio = False
        if not isstdio:
            file.close()
        elif hasattr(file, '_changed_encoding') and file.buffer:
            file.detach()

@contextlib.contextmanager
def maybeclose(file, close):
    try:
        yield file
    finally:
        if close:
            file.close()

@contextlib.contextmanager
def maybeopen(file, *args, **kwargs):
    if isinstance(file, PATHTYPES):
        with safeclose(extopen(file, *args, **kwargs)) as file:
            yield file
    else:
        yield file

@contextlib.contextmanager
def maybe_stdopen(file, *args, **kwargs):
    if isinstance(file, PATHTYPES):
        with safeclose(stdopen(file, *args, **kwargs)) as file:
            yield file
    else:
        yield file

def iterchunks(file, blocksize=8192, read1=False):
    read = file.read1 if read1 else file.read
    s = read(blocksize)
    while s:
        yield s
        s = read(blocksize)

def iterchars(file):
    return iterchunks(file, 1)

def iterlines(file, keepends=False):
    return iter(file) if keepends else (l.rstrip('\r\n') for l in file)

chunks = iterchunks
chars = iterchars
lines = iterlines

def getfiles(paths=None, mode='r', encoding=None, errors=ERRORS, default='-',
             stdio=True, guess=False, recursive=True, close=True,
             catch_errors=True):
    """Return an iterator yielding file objects matching glob patterns."""
    if not stdio and default == '-':
        default = None
    if paths is None:
        paths = sys.argv[1:]
    if not paths and default is not None:
        paths = [default]
    if isinstance(paths, PATHTYPES):
        paths = [paths]
    for path in paths:
        if not isinstance(path, PATHTYPES):
            yield path
            continue
        for file in expandpaths(path, recursive=recursive):
            try:
                f = extopen(file, mode, encoding=encoding, errors=errors,
                            stdio=stdio, guess=guess)
                if close:
                    with safeclose(f):
                        yield f
                else:
                    yield f
            except IOError:
                if catch_errors:
                    printerr()
                else:
                    raise

def expandpaths(*paths, recursive=True):
    """Return a list of paths expanded from glob patterns."""
    if len(paths) == 1 and not isinstance(paths[0], PATHTYPES):
        paths = paths[0]
    if sys.version_info >= (3, 5):
        return [file for path in paths for file in
                glob.glob(path, recursive=recursive) or (path,)]
    return [file for path in paths for file in glob.glob(path) or (path,)]

def extopen(file, mode='r', encoding=None, errors=ERRORS, stdio=False,
            guess=False):
    if stdio:
        return stdopen(file, mode, encoding=encoding, errors=errors,
                       guess=guess)
    elif guess:
        return guess_open(file, mode, encoding=encoding, errors=errors)
    else:
        if 'b' in mode:
            errors = None
        return open(file, mode, encoding=encoding, errors=errors)

def stdopen(file, mode='r', encoding=None, errors=ERRORS, guess=False):
    """Open a file, or return stdin or stdout for '-'"""
    if file == '-':
        mode2 = mode.strip('btU')
        if mode2 == 'r':
            file = sys.stdin
        elif mode2 in ('w', 'a', 'x'):
            file = sys.stdout
        else:
            raise ValueError("mode '{}' not allowed for '-'".format(mode))
        if _PY3:
            if encoding in ('-', ''):
                encoding = None
            if 'b' in mode:
                file = file.buffer
            elif encoding or errors:
                try:
                    file = change_encoding(file, encoding, errors)
                except AttributeError:
                    pass
        return file
    return extopen(file, mode, encoding=encoding, errors=errors, guess=guess)

def guess_open(file, mode='r', encoding=None, errors=ERRORS):
    if not _PY3:
        return open(file, mode)
    if (encoding is None
            and 'b' not in mode and ('r' in mode or 'a' in mode)
            and os.path.isfile(file)):
        with open(file, 'rb') as f:
            if f.seekable() and not f.isatty():
                encoding = detect_enc(f)
    if encoding in ('-', ''):
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
    if encoding == file.encoding and errors == file.errors:
        return file
    codecs.lookup_error(errors)
    newfile = io.TextIOWrapper(file.buffer, encoding, errors,
                               line_buffering=file.line_buffering)
    newfile.mode = file.mode
    newfile._changed_encoding = True
    return newfile

def set_stdout_encoding(encoding=None, errors=ERRORS):
    stdout = sys.stdout
    try:
        sys.stdout = change_encoding(stdout, encoding, errors)
    except AttributeError:
        pass
    return stdout

def reset_stdout_encoding(stdout=None):
    stdout = stdout or sys.__stdout__
    if stdout and sys.stdout is not stdout:
        sys.stdout.detach()
        sys.stdout = stdout

@contextlib.contextmanager
def stdout_encoding(encoding=None, errors=ERRORS):
    stdout = set_stdout_encoding(encoding, errors)
    try:
        yield
    finally:
        reset_stdout_encoding(stdout)


def stdcon(mode='w', **kwargs):
    if os.name == 'nt':
        return open('con', mode, **kwargs)
    else:
        return open('/dev/tty', mode, **kwargs)
