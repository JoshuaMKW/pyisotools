from __future__ import annotations

import json
import os
import sys
import time
from fnmatch import fnmatch
from pathlib import Path

from pyisotools.iohelper import align_int, read_string, read_ubyte, read_uint32, write_uint32


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

    def __init__(self, name: str, nodetype: int = None, nodeid: int = None, filesize: int = None, fileoffset: int = None, parentnode: int = None, nextnode: int = None):
        self.name = name
        self.type = nodetype

        # file attributes
        self._filesize = filesize
        self._fileoffset = fileoffset

        # folder attributes
        self._dirparent = parentnode
        self._dirnext = nextnode

        self._children = {}
        self._alignment = 4
        self._parent = None
        self._id = None

    def __repr__(self):
        return f"FST Node <{vars(self)}>"

    @classmethod
    def file(cls, name: str):
        return cls(name, FSTNode.FILE)

    @classmethod
    def folder(cls, name: str):
        return cls(name, FSTNode.FOLDER)

    @classmethod
    def empty(cls):
        return cls("")

    @property
    def path(self) -> Path:
        path = Path(self.name)
        parent = self.parent
        while parent is not None:
            path = Path(parent.name) / path
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
    def parent(self) -> FSTNode:
        return self._parent

    @parent.setter
    def parent(self, node: FSTNode):
        if self.parent is not None:
            self.parent.remove_child(self)

        if node is not None:
            node.add_child(self)

        self._parent = node

    @property
    def children(self):
        for child in self._children.values():
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
            return self._get_node_info(self, 0, 0)[0]

    @property
    def datasize(self) -> int:
        return self._collect_size(0)

    @size.setter
    def size(self, size: int):
        if self.is_file():
            self._filesize = size

    def walk(self, topdown: bool = True):
        dirs, files = [], []
        for node in self.children:
            if node.is_file():
                files.append(node)
            elif node.is_dir():
                dirs.append(node)

        if topdown:
            yield self.path, dirs, files
        for node in dirs:
            yield from node.walk(topdown)
        if not topdown:
            yield self.path, dirs, files

    def add_child(self, node: FSTNode):
        self._children[node.name] = node
        node._parent = self

    def remove_child(self, node: FSTNode):
        self._children.pop(node.name)
        node.parent = None

    def is_dir(self) -> bool:
        return self.type == FSTNode.FOLDER

    def is_file(self) -> bool:
        return self.type == FSTNode.FILE

    def is_root(self) -> bool:
        return self.type == FSTNode.FOLDER and self.name == "root" and self.parent == None

    def _collect_size(self, size: int) -> int:
        for node in self.children:
            if node._get_excluded() is True or self._get_location() is not None:
                continue

            if node.is_file():
                alignment = node._get_alignment()
                size = align_int(size, alignment)
                size += node.size

            size = node._collect_size(size)

        return align_int(size, 4)

    def _get_greatest_alignment(self) -> int:
        root = self.rootnode
        return sorted(root._alignmentTable.values(), reverse=True)[0]

    def _get_alignment(self) -> int:
        root = self.rootnode
        if root._alignmentTable:
            for entry in root._alignmentTable:
                if fnmatch(str(self.path).replace(os.sep, '/').lower(), entry.strip().lower()):
                    return root._alignmentTable[entry]
        return 4

    def _get_location(self) -> int:
        root = self.rootnode
        if root._locationTable:
            for entry in root._locationTable:
                if fnmatch(str(self.path).replace(os.sep, '/').lower(), entry.strip().lower()):
                    return root._locationTable[entry]
        return None

    def _get_excluded(self) -> bool:
        root = self.rootnode
        if root._excludeTable:
            for entry in root._excludeTable:
                if fnmatch(str(self.path).replace(os.sep, '/').lower(), entry.strip().lower()):
                    return True
        return False

    def _get_node_info(self, node: FSTNode, counter: int, strTabSize: int) -> (int, int):
        counter += 1
        if counter > 1:
            strTabSize += len(node.name) + 1

        for child in node.children:
            counter, strTabSize = self._get_node_info(child, counter, strTabSize)

        return counter, strTabSize


