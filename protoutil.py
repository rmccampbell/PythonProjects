import enum
from itertools import islice

UINT64_MASK = (1<<64) - 1

class WireType(enum.IntEnum):
    VARINT = 0 # int32, int64, uint32, uint64, sint32, sint64, bool, enum
    I64    = 1 # fixed64, sfixed64, double
    LEN    = 2 # string, bytes, embedded messages, packed repeated fields
    SGROUP = 3 # group start (deprecated)
    EGROUP = 4 # group end (deprecated)
    I32    = 5 # fixed32, sfixed32, float

def encode_varint(x):
    x &= UINT64_MASK
    b = bytearray()
    while x2 := x >> 7:
        b.append(x & 0x7f | 0x80)
        x = x2
    b.append(x)
    return bytes(b)

def decode_varint(bts):
    x = 0
    shift = 0
    for b in bts:
        x |= (b & 0x7f) << shift
        if not b & 0x80:
            break
        shift += 7
    return x

def sint_to_int(x):
    return (x << 1) ^ (x >> 63)

def int_to_sint(x):
    return (x ^ -(x & 1)) >> 1

def encode_sint(x):
    return encode_varint(sint_to_int(x))

def decode_sint(bts, off=0):
    return int_to_sint(decode_varint(bts, off))

def pack_tag(field_number, wire_type):
    return (field_number << 3) | wire_type

def unpack_tag(tag):
    return tag >> 3, WireType(tag & 0x7)

def encode_tag(field_number, wire_type):
    return encode_varint(pack_tag(field_number, wire_type))

def decode_tag(bts):
    return unpack_tag(decode_varint(bts))

def decode_len_field(bts):
    bts = iter(bts)
    n = decode_varint(bts)
    return bytes(islice(bts, n))

def decode_i64(bts):
    return int.from_bytes(bytes(islice(bts, 8)), 'little')

def decode_i32(bts):
    return int.from_bytes(bytes(islice(bts, 4)), 'little')
