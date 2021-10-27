import struct
from typing import BinaryIO, Optional

from chardet import UniversalDetector


def read_sbyte(f: BinaryIO):
    return struct.unpack("b", f.read(1))[0]


def write_sbyte(f: BinaryIO, val):
    f.write(struct.pack("b", val))


def read_sint16(f: BinaryIO):
    return struct.unpack(">h", f.read(2))[0]


def write_sint16(f: BinaryIO, val):
    f.write(struct.pack(">h", val))


def read_sint32(f: BinaryIO):
    return struct.unpack(">i", f.read(4))[0]


def write_sint32(f: BinaryIO, val):
    f.write(struct.pack(">i", val))


def read_ubyte(f: BinaryIO):
    return struct.unpack("B", f.read(1))[0]


def write_ubyte(f: BinaryIO, val):
    f.write(struct.pack("B", val))


def read_uint16(f: BinaryIO):
    return struct.unpack(">H", f.read(2))[0]


def write_uint16(f: BinaryIO, val):
    f.write(struct.pack(">H", val))


def read_uint32(f: BinaryIO):
    return struct.unpack(">I", f.read(4))[0]


def write_uint32(f: BinaryIO, val):
    f.write(struct.pack(">I", val))


def read_float(f: BinaryIO):
    return struct.unpack(">f", f.read(4))[0]


def write_float(f: BinaryIO, val):
    f.write(struct.pack(">f", val))


def read_double(f: BinaryIO):
    return struct.unpack(">d", f.read(4))[0]


def write_double(f: BinaryIO, val):
    f.write(struct.pack(">d", val))


def read_bool(f: BinaryIO, vSize=1):
    return struct.unpack("B", f.read(vSize))[0] > 0


def write_bool(f: BinaryIO, val: bool, vSize=1):
    if val is True:
        f.write(b'\x00'*(vSize-1) + b'\x01')
    else:
        f.write(b'\x00' * vSize)


def read_string(
    f: BinaryIO,
    offset: int = 0,
    maxlen: int = 0,
    encoding: Optional[str] = None
) -> str:
    """ Reads a null terminated string from the specified address """
    f.seek(offset)

    length = 0
    binary: bytes = f.read(1)
    while binary[-1]:
        if length >= maxlen > 0:
            break
        binary += f.read(1)
        length += 1

    binary = binary[:-1]

    if encoding is None:
        encoder = UniversalDetector()
        encoder.feed(binary)
        encoding = encoder.close()["encoding"]

    try:
        if not encoding or encoding.lower() not in {"ascii", "utf-8", "shift-jis", "iso-8859-1"}:
            encoding = "shift-jis"
        return binary.decode(encoding)
    except UnicodeDecodeError:
        return ""


def align_int(num: int, alignment: int) -> int:
    return (num + (alignment - 1)) & -alignment
