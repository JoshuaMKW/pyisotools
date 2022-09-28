from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path
from typing import Iterator, Optional, Union


class FileAccessOnFolderError(Exception):
    ...


class FolderAccessOnFileError(Exception):
    ...


class InvalidEntryError(Exception):
    ...


class InvalidFSTError(Exception):
    ...


class FSTNode():

    FILE = 0
    FOLDER = 1

    def __init__(self, name: str, nodetype: int = None, nodeid: int = 0, parent: FSTNode = None, children: tuple = ()):
        """
        Initialize a new FSTNode object, and set the parent and children according to the optional args :parentnode: and :children:

            name:     Name of the node
            nodetype: Node type (0 = File, 1 = Folder)
            nodeid:   Node id
            parent:   Parent node
            children: Tuple of children nodes
        """

        self.name = name
        self.type = nodetype

        # metadata
        self._alignment = 4
        self._position = None
        self._exclude = False

        # file attributes
        self._filesize = None
        self._fileoffset = None

        # folder attributes
        self._dirparent = None
        self._dirnext = None

        self._parent = None
        self._children = {}
        self._id = nodeid

        # setup
        self.parent = parent

        for child in children:
            self.add_child(child)

    def __repr__(self):
        if self.is_dir():
            info = f"Parent: {self._parent}, Children: {self.size}"
        else:
            info = f"Offset: {self._fileoffset}, Size: {self.size}, Parent: {self._parent}"

        return f"{self.__class__.__name__}<Type: {self.type}, {info}>"

    @classmethod
    def file(cls, name: str, parent: FSTNode = None, size: int = None, offset: int = None):
        node = cls(name, FSTNode.FILE, parent=parent)
        node._filesize = size
        node._fileoffset = offset
        return node

    @classmethod
    def folder(cls, name: str, parent: FSTNode = None, children: tuple = ()):
        return cls(name, FSTNode.FOLDER, parent=parent, children=children)

    @classmethod
    def from_path(cls, path: Path) -> FSTNode:
        if path.is_file():
            node = cls.file(path.name, size=path.stat().st_size())
        elif path.is_dir():
            node = cls.folder(path.name, children=[
                              cls.from_path(f) for f in path.iterdir()])
        else:
            raise NotImplementedError(
                "Initializing a node using anything other than a file or folder is not allowed")
        return node

    @classmethod
    def empty(cls):
        return cls("")

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

    @property
    def dirs(self) -> FSTNode:
        for node in self.children:
            if node.is_dir():
                yield node

    @property
    def files(self) -> FSTNode:
        for node in self.children:
            if node.is_file():
                yield node

    def rdirs(self, includedOnly: bool = False) -> Iterator[FSTNode]:
        for node in self.children:
            if includedOnly and node._exclude:
                continue

            if node.is_dir():
                yield node
                yield from node.rdirs(includedOnly=includedOnly)

    def rfiles(self, includedOnly: bool = False) -> Iterator[FSTNode]:
        for node in self.children:
            if includedOnly and node._exclude:
                continue

            if node.is_file():
                yield node
            else:
                yield from node.rfiles(includedOnly=includedOnly)

    def rchildren(self, includedOnly: bool = False) -> Iterator[FSTNode]:
        for node in self.children:
            if includedOnly and node._exclude:
                continue

            yield node
            yield from node.rchildren(includedOnly=includedOnly)

    @property
    def parent(self) -> FSTNode:
        return self._parent

    @parent.setter
    def parent(self, node: FSTNode):
        if self.is_dir():
            if node:
                self._dirparent = node._id
            else:
                self._dirparent = 0
        if self._parent:
            self._parent.remove_child(self)
        if node:
            node._children[self.name] = self

        self._parent = node

    @property
    def children(self) -> Iterator[FSTNode]:
        for child in sorted(self._children.values(), key=lambda x: x.name.upper()):
            yield child

    @property
    def rootnode(self) -> FSTRoot:
        prev = self
        parent = self.parent
        while parent is not None:
            prev = parent
            parent = parent.parent
        return prev

    @property
    def size(self) -> int:
        if self.is_file():
            return self._filesize
        return self.num_children()

    @size.setter
    def size(self, size: int):
        if self.is_file():
            self._filesize = size

    @property
    def datasize(self) -> int:
        if self.is_file():
            return self._filesize

        size = sum((node.size for node in self.rfiles(includedOnly=True)))
        return size

    def find_by_path(self, path: Union[Path, str], skipExcluded: bool = True) -> FSTNode:
        _path = path.as_posix().lower()
        doGlob = "?" in _path or "*" in _path

        if _path in {"", "."}:
            return self.rootnode

        for node in self.rchildren(skipExcluded):
            if doGlob:
                if fnmatch(node.path, _path):
                    return node
            else:
                if node.path.lower() == _path:
                    return node

        return None

    def add_child(self, node: FSTNode):
        self._children[node.name] = node
        node.parent = self

    def remove_child(self, node: FSTNode):
        self._children.pop(node.name)
        node.parent = None

    def num_children(self, skipExcluded: bool = True) -> int:
        return len(list(self.rchildren(includedOnly=skipExcluded)))

    def destroy(self):
        self.parent = None
        for child in self.children:
            self.remove_child(child)

    def is_dir(self) -> bool:
        return self.type == FSTNode.FOLDER

    def is_file(self) -> bool:
        return self.type == FSTNode.FILE

    def is_root(self) -> bool:
        return self.type == FSTNode.FOLDER and self.name == "files" and self.parent is None

    def __eq__(self, other: FSTNode) -> bool:
        return self.name == other.name and self.type == other.type

    def __ne__(self, other: FSTNode) -> bool:
        return self.name != other.name or self.type != other.type

    def __len__(self) -> int:
        if self.is_file():
            return self._filesize
        return self.num_children() + 1

    def __bool__(self) -> bool:
        return True

    def __contains__(self, other: Union[FSTNode, Path]) -> bool:
        if isinstance(other, FSTNode):
            for child in self.children:
                if child == other:
                    return True
            return False
        return bool(self.find_by_path(other))


