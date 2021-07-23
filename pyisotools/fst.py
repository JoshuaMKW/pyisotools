from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from enum import Enum
from fnmatch import fnmatch
from io import BufferedIOBase, BytesIO, IOBase, RawIOBase, StringIO
from pathlib import Path
from typing import BinaryIO, Dict, Iterable, List, Optional, TextIO, Union
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


class classproperty(property):
    def __get__(self, cls, owner):
        return classmethod(self.fget).__get__(None, owner)()


class FSTNode(ABC):
    name: str
    parent: FSTFolder

    _PrinterIndentWidth = 2
    _PrinterIndention = 0

    _active = True

    class NodeType(Enum):
        FILE = 0
        FOLDER = 1

    @classmethod
    @abstractmethod
    def from_path(cls, path: Union[str, Path]) -> FSTNode: ...

    @classproperty
    @abstractmethod
    def type(self) -> NodeType: ...

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
    def num_children(self, onlyEnabled: bool = True) -> int: ...

    @abstractmethod
    def print(self, io: TextIO = sys.stdout): ...

    @property
    def path(self) -> str:
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
        return self.type == FSTNode.NodeType.FOLDER and self.name == "." and self.parent is None

    def is_active(self) -> bool:
        return self._active

    def __str__(self) -> str:
        return self.path

    def __format__(self, format_spec: str) -> str:
        return str(self)

    def __bool__(self) -> bool:
        return True


class FSTFile(BytesIO, FSTNode):
    alignment: int
    position: int

    def __init__(self, name: str, data: Union[bytes, BinaryIO], alignment: int = 4, offset: Optional[int] = None, active: bool = True):
        if isinstance(data, (RawIOBase, BufferedIOBase)):
            super(BytesIO, self).__init__(data.read())
        else:
            super(BytesIO, self).__init__(data)

        self.name = name
        self._alignment = alignment
        self._positionInfo = tuple(offset, offset is not None)
        self._active = True

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
        return self._positionInfo[0]

    @position.setter
    def position(self, position: int):
        self._positionInfo = tuple(
            ((position + self._alignment) - 1) & ~self._alignment, True)

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

    def num_children(self, onlyEnabled: bool = True) -> int:
        return 0

    def print(self, io: TextIO = sys.stdout):
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
        return sum([ord(c) for c in self.name]) + hash(self.getvalue())

    def __len__(self) -> int:
        return len(self.getvalue())

    def __contains__(self, other) -> bool:
        return False


class FSTFolder(FSTNode):
    alignment: int
    position: int

    def __init__(self, name: str, children: Optional[List[FSTNode]] = None, active: bool = True):
        if children is None:
            children = tuple()

        self.name = name
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
                    
        node = cls(path.name, children=[cls.from_path(f) for f in path.iterdir()])
        return node

    @classproperty
    def type(self) -> FSTNode.NodeType:
        return FSTNode.NodeType.FOLDER

    @property
    def children(self) -> Iterable[Union[FSTFile, FSTFolder]]:
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
        return self.num_children()

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

    def dirs(self, enabledOnly: bool = False) -> Iterable[FSTFolder]:
        for node in self.children:
            if enabledOnly and not node.is_active():
                continue

            if node.is_dir():
                yield node

    def files(self, enabledOnly: bool = False) -> Iterable[FSTFile]:
        for node in self.children:
            if enabledOnly and not node.is_active():
                continue

            if node.is_file():
                yield node

    def recurse_dirs(self, enabledOnly: bool = False) -> Iterable[FSTFolder]:
        for node in self.children:
            if enabledOnly and not node.is_active():
                continue

            if node.is_dir():
                yield node
                yield from node.recurse_dirs(enabledOnly=enabledOnly)

    def recurse_files(self, enabledOnly: bool = False) -> Iterable[FSTFile]:
        for node in self.children:
            if enabledOnly and not node.is_active():
                continue

            if node.is_file():
                yield node
            else:
                yield from node.recurse_files(enabledOnly=enabledOnly)

    def recurse_children(self, enabledOnly: bool = False) -> Iterable[Union[FSTFile, FSTFolder]]:
        for node in self.children:
            if enabledOnly and node.is_active():
                continue

            yield node
            if node.is_dir():
                yield from node.recurse_children(enabledOnly=enabledOnly)

    def get_node_by_path(self, path: Union[str, Path], skipExcluded: bool = True) -> FSTNode:
        _path = str(path).lower()
        doGlob = "?" in _path or "*" in _path

        if _path == "" or _path == ".":
            return self

        for node in self.recurse_files(skipExcluded):
            if doGlob:
                if fnmatch(node.path, _path):
                    return node
            else:
                if node.path.lower() == _path:
                    return node
        for node in self.recurse_dirs(skipExcluded):
            if doGlob:
                if fnmatch(node.path, _path):
                    return node
            else:
                if node.path.lower() == _path:
                    return node


    def add_child(self, child: "FSTNode"):
        self._children[child.name] = child
        child.parent = self

    def remove_child(self, child: "FSTNode"):
        self._children.pop(child.name)
        child.parent = None

    def num_children(self, onlyEnabled: bool = True) -> int:
        if onlyEnabled:
            return len([n for n in self.children if n.is_active()])

        return len([n for n in self.children])

    def print(self, io: TextIO = sys.stdout):
        io.write((" "*FSTNode._PrinterIndentWidth *
                  FSTNode._PrinterIndention) + "- " + str(self))
        FSTNode._PrinterIndention += 1
        for child in self.children:
            child.print(io)
        FSTNode._PrinterIndention -= 1

    def __del__(self):
        self.parent = None
        self._children.clear()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(Name: {self.name}, {self.num_children()} entries)"

    def __eq__(self, other: FSTFile) -> bool:
        return hash(self) == hash(other)

    def __ne__(self, other: FSTFile) -> bool:
        return hash(self) != hash(other)

    def __hash__(self) -> int:
        return sum([ord(c) for c in self.name]) + sum([hash(c) for c in self.children])

    def __len__(self) -> int:
        return self.num_children() + 1

    def __contains__(self, other: Union[FSTNode, Path]) -> bool:
        if isinstance(other, FSTNode):
            for child in self.children:
                if child == other:
                    return True
            return False

        return bool(self.get_node_by_path(other))


