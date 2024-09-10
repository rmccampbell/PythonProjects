import enum
import struct
from itertools import islice
from collections.abc import Iterable, Sequence
from more_itertools import peekable
from typing import TypeAlias

UINT64_MASK = (1 << 64) - 1


class WireType(enum.IntEnum):
    VARINT = 0  # int32, int64, uint32, uint64, sint32, sint64, bool, enum
    I64    = 1  # fixed64, sfixed64, double
    LEN    = 2  # string, bytes, embedded messages, packed repeated fields
    SGROUP = 3  # group start (deprecated)
    EGROUP = 4  # group end (deprecated)
    I32    = 5  # fixed32, sfixed32, float


Value: TypeAlias = int | bytes | str | float | list['FieldArgs']

FieldArgs: TypeAlias = tuple[int, Value] | tuple[int, Value, WireType]


def bslice(bts: Iterable[int], n: int):
    slc = bytes(bts[:n] if isinstance(bts, Sequence) else islice(bts, n))
    if len(slc) != n:
        raise ValueError(f'not enough bytes: {len(slc)} < {n}')
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
        raise ValueError('not enough bytes for varint')
    return x


def sint_to_int(x: int):
    return (x << 1) ^ (x >> 63)


def int_to_sint(x: int):
    return (x ^ -(x & 1)) >> 1


def encode_sint(x: int):
    return encode_varint(sint_to_int(x))


def decode_sint(bts: Iterable[int], off=0):
    return int_to_sint(decode_varint(bts, off))


def double_to_int(x):
    return int.from_bytes(struct.pack('<d', x), 'little')


def float_to_int(x):
    return int.from_bytes(struct.pack('<f', x), 'little')


def int_to_double(x):
    return struct.unpack('<d', x.to_bytes(8, 'little'))[0]


def int_to_float(x):
    return struct.unpack('<f', x.to_bytes(4, 'little'))[0]


def encode_double(x):
    return struct.pack('<d', x)


def encode_float(x):
    return struct.pack('<f', x)


def decode_double(bts: Iterable[int]):
    return struct.unpack('<d', bslice(bts, 8))


def decode_float(bts: Iterable[int]):
    return struct.unpack('<f', bslice(bts, 4))


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


def encode_len_field(value: bytes | str | list[FieldArgs]):
    if isinstance(value, str):
        value = value.encode()
    elif isinstance(value, list):
        value = encode_message(value)
    return encode_varint(len(value)) + value


def decode_i64(bts: Iterable[int]):
    return int.from_bytes(bslice(bts, 8), 'little')


def decode_i32(bts: Iterable[int]):
    return int.from_bytes(bslice(bts, 4), 'little')


def encode_i64(x: int | float):
    if isinstance(x, float):
        x = double_to_int(x)
    return x.to_bytes(8, 'little')


def encode_i32(x: int | float):
    if isinstance(x, float):
        x = float_to_int(x)
    return x.to_bytes(4, 'little')


def encode_field(field_num: int, value: Value, wire_type: WireType | None = None):
    if wire_type is None:
        wire_type = (WireType.VARINT if isinstance(value, int)
                     else WireType.I64 if isinstance(value, float)
                     else WireType.LEN)
    bts = bytearray(encode_tag(field_num, wire_type))
    match wire_type:
        case WireType.VARINT:
            bts += encode_varint(value)
        case WireType.LEN:
            bts += encode_len_field(value)
        case WireType.I64:
            bts += encode_i64(value)
        case WireType.I32:
            bts += encode_i32(value)
        case WireType.SGROUP:
            bts += encode_message(value)
            bts += encode_tag(field_num, WireType.EGROUP)
        case _:
            raise ValueError(f'invalid wire type: {wire_type}')
    return bytes(bts)


def decode_field(bts: Iterable[int], with_wire_type=False):
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
        case WireType.SGROUP:
            value = decode_message(bts, group=field_num)
        case WireType.EGROUP:
            value = None
        case _:
            raise ValueError(f'invalid wire type: {wire_type}')
    if with_wire_type:
        return field_num, value, wire_type
    return field_num, value


def encode_message(fields: Iterable[FieldArgs]):
    bts = bytearray()
    for field_tup in fields:
        bts.extend(encode_field(*field_tup))
    return bytes(bts)


def decode_message(bts: Iterable[int], with_wire_types=False, group=None):
    bts = peekable(iter(bts))
    fields = []
    while bts:
        num, val, wtype = decode_field(bts, with_wire_type=True)
        if wtype == WireType.EGROUP:
            if num != group:
                raise ValueError(f'invalid end group: {num}')
            return fields
        fields.append((num, val) + ((wtype,) if with_wire_types else ()))
    if group:
        raise ValueError(f'missing end group: {group}')
    return fields
