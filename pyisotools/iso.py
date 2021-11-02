from __future__ import annotations

import json
from abc import ABC, abstractmethod
from fnmatch import fnmatch
from io import BytesIO
from pathlib import Path
from typing import BinaryIO, Callable, Dict, List, Optional, Tuple, Union

from dolreader.dol import DolFile
from sortedcontainers import SortedDict, SortedList

from pyisotools.apploader import Apploader
from pyisotools.bi2 import BI2
from pyisotools.bnrparser import BNR
from pyisotools.boot import Boot
from pyisotools.fst import (FileSystemTable, FSTFile, FSTFolder,
                            FSTInvalidError, FSTInvalidNodeError, FSTNode)
from pyisotools.iohelper import (align_int, read_string, read_ubyte,
                                 read_uint32, write_uint32)
from pyisotools.partition import Partition, PartitionInvalidError


class DiscTooLargeError(Exception):
    ...


# pylint: disable=not-callable


class BaseISO(ABC):
    def __init__(self):
        super().__init__()
        self.partitions: Dict[str, Partition] = {}

    @staticmethod
    def get_auto_data_size(partition: Partition) -> int:
        _size = 0

        for child in partition.recurse_files(includedOnly=True):
            if child.position:
                continue

            _size = align_int(_size, child.alignment) + child.size

        return _size

    @staticmethod
    @abstractmethod
    def build_root(root: Path, dest: Union[Path, str] = None, genNewInfo: bool = False):
        ...

    @staticmethod
    @abstractmethod
    def extract_iso(iso: Path, dest: Union[Path, str] = None):
        ...

    @abstractmethod
    def init_from_iso(self, iso: Union[Path, str]):
        ...

    @abstractmethod
    def init_from_root(self, root: Union[Path, str]):
        ...

    @abstractmethod
    def build(dest: Optional[Union[Path, str]] = None, preCalc: bool = True):
        ...

    @abstractmethod
    def extract(self, dest: Optional[Union[Path, str]] = None, dumpPositions: bool = True):
        ...

    def extract_path(
        self,
        path: Union[Path, str],
        dest: Union[Path, str],
        partitionName: str = "DATA",
        dumpPositions: bool = False,
        blockEnterExitSignals: bool = False
    ):
        """
        Extracts the data at `path`, which is a path within the partition as referenced by `partitionName`, and stores it at `dest`
        """
        if partitionName not in self.partitions:
            return

        partition = self.partitions[partitionName]

        if isinstance(path, str):
            path = Path(path)

        if isinstance(dest, str):
            dest = Path(dest)

        node = partition.find_by_path(path)
        if not node:
            return

        if not blockEnterExitSignals:
            jobSize = node.datasize
            self.onPhysicalJobEnter(jobSize)

        with self.isoPath.open("rb") as _rawISO:
            self._recursive_extract(
                node, dest / node.name, _rawISO, dumpPositions)

        if not blockEnterExitSignals:
            self.onPhysicalJobExit(jobSize)

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

    def add_partition(self, partition: Partition):
        self.partitions.append(partition)

    def remove_partition(self, partition: Partition):
        self.partitions.remove(partition)

    def _load_from_path(self, path: Path, parentNode: FSTNode = None, ignoreList: tuple = ()):
        for entry in sorted(path.iterdir(), key=lambda x: x.name.upper()):
            if self.is_gcr_root() and entry.name.lower() == "&&systemdata":
                continue

            disable = False
            for badPath in ignoreList:
                if entry.match(badPath):
                    disable = True

            if entry.is_file():
                child = FSTFile(
                    name=entry.name,
                    size=entry.stat().st_size,
                )

                if parentNode is not None:
                    parentNode.add_child(child)

                child.alignment = self._get_alignment(child)
                child.position = self._get_location(child)
                child._exclude = disable
                child.size = entry.stat().st_size

            elif entry.is_dir():
                child = FSTFolder(entry.name)

                if parentNode is not None:
                    parentNode.add_child(child)

                self._load_from_path(entry, child, ignoreList=ignoreList)
            else:
                raise FSTInvalidNodeError("Not a dir or file")

    def _recursive_extract(self, node: FSTNode, dest: Path, iso: BinaryIO, dumpPositions: bool = False):
        self.onPhysicalTaskDescribe(node.absPath)
        if node.is_file():
            iso.seek(node._fileoffset)
            dest.write_bytes(iso.read(node.size))
            self.onPhysicalTaskComplete(node.size)
        else:
            dest.mkdir(parents=True, exist_ok=True)
            for child in node.children:
                self._recursive_extract(child, dest/child.name, iso)
            self.onPhysicalTaskComplete(0)

        if dumpPositions:
            self._locationTable[node.absPath] = node._fileoffset


class WiiISO():

    MaxSize = 4699979776

    @classmethod
    def from_root(cls, root: Path) -> BaseISO:
        virtualISO = cls()
        virtualISO.init_from_root(root)
        return virtualISO

    @classmethod
    def from_iso(cls, iso: Path):
        virtualISO = cls()
        virtualISO.init_from_iso(iso)
        return virtualISO


