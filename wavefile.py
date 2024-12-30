import struct
import numpy as np

WAVE_FORMAT_PCM = 0x1
WAVE_FORMAT_IEEE_FLOAT = 0x3
WAVE_FORMAT_ALAW = 0x6
WAVE_FORMAT_MULAW = 0x7
WAVE_FORMAT_EXTENSIBLE = 0xFFFE

def to_bytes(x, length):
    return x.to_bytes(length, 'little')

def encode_riff(typeid, subchunks):
    assert len(typeid) == 4
    if not isinstance(subchunks, (bytes, bytearray, memoryview)):
        subchunks = b''.join(subchunks)
    return encode_chunk(b'RIFF', typeid + subchunks)

def encode_wave(chunks):
    return encode_riff(b'WAVE', chunks)

def encode_chunk(chunkid, data):
    assert len(chunkid) == 4
    data = memoryview(data)
    b = bytearray(chunkid)
    b += to_bytes(data.nbytes, 4)
    b += data
    if len(b) % 2 == 1:
        b += b'\x00'
    return bytes(b)

_PCMWAVEFORMAT = struct.Struct('<HHIIHH')
_WAVEFORMATEX = struct.Struct('<HHIIHHH')
_WAVEFORMATEXTENSIBLE = struct.Struct('<HHIIHHHHI16s')

_SUBFMT_GUID_SUFFIX = b'\x00\x00\x00\x00\x10\x00\x80\x00\x00\xAA\x00\x38\x9B\x71'

def encode_fmt(format_tag, channels, samples_per_sec, avg_bytes_per_sec,
               block_align, bits_per_sample, *, valid_bits_per_sample=None,
               channel_mask=0, sub_format=None, extra_data=b''):
    extra_data = bytes(extra_data)
    if format_tag == WAVE_FORMAT_PCM:
        data = _PCMWAVEFORMAT.pack(
            format_tag, channels, samples_per_sec, avg_bytes_per_sec,
            block_align, bits_per_sample)
    elif format_tag != WAVE_FORMAT_EXTENSIBLE:
        data = _WAVEFORMATEX.pack(
            format_tag, channels, samples_per_sec, avg_bytes_per_sec,
            block_align, bits_per_sample, len(extra_data)) + extra_data
    else:  # WAVE_FORMAT_EXTENSIBLE
        assert sub_format is not None
        if isinstance(sub_format, int):
            sub_format = to_bytes(sub_format, 2) + _SUBFMT_GUID_SUFFIX
        valid_bits_per_sample = valid_bits_per_sample or bits_per_sample
        data = _WAVEFORMATEXTENSIBLE.pack(
            format_tag, channels, samples_per_sec, avg_bytes_per_sec,
            block_align, bits_per_sample, 22 + len(extra_data),
            valid_bits_per_sample, channel_mask, sub_format) + extra_data
    return encode_chunk(b'fmt ', data)

def encode_fact(sample_length):
    return encode_chunk(b'fact', to_bytes(sample_length, 4))

def encode_data(data):
    return encode_chunk(b'data', data)

def make_wavefile(data, sample_rate, channels=None, format=None, **kwargs):
    data = np.asarray(data)
    assert data.ndim in (1, 2)
    if channels is None:
        channels = 1 if data.ndim == 1 else data.shape[1]
    bytesize = data.itemsize
    bytes_per_sec = sample_rate * bytesize * channels
    block_align = bytesize * channels
    bits = 8 * bytesize
    if format is None:
        format = (WAVE_FORMAT_IEEE_FLOAT
                  if np.issubdtype(data.dtype, np.floating)
                  else WAVE_FORMAT_PCM)

    fmtc = encode_fmt(format, channels, sample_rate, bytes_per_sec, block_align,
                      bits, **kwargs)
    factc = b''
    if format != WAVE_FORMAT_PCM:
        factc = encode_fact(data.size)
    datac = encode_data(data)

    return encode_wave([fmtc, factc, datac])


def to_stereo(a):
    a = np.asarray(a)
    if a.ndim == 2 and a.shape[1] >= 2:
        return a
    return np.repeat(a, 2).reshape(-1, 2)

def to_float(a, dtype=np.float32):
    assert np.issubdtype(dtype, np.floating)
    a = np.asarray(a)
    if a.dtype == dtype:
        return a
    elif np.issubdtype(a.dtype, np.floating):
        return a.astype(dtype)
    info = np.iinfo(a.dtype)
    a = a.astype(dtype) / (info.max+1)
    if info.min == 0:
        return 2*a - 1
    return a

def to_uint8(a):
    a = np.asarray(a)
    if a.dtype == np.uint8:
        return a
    a = to_float(a)
    return np.clip(a*128 + 128, 0, 255).astype(np.uint8)

def to_int16(a):
    a = np.asarray(a)
    if a.dtype == np.int16:
        return a
    a = to_float(a)
    return np.clip(a*2**15, -2**15, 2**15-1).astype(np.int16)
