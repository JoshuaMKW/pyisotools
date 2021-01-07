from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from iohelper import read_string, read_ubyte, read_uint32, write_uint32


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
        self.data = None

        # folder attributes
        self.dirparent = parentnode
        self.dirnext = nextnode

        self._children = {}
        self._parent = None
        self._datasize = 0
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

    def rcreate(self, path: Path, parentnode: FSTNode = None, ignorePath=()):
        for entry in path.iterdir():
            skip = False
            for p in ignorePath:
                if entry == p:
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
                self.rcreate(entry, child, ignorePath=ignorePath)
                if parentnode is not None:
                    parentnode.add_child(child)
            else:
                raise InvalidEntryError("Not a dir or file")

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
    def size(self) -> int:
        if self.is_file():
            return self._filesize
        else:
            return self._get_node_info(self, 0, 0)[0]

    @size.setter
    def size(self, size: int):
        if self.is_file():
            self._filesize = size

    @property
    def datasize(self) -> int:
        return self._collect_size(0)

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

    def _get_node_info(self, node: FSTNode, counter: int, strTabSize: int) -> (int, int):
        counter += 1
        if counter > 1:
            strTabSize += len(node.name) + 1

        for child in node.children:
            counter, strTabSize = self._get_node_info(
                child, counter, strTabSize)

        return counter, strTabSize

    def _collect_size(self, size: int) -> int:
        for child in self.children:
            if child.is_file():
                size += (child.size + 0x7FF) & -0x800
            else:
                size = child._collect_size(size)

        return (size + 0x7FF) & -0x800


class FSTRoot(FSTNode):
    def __init__(self):
        super().__init__("root", FSTNode.FOLDER)
        self.entryCount = 0
        self._id = 0

    def __repr__(self):
        return f"FST Root <{self.entryCount} entries>"

    def __len__(self):
        return self.entryCount


class FST(FSTRoot):
    def __init__(self):
        super().__init__()
        self._curEntry = 0
        self._strOfs = 0
        self._dataOfs = 0

        self._alignmentTable = {}
        self._init_alignment_table()

    def __repr__(self):
        return f"FST Object <{self.entryCount} entries>"

    @property
    def strTableOfs(self):
        return len(self) * 0xC

    def save(self, fst, startpos: int = 0):
        self.entryCount, _ = self._get_node_info(self, 0, 0)

        fst.write(b"\x01\x00\x00\x00\x00\x00\x00\x00")
        write_uint32(fst, self.entryCount)

        self._dataOfs = startpos
        self._curEntry = 1
        self._strOfs = 0
        for child in self.children:
            self._write_nodes(fst, child)
        fst.write(b"\x00" * ((fst.tell() + 3) & -4))

    def load(self, fst) -> FSTNode:
        if fst.read(1) != b"\x01":
            raise InvalidFSTError("Invalid Root flag found")
        elif fst.read(3) != b"\x00\x00\x00":
            raise InvalidFSTError("Invalid Root string offset found")
        elif fst.read(4) != b"\x00\x00\x00\x00":
            raise InvalidFSTError("Invalid Root offset found")

        self.entryCount = read_uint32(fst)

        self._curEntry = 1
        while self._curEntry < self.entryCount:
            child = self._read_nodes(fst, FSTNode.empty())
            self.add_child(child)
        
        return self

    def print_info(self, fst=None):
        def print_tree(node: FSTNode, string: str, depth: int) -> str:
            if node.is_file():
                string += "  "*depth + node.name + "\n"
            else:
                string += "  "*depth + \
                    f"{node.name} ({node.dirparent}, {node.dirnext})\n" + \
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
            node.dirparent = _entryOfs
            node.dirnext = _size

            while self._curEntry < _size:
                child = self._read_nodes(fst, FSTNode.empty())
                node.add_child(child)
        else:
            node.type = FSTNode.FILE
            node.size = _size
            node._fileoffset = _entryOfs

        return node

    def _write_nodes(self, fst, node: FSTNode):
        self._dataOfs = (self._dataOfs + 0x7FF) & -0x800
        if node.is_file():
            if node._fileoffset == None:
                node._fileoffset = self._dataOfs
        
        node._id = self._curEntry

        totalChildren, _ = self._get_node_info(node, 0, 0)

        fst.write(b"\x01" if node.is_dir() else b"\x00")
        fst.write((self._strOfs).to_bytes(3, "big", signed=False))
        write_uint32(fst, node.parent._id if node.is_dir() else self._dataOfs)
        write_uint32(fst, totalChildren +
                     self._curEntry if node.is_dir() else node.size)

        self._curEntry += 1

        _oldpos = fst.tell()
        fst.seek(self._strOfs + self.strTableOfs)
        fst.write(node.name.encode("ascii") + b"\x00")
        self._strOfs += len(node.name) + 1
        if node.is_file():
            self._dataOfs += node.size

        fst.seek(_oldpos)

        for child in node.children:
            self._write_nodes(fst, child)

    def _init_alignment_table(self, configPath: Path = Path("alignment.json")):
        with configPath.open("r") as config:
            data = json.load(config)

        self._alignmentTable = data


if __name__ == "__main__":
    fst = FST()

    with open(sys.argv[1], "rb") as _fstbin:
        fst.print_info(_fstbin)
