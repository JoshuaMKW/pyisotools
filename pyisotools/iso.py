from __future__ import annotations

import json
from fnmatch import fnmatch
from io import BytesIO
from pathlib import Path
from typing import BinaryIO, Callable, Optional, Union

from dolreader.dol import DolFile
from sortedcontainers import SortedDict, SortedList

from pyisotools.apploader import Apploader
from pyisotools.bi2 import BI2
from pyisotools.bnrparser import BNR
from pyisotools.boot import Boot
from pyisotools.fst import FST, FSTNode, InvalidEntryError, InvalidFSTError
from pyisotools.iohelper import (align_int, read_string, read_ubyte,
                                 read_uint32, write_uint32)


class FileSystemTooLargeError(Exception):
    ...


class FileSystemInvalidError(Exception):
    ...


class _ISOInfo(FST):

    def __init__(self):
        super().__init__()
        self.root: Path = None

        self._curEntry = 0
        self._strOfs = 0
        self._dataOfs = 0
        self._prevfile = None

# pylint: disable=not-callable


class ISOBase(_ISOInfo):

    def __init__(self):
        super().__init__()

        # File extraction callbacks
        self._onPhysicalJobStart: Callable[[int], None] = None
        self._onPhysicalTaskComplete: Callable[[int], None] = None
        self._onPhysicalJobEnd: Callable[[int], None] = None

        # ISO build callbacks
        self._onVirtualJobStart: Callable[[int], None] = None
        self._onVirtualTaskComplete: Callable[[int], None] = None
        self._onVirtualJobEnd: Callable[[int], None] = None

        self.isoPath = None
        self.bootheader = None
        self.bootinfo = None
        self.apploader = None
        self.dol = None
        self._rawFST = None

        self._alignmentTable = SortedDict()
        self._locationTable = SortedDict()
        self._excludeTable = SortedList()

    # pylint: disable=unused-argument
    @staticmethod
    def __default_callback(*args, **kwargs) -> None:
        return None
    # pylint: enable=unused-argument

    @property
    def onPhysicalJobStart(self) -> Callable[[str, int], None]:
        if self._onPhysicalJobStart:
            return self._onPhysicalJobStart
        return self.__default_callback

    @onPhysicalJobStart.setter
    def onPhysicalJobStart(self, callback: Callable[[str, int], None]):
        self._onPhysicalJobStart = callback

    @property
    def onPhysicalTaskStart(self) -> Callable[[str, int], None]:
        if self._onPhysicalTaskStart:
            return self._onPhysicalTaskStart
        return self.__default_callback

    @onPhysicalTaskStart.setter
    def onPhysicalTaskStart(self, callback: Callable[[str, int], None]):
        self._onPhysicalTaskStart = callback

    @property
    def onPhysicalTaskComplete(self) -> Callable[[], None]:
        if self._onPhysicalTaskComplete:
            return self._onPhysicalTaskComplete
        return self.__default_callback

    @onPhysicalTaskComplete.setter
    def onPhysicalTaskComplete(self, callback: Callable[[], None]):
        self._onPhysicalTaskComplete = callback

    @property
    def onPhysicalJobEnd(self) -> Callable[[], None]:
        if self._onPhysicalJobEnd:
            return self._onPhysicalJobEnd
        return self.__default_callback

    @onPhysicalJobEnd.setter
    def onPhysicalJobEnd(self, callback: Callable[[], None]):
        self._onPhysicalJobEnd = callback

    @property
    def onVirtualJobStart(self) -> Callable[[str, int], None]:
        if self._onVirtualJobStart:
            return self._onVirtualJobStart
        return self.__default_callback

    @onVirtualJobStart.setter
    def onVirtualJobStart(self, callback: Callable[[str, int], None]):
        self._onVirtualJobStart = callback

    @property
    def onVirtualTaskStart(self) -> Callable[[str, int], None]:
        if self._onVirtualTaskStart:
            return self._onVirtualTaskStart
        return self.__default_callback

    @onVirtualTaskStart.setter
    def onVirtualTaskStart(self, callback: Callable[[str, int], None]):
        self._onVirtualTaskStart = callback

    @property
    def onVirtualTaskComplete(self) -> Callable[[], None]:
        if self._onVirtualTaskComplete:
            return self._onVirtualTaskComplete
        return self.__default_callback

    @onVirtualTaskComplete.setter
    def onVirtualTaskComplete(self, callback: Callable[[], None]):
        self._onVirtualTaskComplete = callback

    @property
    def onVirtualJobEnd(self) -> Callable[[], None]:
        if self._onVirtualJobEnd:
            return self._onVirtualJobEnd
        return self.__default_callback

    @onVirtualJobEnd.setter
    def onVirtualJobEnd(self, callback: Callable[[], None]):
        self._onVirtualJobEnd = callback

    def _read_nodes(self, fst, node: FSTNode, strTabOfs: int) -> FSTNode:
        _type = read_ubyte(fst)
        _nameOfs = int.from_bytes(fst.read(3), "big", signed=False)
        _entryOfs = read_uint32(fst)
        _size = read_uint32(fst)

        _oldpos = fst.tell()
        node.name = read_string(fst, strTabOfs + _nameOfs)
        fst.seek(_oldpos)

        node._id = self._curEntry

        self._curEntry += 1

        if _type == FSTNode.FOLDER:
            node.type = FSTNode.FOLDER
            node._dirparent = _entryOfs
            node._dirnext = _size

            while self._curEntry < _size:
                child = self._read_nodes(fst, FSTNode.empty(), strTabOfs)
                node.add_child(child)
        else:
            node.type = FSTNode.FILE
            node.size = _size
            node._fileoffset = _entryOfs

        return node

    def _init_tables(self, config: Optional[Path] = None):
        if not config:
            self._alignmentTable = SortedDict()
            self._locationTable = SortedDict()
            self._excludeTable = SortedList()
        elif isinstance(config, dict):
            self._alignmentTable = SortedDict(config["alignment"])
            self._locationTable = SortedDict(config["location"])
            self._excludeTable = SortedList(config["exclude"])
        else:
            with config.open("r") as f:
                data = json.load(f)
            self._alignmentTable = SortedDict(data["alignment"])
            self._locationTable = SortedDict(data["location"])
            self._excludeTable = SortedList(data["exclude"])

    def _recursive_extract(self, node: FSTNode, dest: Path, iso: BinaryIO, dumpPositions: bool = False):
        if node.is_file():
            self.onPhysicalTaskStart(node.path, node.size)
            iso.seek(node._fileoffset)
            dest.write_bytes(iso.read(node.size))
            self.onPhysicalTaskComplete()
        else:
            dest.mkdir(parents=True, exist_ok=True)
            for child in node.children:
                self._recursive_extract(child, dest/child.name, iso)

        if dumpPositions:
            self._locationTable[node.path] = node._fileoffset

    def _collect_size(self, size: int) -> int:
        for node in self.children:
            if self._get_excluded(node) is True or self._get_location(node) is not None:
                continue

            if node.is_file():
                alignment = self._get_alignment(node)
                size = align_int(size, alignment)
                size += node.size
            else:
                size = node._collect_size(size)

        return align_int(size, 4)

    def _get_greatest_alignment(self) -> int:
        try:
            return self._alignmentTable.peekitem()[1]
        except IndexError:
            return 4

    def _get_alignment(self, node: Union[FSTNode, str]) -> int:
        if isinstance(node, FSTNode):
            _path = node.path
        else:
            _path = node

        alignment = 4
        if self._alignmentTable is None:
            return alignment

        for entry, width in self._alignmentTable.items():
            if fnmatch(_path, entry.strip()):
                alignment = width
                break

        return alignment

    def _get_location(self, node: Union[FSTNode, str]) -> int:
        if isinstance(node, FSTNode):
            _path = node.path
        else:
            _path = node

        if self._locationTable:
            return self._locationTable.get(_path)
        return None

    def _get_excluded(self, node: Union[FSTNode, str]) -> bool:
        if isinstance(node, FSTNode):
            _path = node.path
        else:
            _path = node

        if self._excludeTable:
            for entry in self._excludeTable:
                if fnmatch(_path, entry.strip()):
                    return True
        return False