class GamecubeISO():

    MaxSize = 1459978240

    def __init__(self):
        super().__init__()
        self.bnr: Optional[BNR] = None

    @classmethod
    def from_root(cls, root: Path) -> BaseISO:
        virtualISO = cls()
        virtualISO.init_from_root(root)
        return virtualISO

    @classmethod
    def from_iso(cls, iso: Path):
        virtualISO = cls()
        virtualISO.init_from_iso(iso)
        return virtualISO

    def build(self, dest: Union[Path, str] = None, preCalc: bool = True):
        self.onVirtualJobEnter(self.MaxSize)

        if dest is not None:
            fmtpath = str(dest).replace(
                r"%fullname%", f"{self.bootheader.gameName} [{self.bootheader.gameCode}{self.bootheader.makerCode}]")
            fmtpath = fmtpath.replace(r"%name%", self.bootheader.gameName)
            fmtpath = fmtpath.replace(
                r"%gameid%", f"{self.bootheader.gameCode}{self.bootheader.makerCode}")

            self.isoPath = Path(self.root / fmtpath)

        self.isoPath.parent.mkdir(parents=True, exist_ok=True)

        # --- FST --- #

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

        self.bootheader.fstSize = len(self._rawFST.getbuffer())
        self.bootheader.fstMaxSize = self.bootheader.fstSize

        # ----------- #

        # -- System -- #

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
            raise FSTInvalidError(f"{self.root} is not a valid root folder")

        # ------------ #

        # -- Files -- #

        self.bnr.save_bnr(self.dataPath / "opening.bnr")

        with self.isoPath.open("wb") as f:
            self.save_system_datav(f, True)

            for child in self.rfiles(includedOnly=True):
                self.onVirtualTaskDescribe(child.absPath)
                f.write(b"\x00" * (child._fileoffset - f.tell()))
                f.seek(child._fileoffset)
                f.write((self.dataPath / child.absPath).read_bytes())
                f.seek(0, 2)
                self.onVirtualTaskComplete(child.datasize)

            padSize = self.MaxSize - f.tell()
            f.write(b"\x00" * padSize)
            self.onVirtualTaskComplete(child.padSize)

        # ----------- #

        self.onVirtualJobExit(self.MaxSize)

    def extract(self, dest: Optional[Union[Path, str]] = None, dumpPositions: bool = True):
        """
        Extracts the entire contents of this virtual filesystem (ISO) to a path described by `dest`

        `dest`: Where to extract the root filesystem to. If None it will be the default root path
        `dumpPositions`: If true, the position of every file will be dumped into the `.config.json`
        """
        jobSize = self.datasize + self._get_sys_size()
        self.onPhysicalJobEnter(jobSize)

        if dest is not None:
            self.root = Path(f"{dest}/root")

        # Create `root` and `files` folders
        self.root.mkdir(parents=True, exist_ok=True)
        self.dataPath.mkdir(parents=True, exist_ok=True)

        self.extract_system_data(self.systemPath, blockEnterExitSignals=True)
        self.extract_path("", self.dataPath.parent,
                          dumpPositions, blockEnterExitSignals=True)
        self.save_config()

        self.onPhysicalJobExit(jobSize)

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
            if child.is_file() and fnmatch(child.absPath, "*opening.bnr"):
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
                self._alignmentTable[node.absPath] = alignment
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
            raise PartitionInvalidError("Non Dolphin or GCR root type found")

        self.bootheader.dolOffset = (
            0x2440 + self.apploader.trailerSize + 0x1FFF) & -0x2000
        self.bootheader.fstOffset = (
            self.bootheader.dolOffset + self.dol.size + 0x3) & -0x4

        self._rawFST = BytesIO()
        self.load_file_system(self.dataPath, self, ignoreList=[])

        self.bootheader.fstSize = len(self._rawFST.getbuffer())
        self.bootheader.fstMaxSize = self.bootheader.fstSize

        if ((self.bootheader.fstOffset + self.bootheader.fstSize + 0x3) & -0x4) + self.datasize > self.MaxSize:
            raise DiscTooLargeError(
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

    def extract_path(self, path: Union[Path, str], dest: Union[Path, str], dumpPositions: bool = False, blockEnterExitSignals: bool = False):
        if isinstance(path, str):
            path = Path(path)

        if isinstance(dest, str):
            dest = Path(dest)

        node = self.find_by_path(path)
        if not node:
            return

        if not blockEnterExitSignals:
            jobSize = node.datasize
            self.onPhysicalJobEnter(jobSize)

        with self.isoPath.open("rb") as _rawISO:
            self._recursive_extract(
                node, dest / node.name, _rawISO, dumpPositions)

        if not blockEnterExitSignals:
            self.onPhysicalJobExit(jobSize)

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

# pylint: enable=not-callable
