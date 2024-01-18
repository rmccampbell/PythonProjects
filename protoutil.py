import enum
from itertools import islice
from collections.abc import Iterable
from more_itertools import peekable

UINT64_MASK = (1<<64) - 1

class WireType(enum.IntEnum):
    VARINT = 0 # int32, int64, uint32, uint64, sint32, sint64, bool, enum
    I64    = 1 # fixed64, sfixed64, double
    LEN    = 2 # string, bytes, embedded messages, packed repeated fields
    SGROUP = 3 # group start (deprecated)
    EGROUP = 4 # group end (deprecated)
    I32    = 5 # fixed32, sfixed32, float

def bslice(bts: Iterable[int], n: int):
    slc = bytes(islice(bts, n))
    if len(slc) != n:
        raise ValueError('not enough bytes')
    return slc

def encode_varint(x: int):
    x &= UINT64_MASK
    b = bytearray()
    while x2 := x >> 7:
        b.append(x & 0x7f | 0x80)
        x = x2
    b.append(x)
    return bytes(b)

def decode_varint(bts: Iterable[int]):
    x = 0
    shift = 0
    for b in bts:
        x |= (b & 0x7f) << shift
        if not b & 0x80:
            break
        shift += 7
    else:
        raise ValueError
    return x

def sint_to_int(x: int):
    return (x << 1) ^ (x >> 63)

def int_to_sint(x: int):
    return (x ^ -(x & 1)) >> 1

def encode_sint(x: int):
    return encode_varint(sint_to_int(x))

def decode_sint(bts: Iterable[int], off=0):
    return int_to_sint(decode_varint(bts, off))

def pack_tag(field_num: int, wire_type: WireType):
    return (field_num << 3) | wire_type

def unpack_tag(tag: int):
    return tag >> 3, WireType(tag & 0x7)

def encode_tag(field_num: int, wire_type: WireType):
    return encode_varint(pack_tag(field_num, wire_type))

def decode_tag(bts: Iterable[int]):
    return unpack_tag(decode_varint(bts))

def decode_len_field(bts: Iterable[int]):
    bts = iter(bts)
    n = decode_varint(bts)
    return bslice(bts, n)

def encode_len_field(value: bytes):
    return encode_varint(value) + value

def decode_i64(bts: Iterable[int]):
    return int.from_bytes(bslice(bts, 8), 'little')

def decode_i32(bts: Iterable[int]):
    return int.from_bytes(bslice(bts, 4), 'little')

def encode_i64(x: int):
    return x.to_bytes(8, 'little')

def encode_i32(x: int):
    return x.to_bytes(4, 'little')

def encode_field(field_num: int, value: int|bytes, wire_type: WireType|None=None):
    if wire_type is None:
        wire_type = WireType.VARINT if isinstance(value, int) else WireType.LEN
    bts = encode_tag(field_num, wire_type)
    match wire_type:
        case WireType.VARINT:
            bts += encode_varint(value)
        case WireType.LEN:
            bts += encode_len_field(value)
        case WireType.I64:
            bts += encode_i64(value)
        case WireType.I32:
            bts += encode_i32(value)
        case _:
            raise ValueError
    return bts

def decode_field(bts: Iterable[int]):
    bts = iter(bts)
    field_num, wire_type = decode_tag(bts)
    match wire_type:
        case WireType.VARINT:
            value = decode_varint(bts)
        case WireType.LEN:
            value = decode_len_field(bts)
        case WireType.I64:
            value = decode_i64(bts)
        case WireType.I32:
            value = decode_i32(bts)
        case _:
            raise ValueError
    return field_num, value

def decode_message(bts: Iterable[int]):
    bts = peekable(iter(bts))
    fields = []
    while bts:
        try:
            num, val = decode_field(bts)
        except:
            break
        fields.append((num, val))
    return fields