class WiiISO(ISOBase):

    MaxSize = 4699979776


class GamecubeISO(ISOBase):

    MaxSize = 1459978240

    def __init__(self):
        super().__init__()
        self.bnr: Optional[BNR] = None

    @classmethod
    def from_root(cls, root: Path, genNewInfo: bool = False) -> GamecubeISO:
        virtualISO = cls()
        virtualISO.init_from_root(root, genNewInfo)
        return virtualISO

    @classmethod
    def from_iso(cls, iso: Path):
        virtualISO = cls()
        virtualISO.init_from_iso(iso)
        return virtualISO

    @property
    def configPath(self) -> Path:
        if self.root:
            return self.systemPath / ".config.json"
        return None

    @property
    def systemPath(self) -> Path:
        if self.root:
            if self.is_gcr_root():
                return self.root / "&&systemdata"
            return self.root / "sys"
        return None

    @property
    def dataPath(self) -> Path:
        if self.root:
            if self.is_gcr_root():
                return self.root
            return self.root / self.name
        return None

    @staticmethod
    def build_root(root: Path, dest: Union[Path, str] = None, genNewInfo: bool = False):
        virtualISO = GamecubeISO.from_root(root, genNewInfo)
        virtualISO.build(dest)

    @staticmethod
    def extract_from(iso: Path, dest: Union[Path, str] = None):
        virtualISO = GamecubeISO.from_iso(iso)
        virtualISO.extract(dest)

    def is_dolphin_root(self) -> bool:
        if self.root:
            folders = {x.name.lower()
                       for x in self.root.iterdir() if x.is_dir()}
            return "sys" in folders and "files" in folders and "&&systemdata" not in folders
        return False

    def is_gcr_root(self) -> bool:
        if self.root:
            folders = {x.name.lower()
                       for x in self.root.iterdir() if x.is_dir()}
            return "&&systemdata" in folders
        return False

    def build(self, dest: Union[Path, str] = None, preCalc: bool = True):
        if dest is not None:
            fmtpath = str(dest).replace(
                r"%fullname%", f"{self.bootheader.gameName} [{self.bootheader.gameCode}{self.bootheader.makerCode}]")
            fmtpath = fmtpath.replace(r"%name%", self.bootheader.gameName)
            fmtpath = fmtpath.replace(
                r"%gameid%", f"{self.bootheader.gameCode}{self.bootheader.makerCode}")

            self.isoPath = Path(self.root / fmtpath)

        self.isoPath.parent.mkdir(parents=True, exist_ok=True)

        # --- FST --- #

        fstsize = sum([len(n.name) + 13 for n in self.rchildren()])
        self.onVirtualJobStart("FST Generation", fstsize)

        if preCalc:
            self.pre_calc_metadata(
                (self.MaxSize - self.get_auto_blob_size()) & -self._get_greatest_alignment())

        self._rawFST.seek(0)
        self._rawFST.write(b"\x01\x00\x00\x00\x00\x00\x00\x00")
        write_uint32(self._rawFST, len(self))

        _curEntry = 1
        _strOfs = 0
        _strTableOfs = self.strTableOfs
        for child in self.rchildren(includedOnly=True):
            self.onVirtualTaskStart(child.path, len(child.name) + 13)

            child._id = _curEntry
            self._rawFST.write(b"\x01" if child.is_dir() else b"\x00")
            self._rawFST.write((_strOfs).to_bytes(3, "big", signed=False))
            write_uint32(
                self._rawFST, child.parent._id if child.is_dir() else child._fileoffset)
            write_uint32(self._rawFST, len(child) +
                         _curEntry if child.is_dir() else child.size)
            _curEntry += 1

            _oldpos = self._rawFST.tell()
            self._rawFST.seek(_strOfs + _strTableOfs)
            self._rawFST.write(child.name.encode() + b"\x00")
            _strOfs += len(child.name) + 1
            self._rawFST.seek(_oldpos)

            self.onVirtualTaskComplete()

        self.bootheader.fstSize = len(self._rawFST.getbuffer())
        self.bootheader.fstMaxSize = self.bootheader.fstSize

        self.onVirtualJobEnd()

        # ----------- #

        # -- System -- #

        self.onVirtualJobStart("System Generation", 0x2440 + self.apploader.loaderSize +
                               self.apploader.trailerSize + len(self._rawFST.getvalue()))

        if self.is_dolphin_root():
            with Path(self.systemPath, "boot.bin").open("wb") as f:
                self.bootheader.save(f)

            with Path(self.systemPath, "bi2.bin").open("wb") as f:
                self.bootinfo.save(f)

            with Path(self.systemPath, "apploader.img").open("wb") as f:
                self.apploader.save(f)

            with Path(self.systemPath, "fst.bin").open("wb") as f:
                f.write(self._rawFST.getvalue())
        elif self.is_gcr_root():
            with Path(self.systemPath, "ISO.hdr").open("wb") as f:
                self.bootheader.save(f)
                self.bootinfo.save(f)

            with Path(self.systemPath, "AppLoader.ldr").open("wb") as f:
                self.apploader.save(f)

            with Path(self.systemPath, "Game.toc").open("wb") as f:
                f.write(self._rawFST.getvalue())
        else:
            raise InvalidFSTError(f"{self.root} is not a valid root folder")

        self.onVirtualJobEnd()

        # ------------ #

        # -- Files -- #

        self.bnr.save_bnr(Path(self.dataPath, "opening.bnr"))

        self.onVirtualJobStart("(ISO)", self.MaxSize)

        with self.isoPath.open("wb") as f:
            self.onVirtualTaskStart("boot.bin", 0x440)
            self.bootheader.save(f)
            self.onVirtualTaskComplete()

            self.onVirtualTaskStart("bi2.bin", 0x2000)
            self.bootinfo.save(f)
            self.onVirtualTaskComplete()

            self.onVirtualTaskStart(
                "apploader.img", self.apploader.loaderSize + self.apploader.trailerSize)
            self.apploader.save(f)
            self.onVirtualTaskComplete()

            self.onVirtualTaskStart("main.dol", self.dol.size)
            f.write(b"\x00" * (self.bootheader.dolOffset - f.tell()))
            self.dol.save(f, self.bootheader.dolOffset)
            self.onVirtualTaskComplete()

            self.onVirtualTaskStart(
                "FST Padding", (self.bootheader.fstOffset - f.tell()))
            f.seek(f.tell() + self.dol.size)
            f.write(b"\x00" * (self.bootheader.fstOffset - f.tell()))
            self.onVirtualTaskComplete()

            self.onVirtualTaskStart("fst.bin", len(self._rawFST.getbuffer()))
            f.write(self._rawFST.getvalue())
            self.onVirtualTaskComplete()

            for child in self.rfiles(includedOnly=True):
                self.onVirtualTaskStart(child.path, child.size)
                f.write(b"\x00" * (child._fileoffset - f.tell()))
                f.seek(child._fileoffset)
                f.write((self.dataPath / child.path).read_bytes())
                f.seek(0, 2)
                self.onVirtualTaskComplete()

            self.onVirtualTaskStart("Padding", (self.MaxSize - f.tell()))
            f.write(b"\x00" * (self.MaxSize - f.tell()))

        # ----------- #

        self.onVirtualJobEnd()

    def extract(self, dest: Union[Path, str] = None, dumpPositions: bool = True):
        jobSize = self.size + \
            (0x2440 + (self.apploader.loaderSize + self.apploader.trailerSize))
        jobSize += self.dol.size
        jobSize += len(self._rawFST.getbuffer())

        self.onPhysicalJobStart("(System)", jobSize)

        if dest is not None:
            self.root = Path(f"{dest}/root")

        self.root.mkdir(parents=True, exist_ok=True)
        systemPath = self.systemPath
        systemPath.mkdir(exist_ok=True)

        self.onPhysicalTaskStart("boot.bin", 0x440)
        with Path(systemPath, "boot.bin").open("wb") as f:
            self.bootheader.save(f)
        self.onPhysicalTaskComplete()

        self.onPhysicalTaskStart("bi2.bin", 0x2000)
        with Path(systemPath, "bi2.bin").open("wb") as f:
            self.bootinfo.save(f)
        self.onPhysicalTaskComplete()

        self.onPhysicalTaskStart(
            "apploader.img", self.apploader.loaderSize + self.apploader.trailerSize)
        with Path(systemPath, "apploader.img").open("wb") as f:
            self.apploader.save(f)
        self.onPhysicalTaskComplete()

        self.onPhysicalTaskStart("main.dol", self.dol.size)
        with Path(systemPath, "main.dol").open("wb") as f:
            self.dol.save(f)
        self.onPhysicalTaskComplete()

        self.onPhysicalTaskStart("fst.bin", len(self._rawFST.getbuffer()))
        with Path(systemPath, "fst.bin").open("wb") as f:
            f.write(self._rawFST.getvalue())
        self.onPhysicalTaskComplete()

        self.onPhysicalJobEnd()

        self.dataPath.mkdir(parents=True, exist_ok=True)
        self.extract_path("", self.dataPath.parent, dumpPositions)

        self.save_config()

    def extract_system_data(self, dest: Union[Path, str] = None):
        jobSize = 0x2440 + (self.apploader.loaderSize +
                            self.apploader.trailerSize)
        jobSize += self.dol.size
        jobSize += len(self._rawFST.getbuffer())

        self.onPhysicalJobStart("(System)", jobSize)

        systemPath = dest / "sys"
        systemPath.mkdir(parents=True, exist_ok=True)

        self.onPhysicalTaskStart("boot.bin", 0x440)
        with Path(systemPath, "boot.bin").open("wb") as f:
            self.bootheader.save(f)
        self.onPhysicalTaskComplete()

        self.onPhysicalTaskStart("bi2.bin", 0x2000)
        with Path(systemPath, "bi2.bin").open("wb") as f:
            self.bootinfo.save(f)
        self.onPhysicalTaskComplete()

        self.onPhysicalTaskStart(
            "apploader.img", self.apploader.loaderSize + self.apploader.trailerSize)
        with Path(systemPath, "apploader.img").open("wb") as f:
            self.apploader.save(f)
        self.onPhysicalTaskComplete()

        self.onPhysicalTaskStart("main.dol", self.dol.size)
        with Path(systemPath, "main.dol").open("wb") as f:
            self.dol.save(f)
        self.onPhysicalTaskComplete()

        self.onPhysicalTaskStart("fst.bin", len(self._rawFST.getbuffer()))
        with Path(systemPath, "fst.bin").open("wb") as f:
            f.write(self._rawFST.getvalue())
        self.onPhysicalTaskComplete()

        self.onPhysicalJobEnd()

    def save_system_data(self):
        jobSize = 0x2440 + (self.apploader.loaderSize +
                            self.apploader.trailerSize)
        jobSize += self.dol.size
        jobSize += self.num_children()

        self.onPhysicalJobStart("(System)", jobSize)

        systemPath = self.systemPath

        if self.is_dolphin_root():
            self.onPhysicalTaskStart("boot.bin", 0x440)
            with Path(systemPath, "boot.bin").open("wb") as f:
                self.bootheader.save(f)
            self.onPhysicalTaskComplete()

            self.onPhysicalTaskStart("bi2.bin", 0x2000)
            with Path(systemPath, "bi2.bin").open("wb") as f:
                self.bootinfo.save(f)
            self.onPhysicalTaskComplete()

            self.onPhysicalTaskStart(
                "apploader.img", self.apploader.loaderSize + self.apploader.trailerSize)
            with Path(systemPath, "apploader.img").open("wb") as f:
                self.apploader.save(f)
            self.onPhysicalTaskComplete()

            self.onPhysicalTaskStart("main.dol", self.dol.size)
            with Path(systemPath, "main.dol").open("wb") as f:
                self.dol.save(f)
            self.onPhysicalTaskComplete()

        elif self.is_gcr_root():
            self.onPhysicalTaskStart("ISO.hdr", 0x2440)
            with Path(systemPath, "ISO.hdr").open("wb") as f:
                self.bootheader.save(f)
                self.bootinfo.save(f)
            self.onPhysicalTaskComplete()

            self.onPhysicalTaskStart(
                "Apploader.ldr", self.apploader.loaderSize + self.apploader.trailerSize)
            with Path(systemPath, "Apploader.ldr").open("wb") as f:
                self.apploader.save(f)
            self.onPhysicalTaskComplete()

            self.onPhysicalTaskStart("Start.dol", self.dol.size)
            with Path(systemPath, "Start.dol").open("wb") as f:
                self.dol.save(f)
            self.onPhysicalTaskComplete()
        else:
            raise InvalidFSTError(f"{self.root} is not a valid root folder")

        if self.bnr:
            self.bnr.save_bnr(Path(self.dataPath, "opening.bnr"))

        self._save_config_regen()

        self.onPhysicalJobEnd()

    def save_system_datav(self):
        jobSize = 0x2440 + (self.apploader.loaderSize +
                            self.apploader.trailerSize)
        jobSize += self.dol.size

        self.onVirtualJobStart("(System)", jobSize)

        with self.isoPath.open("r+b") as f:
            self.onVirtualTaskStart("boot.bin", 0x440)
            self.bootheader.save(f)
            self.onVirtualTaskComplete()

            self.onVirtualTaskStart("bi2.bin", 0x2000)
            self.bootinfo.save(f)
            self.onVirtualTaskComplete()

            self.onVirtualTaskStart(
                "apploader.img", self.apploader.loaderSize + self.apploader.trailerSize)
            self.apploader.save(f)
            self.onVirtualTaskComplete()

            self.onVirtualTaskStart("main.dol", self.bootheader.dolOffset)
            self.dol.save(f, self.bootheader.dolOffset)
            self.onVirtualTaskComplete()

            bnrNode = self.find_by_path("opening.bnr")
            if bnrNode:
                self.onVirtualTaskStart("opening.bnr", len(self.bnr))
                f.seek(bnrNode._fileoffset)
                f.write(self.bnr._rawdata.getvalue())
                self.onVirtualTaskComplete()

        self.onVirtualJobEnd()

    def get_auto_blob_size(self) -> int:
        _size = 0

        for child in self.rfiles(includedOnly=True):
            if child._position:
                continue

            _size = align_int(_size, child._alignment) + child.size

        return _size

    def init_from_iso(self, iso: Path):
        self.isoPath = iso
        self.root = Path(iso.parent, "root").resolve()

        with iso.open("rb") as _rawISO:
            self.bootheader = Boot(_rawISO)
            self.bootinfo = BI2(_rawISO)
            self.apploader = Apploader(_rawISO)
            self.dol = DolFile(_rawISO, startpos=self.bootheader.dolOffset)
            _rawISO.seek(self.bootheader.fstOffset)
            self._rawFST = BytesIO(_rawISO.read(self.bootheader.fstSize))

        self.load_file_systemv(self._rawFST)

        if self.bootinfo.countryCode == BI2.Country.JAPAN:
            region = BNR.Regions.JAPAN
        else:
            region = self.bootinfo.countryCode - 1

        bnrNode = None
        for child in self.children:
            if child.is_file() and fnmatch(child.path, "*opening.bnr"):
                bnrNode = child
                break

        if bnrNode:
            with iso.open("rb") as _rawISO:
                _rawISO.seek(bnrNode._fileoffset)
                self.bnr = BNR.from_data(
                    _rawISO, region=region, size=bnrNode.size)
        else:
            self.bnr = None

        prev = FSTNode.file("", None, self.bootheader.fstSize,
                            self.bootheader.fstOffset)
        for node in self.nodes_by_offset():
            alignment = self._detect_alignment(node, prev)
            if alignment != 4:
                self._alignmentTable[node.path] = alignment
            prev = node

    def init_from_root(self, root: Path, genNewInfo: bool = False):
        self.root = root

        if self.is_dolphin_root():
            with Path(self.systemPath, "main.dol").open("rb") as f:
                self.dol = DolFile(f)

            with Path(self.systemPath, "boot.bin").open("rb") as f:
                self.bootheader = Boot(f)

            with Path(self.systemPath, "bi2.bin").open("rb") as f:
                self.bootinfo = BI2(f)

            with Path(self.systemPath, "apploader.img").open("rb") as f:
                self.apploader = Apploader(f)
        elif self.is_gcr_root():
            with Path(self.systemPath, "Start.dol").open("rb") as f:
                self.dol = DolFile(f)

            with Path(self.systemPath, "ISO.hdr").open("rb") as f:
                self.bootheader = Boot(f)
                self.bootinfo = BI2(f)

            with Path(self.systemPath, "Apploader.ldr").open("rb") as f:
                self.apploader = Apploader(f)
        else:
            raise FileSystemInvalidError("Non Dolphin or GCR root type found")

        self.bootheader.dolOffset = (
            0x2440 + self.apploader.trailerSize + 0x1FFF) & -0x2000
        self.bootheader.fstOffset = (
            self.bootheader.dolOffset + self.dol.size + 0x3) & -0x4

        self._rawFST = BytesIO()
        self.load_file_system(self.dataPath, self, ignoreList=[])

        self.bootheader.fstSize = len(self._rawFST.getbuffer())
        self.bootheader.fstMaxSize = self.bootheader.fstSize

        if ((self.bootheader.fstOffset + self.bootheader.fstSize + 0x3) & -0x4) + self.datasize > self.MaxSize:
            raise FileSystemTooLargeError(
                f"{((self.bootheader.fstOffset + self.bootheader.fstSize + 0x3) & -0x4) + self.datasize} is larger than the max size of a GCM ({self.MaxSize})")

        if self.bootinfo.countryCode == BI2.Country.JAPAN:
            region = 2
        elif self.bootinfo.countryCode == BI2.Country.KOREA:
            region = 0
        else:
            region = self.bootinfo.countryCode - 1

        for f in self.dataPath.iterdir():
            if f.is_file() and f.match("*opening.bnr"):
                if self._get_excluded(f.name):
                    continue
                self.bnr = BNR(f, region=region)
                break

        if self.configPath.is_file() and genNewInfo:
            self.load_config(self.configPath)

        self.isoPath = Path(
            root.parent / f"{self.bootheader.gameName} [{self.bootheader.gameCode}{self.bootheader.makerCode}].iso").resolve()

    def extract_path(self, path: Union[Path, str], dest: Union[Path, str], dumpPositions: bool = False):
        if isinstance(path, str):
            path = Path(path)

        if isinstance(dest, str):
            dest = Path(dest)

        node = self.find_by_path(path)
        if not node:
            return

        jobSize = node.datasize
        self.onPhysicalJobStart("(Files)", jobSize)

        with self.isoPath.open("rb") as _rawISO:
            self._recursive_extract(
                node, dest / node.name, _rawISO, dumpPositions)

        self.onPhysicalJobEnd()

    def replace_path(self, path: str, new: Path):
        """
        Replaces the node that matches `path` with the data at path `new`

            path: Virtual path to node to replace
            new:  Path to file/folder to replace with
        """
        if not new.exists():
            return

        newNode = self.from_path(new)
        oldNode = self.find_by_path(path)

        oldNode.parent.add_child(newNode)
        oldNode.destroy()

    ## FST HANDLING ##

    def pre_calc_metadata(self, startpos: int):
        """
        Pre calculates all node offsets for viewing the node locations before compile

        The results of this function are only valid until the FST is changed in
        a way that impacts file offsets
        """
        _dataOfs = align_int(startpos, 4)
        _curEntry = 1
        _minOffset = self.MaxSize - 4
        for child in self.rchildren():
            if child.is_file() and child._position:
                child._fileoffset = align_int(
                    child._position, child._alignment)
                if child._fileoffset < _minOffset:
                    _minOffset = child._fileoffset

            if child._exclude:
                if child.is_file():
                    child._fileoffset = 0
                continue

            child._id = _curEntry
            _curEntry += 1

            if child.is_file():
                if not child._position:
                    _dataOfs = align_int(_dataOfs, child._alignment)
                    child._fileoffset = _dataOfs
                    if child._fileoffset < _minOffset:
                        _minOffset = child._fileoffset

                    _dataOfs += child.size
            else:
                child._dirparent = child.parent._id
                child._dirnext = child.size + child._id

        self.bootheader.firstFileOffset = max(_minOffset, 0)

    def load_file_system(self, path: Path, parentnode: FSTNode = None, ignoreList=None):
        """
        Converts a directory into an FST and loads into self for further use

            path:       Path to input directory
            parentnode: Parent to store all info under
            ignorelist: List of filepaths to ignore as glob patterns
        """
        if ignoreList is None:
            ignoreList = []

        self._init_tables(self.configPath)

        if len(self._excludeTable) > 0:
            ignoreList.extend(self._excludeTable)

        self._load_from_path(path, parentnode, ignoreList)
        self.pre_calc_metadata(
            (self.MaxSize - self.get_auto_blob_size()) & -self._get_greatest_alignment())

    def load_file_systemv(self, fst: BinaryIO):
        """
        Loads the file system data from a memory buffer into self for further use

            fst: BytesIO or opened file object containing the FST of an ISO
        """

        if fst.read(1) != b"\x01":
            raise InvalidFSTError("Invalid Root flag found")
        if fst.read(3) != b"\x00\x00\x00":
            raise InvalidFSTError("Invalid Root string offset found")
        if fst.read(4) != b"\x00\x00\x00\x00":
            raise InvalidFSTError("Invalid Root offset found")

        self._alignmentTable = SortedDict()
        entryCount = read_uint32(fst)

        self._curEntry = 1
        while self._curEntry < entryCount:
            child = self._read_nodes(fst, FSTNode.empty(), entryCount * 0xC)
            self.add_child(child)

    def load_config(self, path: Path):
        if not path.is_file():
            return

        with path.open("r") as f:
            data = json.load(f)

        self._init_tables(data)

        config = {
            "alignment": self._alignmentTable,
            "location": {k: self._locationTable[k] for k in sorted(self._locationTable, key=str.upper)},
            "exclude": list(self._excludeTable)
        }

        with path.open("w") as f:
            json.dump(config, f, indent=4)

    def save_config(self):
        config = {
            "alignment": self._alignmentTable,
            "location": {k: self._locationTable[k] for k in sorted(self._locationTable, key=str.upper)},
            "exclude": list(self._excludeTable)
        }

        with self.configPath.open("w") as f:
            json.dump(config, f, indent=4)

    def _load_from_path(self, path: Path, parentnode: FSTNode = None, ignoreList: tuple = ()):
        for entry in sorted(path.iterdir(), key=lambda x: x.name.upper()):
            if self.is_gcr_root() and entry.name.lower() == "&&systemdata":
                continue

            disable = False
            for badPath in ignoreList:
                if entry.match(badPath):
                    disable = True

            if entry.is_file():
                child = FSTNode.file(
                    entry.name, parent=parentnode, size=entry.stat().st_size)
                child._alignment = self._get_alignment(child)
                child._position = self._get_location(child)
                child._exclude = disable
                child.size = entry.stat().st_size

            elif entry.is_dir():
                child = FSTNode.folder(entry.name)

                if parentnode is not None:
                    parentnode.add_child(child)

                self._load_from_path(entry, child, ignoreList=ignoreList)
            else:
                raise InvalidEntryError("Not a dir or file")

    def _save_config_regen(self):
        self._alignmentTable.clear()
        self._locationTable.clear()
        self._excludeTable.clear()

        for node in self.rchildren():
            if node.is_file():
                if node._alignment != 4:
                    self._alignmentTable[node.path] = node._alignment
                if node._position:
                    self._locationTable[node.path] = node._position
            if node._exclude:
                self._excludeTable.add(node.path)

        self.save_config()

# pylint: enable=not-callable
