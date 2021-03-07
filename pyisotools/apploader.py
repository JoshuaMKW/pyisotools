from __future__ import annotations

from io import BytesIO

from pyisotools.iohelper import read_string, read_uint32, write_uint32


class Apploader(object):

    def __init__(self, f):
        f.seek(0x14, 1)
        size = read_uint32(f)
        size += read_uint32(f)
        f.seek(-0x1C, 1)
        self._rawdata = BytesIO(f.read(size + 0x20))

    @property
    def buildDate(self) -> str:
        return read_string(self._rawdata, 0, 10)

    @buildDate.setter
    def buildDate(self, date: str):
        self._rawdata.seek(0)
        self._rawdata.write(date[:10].encode("ascii"))

    @property
    def entryPoint(self) -> int:
        self._rawdata.seek(0x10)
        return read_uint32(self._rawdata)

    @entryPoint.setter
    def entryPoint(self, addr: int):
        self._rawdata.seek(0x10)
        write_uint32(self._rawdata, addr)

    @property
    def loaderSize(self) -> int:
        self._rawdata.seek(0x14)
        return read_uint32(self._rawdata)

    @loaderSize.setter
    def loaderSize(self, size: int):
        self._rawdata.seek(0x14)
        write_uint32(self._rawdata, size)

    @property
    def trailerSize(self) -> int:
        self._rawdata.seek(0x18)
        return read_uint32(self._rawdata)

    @trailerSize.setter
    def trailerSize(self, size: int):
        self._rawdata.seek(0x18)
        write_uint32(self._rawdata, size)

    def save(self, _io):
        _io.write(self._rawdata.getvalue()[:self.loaderSize + self.trailerSize + 0x20])
