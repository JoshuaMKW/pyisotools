from __future__ import annotations

import json
from fnmatch import fnmatch
from io import BytesIO
from pathlib import Path
from typing import BinaryIO, Optional, Tuple, Union

from dolreader.dol import DolFile
from sortedcontainers import SortedDict, SortedList

from pyisotools.apploader import Apploader
from pyisotools.bi2 import BI2
from pyisotools.boot import Boot
from pyisotools.fst import (FileSystemTable, FSTFile, FSTFolder,
                            FSTInvalidError, FSTInvalidNodeError, FSTNode)
from pyisotools.iohelper import (align_int, read_string, read_ubyte,
                                 read_uint32, write_uint32)


class PartitionInvalidError(Exception):
    ...


class Partition(FileSystemTable):
    def __init__(self, name: str):
        super().__init__()

        self.name = name

        # System components
        self.targetPath: Path = None  # Root or ISO
        self.bootheader: Boot = None
        self.bootinfo: BI2 = None
        self.apploader: Apploader = None
        self.dol: DolFile = None
        self._rawFST: BytesIO = None

        # FSTNode configurations
        self._alignmentTable = SortedDict()
        self._locationTable = SortedDict()
        self._excludeTable = SortedList()

        # Extraction state preservation
        self._curEntry = 0
        self._strOfs = 0
        self._dataOfs = 0
        self._prevfile = None

    @property
    def systemPath(self) -> Path:
        if self.targetPath:
            if Partition.is_gcr_root(self.targetPath):
                return self.targetPath / "&&systemdata"
            return self.targetPath / "sys"
        return None

    @property
    def dataPath(self) -> Path:
        if self.targetPath:
            if Partition.is_gcr_root(self.targetPath):
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

    @staticmethod
    def is_dolphin_root(path: Union[Path, str]) -> bool:
        if path.is_dir():
            folders = {x.name.lower()
                       for x in path.iterdir() if x.is_dir()}
            return "sys" in folders and "files" in folders and "&&systemdata" not in folders
        return False

    @staticmethod
    def is_gcr_root(path: Union[Path, str]) -> bool:
        path = Path(path)
        if path.is_dir():
            folders = {x.name.lower()
                       for x in path.iterdir() if x.is_dir()}
            return "&&systemdata" in folders
        return False

    def get_sys_size(self) -> int:
        jobSize = 0x2440 + (self.apploader.loaderSize +
                            self.apploader.trailerSize)
        jobSize += self.dol.size
        return jobSize + len(self._rawFST.getbuffer())

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
                  "alignment": self._alignmentTable,
                  "location": {k: self._locationTable[k] for k in sorted(self._locationTable, key=str.upper)},
                  "exclude": list(self._excludeTable)}

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
            raise FSTInvalidError("Invalid Root flag found")
        if fst.read(3) != b"\x00\x00\x00":
            raise FSTInvalidError("Invalid Root string offset found")
        if fst.read(4) != b"\x00\x00\x00\x00":
            raise FSTInvalidError("Invalid Root offset found")

        self._alignmentTable = SortedDict()
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

    def save_system_data(self, dest: Optional[Union[Path, str]] = None, saveBNR: bool = False, blockEnterExitSignals: bool = False):
        """
        Saves system data to the sys folder of the current root.

        `dest`: Path to store system data
        `saveBNR`: Save the opening.bnr if applicable when `True`
        """
        if not blockEnterExitSignals:
            jobSize = self._get_sys_size()
            if self.bnr and saveBNR:
                jobSize += len(self.bnr)
            self.onPhysicalJobEnter(jobSize)

        if not dest:
            systemPath = self.systemPath
        else:
            systemPath = Path(dest)

        if self.is_dolphin_root():
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
                f.write(self._rawFST.getvalue())
            self.onPhysicalTaskComplete(len(self._rawFST.getbuffer()))
        elif self.is_gcr_root():
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
                f.write(self._rawFST.getvalue())
            self.onPhysicalTaskComplete(len(self._rawFST.getbuffer()))
        else:
            raise FSTInvalidError(f"{self.root} is not a valid root folder")

        if self.bnr and saveBNR:
            self.onPhysicalTaskDescribe("opening.bnr")
            self.bnr.save_bnr(Path(self.dataPath, "opening.bnr"))
            self.onPhysicalTaskComplete(len(self.bnr))

        self._save_config_regen()

        if not blockEnterExitSignals:
            self.onPhysicalJobExit(jobSize)

    def save_system_datav(self, f: BinaryIO, blockEnterExitSignals: bool = False):
        """
        Save the system data to in the ISO header format to the binary stream `f`
        """
        jobSize = 0x2440 + (self.apploader.loaderSize +
                            self.apploader.trailerSize)
        jobSize += self.dol.size
        jobSize += len(self._rawFST.getbuffer())

        bnrNode = self.find_by_path("opening.bnr")
        if bnrNode and self.bnr:
            jobSize += len(self.bnr)

        if not blockEnterExitSignals:
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
        f.write(self._rawFST.getvalue())
        self.onVirtualTaskComplete(len(self._rawFST.getbuffer()))

        bnrNode = self.find_by_path("opening.bnr")
        if bnrNode and self.bnr:
            self.onVirtualTaskDescribe("opening.bnr")
            f.seek(bnrNode._fileoffset)
            f.write(self.bnr._rawdata.getvalue())
            self.onVirtualTaskComplete(len(self.bnr))

        if not blockEnterExitSignals:
            self.onVirtualJobExit(jobSize)

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
            _path = node.absPath
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
            _path = node.absPath
        else:
            _path = node

        if self._locationTable:
            return self._locationTable.get(_path)
        return None

    def _get_excluded(self, node: Union[FSTNode, str]) -> bool:
        if isinstance(node, FSTNode):
            _path = node.absPath
        else:
            _path = node

        if self._excludeTable:
            for entry in self._excludeTable:
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
        _curEntry = 1
        _minOffset = endPos - 4
        for child in self.recurse_children():
            if not child.is_active():
                if child.is_file():
                    child.position = 0
                continue

            self._nodeInfoTable[child.absPath] = _curEntry
            _curEntry += 1

            if child.is_file():
                if child.has_manual_position():
                    _minOffset = min(child.position, _minOffset)
                else:
                    _dataOfs = align_int(_dataOfs, child.alignment)
                    child.position = _dataOfs
                    _minOffset = min(_dataOfs, _minOffset)
                    _dataOfs += child.size
            else:
                child._dirparent = child.parent._id
                child._dirnext = child.size + child._id

        self.bootheader.firstFileOffset = max(_minOffset, 0)

    def _load_from_path(self, path: Path, parentnode: FSTNode = None, ignoreList: Optional[Tuple] = None):
        if ignoreList is None:
            ignoreList = ()

        # Uppercase bound sort
        for entry in sorted(path.iterdir(), key=lambda x: x.name.upper()):
            if self.is_gcr_root() and entry.name.lower() == "&&systemdata":
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
        self._alignmentTable.clear()
        self._locationTable.clear()
        self._excludeTable.clear()

        for node in self.recurse_children():
            if node.is_file():
                if node.alignment != 4:
                    self._alignmentTable[node.absPath] = node.alignment
                if node.position:
                    self._locationTable[node.absPath] = node.position
            if not node.is_active():
                self._excludeTable.add(node.absPath)

        self.save_config()