from __future__ import annotations

import json
from enum import IntEnum
from fnmatch import fnmatch
from io import BytesIO
from pathlib import Path
from typing import BinaryIO, Callable, Optional, Tuple, Union

from dolreader.dol import DolFile
from pyisotools.apploader import Apploader
from pyisotools.bi2 import BI2
from pyisotools.boot import Boot
from pyisotools.filesystem.fst import (FileSystemTable, FSTFile, FSTFolder,
                                       FSTInvalidError, FSTInvalidNodeError,
                                       FSTNode, GlobBlackList)
from pyisotools.tools import (align_int, read_string, read_ubyte, read_uint32,
                              write_bool, write_uint32)
from sortedcontainers import SortedDict, SortedList


class PartitionInvalidError(Exception):
    ...


class Partition():
    """
    Represents a GC/Wii partition, containing a system folder and file tree
    """

    class Type(IntEnum):
        DATA = 0
        UPDATE = 1
        CHANNEL = 2

    def __init__(self, name: str):
        self.name = name

        # System components
        self.targetPath: Path = None  # Root or ISO
        self.bootheader: Boot = None
        self.bootinfo: BI2 = None
        self.apploader: Apploader = None
        self.dol: DolFile = None
        self.fst: FileSystemTable = None

        # FSTNode configurations
        self.alignmentTable = SortedDict()
        self.locationTable = SortedDict()
        self.excludeTable = SortedList()

        # File extraction callbacks
        self._onPhysicalJobEnter: Callable[[int], None] = None
        self._onPhysicalTaskDescribe: Callable[[str], None] = None
        self._onPhysicalTaskComplete: Callable[[int], None] = None
        self._onPhysicalJobExit: Callable[[int], None] = None

        # ISO build callbacks
        self._onVirtualJobEnter: Callable[[int], None] = None
        self._onVirtualTaskDescribe: Callable[[str], None] = None
        self._onVirtualTaskComplete: Callable[[int], None] = None
        self._onVirtualJobExit: Callable[[int], None] = None

        # Extraction state preservation
        self._curEntry = 0
        self._strOfs = 0
        self._dataOfs = 0
        self._prevfile = None

    @staticmethod
    def is_dolphin_partition(path: Union[Path, str]) -> bool:
        """
        Check if `path` in the filesystem is structured for a dolphin style partition
        """
        if path.is_dir():
            folders = {x.name.lower()
                       for x in path.iterdir() if x.is_dir()}
            return "sys" in folders and "files" in folders and "&&systemdata" not in folders
        return False

    @staticmethod
    def is_gcr_partition(path: Union[Path, str]) -> bool:
        """
        Check if `path` in the filesystem is structured for a GCR style partition
        """
        path = Path(path)
        if path.is_dir():
            folders = {x.name.lower()
                       for x in path.iterdir() if x.is_dir()}
            return "&&systemdata" in folders
        return False

    @classmethod
    def from_physical(cls, path: Union[Path, str]) -> Partition:
        """
        Converts a physical path in the filesystem described by `path` into a `Partition`
        """
        if isinstance(path, str):
            dst = Path(path)

        partition = cls()
        partition.targetPath = path

        sysPath = path / "sys"
        if Partition.is_dolphin_partition(path):
            with Path(sysPath, "boot.bin").open("rb") as f:
                partition.bootheader = Boot(f)
            with Path(sysPath, "bi2.bin").open("rb") as f:
                partition.bootinfo = BI2(f)
            with Path(sysPath, "apploader.img").open("rb") as f:
                partition.apploader = Apploader(f)
            with Path(sysPath, "main.dol").open("rb") as f:
                partition.dol = DolFile(f)
        else:
            with Path(sysPath, "ISO.hdr").open("rb") as f:
                partition.bootheader = Boot(f)
                partition.bootinfo = BI2(f)
            with Path(sysPath, "Apploader.ldr").open("rb") as f:
                partition.apploader = Apploader(f)
            with Path(sysPath, "Start.dol").open("rb") as f:
                partition.dol = DolFile(f)

        if partition.has_config():
            partition.load_config(partition.configPath)

        blacklist = GlobBlackList(partition.dataPath, partition.excludeTable)
        partition.fst = FileSystemTable.from_physical(
            partition.dataPath, blacklist)

    @classmethod
    def from_virtual(cls, partition: BinaryIO, isRaw: bool) -> FileSystemTable:
        """
        Loads the partition data from a memory buffer into a `Partition`

        `isRaw`: Does this partition have no header information (GCN)?
        """
        partition = cls()

           with Path(sysPath, "boot.bin").open("rb") as f:
                partition.bootheader = Boot(f)
            with Path(sysPath, "bi2.bin").open("rb") as f:
                partition.bootinfo = BI2(f)
            with Path(sysPath, "apploader.img").open("rb") as f:
                partition.apploader = Apploader(f)
            with Path(sysPath, "main.dol").open("rb") as f:
                partition.dol = DolFile(f)

            with Path(sysPath, "ISO.hdr").open("rb") as f:
                partition.bootheader = Boot(f)
                partition.bootinfo = BI2(f)
            with Path(sysPath, "Apploader.ldr").open("rb") as f:
                partition.apploader = Apploader(f)
            with Path(sysPath, "Start.dol").open("rb") as f:
                partition.dol = DolFile(f)

        if partition.has_config():
            partition.load_config(partition.configPath)

        blacklist = GlobBlackList(partition.dataPath, partition.excludeTable)
        partition.fst = FileSystemTable.from_physical(
            partition.dataPath, blacklist)

    @property
    def systemPath(self) -> Path:
        if self.targetPath:
            if Partition.is_gcr_partition(self.targetPath):
                return self.targetPath / "&&systemdata"
            return self.targetPath / "sys"
        return None

    @property
    def dataPath(self) -> Path:
        if self.targetPath:
            if Partition.is_gcr_partition(self.targetPath):
                return self.targetPath
            return self.targetPath / self.name
        return None

    @property
    def configPath(self) -> Path:
        if self.targetPath:
            return self.systemPath / ".config.json"
        return None

    @property
    def bnrPath(self) -> Path:
        if self.targetPath:
            return self.dataPath / "opening.bnr"
        return None

    def get_sys_size(self) -> int:
        """
        Retrieve the size of sys in this partition
        """
        size = 0x2440 + (self.apploader.loaderSize +
                         self.apploader.trailerSize)
        size += self.dol.size
        return size + self.fst.rawsize

    def get_fs_size(self) -> int:
        """
        Retrieve the size of the files in this partition
        """
        return self.fst.datasize

    def get_size(self) -> int:
        """
        Retrieve the size of the files and sys in this partition
        """
        return self.get_sys_size() + self.fst.datasize

    def has_config(self) -> bool:
        """
        Returns if this partition has a file system config
        """
        return ".config.json" in [node.name.lower() for node in self.systemPath.iterdir()]

    def build(self, systemOut: BinaryIO, dataOut: BinaryIO, virtualAddress: int, preCalc: bool = True):
        """
        Build this partition into a virtual archive, writing system data to `systemOut` and filesystem data to `dataOut`

        dataOut should come directly after the system data

        `virtualAddress` determines the location information of the nodes
        """
        partitionSize = self.get_size()
        self.onVirtualJobEnter(partitionSize)

        self.pre_calc_metadata(virtualAddress)

        systemOut.seek(self.bootheader.fstOffset)
        systemOut.write(b"\x01\x00\x00\x00\x00\x00\x00\x00")
        write_uint32(systemOut, len(self))

        _strOfs = 0
        _strTableOfs = self.fst.num_children(enabledOnly=True) * 0xC
        _minOffset = 0xFFFFFFFF
        for child in self.fst.recurse_children(enabledOnly=True):
            # Construct node in the raw FST
            _parentID = _parentID
            _childID = self._nodeInfoTable[child.absPath]
            _rawName = _rawName
            _position = child.position

            write_bool(systemOut, child.is_dir())
            systemOut.write((_strOfs).to_bytes(3, "big", signed=False))
            write_uint32(
                systemOut, _parentID if child.is_dir() else _position)
            write_uint32(systemOut, len(child) +
                         _childID if child.is_dir() else child.size)

            _minOffset = min(_position, _minOffset)

            _oldpos = systemOut.tell()
            systemOut.seek(_strOfs + _strTableOfs)
            systemOut.write(_rawName)
            _strOfs += len(_rawName)
            systemOut.seek(_oldpos)

            # Write contents of this file to the binary stream
            if child.is_file():
                dataOut.seek(_position)
                child.to_virtual(self.dataPath, dataOut)

        systemOut.seek(0)
        self.bootheader.fstSize = len(systemOut.read())
        self.bootheader.fstMaxSize = self.bootheader.fstSize
        self.bootheader.firstFileOffset = _minOffset

        # ------------ #
        # -- System -- #
        # ------------ #

        self.save_system_datav(self.systemPath, blockEnterExitSignals=True)

        # ------------- #
        # --- Files --- #
        # ------------- #

        # ------------- #

        self.onVirtualJobExit(partitionSize)

    def extract(self, dest: Optional[Union[Path, str]] = None, dumpPositions: bool = True):
        """
        Extracts the entire contents of this virtual partition to a path described by `dest`

        `dest`: Where to extract the partition to. If None it will be the default root path
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

    def load_config(self, path: Path):
        if not path.is_file():
            return

        with path.open("r") as f:
            data = json.load(f)

        self._init_tables(data)

        self.bootheader.gameName = data["gamename"]
        self.bootheader.gameCode = data["gameid"][:4]
        self.bootheader.makerCode = data["gameid"][4:6]
        self.bootheader.diskID = data["diskid"]
        self.bootheader.version = data["version"]

    def save_config(self):
        config = {"gamename": self.bootheader.gameName,
                  "gameid": self.bootheader.gameCode + self.bootheader.makerCode,
                  "diskid": self.bootheader.diskID,
                  "version": self.bootheader.version,
                  "alignment": self.alignmentTable,
                  "location": {k: self.locationTable[k] for k in sorted(self.locationTable, key=str.upper)},
                  "exclude": list(self.excludeTable)}

        with self.configPath.open("w") as f:
            json.dump(config, f, indent=4)

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

        if len(self.excludeTable) > 0:
            ignoreList.extend(self.excludeTable)

        self._load_from_path(path, parentnode, ignoreList)
        self.pre_calc_metadata(
            (self.MaxSize - self.get_auto_blob_size()) & -self._get_greatest_alignment())

    def load_file_systemv(self, fst: BinaryIO):
        """
        Loads the file system data from a memory buffer into self for further use

            fst: BytesIO or opened file object containing the FST of an ISO
        """

        if fst.read(1) != b"\x01":
            raise FSTInvalidError("Invalid Root flag found")
        if fst.read(3) != b"\x00\x00\x00":
            raise FSTInvalidError("Invalid Root string offset found")
        if fst.read(4) != b"\x00\x00\x00\x00":
            raise FSTInvalidError("Invalid Root offset found")

        self.alignmentTable = SortedDict()
        entryCount = read_uint32(fst)

        self._curEntry = 1
        while self._curEntry < entryCount:
            child = self._read_nodes(fst, self, entryCount * 0xC)
            self.add_child(child)

    def extract_system_data(self, dest: Union[Path, str], blockEnterExitSignals: bool = False):
        """
        Extracts the system data of this virtual filesystem (ISO) to a path described by `dest`

        `dest`: Where to extract the system data to
        """
        if isinstance(dest, str):
            dest = Path(dest)

        systemPath = dest / "sys"
        systemPath.mkdir(parents=True, exist_ok=True)

        self.save_system_data(
            systemPath, blockEnterExitSignals=blockEnterExitSignals)

    def save_system_data(self, dest: Optional[Union[Path, str]] = None, blockEnterExitSignals: bool = False):
        """
        Saves system data to the sys folder of the current root.

        `dest`: Path to store system data
        `saveBNR`: Save the opening.bnr if applicable when `True`
        """

        if not blockEnterExitSignals:
            jobSize = self.get_sys_size()
            self.onPhysicalJobEnter(jobSize)

        if not dest:
            systemPath = self.systemPath
        else:
            systemPath = Path(dest)

        if self.is_dolphin_partition():
            self.onPhysicalTaskDescribe("boot.bin")
            with Path(systemPath, "boot.bin").open("wb") as f:
                self.bootheader.save(f)
            self.onPhysicalTaskComplete(0x440)

            self.onPhysicalTaskDescribe("bi2.bin")
            with Path(systemPath, "bi2.bin").open("wb") as f:
                self.bootinfo.save(f)
            self.onPhysicalTaskComplete(0x2000)

            self.onPhysicalTaskDescribe("apploader.img")
            with Path(systemPath, "apploader.img").open("wb") as f:
                self.apploader.save(f)
            self.onPhysicalTaskComplete(
                self.apploader.loaderSize + self.apploader.trailerSize)

            self.onPhysicalTaskDescribe("main.dol")
            with Path(systemPath, "main.dol").open("wb") as f:
                self.dol.save(f)
            self.onPhysicalTaskComplete(self.dol.size)

            self.onPhysicalTaskDescribe("fst.bin")
            with Path(systemPath, "fst.bin").open("wb") as f:
                self.fst.to_virtual(f)
            self.onPhysicalTaskComplete(self.fst.rawsize)
        elif self.is_gcr_partition():
            self.onPhysicalTaskDescribe("ISO.hdr")
            with Path(systemPath, "ISO.hdr").open("wb") as f:
                self.bootheader.save(f)
                self.bootinfo.save(f)
            self.onPhysicalTaskComplete(0x2440)

            self.onPhysicalTaskDescribe("Apploader.ldr")
            with Path(systemPath, "Apploader.ldr").open("wb") as f:
                self.apploader.save(f)
            self.onPhysicalTaskComplete(
                self.apploader.loaderSize + self.apploader.trailerSize)

            self.onPhysicalTaskDescribe("Start.dol")
            with Path(systemPath, "Start.dol").open("wb") as f:
                self.dol.save(f)
            self.onPhysicalTaskComplete(self.dol.size)

            self.onPhysicalTaskDescribe("Game.toc")
            with Path(systemPath, "Game.toc").open("wb") as f:
                self.fst.to_virtual(f)
            self.onPhysicalTaskComplete(self.fst.rawsize)
        else:
            raise FSTInvalidError(f"{self.root} is not a valid root folder")

        self._save_config_regen()

        if not blockEnterExitSignals:
            self.onPhysicalJobExit(jobSize)

    def save_system_datav(self, f: BinaryIO, blockEnterExitSignals: bool = False):
        """
        Save the system data to in the ISO header format to the binary stream `f`
        """

        if not blockEnterExitSignals:
            jobSize = self.get_sys_size()
            self.onVirtualJobEnter(jobSize)

        self.onVirtualTaskDescribe("boot.bin")
        self.bootheader.save(f)
        self.onVirtualTaskComplete(0x440)

        self.onVirtualTaskDescribe("bi2.bin")
        self.bootinfo.save(f)
        self.onVirtualTaskComplete(0x2000)

        self.onVirtualTaskDescribe("apploader.img")
        self.apploader.save(f)
        self.onVirtualTaskComplete(
            self.apploader.loaderSize + self.apploader.trailerSize)

        self.onVirtualTaskDescribe("main.dol")
        f.write(b"\x00" * (self.bootheader.dolOffset - f.tell()))  # Pad zeros
        self.dol.save(f, self.bootheader.dolOffset)
        self.onVirtualTaskComplete(self.dol.size)

        self.onVirtualTaskDescribe("fst.bin")
        f.seek(f.tell() + self.dol.size)
        f.write(b"\x00" * (self.bootheader.fstOffset - f.tell()))  # Pad zeros
        self.fst.to_virtual(f)
        self.onVirtualTaskComplete(self.fst.rawsize)

        if not blockEnterExitSignals:
            self.onVirtualJobExit(jobSize)

    # pylint: disable=unused-argument
    @staticmethod
    def __default_callback(*args, **kwargs) -> None:
        return None
    # pylint: enable=unused-argument

    @property
    def onPhysicalJobEnter(self) -> Callable[[int], None]:
        if self._onPhysicalJobEnter:
            return self._onPhysicalJobEnter
        return self.__default_callback

    @onPhysicalJobEnter.setter
    def onPhysicalJobEnter(self, callback: Callable[[int], None]):
        self._onPhysicalJobEnter = callback

    @property
    def onPhysicalTaskDescribe(self) -> Callable[[str], None]:
        if self._onPhysicalTaskDescribe:
            return self._onPhysicalTaskDescribe
        return self.__default_callback

    @onPhysicalTaskDescribe.setter
    def onPhysicalTaskDescribe(self, callback: Callable[[str], None]):
        self._onPhysicalTaskDescribe = callback

    @property
    def onPhysicalTaskComplete(self) -> Callable[[int], None]:
        if self._onPhysicalTaskComplete:
            return self._onPhysicalTaskComplete
        return self.__default_callback

    @onPhysicalTaskComplete.setter
    def onPhysicalTaskComplete(self, callback: Callable[[int], None]):
        self._onPhysicalTaskComplete = callback

    @property
    def onPhysicalJobExit(self) -> Callable[[int], None]:
        if self._onPhysicalJobExit:
            return self._onPhysicalJobExit
        return self.__default_callback

    @onPhysicalJobExit.setter
    def onPhysicalJobExit(self, callback: Callable[[int], None]):
        self._onPhysicalJobExit = callback

    @property
    def onVirtualJobEnter(self) -> Callable[[int], None]:
        if self._onVirtualJobEnter:
            return self._onVirtualJobEnter
        return self.__default_callback

    @onVirtualJobEnter.setter
    def onVirtualJobEnter(self, callback: Callable[[int], None]):
        self._onVirtualJobEnter = callback

    @property
    def onVirtualTaskDescribe(self) -> Callable[[str], None]:
        if self._onVirtualTaskDescribe:
            return self._onVirtualTaskDescribe
        return self.__default_callback

    @onVirtualTaskDescribe.setter
    def onVirtualTaskDescribe(self, callback: Callable[[str], None]):
        self._onVirtualTaskDescribe = callback

    @property
    def onVirtualTaskComplete(self) -> Callable[[int], None]:
        if self._onVirtualTaskComplete:
            return self._onVirtualTaskComplete
        return self.__default_callback

    @onVirtualTaskComplete.setter
    def onVirtualTaskComplete(self, callback: Callable[[int], None]):
        self._onVirtualTaskComplete = callback

    @property
    def onVirtualJobExit(self) -> Callable[[int], None]:
        if self._onVirtualJobExit:
            return self._onVirtualJobExit
        return self.__default_callback

    @onVirtualJobExit.setter
    def onVirtualJobExit(self, callback: Callable[[int], None]):
        self._onVirtualJobExit = callback

    def _read_nodes(self, fst, parent: FSTFolder, strTabOfs: int) -> FSTNode:
        _type = read_ubyte(fst)
        _nameOfs = int.from_bytes(fst.read(3), "big", signed=False)
        _entryOfs = read_uint32(fst)
        _size = read_uint32(fst)

        _oldpos = fst.tell()
        _name = read_string(fst, strTabOfs + _nameOfs)
        fst.seek(_oldpos)

        if _type == FSTNode.NodeType.FOLDER:
            node = FSTFolder(_name)
            node.parent = parent

            self._nodeInfoTable[node.absPath] = self._curEntry
            self._curEntry += 1
            while self._curEntry < _size:
                child = self._read_nodes(fst, strTabOfs)
                node.add_child(child)
        else:
            node = FSTFile(_name, _size)
            node.parent = parent

            self._nodeInfoTable[node.absPath] = self._curEntry
            self._curEntry += 1
            # node.position = _entryOfs

        return node

    def _init_tables(self, config: Optional[Path] = None):
        if not config:
            self.alignmentTable = SortedDict()
            self.locationTable = SortedDict()
            self.excludeTable = SortedList()
        elif isinstance(config, dict):
            self.alignmentTable = SortedDict(config["alignment"])
            self.locationTable = SortedDict(config["location"])
            self.excludeTable = SortedList(config["exclude"])
        else:
            with config.open("r") as f:
                data = json.load(f)
            self.alignmentTable = SortedDict(data["alignment"])
            self.locationTable = SortedDict(data["location"])
            self.excludeTable = SortedList(data["exclude"])

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
            return self.alignmentTable.peekitem()[1]
        except IndexError:
            return 4

    def _get_alignment(self, node: Union[FSTNode, str]) -> int:
        if isinstance(node, FSTNode):
            _path = node.absPath
        else:
            _path = node

        alignment = 4
        if self.alignmentTable is None:
            return alignment

        for entry, width in self.alignmentTable.items():
            if fnmatch(_path, entry.strip()):
                alignment = width
                break

        return alignment

    def _get_location(self, node: Union[FSTNode, str]) -> int:
        if isinstance(node, FSTNode):
            _path = node.absPath
        else:
            _path = node

        if self.locationTable:
            return self.locationTable.get(_path)
        return None

    def _get_excluded(self, node: Union[FSTNode, str]) -> bool:
        if isinstance(node, FSTNode):
            _path = node.absPath
        else:
            _path = node

        if self.excludeTable:
            for entry in self.excludeTable:
                if fnmatch(_path, entry.strip()):
                    return True
        return False

    def pre_calc_metadata(self, startPos: int, endPos):
        """
        Pre calculates all node offsets for viewing the node locations before compile

        The results of this function are only valid until the FST is changed in
        a way that impacts file offsets
        """
        _dataOfs = align_int(startPos, 4)
        _minOffset = endPos - 4
        for _curEntry, child in enumerate(self.recurse_children(enabledOnly=True), 1):
            self._nodeInfoTable[child.absPath] = _curEntry

            if child.is_file():
                if child.has_manual_position():
                    _minOffset = min(child.position, _minOffset)
                else:
                    _dataOfs = align_int(_dataOfs, child.alignment)
                    child.position = _dataOfs
                    _minOffset = min(_dataOfs, _minOffset)
                    _dataOfs += child.size

    def _load_from_path(self, path: Path, parentnode: FSTNode = None, ignoreList: Optional[Tuple] = None):
        if ignoreList is None:
            ignoreList = ()

        # Uppercase bound sort
        for entry in sorted(path.iterdir(), key=lambda x: x.name.upper()):
            if self.is_gcr_partition() and entry.name.lower() == "&&systemdata":
                continue

            active = True
            for badPath in ignoreList:
                if entry.match(badPath):
                    active = False

            if entry.is_file():
                child = FSTNode.file(
                    entry.name, parent=parentnode, size=entry.stat().st_size)
                child.alignment = self._get_alignment(child)
                child.position = self._get_location(child)
                child.active = active

            elif entry.is_dir():
                child = FSTFolder(entry.name)

                if parentnode is not None:
                    parentnode.add_child(child)

                self._load_from_path(entry, child, ignoreList=ignoreList)
            else:
                raise FSTInvalidNodeError("Not a dir or file")

    def _save_config_regen(self):
        self.alignmentTable.clear()
        self.locationTable.clear()
        self.excludeTable.clear()

        for node in self.recurse_children():
            if node.is_file():
                if node.alignment != 4:
                    self.alignmentTable[node.absPath] = node.alignment
                if node.position:
                    self.locationTable[node.absPath] = node.position
            if not node.is_active():
                self.excludeTable.add(node.absPath)

        self.save_config()
