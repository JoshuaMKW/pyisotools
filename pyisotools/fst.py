from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import IntEnum
from fnmatch import fnmatch
from io import BufferedIOBase, BytesIO, RawIOBase
from pathlib import Path
from typing import (BinaryIO, Dict, Iterable, List, Optional, TextIO, Tuple,
                    Union)

from .iohelper import read_string, read_ubyte, read_uint32, write_uint32


def _round_up_to_power_of_2(n):
    n -= 1
    n |= n >> 1
    n |= n >> 2
    n |= n >> 4
    n |= n >> 8
    n |= n >> 16
    return n + 1


class FileAccessOnFolderError(Exception):
    ...


class FolderAccessOnFileError(Exception):
    ...


class FSTInvalidNodeError(Exception):
    ...


class FSTInvalidError(Exception):
    ...


class FSTClobberedParentError(FSTInvalidNodeError):
    ...


# pylint: disable=invalid-name
class classproperty(property):
    def __get__(self, cls, owner):
        return classmethod(self.fget).__get__(None, owner)()
# pylint: enable=invalid-name


class FSTNode(ABC):
    """
    Abstract class describing a node in an FST structure
    """

    name: str
    parent: FSTFolder

    _PrinterIndentWidth = 2
    _PrinterIndention = 0

    _active = True

    @dataclass(init=True, repr=True, eq=True)
    class _PositionInfo:
        autoPosition: int
        truePosition: int

    class NodeType(IntEnum):
        FILE = 0
        FOLDER = 1
        ROOT = 2

    @classmethod
    @abstractmethod
    def from_path(cls, path: Union[str, Path]) -> FSTNode: ...

    @classproperty
    @abstractmethod
    def type(self) -> NodeType: ...

    @property
    @abstractmethod
    def alignment(self) -> int: ...

    @alignment.setter
    @abstractmethod
    def alignment(self, align: int): ...

    @property
    @abstractmethod
    def position(self) -> int: ...

    @position.setter
    @abstractmethod
    def position(self, position: int): ...

    @property
    @abstractmethod
    def children(self) -> Iterable[FSTNode]: ...

    @property
    @abstractmethod
    def parent(self) -> FSTNode: ...

    @parent.setter
    @abstractmethod
    def parent(self, node: FSTNode): ...

    @property
    @abstractmethod
    def rootnode(self) -> FSTNode: ...

    @property
    @abstractmethod
    def size(self) -> int: ...

    @property
    @abstractmethod
    def datasize(self) -> int: ...

    @abstractmethod
    def add_child(self, child: "FSTNode"): ...

    @abstractmethod
    def remove_child(self, child: "FSTNode"): ...

    @abstractmethod
    def num_children(self, enabledOnly: bool = True) -> int: ...

    @abstractmethod
    def has_manual_position(self) -> bool: ...

    @abstractmethod
    def set_auto_position(self, position: int): ...

    @abstractmethod
    def to_real(self, src: BinaryIO, dest: Union[Path, str]): ...

    @abstractmethod
    def to_virtual(self, src: Union[Path, str], dest: BinaryIO): ...

    @abstractmethod
    def print(self, io: TextIO = sys.stdout): ...

    @property
    def absPath(self) -> str:
        path = self.name
        parent = self.parent
        while parent is not None:
            if parent.is_root():
                break
            path = f"{parent.name}/{path}"
            parent = parent.parent
        return path

    def is_dir(self) -> bool:
        return self.type == FSTNode.NodeType.FOLDER

    def is_file(self) -> bool:
        return self.type == FSTNode.NodeType.FILE

    def is_root(self) -> bool:
        return self.type == FSTNode.NodeType.ROOT

    def is_active(self) -> bool:
        return self._active

    def set_active(self, active: bool):
        self._active = active

    def __str__(self) -> str:
        return self.absPath

    def __format__(self, format_spec: str) -> str:
        return str(self)

    def __bool__(self) -> bool:
        return True