class FSTRoot(FSTFolder):
    def __init__(self, children: Dict[str, FSTNode] = None):
        super().__init__(".", children)

    @classmethod
    def from_path(cls, path: Union[str, Path]) -> FSTNode:
        if isinstance(path, str):
            path = Path(str)

        if not path.is_dir():
            error = "a non folder" if path.exists() else "a folder that doesn't exist"
            raise NotImplementedError(
                f"Initializing an {cls.__name__} using {error} is not allowed")
                    
        node = cls(children=[FSTFolder.from_path(f) if f.is_dir() else FSTFile.from_path(f) for f in path.iterdir()])
        return node

    @property
    def parent(self) -> FSTNode:
        return None

    @parent.setter
    def parent(self, node: FSTNode):
        return

    def nodes_by_position(self, reverse: bool = False) -> FSTNode:
        for node in sorted(self.recurse_files(), key=lambda x: x.position, reverse=reverse):
            yield node

    def print(self, io: TextIO = sys.stdout):
        for child in self.children:
            child.print(io)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.num_children()} entries)"

    def __str__(self) -> str:
        return "~"

    def _detect_alignment(self, node: FSTFile, prev: FSTFile = None) -> int:
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


class FileSystemTable(FSTRoot):
    RootName = "root"
    FileSystemName = "files"

    def __init__(self, children: Optional[List[FSTNode]] = None):
        super().__init__(children)
        self._nodeInfoTable = dict()

        for i, child in enumerate(self.recurse_children(), start=1):
            self._nodeInfoTable[child.path] = i

    @classmethod
    def from_physical(cls, path: Union[str, Path]) -> FileSystemTable:
        return cls.from_path(path)

    @classmethod
    def from_virtual(cls, io: BinaryIO) -> FileSystemTable:
        """
        Loads the file system data from a memory buffer into self for further use

            io: BytesIO or opened file object containing the FST of an ISO
        """

        if io.read(1) != b"\x01":
            raise FSTInvalidError("Invalid Root flag found")
        elif io.read(3) != b"\x00\x00\x00":
            raise FSTInvalidError("Invalid Root string offset found")
        elif io.read(4) != b"\x00\x00\x00\x00":
            raise FSTInvalidError("Invalid Root offset found")

        fst = cls()

        curEntry: int = 1
        strTabOfs: int = 0

        def _read_nodes(fst, io: BinaryIO) -> FSTNode:
            nonlocal strTabOfs
            nonlocal curEntry

            _type = read_ubyte(io)
            _nameOfs = int.from_bytes(io.read(3), "big", signed=False)
            _entryOfs = read_uint32(io)
            _size = read_uint32(io)

            _oldpos = io.tell()
            _name = read_string(io, strTabOfs + _nameOfs, encoding="shift-jis")
            io.seek(_oldpos)

            if _type == FSTNode.NodeType.FOLDER:
                node = FSTFolder(_name)
                while curEntry < _size:
                    child = _read_nodes(fst, io)
                    node.add_child(child)
            else:
                io.seek(_entryOfs)
                node = FSTFile(_name, BytesIO(io.read(_size)), offset=_entryOfs)
                io.seek(_oldpos)

            return node

        entryCount = read_uint32(io)
        strTabOfs = entryCount * 0xC

        while curEntry < entryCount:
            child = _read_nodes(fst, io)
            fst.add_child(child)

        return fst

    def write_physical(self, dst: Union[str, Path], onlyActive: bool = False):
        ...

    def write_virtual(self, fst: BinaryIO, dataIO: BinaryIO, onlyActive: bool = False) -> BytesIO:
        _strTableOfs = len(self) * 0xC  # Get the offset to the string table

        _oldpos = fst.tell()
        fst.write(b"\x00"*_strTableOfs)
        fst.seek(_oldpos)

        fst.write(b"\x01\x00\x00\x00\x00\x00\x00\x00")
        write_uint32(fst, len(self))

        _idCache = dict()
        
        _strOfs = 0
        for i, child in enumerate(self.recurse_children(), start=1):
            _idCache[child.path] = i
            fst.write(b"\x01" if child.is_dir() else b"\x00")
            fst.write(_strOfs.to_bytes(3, "big", signed=False))
            write_uint32(fst, _idCache[child.parent.name] if child.is_dir() else child.position)
            write_uint32(fst, len(child) +
                        i if child.is_dir() else child.size)

            _oldpos = fst.tell()
            fst.seek(_strOfs + _strTableOfs)
            fst.write(child.name.encode("shift-jis") + b"\x00")
            _strOfs += len(child.name) + 1
            fst.seek(_oldpos)

            

    def print(self, io: TextIO = sys.stdout):
        io.write(f"{self.__class__.__name__} [{self.num_children()} entries]")
        for child in self.children:
            child.print(io)
