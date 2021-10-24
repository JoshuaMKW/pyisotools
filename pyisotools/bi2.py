from __future__ import annotations
from enum import IntEnum

from io import BytesIO
from typing import BinaryIO

from pyisotools.iohelper import read_uint32, write_uint32


class BI2(BytesIO):
    class Country(IntEnum):
        JAPAN = 0
        AMERICA = 1
        EUROPE = 2
        KOREA = 0

    def __init__(self, f: BinaryIO):
        super().__init__(f.read(0x2000))

    @property
    def debugMonitorSize(self) -> int:
        self.seek(0)
        return read_uint32(self)

    @debugMonitorSize.setter
    def debugMonitorSize(self, size: int):
        self.seek(0)
        write_uint32(self, size)

    @property
    def simulatedMemSize(self) -> int:
        self.seek(4)
        return read_uint32(self)

    @simulatedMemSize.setter
    def simulatedMemSize(self, size: int):
        self.seek(4)
        write_uint32(self, size)

    @property
    def debugFlag(self) -> int:
        self.seek(8)
        return read_uint32(self)

    @debugFlag.setter
    def debugFlag(self, flag: int):
        self.seek(8)
        write_uint32(self, flag)

    @property
    def argumentOffset(self) -> int:
        self.seek(12)
        return read_uint32(self)

    @argumentOffset.setter
    def argumentOffset(self, offset: int):
        self.seek(12)
        write_uint32(self, offset)

    @property
    def trackLocation(self) -> int:
        self.seek(16)
        return read_uint32(self)

    @trackLocation.setter
    def trackLocation(self, loc: int):
        self.seek(16)
        write_uint32(self, loc)

    @property
    def trackSize(self) -> int:
        self.seek(20)
        return read_uint32(self)

    @trackSize.setter
    def trackSize(self, size: int):
        self.seek(20)
        write_uint32(self, size)

    @property
    def countryCode(self) -> int:
        self.seek(24)
        return read_uint32(self)

    @countryCode.setter
    def countryCode(self, code: BI2.Country):
        self.seek(24)
        write_uint32(self, code)

    def save(self, f: BinaryIO):
        f.write(self.getvalue()[:0x2000])