class FSTFile(FSTNode):
    """
    Class representing a file node of an FST
    """

    alignment: int
    position: int

    def __init__(self, name: str, size: int = 0, alignment: int = 4, offset: Optional[int] = None, active: bool = True):
        self.name = name
        self._alignment = alignment
        self._active = active
        self._fsize = size
        self._parent = None

        if offset is None:
            self._positionInfo: Tuple[FSTNode._PositionInfo, bool] = tuple(
                FSTNode._PositionInfo(0, 0), False)
        else:
            self._positionInfo: Tuple[FSTNode._PositionInfo, bool] = tuple(
                FSTNode._PositionInfo(0, offset), True)

    @classmethod
    def from_path(cls, path: Union[Path, str]) -> FSTNode:
        if isinstance(path, str):
            path = Path(str)

        if not path.is_file():
            error = "a non file" if path.exists() else "a file that doesn't exist"
            raise NotImplementedError(
                f"Initializing an {cls.__name__} using {error} is not allowed")

        name = path.name
        size = path.stat().st_size

        node = cls(name, size)
        return node

    @classproperty
    def type(self) -> FSTNode.NodeType:
        return FSTNode.NodeType.FILE

    @property
    def alignment(self) -> int:
        return self._alignment

    @alignment.setter
    def alignment(self, align: int):
        self._alignment = _round_up_to_power_of_2(align)

    @property
    def position(self) -> int:
        pInfo = self._positionInfo
        if pInfo[1] == True:
            return self._positionInfo[1]
        return self._positionInfo[0]

    @position.setter
    def position(self, position: Union[int, None]):
        if position is None:
            self._positionInfo[0].truePosition = 0
            self._positionInfo[1] = False
        else:
            self._positionInfo[0].truePosition = (
                (position + self._alignment) - 1) & ~self._alignment
            self._positionInfo[1] = True

    @property
    def children(self) -> Iterable[FSTNode]:
        return None

    @property
    def parent(self) -> FSTFolder:
        return self._parent

    @parent.setter
    def parent(self, node: FSTFolder):
        if self._parent:
            self._parent.remove_child(self)
        if node:
            node._children[self.name] = self
        self._parent = node

    @property
    def rootnode(self) -> FSTFolder:
        node = self.parent
        if node is None:
            return None

        while True:
            if node.parent is None:
                return node
            node = node.parent

    @property
    def size(self) -> int:
        return len(self)

    @property
    def datasize(self) -> int:
        return self.size

    def add_child(self, child: "FSTNode"):
        return

    def remove_child(self, child: "FSTNode"):
        return

    def num_children(self, enabledOnly: bool = True) -> int:
        """
        Returns the number of children nodes this node contains
        """
        return 0

    def has_manual_position(self) -> bool:
        """
        Returns if this node has a manual position described
        """
        return self._positionInfo[1]

    def set_auto_position(self, position: int):
        """
        Set the position of this node when a manual position is not described
        """
        self._positionInfo[0].autoPosition = position

    def to_real(self, src: BinaryIO, dest: Union[Path, str]):
        """
        Extracts the data at `src` and creates a file with the name of this node
        at a path that is `dest` / self.absPath
        """
        if isinstance(dest, str):
            dest = Path(dest)

        dest = dest / self.absPath
        dest.parent.mkdir(parents=True, exist_ok=True)

        dest.write_bytes(src.read(self.datasize))

    def to_virtual(self, src: Union[Path, str], dest: BinaryIO):
        """
        Packs the data at the path `src` / self.absPath into the binary stream `dest`
        """
        if isinstance(src, str):
            src = Path(src)

        src = src / self.absPath
        dest.write(src.read_bytes())

    def print(self, io: TextIO = sys.stdout):
        """
        Print this node to the stream `io`
        """
        io.write("\n".join([(" "*FSTNode._PrinterIndentWidth) *
                            FSTNode._PrinterIndention + l for l in self.name.split("\n")]))

    def __del__(self):
        self.parent = None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(Name: {self.name}, Data: 0x{int.from_bytes(self.getvalue()[:8], 'big', False):X}..., Offset: 0x{self._fileoffset:X}, Size: 0x{self.size:X}, Parent: {self._parent})"

    def __eq__(self, other: FSTFile) -> bool:
        return hash(self) == hash(other)

    def __ne__(self, other: FSTFile) -> bool:
        return hash(self) != hash(other)

    def __hash__(self) -> int:
        return (sum([ord(c) for c in self.name]) + hash(self.parent)) % (2**64)

    def __len__(self) -> int:
        return self._fsize

    def __contains__(self, other: Union[FSTNode, Path]) -> bool:
        return False


