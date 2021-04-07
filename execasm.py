import os
import ctypes

RET = b'\xC3'


def get_buffer(buffer):
    try:
        buffer = memoryview(buffer)
    except TypeError:
        buffer = memoryview(bytes(buffer))
    buftype = ctypes.c_char * buffer.nbytes
    if buffer.readonly:
        return buftype.from_buffer_copy(buffer)
    return buftype.from_buffer(buffer)

if os.name == 'nt':
    kernel32 = ctypes.windll.kernel32
    kernel32.VirtualAlloc.restype = ctypes.c_void_p

    MEM_COMMIT = 0x00001000
    PAGE_READWRITE = 0x04
    PAGE_EXECUTE_READ = 0x20
    MEM_RELEASE = 0x8000

    def asm_func(code, restype=None, *argtypes):
        code = get_buffer(code)
        buff = ctypes.c_void_p(
            kernel32.VirtualAlloc(None, len(code), MEM_COMMIT, PAGE_READWRITE))
        ctypes.memmove(buff, code, len(code))
        oldp = ctypes.c_uint32()
        kernel32.VirtualProtect(
            buff, len(code), PAGE_EXECUTE_READ, ctypes.byref(oldp))
        funcptr = ctypes.cast(buff, ctypes.CFUNCTYPE(restype, *argtypes))
        return funcptr

    def free_asm_func(funcptr):
        kernel32.VirtualFree(funcptr, 0, MEM_RELEASE)

else:
    import mmap

    libc = ctypes.CDLL(None)
    libc.mmap.restype = ctypes.c_void_p

    def asm_func(code, restype=None, *argtypes):
        code = get_buffer(code)
        buff = ctypes.c_void_p(libc.mmap(
            None, len(code), mmap.PROT_READ | mmap.PROT_WRITE,
            mmap.MAP_PRIVATE | mmap.MAP_ANONYMOUS, -1, 0))
        ctypes.memmove(buff, code, len(code))
        libc.mprotect(buff, len(code), mmap.PROT_READ | mmap.PROT_EXEC)
        funcptr = ctypes.cast(buff, ctypes.CFUNCTYPE(restype, *argtypes))
        funcptr.length = len(code)
        return funcptr

    def free_asm_func(funcptr):
        libc.munmap(funcptr, getattr(funcptr, 'length', mmap.PAGESIZE))


def exec_asm(code, restype=None, argtypes=(), args=(), add_ret=False):
    if add_ret:
        code = bytes(code) + RET
    funcptr = asm_func(code, restype, *argtypes)
    try:
        res = funcptr(*args)
    finally:
        free_asm_func(funcptr)
    return res
