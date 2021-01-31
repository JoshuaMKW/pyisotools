from __future__ import annotations

import os
from io import BytesIO
from pathlib import Path

from pyisotools.iohelper import read_string, read_uint32, write_uint32


class BI2(object):

    class Country:
        JAPAN = 0
        AMERICA = 1
        EUROPE = 2
        KOREA = 0

    def __init__(self, f):
        self._rawdata = BytesIO(f.read(0x2000))

    @property
    def debugMonitorSize(self) -> int:
        self._rawdata.seek(0)
        return read_uint32(self._rawdata)

    @debugMonitorSize.setter
    def debugMonitorSize(self, size: int):
        self._rawdata.seek(0)
        write_uint32(self._rawdata, size)

    @property
    def simulatedMemSize(self) -> int:
        self._rawdata.seek(4)
        return read_uint32(self._rawdata)

    @simulatedMemSize.setter
    def simulatedMemSize(self, size: int):
        self._rawdata.seek(4)
        write_uint32(self._rawdata, size)

    @property
    def debugFlag(self) -> int:
        self._rawdata.seek(8)
        return read_uint32(self._rawdata)

    @debugFlag.setter
    def debugFlag(self, flag: int):
        self._rawdata.seek(8)
        write_uint32(self._rawdata, flag)
    
    @property
    def argumentOffset(self) -> int:
        self._rawdata.seek(12)
        return read_uint32(self._rawdata)

    @argumentOffset.setter
    def argumentOffset(self, offset: int):
        self._rawdata.seek(12)
        write_uint32(self._rawdata, offset)

    @property
    def trackLocation(self) -> int:
        self._rawdata.seek(16)
        return read_uint32(self._rawdata)

    @trackLocation.setter
    def trackLocation(self, loc: int):
        self._rawdata.seek(16)
        write_uint32(self._rawdata, loc)

    @property
    def trackSize(self) -> int:
        self._rawdata.seek(20)
        return read_uint32(self._rawdata)

    @trackSize.setter
    def trackSize(self, size: int):
        self._rawdata.seek(20)
        write_uint32(self._rawdata, size)
    
    @property
    def countryCode(self) -> int:
        self._rawdata.seek(24)
        return read_uint32(self._rawdata)

    @countryCode.setter
    def countryCode(self, code: BI2.Country):
        self._rawdata.seek(24)
        write_uint32(self._rawdata, code)

    def save(self, _io):
        _io.write(self._rawdata.getvalue()[:0x2000])
