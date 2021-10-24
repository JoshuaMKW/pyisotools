from __future__ import annotations
from enum import IntEnum

from io import BytesIO
from typing import BinaryIO

from pyisotools.iohelper import (read_string, read_ubyte, read_uint32,
                                 write_ubyte, write_uint32)


class BootHeader(BytesIO):
    class Country(IntEnum):
        JAPAN = 0
        AMERICA = 1
        PAL = 2
        KOREA = 0

    class Type(IntEnum):
        GCN = 0
        WII = 1
        UNKNOWN = -1

    class Magic(IntEnum):
        GCNMAGIC = 0xC2339F3D
        WIIMAGIC = 0x5D1C9EA3

    def __init__(self, f: BinaryIO):
        super().__init__(f.read(0x440))

    @property
    def gameCode(self) -> str:
        return read_string(self, 0, 4)

    @gameCode.setter
    def gameCode(self, code: str):
        self.seek(0)
        self.write(code[:4].encode("ascii"))

    @property
    def makerCode(self) -> str:
        return read_string(self, 4, 2)

    @makerCode.setter
    def makerCode(self, code: str):
        self.seek(4)
        self.write(code[:2].encode("ascii"))

    @property
    def diskID(self) -> int:
        self.seek(6)
        return read_ubyte(self)

    @diskID.setter
    def diskID(self, _id: int):
        self.seek(6)
        write_ubyte(self, _id)

    @property
    def version(self) -> int:
        self.seek(7)
        return read_ubyte(self)

    @version.setter
    def version(self, version: int):
        self.seek(7)
        write_ubyte(self, version)

    @property
    def audioStreaming(self) -> bool:
        self.seek(8)
        return True if self.read(1) == b"\x01" else False

    @audioStreaming.setter
    def audioStreaming(self, active: bool):
        self.seek(8)
        self.write(b"\x01" if active is True else b"\x00")

    @property
    def streamBufferSize(self) -> int:
        self.seek(9)
        return read_ubyte(self)

    @streamBufferSize.setter
    def streamBufferSize(self, size: int):
        self.seek(9)
        write_ubyte(self, size)

    @property
    def gameType(self) -> BootHeader.Type:
        self.seek(24)
        if read_uint32(self) == BootHeader.Magic.WIIMAGIC:
            return BootHeader.Type.WII
        elif read_uint32(self) == BootHeader.Magic.GCNMAGIC:
            return BootHeader.Type.GCN
        else:
            return BootHeader.Type.UNKNOWN

    @gameType.setter
    def gameType(self, _type: BootHeader.Type):
        self.seek(24)
        if _type == BootHeader.Type.WII:
            write_uint32(self, BootHeader.Magic.WIIMAGIC)
            write_uint32(self, 0)
        elif _type == BootHeader.Type.GCN:
            write_uint32(self, 0)
            write_uint32(self, BootHeader.Magic.GCNMAGIC)
        else:
            write_uint32(self, 0)
            write_uint32(self, 0)

    @property
    def gameName(self) -> str:
        return read_string(self, 0x20, 0x3E0)

    @gameName.setter
    def gameName(self, name: str):
        self.seek(0x20)
        self.write(name[:0x3E0].encode("ascii"))

    @property
    def debugMonitorOffset(self) -> int:
        self.seek(0x400)
        return read_uint32(self)

    @debugMonitorOffset.setter
    def debugMonitorOffset(self, offset: int):
        self.seek(0x400)
        write_uint32(self, offset)

    @property
    def debugMonitorVirtualAddr(self) -> int:
        self.seek(0x404)
        return read_uint32(self)

    @debugMonitorVirtualAddr.setter
    def debugMonitorVirtualAddr(self, addr: int):
        self.seek(0x404)
        write_uint32(self, addr)

    @property
    def dolOffset(self) -> int:
        self.seek(0x420)
        return read_uint32(self)

    @dolOffset.setter
    def dolOffset(self, offset: int):
        self.seek(0x420)
        write_uint32(self, offset)

    @property
    def fstOffset(self) -> int:
        self.seek(0x424)
        return read_uint32(self)

    @fstOffset.setter
    def fstOffset(self, offset: int):
        self.seek(0x424)
        write_uint32(self, offset)

    @property
    def fstSize(self) -> int:
        self.seek(0x428)
        return read_uint32(self)

    @fstSize.setter
    def fstSize(self, size: int):
        self.seek(0x428)
        write_uint32(self, size)

    @property
    def fstMaxSize(self) -> int:
        self.seek(0x42C)
        return read_uint32(self)

    @fstMaxSize.setter
    def fstMaxSize(self, size: int):
        self.seek(0x42C)
        write_uint32(self, size)

    @property
    def userVirtualAddress(self) -> int:
        self.seek(0x430)
        return read_uint32(self)

    @userVirtualAddress.setter
    def userVirtualAddress(self, addr: int):
        self.seek(0x430)
        write_uint32(self, addr)

    @property
    def firstFileOffset(self) -> int:
        self.seek(0x434)
        return read_uint32(self)

    @firstFileOffset.setter
    def firstFileOffset(self, size: int):
        self.seek(0x434)
        write_uint32(self, size)

    def save(self, _io):
        _io.write(self.getvalue()[:0x440])
