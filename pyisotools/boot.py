from __future__ import annotations

from io import BytesIO

from pyisotools.iohelper import (read_string, read_ubyte, read_uint32,
                                 write_ubyte, write_uint32)


class Boot():

    class Country:
        JAPAN = 0
        AMERICA = 1
        PAL = 2
        KOREA = 0

    class Type:
        GCN = 0
        WII = 1
        UNKNOWN = -1

    class Magic:
        GCNMAGIC = 0xC2339F3D
        WIIMAGIC = 0x5D1C9EA3

    def __init__(self, f):
        self._rawdata = BytesIO(f.read(0x440))

    @property
    def gameCode(self) -> str:
        return read_string(self._rawdata, 0, 4)

    @gameCode.setter
    def gameCode(self, code: str):
        self._rawdata.seek(0)
        self._rawdata.write(code[:4].encode("ascii"))

    @property
    def makerCode(self) -> str:
        return read_string(self._rawdata, 4, 2)

    @makerCode.setter
    def makerCode(self, code: str):
        self._rawdata.seek(4)
        self._rawdata.write(code[:2].encode("ascii"))

    @property
    def diskID(self) -> int:
        self._rawdata.seek(6)
        return read_ubyte(self._rawdata)

    @diskID.setter
    def diskID(self, _id: int):
        self._rawdata.seek(6)
        write_ubyte(self._rawdata, _id)

    @property
    def version(self) -> int:
        self._rawdata.seek(7)
        return read_ubyte(self._rawdata)

    @version.setter
    def version(self, version: int):
        self._rawdata.seek(7)
        write_ubyte(self._rawdata, version)

    @property
    def audioStreaming(self) -> bool:
        self._rawdata.seek(8)
        return bool(self._rawdata.read(1))

    @audioStreaming.setter
    def audioStreaming(self, active: bool):
        self._rawdata.seek(8)
        self._rawdata.write(b"\x01" if active is True else b"\x00")

    @property
    def streamBufferSize(self) -> int:
        self._rawdata.seek(9)
        return read_ubyte(self._rawdata)

    @streamBufferSize.setter
    def streamBufferSize(self, size: int):
        self._rawdata.seek(9)
        write_ubyte(self._rawdata, size)

    @property
    def gameType(self) -> Boot.Type:
        self._rawdata.seek(24)
        if read_uint32(self._rawdata) == Boot.Magic.WIIMAGIC:
            return Boot.Type.WII
        if read_uint32(self._rawdata) == Boot.Magic.GCNMAGIC:
            return Boot.Type.GCN
        return Boot.Type.UNKNOWN

    @gameType.setter
    def gameType(self, _type: Boot.Type):
        self._rawdata.seek(24)
        if _type == Boot.Type.WII:
            write_uint32(self._rawdata, Boot.Magic.WIIMAGIC)
            write_uint32(self._rawdata, 0)
        elif _type == Boot.Type.GCN:
            write_uint32(self._rawdata, 0)
            write_uint32(self._rawdata, Boot.Magic.GCNMAGIC)
        else:
            write_uint32(self._rawdata, 0)
            write_uint32(self._rawdata, 0)

    @property
    def gameName(self) -> str:
        return read_string(self._rawdata, 0x20, 0x3E0)

    @gameName.setter
    def gameName(self, name: str):
        self._rawdata.seek(0x20)
        self._rawdata.write(name[:0x3E0].encode("ascii"))

    @property
    def debugMonitorOffset(self) -> int:
        self._rawdata.seek(0x400)
        return read_uint32(self._rawdata)

    @debugMonitorOffset.setter
    def debugMonitorOffset(self, offset: int):
        self._rawdata.seek(0x400)
        write_uint32(self._rawdata, offset)

    @property
    def debugMonitorVirtualAddr(self) -> int:
        self._rawdata.seek(0x404)
        return read_uint32(self._rawdata)

    @debugMonitorVirtualAddr.setter
    def debugMonitorVirtualAddr(self, addr: int):
        self._rawdata.seek(0x404)
        write_uint32(self._rawdata, addr)

    @property
    def dolOffset(self) -> int:
        self._rawdata.seek(0x420)
        return read_uint32(self._rawdata)

    @dolOffset.setter
    def dolOffset(self, offset: int):
        self._rawdata.seek(0x420)
        write_uint32(self._rawdata, offset)

    @property
    def fstOffset(self) -> int:
        self._rawdata.seek(0x424)
        return read_uint32(self._rawdata)

    @fstOffset.setter
    def fstOffset(self, offset: int):
        self._rawdata.seek(0x424)
        write_uint32(self._rawdata, offset)

    @property
    def fstSize(self) -> int:
        self._rawdata.seek(0x428)
        return read_uint32(self._rawdata)

    @fstSize.setter
    def fstSize(self, size: int):
        self._rawdata.seek(0x428)
        write_uint32(self._rawdata, size)

    @property
    def fstMaxSize(self) -> int:
        self._rawdata.seek(0x42C)
        return read_uint32(self._rawdata)

    @fstMaxSize.setter
    def fstMaxSize(self, size: int):
        self._rawdata.seek(0x42C)
        write_uint32(self._rawdata, size)

    @property
    def userVirtualAddress(self) -> int:
        self._rawdata.seek(0x430)
        return read_uint32(self._rawdata)

    @userVirtualAddress.setter
    def userVirtualAddress(self, addr: int):
        self._rawdata.seek(0x430)
        write_uint32(self._rawdata, addr)

    @property
    def firstFileOffset(self) -> int:
        self._rawdata.seek(0x434)
        return read_uint32(self._rawdata)

    @firstFileOffset.setter
    def firstFileOffset(self, size: int):
        self._rawdata.seek(0x434)
        write_uint32(self._rawdata, size)

    def save(self, _io):
        _io.write(self._rawdata.getvalue()[:0x440])
