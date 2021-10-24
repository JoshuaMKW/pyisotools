from __future__ import annotations

from io import BytesIO
from typing import BinaryIO

from pyisotools.iohelper import read_string, read_uint32, write_uint32


class Apploader(BytesIO):
    def __init__(self, f: BinaryIO):
        f.seek(0x14, 1)
        size = read_uint32(f) + read_uint32(f)
        f.seek(-0x1C, 1)
        super().__init__(f.read(size + 0x20))

    @property
    def buildDate(self) -> str:
        return read_string(self, 0, 10)

    @buildDate.setter
    def buildDate(self, date: str):
        self.seek(0)
        self.write(date[:10].encode("ascii"))

    @property
    def entryPoint(self) -> int:
        self.seek(0x10)
        return read_uint32(self)

    @entryPoint.setter
    def entryPoint(self, addr: int):
        self.seek(0x10)
        write_uint32(self, addr)

    @property
    def loaderSize(self) -> int:
        self.seek(0x14)
        return read_uint32(self)

    @loaderSize.setter
    def loaderSize(self, size: int):
        self.seek(0x14)
        write_uint32(self, size)

    @property
    def trailerSize(self) -> int:
        self.seek(0x18)
        return read_uint32(self)

    @trailerSize.setter
    def trailerSize(self, size: int):
        self.seek(0x18)
        write_uint32(self, size)

    def save(self, f: BinaryIO):
        f.write(self.getvalue()[:self.loaderSize + self.trailerSize + 0x20])
