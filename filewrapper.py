from __future__ import print_function
import sys, io, types, functools

class FileWrapper(io.IOBase):
    def __init__(self, file):
        self._file = file

    def close(self):
        self._file.close()

    @property
    def closed(self):
        return self._file.closed

    def fileno(self):
        return self._file.fileno()

    def flush(self):
        self._file.flush()

    def isatty(self):
        return self._file.isatty()

    def read(self, size=-1):
        return self._file.read(size)

    def readable(self):
        return self._file.readable()

    def readline(self, size=-1):
        return self._file.readline(size)

    def readlines(self, hint=-1):
        return self._file.readlines(hint)

    def seek(self, offset, whence=0):
        return self._file.seek(offset, whence)

    def seekable(self):
        return self._file.seekable()

    def tell(self):
        return self._file.tell()

    def truncate(self, size=None):
        return self._file.truncate(size)

    def write(self, s):
        return self._file.write(s)

    def writable(self):
        return self._file.writable()

    def writelines(self, lines):
        self._file.writelines(lines)

    def __enter__(self):
        self._file.__enter__()
        return self

    def __exit__(self, *args):
        return self._file.__exit__(*args)

    def __next__(self):
        return self._file.__next__()

    def __getattr__(self, name):
        return getattr(self._file, name)

    def __del__(self):
        pass


class LoggingFileWrapper(FileWrapper):
    def __init__(self, file, logfile=None):
        super().__init__(file)
        self._logfile = logfile or sys.stdout

    def _wrap(func):
        @functools.wraps(func)
        def wrapper(self, *args):
            print('{}({})'.format(func.__name__, ', '.join(map(repr, args))),
                  file=self._logfile)
            return func(self, *args)
        return wrapper

    for _name, _func in vars(FileWrapper).items():
        if isinstance(_func, types.FunctionType) and _name != '__init__':
            locals()[_name] = _wrap(_func)
        elif isinstance(_func, property):
            locals()[_name] = property(_wrap(_func.fget))

    del _wrap, _name, _func
