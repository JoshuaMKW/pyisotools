import struct
from typing import BinaryIO, List, Optional, Union

from chardet import UniversalDetector


def read_sbyte(f: BinaryIO):
    return struct.unpack("b", f.read(1))[0]


def write_sbyte(f: BinaryIO, val: Union[int, list[int]]):
    if isinstance(val, (list, tuple)):
        f.write(struct.pack(">" + ("b"*len(val)), *val))
        return
    f.write(struct.pack(">b", val))


def read_sint16(f: BinaryIO):
    return struct.unpack(">h", f.read(2))[0]


def write_sint16(f: BinaryIO, val: Union[int, list[int]]):
    if isinstance(val, (list, tuple)):
        f.write(struct.pack(">" + ("h"*len(val)), *val))
        return
    f.write(struct.pack(">h", val))


def read_sint32(f: BinaryIO):
    return struct.unpack(">i", f.read(4))[0]


def write_sint32(f: BinaryIO, val: Union[int, list[int]]):
    if isinstance(val, (list, tuple)):
        f.write(struct.pack(">" + ("i"*len(val)), *val))
        return
    f.write(struct.pack(">i", val))


def read_ubyte(f: BinaryIO):
    return struct.unpack("B", f.read(1))[0]


def write_ubyte(f: BinaryIO, val: Union[int, list[int]]):
    if isinstance(val, (list, tuple)):
        f.write(struct.pack(">" + ("B"*len(val)), *val))
        return
    f.write(struct.pack(">B", val))


def read_uint16(f: BinaryIO):
    return struct.unpack(">H", f.read(2))[0]


def write_uint16(f: BinaryIO, val: Union[int, list[int]]):
    if isinstance(val, (list, tuple)):
        f.write(struct.pack(">" + ("H"*len(val)), *val))
        return
    f.write(struct.pack(">H", val))


def read_uint32(f: BinaryIO):
    return struct.unpack(">I", f.read(4))[0]


def write_uint32(f: BinaryIO, val: Union[int, list[int]]):
    if isinstance(val, (list, tuple)):
        f.write(struct.pack(">" + ("I"*len(val)), *val))
        return
    f.write(struct.pack(">I", val))


def read_float(f: BinaryIO):
    return struct.unpack(">f", f.read(4))[0]


def write_float(f: BinaryIO, val: Union[float, list[float]]):
    if isinstance(val, (list, tuple)):
        f.write(struct.pack(">" + ("f"*len(val)), *val))
        return
    f.write(struct.pack(">f", val))


def read_double(f: BinaryIO):
    return struct.unpack(">d", f.read(4))[0]


def write_double(f: BinaryIO, val: Union[float, list[float]]):
    if isinstance(val, (list, tuple)):
        f.write(struct.pack(">" + ("d"*len(val)), *val))
        return
    f.write(struct.pack(">d", val))


def read_vec3f(f: BinaryIO):
    return struct.unpack(">fff", f.read(12))


def write_vec3f(f: BinaryIO, val: (list, tuple)):
    f.write(struct.pack(">fff", *val))


def read_bool(f: BinaryIO, vSize: int = 1):
    return struct.unpack(">?", f.read(vSize))[0] > 0


def write_bool(f: BinaryIO, val: bool, vSize: int = 1):
    if val is True:
        f.write(b'\x00'*(vSize-1) + b'\x01')
    else:
        f.write(b'\x00' * vSize)


def read_string(
    f: BinaryIO,
    offset: Optional[int] = None,
    maxlen: Optional[int] = None,
    encoding: Optional[str] = None
) -> str:
    """ Reads a null terminated string from the specified address """
    if offset is not None:
        f.seek(offset)

    if maxlen is None:
        maxlen = 0

    length = 0
    binary = f.read(1)
    while binary[-1]:
        if length >= maxlen > 0:
            break
        binary += f.read(1)
        length += 1
    else:
        binary = binary[:-1]

    if encoding is None:
        return decode_raw_string(binary)
    return binary.decode(encoding)


def write_string(f: BinaryIO, val: str, encoding: Optional[str] = None):
    if encoding is None:
        encoding = get_likely_encoding(val.encode())
        
    f.write(val.encode(encoding) + b"\x00")


def get_likely_encoding(data: bytes) -> str:
    encoder = UniversalDetector()
    encoder.feed(data)
    encoding = encoder.close()["encoding"]
    try:
        if not encoding or encoding.lower() not in {"ascii", "utf-8", "shift-jis", "iso-8859-1"}:
            encoding = "shift-jis"
        return encoding
    except UnicodeDecodeError:
        return "utf-8"


def decode_raw_string(data: bytes, encoding: Optional[str] = None) -> str:
    try:
        if encoding is None:
            return data.decode(get_likely_encoding(data))
        return data.decode(encoding)
    except UnicodeDecodeError:
        return ""


def align_int(num: int, alignment: int) -> int:
    return (num + (alignment - 1)) & -alignment