class FSTRoot(FSTNode):
    def __init__(self):
        super().__init__("root", FSTNode.FOLDER)
        self.entryCount = 0
        self._id = 0

        self._alignmentTable = {}
        self._locationTable = {}
        self._excludeTable = []

    def __repr__(self):
        return f"FST Root <{self.entryCount} entries>"

    def __len__(self):
        return self.entryCount

    def find_by_path(self, path: Path) -> FSTNode:
        for node in self.rfiles:
            if node.path == path:
                return node

    def nodes_by_offset(self, reverse: bool = False) -> FSTNode:
        filenodes = [node for node in self.rfiles]

        for node in sorted(filenodes, key=lambda x: x._fileoffset, reverse=reverse):
            yield node

    def _init_tables(self, configPath: Path):
        with configPath.open("r") as config:
            data = json.load(config)

        self._alignmentTable = data["alignment"]
        self._locationTable = data["location"]
        self._excludeTable = data["exclude"]


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
        self.root = None
        self._curEntry = 0
        self._strOfs = 0
        self._dataOfs = 0
        self._prevfile = None

    def __repr__(self):
        return f"FST Object <{self.entryCount} entries>"

    @property
    def strTableOfs(self):
        return len(self) * 0xC

    def rcreate(self, path: Path, parentnode: FSTNode = None, ignoreList=[]):
        self._init_tables(path / "sys" / ".config.json") 
        ignoreList.append(*self._excludeTable)
        self._load_from_path(path, parentnode, ignoreList)

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

        if fst:
            self.load(fst)
        print(self)
        print("-"*32)

        string = ""
        for child in self.children:
            string = print_tree(child, string, 0)

        print(string)

    def load(self, fst) -> FSTNode:
        if fst.read(1) != b"\x01":
            raise InvalidFSTError("Invalid Root flag found")
        elif fst.read(3) != b"\x00\x00\x00":
            raise InvalidFSTError("Invalid Root string offset found")
        elif fst.read(4) != b"\x00\x00\x00\x00":
            raise InvalidFSTError("Invalid Root offset found")

        self._alignmentTable = {}
        self.entryCount = read_uint32(fst)

        self._curEntry = 1
        while self._curEntry < self.entryCount:
            child = self._read_nodes(fst, FSTNode.empty())
            self.add_child(child)

        return self

    def save(self, fst, startpos: int = 0):
        self._init_tables(self.root / "sys" / ".config.json")
        self.entryCount, _ = self._get_node_info(self, 0, 0)

        fst.write(b"\x01\x00\x00\x00\x00\x00\x00\x00")
        write_uint32(fst, self.entryCount)

        self._curEntry = 1
        self._strOfs = 0
        self._dataOfs = align_int(startpos, 4)
        for child in self.children:
            self._write_nodes(fst, child)

    def _read_nodes(self, fst, node: FSTNode) -> (FSTNode, int):
        _type = read_ubyte(fst)
        _nameOfs = int.from_bytes(fst.read(3), "big", signed=False)
        _entryOfs = read_uint32(fst)
        _size = read_uint32(fst)

        _oldpos = fst.tell()
        node.name = read_string(fst, self.strTableOfs + _nameOfs)
        fst.seek(_oldpos)

        self._curEntry += 1

        if _type == FSTNode.FOLDER:
            node.type = FSTNode.FOLDER
            node._dirparent = _entryOfs
            node._dirnext = _size

            while self._curEntry < _size:
                child = self._read_nodes(fst, FSTNode.empty())
                node.add_child(child)
        else:
            node.type = FSTNode.FILE
            node.size = _size
            node._fileoffset = _entryOfs

        return node

    def _write_nodes(self, fst, node: FSTNode):
        align = node._get_alignment()
        dataOfs = node._get_location()

        if not dataOfs:
            hasManualLocation = False
            dataOfs = self._dataOfs = align_int(self._dataOfs, align)
        else:
            hasManualLocation = True
            dataOfs = align_int(dataOfs, align)
            
        if node.is_file():
            if node._fileoffset == None:
                node._fileoffset = dataOfs

        node._id = self._curEntry

        totalChildren, _ = self._get_node_info(node, 0, 0)

        fst.write(b"\x01" if node.is_dir() else b"\x00")
        fst.write((self._strOfs).to_bytes(3, "big", signed=False))
        write_uint32(fst, node.parent._id if node.is_dir() else dataOfs)
        write_uint32(fst, totalChildren +
                     self._curEntry if node.is_dir() else node.size)

        self._curEntry += 1

        _oldpos = fst.tell()
        fst.seek(self._strOfs + self.strTableOfs)
        fst.write(node.name.encode("ascii") + b"\x00")
        self._strOfs += len(node.name) + 1

        if node.is_file() and not hasManualLocation:
            self._dataOfs += node.size

        fst.seek(_oldpos)

        for child in node.children:
            self._write_nodes(fst, child)

    def _load_from_path(self, path: Path, parentnode: FSTNode = None, ignoreList=()):
        for entry in path.iterdir():
            skip = False
            for p in ignoreList:
                if fnmatch(entry, p):
                    print(f"Skipping {entry}, {p}")
                    skip = True
                    break
            if skip:
                continue

            if entry.is_file():
                child = FSTNode.file(entry.name)
                child.size = entry.stat().st_size
                if parentnode is not None:
                    parentnode.add_child(child)
            elif entry.is_dir():
                child = FSTNode.folder(entry.name)
                self._load_from_path(entry, child, ignoreList=ignoreList)
                if parentnode is not None:
                    parentnode.add_child(child)
            else:
                raise InvalidEntryError("Not a dir or file")
