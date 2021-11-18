import struct
from pathlib import Path
from typing import BinaryIO, Optional

from chardet import UniversalDetector


# pylint: disable=invalid-name
class classproperty(property):
    def __get__(self, cls, owner):
        return classmethod(self.fget).__get__(None, owner)()
# pylint: enable=invalid-name


def resource_path(relPath: str = "") -> Path:
    """ Get absolute path to resource, works for dev and for cx_freeze """
    import sys

    if hasattr(sys, "_MEIPASS"):
        return getattr(sys, "_MEIPASS", Path(__file__).parent) / relPath
    else:
        if getattr(sys, "frozen", False):
            # The application is frozen
            base_path = Path(sys.executable).parent
        else:
            base_path = Path(__file__).parent

        return base_path / relPath


def get_program_folder(folder: str = "") -> Path:
    """ Get path to appdata """
    from os import getenv
    import sys

    if sys.platform == "win32":
        datapath = Path(getenv("APPDATA")) / folder
    elif sys.platform == "darwin":
        if folder:
            folder = "." + folder
        datapath = Path("~/Library/Application Support").expanduser() / folder
    elif "linux" in sys.platform:
        if folder:
            folder = "." + folder
        datapath = Path.home() / folder
    else:
        raise NotImplementedError(f"{sys.platform} OS is unsupported")
    return datapath


def align_int(num: int, alignment: int) -> int:
    return (num + (alignment - 1)) & -alignment


# bytes pretty-printing
UNITS_MAPPING = (
    (1 << 50, " PB"),
    (1 << 40, " TB"),
    (1 << 30, " GB"),
    (1 << 20, " MB"),
    (1 << 10, " KB"),
    (1, (" byte", " bytes")),
)


# CREDITS: https://stackoverflow.com/a/12912296/13189621
def pretty_filesize(bytes, units=UNITS_MAPPING):
    """Get human-readable file sizes.
    simplified version of https://pypi.python.org/pypi/hurry.filesize/
    """
    for factor, suffix in units:
        if bytes >= factor:
            break
    amount = int(bytes / factor)

    if isinstance(suffix, tuple):
        singular, multiple = suffix
        if amount == 1:
            suffix = singular
        else:
            suffix = multiple
    return str(amount) + suffix


def bytes_to_string(data: bytes, encoding: Optional[str] = None) -> str:
    """
    Smartly decodes an array of bytes to a string using `chardet`
    """
    KNOWN_ENCODES = {"ascii", "utf-8", "shift-jis", "iso-8859-1"}
    if encoding is None:
        encoder = UniversalDetector()
        encoder.feed(data)
        encoding = encoder.close()["encoding"]

    try:
        if not encoding or encoding.lower() not in KNOWN_ENCODES:
            encoding = "shift-jis"
        return data.decode(encoding)
    except UnicodeDecodeError:
        return ""


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

    return bytes_to_string(binary[:-1], encoding=encoding)