class FSTRoot(FSTNode):
    def __init__(self):
        super().__init__("files", FSTNode.FOLDER)
        self._id = 0

    def __repr__(self):
        return f"{self.__class__.__name__}<{self.num_children()} entries>"

    def nodes_by_offset(self, reverse: bool = False) -> FSTNode:
        for node in sorted(self.rfiles(), key=lambda x: x._fileoffset, reverse=reverse):
            yield node

    @staticmethod
    def _detect_alignment(node: FSTNode, prev: Optional[FSTNode] = None) -> int:
        if prev:
            offset = node._fileoffset - (prev._fileoffset + prev.size)
        else:
            offset = node._fileoffset

        if offset == 0:
            return 4

        alignment = 4
        mask = 0x7FFF
        for _ in range(13):
            if (node._fileoffset & mask) == 0:
                alignment = mask + 1
                break
            mask >>= 1

        mask = 0x7FFF
        found = False
        for _ in range(13):
            if (offset & mask) == 0:
                if mask + 1 <= alignment:
                    alignment = mask + 1
                found = True
                break
            mask >>= 1

        if not found:
            return 4
        return alignment


class FST(FSTRoot):

    @property
    def strTableOfs(self) -> int:
        return len(self) * 0xC

    def print_info(self):
        def print_tree(node: FSTNode, string: str, depth: int) -> str:
            if node.is_file():
                string += "  "*depth + node.name + "\n"
            else:
                string += "  "*depth + \
                    f"{node.name} ({node._dirparent}, {node._dirnext})\n" + \
                    "  "*depth + "{\n"
                for child in node.children:
                    string = print_tree(child, string, depth + 1)
                string += "  "*depth + "}\n"

            return string

        print(self)
        print("-"*32)

        string = ""
        for child in self.children:
            string = print_tree(child, string, 0)

        print(string)