class FSTFileIO(BytesIO, FSTFile):
    alignment: int
    position: int

    def __init__(self, name: str, data: Union[bytes, BinaryIO], alignment: int = 4, offset: Optional[int] = None, active: bool = True):
        if isinstance(data, (RawIOBase, BufferedIOBase)):
            super(BytesIO, self).__init__(data.read())
        else:
            super(BytesIO, self).__init__(data)

        self.name = name
        self._alignment = alignment
        self._positionInfo: Tuple[int, bool] = tuple(
            offset, offset is not None)
        self._active = active

    @classmethod
    def from_path(cls, path: Union[str, Path]) -> FSTNode:
        if isinstance(path, str):
            path = Path(str)

        if not path.is_file():
            error = "a non file" if path.exists() else "a file that doesn't exist"
            raise NotImplementedError(
                f"Initializing an {cls.__name__} using {error} is not allowed")

        node = cls(path.name, data=path.read_bytes())
        return node

    def __len__(self) -> int:
        return len(self.getvalue())

    def __contains__(self, other: Union[FSTNode, Path]) -> bool:
        return False


class FSTFolder(FSTNode):
    """
    Class representing a folder node of an FST
    """

    alignment: int
    position: int

    def __init__(self, name: str, children: Optional[List[FSTNode]] = None, active: bool = True):
        if children is None:
            children = tuple()

        self.name = name

        self._active = active
        self._parent = None
        self._children: Dict[str, FSTNode] = dict()

        for child in children:
            self._children[child.name] = child

    @classmethod
    def from_path(cls, path: Union[str, Path]) -> FSTNode:
        if isinstance(path, str):
            path = Path(str)

        if not path.is_dir():
            error = "a non folder" if path.exists() else "a folder that doesn't exist"
            raise NotImplementedError(
                f"Initializing an {cls.__name__} using {error} is not allowed")

        node = cls(path.name, children=[cls.from_path(f)
                                        for f in path.iterdir()])
        return node

    @classproperty
    def type(self) -> FSTNode.NodeType:
        return FSTNode.NodeType.FOLDER

    @property
    def alignment(self) -> int:
        return None

    @alignment.setter
    def alignment(self, align: int):
        pass

    @property
    def position(self) -> int:
        return None

    @position.setter
    def position(self, position: int):
        pass

    @property
    def children(self) -> Iterable[FSTNode]:
        for child in sorted(self._children.values(), key=lambda x: x.name.upper()):
            yield child

    @property
    def parent(self) -> FSTFolder:
        return self._parent

    @parent.setter
    def parent(self, node: FSTFolder):
        if self._parent:
            self._parent.remove_child(self)
        if node:
            node._children[self.name] = self
        self._parent = node

    @property
    def size(self) -> int:
        return self.num_children(enabledOnly=True)

    @property
    def datasize(self) -> int:
        return sum((node.datasize for node in self.recurse_files(enabledOnly=True)))

    @property
    def rootnode(self) -> FSTFolder:
        node = self.parent
        if node is None:
            return None

        while True:
            if node.parent is None:
                return node
            node = node.parent

    def add_child(self, child: "FSTNode"):
        self._children[child.name] = child
        child.parent = self

    def remove_child(self, child: "FSTNode"):
        self._children.pop(child.name)
        child.parent = None

    def num_children(self, enabledOnly: bool = False) -> int:
        """
        Returns the number of children nodes this node contains
        """
        return len([n for n in self.children if not enabledOnly or n.is_active()])

    def has_manual_position(self) -> bool:
        """
        Returns if this node has a manual position described
        """
        return False

    def set_auto_position(self, position: int):
        """
        Set the position of this node when a manual position is not described
        """
        pass

    def to_real(self, src: BinaryIO, dest: Union[Path, str]):
        """
        Creates a folder with the name of this node
        at a path that is `dest` / self.absPath
        """
        if isinstance(dest, str):
            dest = Path(dest)

        dest = dest / self.absPath
        dest.mkdir(parents=True, exist_ok=True)

    def to_virtual(self, src: Union[Path, str], dest: BinaryIO):
        """
        Packs the data at the path `src` / self.absPath into the binary stream `dest`
        """
        return

    def print(self, io: TextIO = sys.stdout):
        """
        Print this node to the stream `io`
        """
        io.write((" "*FSTNode._PrinterIndentWidth *
                  FSTNode._PrinterIndention) + "- " + str(self))
        FSTNode._PrinterIndention += 1
        for child in self.children:
            child.print(io)
        FSTNode._PrinterIndention -= 1

    # FSTFolder specific functions

    def dirs(self, enabledOnly: bool = False) -> Iterable[FSTFolder]:
        """
        Yields the `FSTFolder` nodes this folder contains
        """
        for node in self.children:
            if enabledOnly and not node.is_active():
                continue

            if node.is_dir():
                yield node

    def files(self, enabledOnly: bool = False) -> Iterable[FSTFile]:
        """
        Yields the `FSTFile` nodes this folder contains
        """
        for node in self.children:
            if enabledOnly and not node.is_active():
                continue

            if node.is_file():
                yield node

    def recurse_dirs(self, enabledOnly: bool = False) -> Iterable[FSTFolder]:
        """
        Recursively yields all `FSTFolder` nodes beneath this folder
        """
        for node in self.children:
            if enabledOnly and not node.is_active():
                continue

            if node.is_dir():
                yield node
                yield from node.recurse_dirs(enabledOnly=enabledOnly)

    def recurse_files(self, enabledOnly: bool = False) -> Iterable[FSTFile]:
        """
        Recursively yields all `FSTFile` nodes beneath this folder
        """
        for node in self.children:
            if enabledOnly and not node.is_active():
                continue

            if node.is_file():
                yield node
            else:
                yield from node.recurse_files(enabledOnly=enabledOnly)

    def recurse_children(self, enabledOnly: bool = False) -> Iterable[FSTNode]:
        """
        Recursively yields all nodes beneath this folder
        """
        for node in self.children:
            if enabledOnly and node.is_active():
                continue

            yield node
            if node.is_dir():
                yield from node.recurse_children(enabledOnly=enabledOnly)

    def get_node_by_path(self, path: Union[str, Path], skipExcluded: bool = True) -> FSTNode:
        """
        Retreive a node beneath this folder that matches `path`, glob patterns are supported
        """
        _path = str(path).lower()
        doGlob = "?" in _path or "*" in _path

        if _path in {"", "."}:
            return self

        for node in self.recurse_files(skipExcluded):
            if doGlob:
                if fnmatch(node.absPath, _path):
                    return node
            else:
                if node.absPath.lower() == _path:
                    return node
        for node in self.recurse_dirs(skipExcluded):
            if doGlob:
                if fnmatch(node.absPath, _path):
                    return node
            else:
                if node.absPath.lower() == _path:
                    return node

        return None

    # End of FSTFolder specific functions

    def __del__(self):
        self.parent = None
        self._children.clear()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(Name: {self.name}, {self.num_children(enabledOnly=True)} entries)"

    def __eq__(self, other: FSTFile) -> bool:
        return hash(self) == hash(other)

    def __ne__(self, other: FSTFile) -> bool:
        return hash(self) != hash(other)

    def __hash__(self) -> int:
        return sum([ord(c) for c in self.name]) + sum([hash(c) for c in self.children])

    def __len__(self) -> int:
        return self.num_children(enabledOnly=True) + 1

    def __contains__(self, other: Union[FSTNode, Path]) -> bool:
        if isinstance(other, FSTNode):
            return other in self.children

        return bool(self.get_node_by_path(other))


