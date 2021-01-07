import struct

def read_sbyte(f):
    return struct.unpack("b", f.read(1))[0]

def write_sbyte(f, val):
    f.write(struct.pack("b", val))

def read_sint16(f):
    return struct.unpack(">h", f.read(2))[0]

def write_sint16(f, val):
    f.write(struct.pack(">h", val))

def read_sint32(f):
    return struct.unpack(">i", f.read(4))[0]

def write_sint32(f, val):
    f.write(struct.pack(">i", val))

def read_ubyte(f):
    return struct.unpack("B", f.read(1))[0]

def write_ubyte(f, val):
    f.write(struct.pack("B", val))

def read_uint16(f):
    return struct.unpack(">H", f.read(2))[0]

def write_uint16(f, val):
    f.write(struct.pack(">H", val))

def read_uint32(f):
    return struct.unpack(">I", f.read(4))[0]

def write_uint32(f, val):
    f.write(struct.pack(">I", val))

def read_float(f):
    return struct.unpack(">f", f.read(4))[0]

def write_float(f, val):
    f.write(struct.pack(">f", val))

def read_double(f):
    return struct.unpack(">d", f.read(4))[0]

def write_double(f, val):
    f.write(struct.pack(">d", val))

def read_bool(f, vSize=1):
    return struct.unpack("B", f.read(vSize))[0] > 0

def write_bool(f, val, vSize=1):
    f.write(b'\x00'*(vSize-1) + b'\x01') if val is True else f.write(b'\x00' * vSize)

def read_string(io, offset: int = 0, maxlen: int = 0, encoding: str = "ascii") -> str:
    """ Reads a null terminated string from the specified address """

    length = 0
    string = ""

    io.seek(offset)
    while (char := io.read(1)) != b"\x00":
        try:
            string += char.decode(encoding)
            length += 1
        except UnicodeDecodeError:
            raise UnicodeDecodeError(f"{char} at pos {length} is not a valid {encoding} character")
        
        if length > (maxlen-1) and maxlen != 0:
            return string

    return string

def align_int(num: int, alignment: int) -> int:
    return (num + (alignment - 1)) & -alignment