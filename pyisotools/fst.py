from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path


class FileAccessOnFolderError(Exception):
    pass


class FolderAccessOnFileError(Exception):
    pass


class InvalidEntryError(Exception):
    pass


class InvalidFSTError(Exception):
    pass


class FSTNode(object):

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

        self._children = {}
        self._parent = None
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
    def folder(cls, name: str, parent: FSTNode = None, children: list = ()):
        return cls(name, FSTNode.FOLDER, parent=parent, children=children)

    @classmethod
    def from_path(cls, path: Path) -> FSTNode:
        if path.is_file():
            node = cls.file(path.name)
            node.size = path.stat().st_size()
        elif path.is_dir():
            node = cls.folder(path.name)
            for f in path.iterdir():
                child = cls.from_path(f)
                node.add_child(child)
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

    @property
    def rdirs(self) -> FSTNode:
        for node in self.children:
            if node.is_dir():
                yield node
                yield from node.rdirs

    @property
    def rfiles(self) -> FSTNode:
        for node in self.children:
            if node.is_file():
                yield node
            else:
                yield from node.rfiles

    @property
    def rchildren(self) -> FSTNode:
        for node in self.children:
            yield node
            yield from node.rchildren

    @property
    def parent(self) -> FSTNode:
        return self._parent

    @parent.setter
    def parent(self, node: FSTNode):
        if self.parent is not None:
            if self.is_dir():
                if node is not None:
                    diff = node._id - self._dirparent
                    self._dirparent = node._id
                else:
                    diff = -self._dirparent
                    self._dirparent = 0
                for child in node.children:
                    child.id += diff
            self.parent.remove_child(self)
        else:
            if node is not None:
                self._dirparent = node._id
            else:
                self._dirparent = 0

        if node is not None:
            node._children[self.name] = self

        self._parent = node

    @property
    def children(self):
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
        else:
            return self.num_children()

    @size.setter
    def size(self, size: int):
        if self.is_file():
            self._filesize = size

    @property
    def datasize(self) -> int:
        if self.is_file():
            return self._filesize
        else:
            return self._collect_size(0)

    def find_by_path(self, path: [Path, str], skipExcluded: bool = True) -> FSTNode:
        _path = str(path).lower()
        doGlob = "?" in _path or "*" in path

        for node in self.rfiles:
            if node._exclude and skipExcluded:
                continue

            if doGlob:
                if fnmatch(node.path, _path):
                    return node
            else:
                if node.path.lower() == _path:
                    return node
        for node in self.rdirs:
            if node._exclude and skipExcluded:
                continue

            if doGlob:
                if fnmatch(node.path, _path):
                    return node
            else:
                if node.path.lower() == _path:
                    return node

    def add_child(self, node: FSTNode):
        self._children[node.name] = node
        node.parent = self

    def remove_child(self, node: FSTNode):
        self._children.pop(node.name)
        node.parent = None

    def num_children(self, onlyActive: bool = True) -> int:

        def _collect_children_count(node: FSTNode, counter: int) -> int:
            for child in node.children:
                if child._exclude and onlyActive:
                    continue

                counter = _collect_children_count(child, counter+1)
            return counter

        return _collect_children_count(self, 0)

    def destroy(self):
        self.parent = None
        for child in self.children:
            self.remove_child(child)

    def is_dir(self) -> bool:
        return self.type == FSTNode.FOLDER

    def is_file(self) -> bool:
        return self.type == FSTNode.FILE

    def is_root(self) -> bool:
        return self.type == FSTNode.FOLDER and self.name == "files" and self.parent == None

    def _collect_size(self, size: int) -> int:
        for node in self.children:
            if node._exclude:
                continue

            if node.is_file():
                size += node.size
            else:
                size = node._collect_size(size)

        return size

    def __eq__(self, other: FSTNode) -> bool:
        return self.name == other.name and self.type == other.name

    def __ne__(self, other: FSTNode) -> bool:
        return self.name != other.name or self.type != other.name

    def __len__(self) -> int:
        if self.is_file():
            return self._filesize
        else:
            return self.num_children() + 1

    def __bool__(self) -> bool:
        return True

    def __contains__(self, other: [FSTNode, Path]) -> bool:
        if isinstance(other, FSTNode):
            for child in self.children:
                if child == other:
                    return True
            return False
        else:
            if self.find_by_path(other):
                return True
            else:
                return False


class FSTRoot(FSTNode):
    def __init__(self):
        super().__init__("files", FSTNode.FOLDER)
        self._id = 0

    def __repr__(self):
        return f"{self.__class__.__name__}<{self.num_children()} entries>"

    def nodes_by_offset(self, reverse: bool = False) -> FSTNode:
        filenodes = [node for node in self.rfiles]
        for node in sorted(filenodes, key=lambda x: x._fileoffset, reverse=reverse):
            yield node

    def _detect_alignment(self, node: FSTNode, prev: FSTNode = None) -> int:
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
                else:
                    found = True
                    break
            mask >>= 1

        if not found:
            return 4
        return alignment


class FST(FSTRoot):

    def __init__(self):
        super().__init__()

    @property
    def strTableOfs(self) -> int:
        return len(self) * 0xC

    def print_info(self, fst=None):
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