class FileSystemTable(FSTFolder):
    """
    Class representing a GC/Wii FST, containing information on the nodes it parents
    """

    RootName = "root"
    FileSystemName = "files"

    def __init__(self, children: Optional[List[FSTNode]] = None):
        super().__init__(".", children)

        self._nodeInfoTable = dict()

        for i, child in enumerate(self.recurse_children(), start=1):
            self._nodeInfoTable[child.absPath] = i

    @staticmethod
    def assert_magic(data: bytes):
        if data[0] != b"\x01":
            raise FSTInvalidError("Invalid Root flag found")
        if data[1:4] != b"\x00\x00\x00":
            raise FSTInvalidError("Invalid Root string offset found")
        if data[4:8] != b"\x00\x00\x00\x00":
            raise FSTInvalidError("Invalid Root offset found")

    @classproperty
    def type(self) -> FSTNode.NodeType:
        return FSTNode.NodeType.ROOT

    @classmethod
    def from_physical(cls, path: Union[str, Path]) -> FileSystemTable:
        return cls.from_path(path)

    @classmethod
    def from_virtual(cls, fst: BinaryIO) -> FileSystemTable:
        """
        Loads the file system data from a memory buffer into self for further use
            fst: BytesIO or opened file object containing the FST of an ISO
        """
        def _read_nodes(fst: BinaryIO) -> FSTNode:
            nonlocal strTabOfs
            nonlocal curEntry
            nonlocal fstTable
            nonlocal nodePath

            _type = read_ubyte(fst)
            _nameOfs = int.from_bytes(fst.read(3), "big", signed=False)
            _entryOfs = read_uint32(fst)
            _size = read_uint32(fst)

            _oldpos = fst.tell()
            _name = read_string(fst, strTabOfs + _nameOfs)
            fst.seek(_oldpos)

            nodePath += _name
            fstTable._nodeInfoTable[nodePath] = curEntry

            curEntry += 1

            if _type == FSTNode.NodeType.FOLDER:
                node = FSTFolder(_name)
                nodePath += "/"
                while curEntry < _size:
                    child = _read_nodes(fst, fst)
                    node.add_child(child)
                nodePath = nodePath[:-1]
            else:
                node = FSTFile(_name, _size, offset=_entryOfs)

            nodePath = nodePath[:-(len(_name)+1)]

            return node

        # Ensure this is an FST binary
        cls.assert_magic(fst.read(8))

        fstTable = cls()

        nodePath = "./"
        entryCount = read_uint32(fst)
        strTabOfs = entryCount * 0xC
        curEntry = 1

        while curEntry < entryCount:
            child = _read_nodes(fstTable, fst)
            fstTable.add_child(child)

        return fstTable

    @property
    def rawsize(self) -> int:
        size = 0
        for child in self.recurse_children(enabledOnly=True):
            size += 8 + len(child.name)
        return size

    def nodes_by_position(self, reverse: bool = False) -> FSTNode:
        """
        Yields all nodes in order of position
        """
        for node in sorted(self.recurse_files(), key=lambda x: x.position, reverse=reverse):
            yield node

    def to_physical(self, dst: Union[str, Path], enabledOnly: bool = False):
        """
        Stores this FST as a file at path `dst`
        """
        if isinstance(dst, str):
            dst = Path(dst)

        with dst.open("wb") as f:
            self.to_virtual(f, enabledOnly)

    def to_virtual(self, fst: BinaryIO, enabledOnly: bool = False) -> BytesIO:
        """
        Converts this FST to its raw form and writes it to `fst`
        """

        _strTableOfs = len(self) * 0xC  # Get the offset to the string table

        _oldpos = fst.tell()
        fst.write(b"\x00"*_strTableOfs)
        fst.seek(_oldpos)

        fst.write(b"\x01\x00\x00\x00\x00\x00\x00\x00")
        write_uint32(fst, len(self))

        _idCache = {self.name: 0}

        _strOfs = 0
        for i, child in enumerate(self.recurse_children(enabledOnly=enabledOnly), start=1):
            _idCache[child.absPath] = i
            fst.write(b"\x01" if child.is_dir() else b"\x00")
            fst.write(_strOfs.to_bytes(3, "big", signed=False))
            write_uint32(fst, _idCache[child.parent.name]
                         if child.is_dir() else child.position)
            write_uint32(fst, (len(child) +
                               i) if child.is_dir() else child.size)

            _oldpos = fst.tell()
            fst.seek(_strOfs + _strTableOfs)
            fst.write(child.name.encode() + b"\x00")
            _strOfs += len(child.name) + 1
            fst.seek(_oldpos)

    def print(self, io: TextIO = sys.stdout):
        io.write(
            f"{self.__class__.__name__} [{self.num_children(enabledOnly=True)} entries]")
        for child in self.children:
            child.print(io)

    @staticmethod
    def _detect_node_alignment(node: FSTFile, prev: FSTFile = None) -> int:
        if prev:
            offset = node.position - (prev.position + prev.size)
        else:
            offset = node.position

        if offset == 0:
            return 4

        alignment = 4
        mask = 0x7FFF
        for _ in range(13):
            if (node.position & mask) == 0:
                alignment = mask + 1
                break
            mask >>= 1

        mask = 0x7FFF
        for _ in range(13):
            if (offset & mask) == 0:
                if mask < alignment:
                    return mask + 1
                return alignment
            mask >>= 1

        return 4

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.num_children(enabledOnly=True)} entries)"

    def __str__(self) -> str:
        return "~"
