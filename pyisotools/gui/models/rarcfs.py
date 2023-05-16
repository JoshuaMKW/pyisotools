from __future__ import annotations
from abc import ABC, abstractmethod

from dataclasses import dataclass
from enum import IntEnum
from genericpath import isfile
from io import BytesIO
from logging import root
import os
from pathlib import Path, PurePath
import shutil
import time
from typing import Any, Optional, Union, overload
from isort import file

from numpy import source
from pyisotools.gui.images import get_icon

from pyisotools.utils.rarc import (A_ResourceHandle, FileConflictAction, ResourceArchive, ResourceDirectory,
                                   ResourceFile)
from PySide6.QtCore import (QAbstractItemModel, QByteArray, QDataStream, QFile, QDir, QFileSystemWatcher, QUrl, QTimer, QMutex, QMutexLocker, QReadWriteLock, QReadLocker, QWriteLocker,
                            QFileInfo, QIODevice, QMimeData, QModelIndex, QIdentityProxyModel,
                            QObject, QPersistentModelIndex, QPoint, QRect,
                            QRectF, QRegularExpression, QSize,
                            QSortFilterProxyModel, Qt, Signal, Slot)
from PySide6.QtGui import (QAction, QBrush, QColor, QFont, QIcon, QImage,
                           QIntValidator, QMouseEvent, QPainter, QPainterPath,
                           QPaintEvent, QPen, QPolygon, QStandardItem,
                           QStandardItemModel, QTextCursor, QTransform)

import threading


class JSystemFSModel(QAbstractItemModel):
    """
    Mimics QFileSystemModel with a watchdog and async updates, with RARC support
    """
    rootPathChanged = Signal(PurePath)
    conflictFound = Signal(PurePath, PurePath, bool)

    FileIconRole = Qt.DecorationRole
    FilePathRole = Qt.UserRole + 1
    FileNameRole = Qt.UserRole + 2

    ArchiveMimeType = "x-application/jsystem-fs-data"

    ExtensionToTypeMap: dict[str, str] = {
        ".szs": "Yaz0 Compressed File",
        ".arc": "Archive (RARC)",
        ".thp": "Nintendo JPEG Video",
        ".map": "Codewarrior Symbol Map",
        ".me": "Dummy File",
        ".bmg": "Message Table",
        ".bnr": "Game Banner",
        ".bin": "Binary Data",
        ".ral": "Rail Table",
        ".ymp": "Pollution Heightmap",
        ".bti": "Texture Image",
        ".blo": "2D Layout",
        ".bcr": "Controller Rumble Script",
        ".bfn": "Font",
        ".bmd": "J3D Model",
        ".bdl": "J3D Model",
        ".bmt": "J3D Material Table",
        ".bck": "J3D Bone Animation",
        ".btp": "J3D Texture Pattern Animation",
        ".btk": "J3D Texture Animation",
        ".brk": "J3D Texture Register Animation",
        ".bpk": "J3D Color Animation",
        ".blk": "J3D Vertex Animation (UNUSED)",
        ".bva": "J3D Mesh Visibility Animation (UNUSED)",
        ".col": "Collision Model",
        ".jpa": "JSystem Particle Effect",
        ".sb": "SPC Script (Sunscript)",
        ".prm": "Parameter Table",
        ".pad": "Controller Input Recording",
        ".bmp": "Bitmap Image",
        ".bas": "Animation Sound Index",
        ".aaf": "Audio Initialization Info",
        ".asn": "Audio Name Table",
        ".bms": "Audio Sequence",
        ".aw": "Audio Archive",
        ".afc": "Streamed Audio (UNUSED)",
        ".ws": "Wave System Table",
        ".bnk": "Instrument Bank",
    }

    class _FsKind(IntEnum):
        UNKNOWN = -1
        FILE = 0
        DIRECTORY = 1
        ARCHIVE = 2

    @dataclass
    class _FsSorter:
        name: str
        fsKind: "JSystemFSModel._FsKind"

        def __lt__(self, other: object) -> bool:
            if not isinstance(other, JSystemFSModel._FsSorter):
                return False

            selfNameLower = self.name.lower()
            otherNameLower = other.name.lower()

            if self.fsKind == JSystemFSModel._FsKind.FILE:
                if other.fsKind == JSystemFSModel._FsKind.FILE:
                    return selfNameLower < otherNameLower
                if other.fsKind == JSystemFSModel._FsKind.ARCHIVE:
                    return False
                if other.fsKind == JSystemFSModel._FsKind.DIRECTORY:
                    return False

            if self.fsKind == JSystemFSModel._FsKind.ARCHIVE:
                if other.fsKind == JSystemFSModel._FsKind.FILE:
                    return True
                if other.fsKind == JSystemFSModel._FsKind.ARCHIVE:
                    return selfNameLower < otherNameLower
                if other.fsKind == JSystemFSModel._FsKind.DIRECTORY:
                    return selfNameLower < otherNameLower

            if self.fsKind == JSystemFSModel._FsKind.DIRECTORY:
                if other.fsKind == JSystemFSModel._FsKind.FILE:
                    return True
                if other.fsKind == JSystemFSModel._FsKind.ARCHIVE:
                    return selfNameLower < otherNameLower
                if other.fsKind == JSystemFSModel._FsKind.DIRECTORY:
                    return selfNameLower < otherNameLower

            return selfNameLower < otherNameLower

    @dataclass
    class _HandleInfo:
        row: int
        path: PurePath
        parent: "JSystemFSModel._HandleInfo" | None
        children: list["JSystemFSModel._HandleInfo"]
        fsKind: "JSystemFSModel._FsKind"
        size: int
        loaded: bool = False
        hasSubDir: bool = False
        icon: QIcon | None = None
        archive: QModelIndex | None = None

        def reparent(self, parent: "JSystemFSModel._HandleInfo" | None = None, cacheIndex: int = -1):
            if cacheIndex == -1:
                selfName = self.path.name
                for i, child in enumerate(parent.children):
                    if child < self:
                        continue
                    cacheIndex = i
                    break

            if self.parent:
                self.parent.children.remove(self)
            self.parent = parent

            self.path = PurePath(selfName)
            if parent:
                self.path = parent.path / selfName
                parent.children.insert(cacheIndex, self)
                for i, child in enumerate(parent.children[cacheIndex:]):
                    child.row = cacheIndex + i

        def __repr__(self) -> str:
            if self.parent:
                return f"Handle(\"{self.path.parent.name}/{self.path.name}\", parent={self.parent.path.name}, id=0x{id(self):016X})"
            return f"Handle(\"{self.path.parent.name}/{self.path.name}\", parent=None, id=0x{id(self)})"

        def __eq__(self, other: object) -> bool:
            if not isinstance(other, JSystemFSModel._HandleInfo):
                return False

            return all([
                self.path == other.path,
                self.parent == other.parent
            ])

        def __lt__(self, other: object) -> bool:
            if not isinstance(other, JSystemFSModel._HandleInfo):
                return False

            if self.fsKind == JSystemFSModel._FsKind.FILE:
                if other.fsKind == JSystemFSModel._FsKind.FILE:
                    return self.path.name < other.path.name
                if other.fsKind == JSystemFSModel._FsKind.ARCHIVE:
                    return False
                if other.fsKind == JSystemFSModel._FsKind.DIRECTORY:
                    return False

            if self.fsKind == JSystemFSModel._FsKind.ARCHIVE:
                if other.fsKind == JSystemFSModel._FsKind.FILE:
                    return True
                if other.fsKind == JSystemFSModel._FsKind.ARCHIVE:
                    return self.path.name < other.path.name
                if other.fsKind == JSystemFSModel._FsKind.DIRECTORY:
                    return self.path.name < other.path.name

            if self.fsKind == JSystemFSModel._FsKind.DIRECTORY:
                if other.fsKind == JSystemFSModel._FsKind.FILE:
                    return True
                if other.fsKind == JSystemFSModel._FsKind.ARCHIVE:
                    return self.path.name < other.path.name
                if other.fsKind == JSystemFSModel._FsKind.DIRECTORY:
                    return self.path.name < other.path.name

            return self.path.name < other.path.name

    def __init__(self, rootPath: Path | None, readOnly: bool = True, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._rootPath: Path | None = None  # Initial state
        self._rootPathExists: bool = False
        self._archives: dict[PurePath, ResourceArchive] = {}

        self._readOnly = readOnly

        self._fileSystemWatcher = QFileSystemWatcher(self)
        self._fileSystemWatcher.fileChanged.connect(self.file_changed)
        self._fileSystemWatcher.directoryChanged.connect(
            self.directory_changed)

        self._fileSystemCache: JSystemFSModel._HandleInfo | None = None

        self._icons: dict[str, QIcon] = {}
        self._conflictAction: FileConflictAction | None = None
        self._actionAll = False

        self._indexesToRecache: set[QModelIndex] = set()
        # QReadWriteLock(recursionMode=QReadWriteLock.Recursive)
        self._fsLock = QReadWriteLock(recursionMode=QReadWriteLock.Recursive)
        self._skipRecache = False
        self._skipArchiveUpdate = False

        self.rootPath = rootPath
        self._initialize_icons()
        self.reset_cache()

    @property
    def rootPath(self) -> Path | None:
        return self._rootPath

    @rootPath.setter
    def rootPath(self, rootPath: Path | None) -> None:
        if rootPath == self._rootPath:
            return

        self._rootPath = rootPath
        if not rootPath or not rootPath.exists():
            self._rootPathExists = False
            self._fileSystemCache = None
            return

        self.beginResetModel()

        self._rootPathExists = True
        self._fileSystemCache = JSystemFSModel._HandleInfo(
            row=0,
            path=rootPath,
            parent=None,
            children=[],
            fsKind=JSystemFSModel._FsKind.DIRECTORY,
            size=0
        )

        files = self._fileSystemWatcher.files()
        if len(files) > 0:
            self._fileSystemWatcher.removePaths(files)

        directories = self._fileSystemWatcher.directories()
        if len(directories) > 0:
            self._fileSystemWatcher.removePaths(directories)

        self.cache_index(self.index(0, 0))

        self.endResetModel()

        self.rootPathChanged.emit(rootPath)
        return

    @property
    def readOnly(self) -> bool:
        return self._readOnly

    @readOnly.setter
    def readOnly(self, readOnly: bool) -> None:
        self._readOnly = readOnly

    @property
    def skipArchiveUpdates(self) -> bool:
        return self._skipArchiveUpdate

    @skipArchiveUpdates.setter
    def skipArchiveUpdates(self, skip: bool) -> None:
        self._skipArchiveUpdate = skip

    def is_loaded(self, index: QModelIndex) -> bool:
        with QReadLocker(self._fsLock):
            if not index.isValid():
                return False

            parentInfo: JSystemFSModel._HandleInfo = index.internalPointer()
            return parentInfo.loaded

    def is_file(self, index: QModelIndex) -> bool:
        with QReadLocker(self._fsLock):
            if not index.isValid():
                return False

            handleInfo: JSystemFSModel._HandleInfo = index.internalPointer()
            return handleInfo.fsKind == JSystemFSModel._FsKind.FILE

    def is_dir(self, index: QModelIndex) -> bool:
        with QReadLocker(self._fsLock):
            if not index.isValid():
                return False

            handleInfo: JSystemFSModel._HandleInfo = index.internalPointer()
            return handleInfo.fsKind == JSystemFSModel._FsKind.DIRECTORY

    def is_archive(self, index: QModelIndex) -> bool:
        with QReadLocker(self._fsLock):
            if not index.isValid():
                return False

            handleInfo: JSystemFSModel._HandleInfo = index.internalPointer()
            return handleInfo.fsKind == JSystemFSModel._FsKind.ARCHIVE

    def is_populated(self, index: QModelIndex) -> bool:
        with QReadLocker(self._fsLock):
            if not index.isValid():
                return False

            if self.is_file(index):
                return False

            handleInfo: JSystemFSModel._HandleInfo = index.internalPointer()
            if handleInfo.size > 0:  # Size is already cached
                return True

            indexPath = self.get_path(index)

            archiveIndex = self.get_parent_archive(index)
            if archiveIndex.isValid():
                return False

                # virtualPath = indexPath.relative_to(archivePath)
                # handle = archive.get_handle(virtualPath)
                # if handle is None:
                #     return False

                # if handle.is_directory():
                #     handleInfo.size = len(handle.get_handles())
                #     return handleInfo.size > 0

                # if handle.is_file() and handle.get_extension() == ".arc":
                #     return not ResourceArchive.is_archive_empty(
                #         BytesIO(handle.get_raw_data())
                #     )

            if os.path.isdir(indexPath):
                for _ in Path(indexPath).glob("*"):
                    return True
                return False

            if os.path.isfile(indexPath) and indexPath.suffix == ".arc":
                with open(indexPath, "rb") as f:
                    isEmpty = ResourceArchive.is_archive_empty(f)
                return not isEmpty

            return False

    def is_child_of_archive(self, index: QModelIndex) -> bool:
        with QReadLocker(self._fsLock):
            if not index.isValid():
                return False

            handleInfo: JSystemFSModel._HandleInfo = index.internalPointer()
            if handleInfo.archive is None:  # Not cached yet
                parent = index.parent()
                while parent.isValid():
                    if self.get_path(parent) in self._archives:
                        return True
                    parent = parent.parent()
                return False
            return handleInfo.archive.isValid()

    def is_yaz0_compressed(self, index: QModelIndex) -> bool:
        with QReadLocker(self._fsLock):
            if not index.isValid():
                return False
            path = self.get_path(index)
            if path.suffix != ".szs":
                return False
            with open(path, "rb") as f:
                magic = f.read(4)
            return magic == b"Yaz0"

    def get_conflict_action(self) -> FileConflictAction | None:
        if self.is_action_for_all():
            return self._conflictAction
        action = self._conflictAction
        self._conflictAction = None
        return action

    def set_conflict_action(self, action: FileConflictAction | None) -> None:
        self._conflictAction = action

    def is_action_for_all(self) -> bool:
        return self._actionAll

    def set_action_for_all(self, forAll: bool) -> None:
        self._actionAll = forAll

    def get_parent_archive(self, index: QModelIndex | QPersistentModelIndex) -> QModelIndex:
        with QReadLocker(self._fsLock):
            if not index.isValid():
                return QModelIndex()

            handleInfo: JSystemFSModel._HandleInfo = index.internalPointer()
            if handleInfo.archive is None:  # Not cached yet
                parent = index.parent()
                while parent.isValid():
                    parentInfo: JSystemFSModel._HandleInfo = parent.internalPointer()
                    if parentInfo.fsKind == JSystemFSModel._FsKind.ARCHIVE:
                        handleInfo.archive = parent
                        return parent  # We found an archive
                    parent = parent.parent()
                handleInfo.archive = QModelIndex()

            return handleInfo.archive

    def get_path_index(self, path: PurePath) -> QModelIndex:
        if self.rootPath is None or self._fileSystemCache is None:
            return QModelIndex()

        if path.name in {"", ".", "scene"}:
            return self.createIndex(0, 0, self._fileSystemCache)

        relPath = path.relative_to(self.rootPath.parent)

        with QReadLocker(self._fsLock):
            handleInfo = self._fileSystemCache
            row = 0
            for part in relPath.parts[1:]:
                row = 0
                for child in handleInfo.children:
                    if child.path.name == part:
                        handleInfo = child
                        break
                    row += 1
                else:
                    return QModelIndex()

            return self.createIndex(row, 0, handleInfo)

    def get_icon(self, index: QModelIndex | QPersistentModelIndex) -> QIcon:
        return self.data(index, self.FileIconRole)

    def get_name(self, index: QModelIndex | QPersistentModelIndex) -> str:
        return self.data(index, self.FileNameRole)

    def get_path(self, index: QModelIndex | QPersistentModelIndex) -> PurePath:
        return self.data(index, self.FilePathRole)

    def get_size(self, index: QModelIndex | QPersistentModelIndex) -> int:
        with QReadLocker(self._fsLock):
            if not index.isValid():
                return -1

            handleInfo: JSystemFSModel._HandleInfo = index.internalPointer()
            return handleInfo.size

    def get_type(self, index: QModelIndex | QPersistentModelIndex) -> str:
        with QReadLocker(self._fsLock):
            if not index.isValid():
                return "UNKNOWN"

            name = self.get_name(index)
            if self.is_file(index):
                return self.ExtensionToTypeMap.get(name, "File")
            return "Folder"

    def move(self, index: QModelIndex | QPersistentModelIndex, destinationParent: QModelIndex | QPersistentModelIndex, action: FileConflictAction | None = None) -> QModelIndex:
        with QReadLocker(self._fsLock):
            sourceHandleInfo: JSystemFSModel._HandleInfo = destinationParent.internalPointer()
            sourceParent = index.parent()
            sourceRow = index.row()
            sourcePath = sourceHandleInfo.path
            sourceName = sourcePath.name

            if not index.isValid() or not destinationParent.isValid():
                return QModelIndex()

            destParentInfo: JSystemFSModel._HandleInfo = destinationParent.internalPointer()
            destParentPath = destParentInfo.path
            destPath = destParentPath / sourceName

            # Check if the source is part of an archive
            sourceArchive: Optional[ResourceArchive] = None
            sourceArchiveIndex = QPersistentModelIndex(
                self.get_parent_archive(sourceParent))
            sourceArchivePath = self.get_path(sourceArchiveIndex)
            if sourceArchiveIndex.isValid():
                sourceArchive = self._archives[sourceArchivePath]

            # Check if the destination is part of an archive
            destArchive: Optional[ResourceArchive] = None
            destArchiveIndex = QPersistentModelIndex(
                self.get_parent_archive(destinationParent))
            destArchivePath = self.get_path(destArchiveIndex)
            if destArchiveIndex.isValid():
                destArchive = self._archives[destArchivePath]

        with QWriteLocker(self._fsLock):
            for i, childHandle in enumerate(destParentInfo.children):
                if childHandle < sourceHandleInfo:
                    continue

                if sourceArchive:  # Source exists in an archive
                    virtualSourcePath = sourcePath.relative_to(
                        sourceArchivePath)
                    sourceHandle = sourceArchive.get_handle(virtualSourcePath)
                    if sourceHandle is None:
                        return QModelIndex()

                    if destArchive:  # Destination exists in an archive
                        virtualDestPath = destPath.relative_to(destArchivePath)
                        destHandle = destArchive.get_handle(virtualDestPath)
                        if destHandle:  # Destination move exists
                            conflictAction = self._capture_conflict_resolution(
                                sourcePath, destPath, destHandle.is_directory()
                            )

                            if conflictAction == FileConflictAction.SKIP:
                                return QModelIndex()

                            if conflictAction == FileConflictAction.KEEP:
                                newPath = self._resolve_path_conflict(
                                    sourcePath.name, destinationParent)
                                if newPath is None:
                                    return QModelIndex()
                                destPath = newPath
                                virtualDestPath = destPath.relative_to(
                                    destArchivePath)

                        # Archives are the same; internal move
                        if sourceArchive == destArchive:
                            self._skipRecache = True
                            self.beginMoveRows(
                                sourceParent, sourceRow, sourceRow, destinationParent, i)
                            successful = sourceHandle.rename(
                                virtualDestPath, action=FileConflictAction.REPLACE)
                            if not successful:
                                raise RuntimeError(
                                    "Failed to export the source file handle to the destination")
                            sourceHandleInfo.reparent(destParentInfo, i)
                            self.endMoveRows()
                            return self.index(i, 0, destinationParent)

                        sourceParentHandle = sourceHandle.get_parent()
                        if sourceParentHandle is None:
                            return QModelIndex()

                        destParentHandle = destArchive.get_handle(
                            virtualDestPath.parent)
                        if destParentHandle is None:
                            return QModelIndex()

                        # Archives are different, move between them
                        self._skipRecache = True
                        self.beginMoveRows(
                            sourceParent, sourceRow, sourceRow, destinationParent, i)
                        sourceParentHandle.remove_handle(sourceHandle)
                        successful = destParentHandle.add_handle(sourceHandle)
                        if not successful:
                            raise RuntimeError(
                                "Failed to export the source file handle to the destination")
                        sourceHandleInfo.reparent(destParentInfo, i)
                        self.endMoveRows()
                        return self.index(i, 0, destinationParent)

                    conflictAction = FileConflictAction.REPLACE

                    # Destination exists in the filesystem
                    if os.path.exists(destPath):
                        conflictAction = self._capture_conflict_resolution(
                            sourcePath, destPath, os.path.isdir(destPath)
                        )

                        if conflictAction == FileConflictAction.SKIP:
                            return QModelIndex()

                        elif conflictAction == FileConflictAction.KEEP:
                            newPath = self._resolve_path_conflict(
                                sourcePath.name, destinationParent)
                            if newPath is None:
                                return QModelIndex()
                            destPath = newPath
                            virtualDestPath = destPath.relative_to(
                                destArchivePath)

                    # Move handle from archive into filesystem
                    self._skipRecache = True
                    self.beginMoveRows(
                        sourceParent, sourceRow, sourceRow, destinationParent, i)
                    successful = sourceHandle.export_to(
                        Path(destPath.parent), action=FileConflictAction.REPLACE
                    )
                    if not successful:
                        raise RuntimeError(
                            "Failed to export the source file handle to the destination")
                    sourceHandleInfo.reparent(destParentInfo, i)
                    self.endMoveRows()
                    return self.index(i, 0, destinationParent)

                # Source exists in filesystem
                if destArchive:  # Destination exists in an archive
                    virtualDestPath = destPath.relative_to(destArchivePath)
                    destHandle = destArchive.get_handle(virtualDestPath)
                    if destHandle:  # Destination move exists
                        conflictAction = self._capture_conflict_resolution(
                            sourcePath, destPath, os.path.isdir(destPath)
                        )

                        if conflictAction == FileConflictAction.SKIP:
                            return QModelIndex()

                        elif conflictAction == FileConflictAction.KEEP:
                            newPath = self._resolve_path_conflict(
                                sourcePath.name, destinationParent)
                            if newPath is None:
                                return QModelIndex()
                            destPath = newPath
                            virtualDestPath = destPath.relative_to(
                                destArchivePath)

                    # Move from filesystem to archive
                    if (isSrcDir := os.path.isdir(sourcePath)):
                        sourceHandle = ResourceDirectory.import_from(
                            Path(sourcePath))
                    else:
                        sourceHandle = ResourceFile.import_from(
                            Path(sourcePath))

                    if sourceHandle is None:
                        return QModelIndex()

                    destParentHandle = destArchive.get_handle(
                        virtualDestPath.parent)
                    if destParentHandle is None:
                        return QModelIndex()

                    successful = destParentHandle.add_handle(
                        sourceHandle, action=FileConflictAction.REPLACE)
                    if not successful:
                        return QModelIndex()

                    self._skipRecache = True
                    self.beginMoveRows(
                        sourceParent, sourceRow, sourceRow, destinationParent, i)

                    # Remove old path
                    if isSrcDir:
                        shutil.rmtree(sourcePath)
                    else:
                        os.remove(sourcePath)

                    sourceHandleInfo.reparent(destParentInfo, i)
                    self.endMoveRows()

                    return self.index(i, 0, destinationParent)

                # Filesystem to filesystem
                conflictAction = FileConflictAction.REPLACE
                pathExists = os.path.exists(destPath)
                if pathExists:
                    conflictAction = self._capture_conflict_resolution(
                        sourcePath, destPath, os.path.isdir(destPath)
                    )

                    if conflictAction == FileConflictAction.SKIP:
                        return QModelIndex()

                    elif conflictAction == FileConflictAction.KEEP:
                        newPath = self._resolve_path_conflict(
                            sourcePath.name, destinationParent)
                        if newPath is None:
                            return QModelIndex()
                        destPath = newPath
                        virtualDestPath = destPath.relative_to(
                            destArchivePath)

                # TODO: Merge directories rather than remove and replace
                self._skipRecache = True
                self.beginMoveRows(
                    sourceParent, sourceRow, sourceRow, destinationParent, i)

                if conflictAction == FileConflictAction.REPLACE:
                    if os.path.isdir(destPath):
                        shutil.rmtree(destPath)
                    elif pathExists:
                        os.remove(destPath)
                shutil.move(sourcePath, destPath)

                sourceHandleInfo.reparent(destParentInfo, i)
                self.endMoveRows()

                return self.index(i, 0, destinationParent)

        return QModelIndex()

    def rename(self, index: QModelIndex | QPersistentModelIndex, name: str, action: FileConflictAction | None = None) -> QModelIndex:
        with QReadLocker(self._fsLock):
            if not index.isValid() or name == "":
                return QModelIndex()

            handleInfo: JSystemFSModel._HandleInfo = index.internalPointer()
            parentInfo = handleInfo.parent

            if parentInfo is None:
                return QModelIndex()

        pIndex = QPersistentModelIndex(index)

        if action:
            self.set_conflict_action(action)

        thisPath = self.get_path(pIndex)
        destPath = thisPath.with_name(name)
        if str(thisPath) == str(destPath):  # Paths are the same (identity rename)
            return QModelIndex(pIndex)

        caseRename = thisPath == destPath  # Case insensitive match

        archiveIndex = self.get_parent_archive(index)
        if archiveIndex.isValid():
            archivePath = self.get_path(archiveIndex)
            archive = self._archives[archivePath]

            virtualPath = thisPath.relative_to(archivePath)
            handle = archive.get_handle(virtualPath)
            if handle is None:
                return QModelIndex()

            if action == FileConflictAction.SKIP:
                return QModelIndex()

            elif action == FileConflictAction.KEEP:
                newPath = self._resolve_path_conflict(
                    destPath.name, index.parent()
                )
                if newPath is None:
                    return QModelIndex()
                destPath = newPath

            with QWriteLocker(self._fsLock):
                successful = handle.rename(
                    name, action=FileConflictAction.REPLACE)
                if not successful:
                    return QModelIndex()

                handleInfo.path = handleInfo.path.with_name(
                    handle.get_name())

            self._sort_and_update_indexes(parentInfo)
            self._apply_rarc_updates(archiveIndex)
            return QModelIndex(pIndex)

        if os.path.exists(destPath) and not caseRename:
            destIsDir = os.path.isdir(destPath)

            if action is None:
                action = self._capture_conflict_resolution(
                    thisPath, destPath, destIsDir
                )

            if action == FileConflictAction.SKIP:
                return QModelIndex()

            if destIsDir:
                if action == FileConflictAction.REPLACE:
                    shutil.rmtree(destPath)

                elif action == FileConflictAction.KEEP:
                    newPath = self._resolve_path_conflict(name, index.parent())
                    if newPath is None:
                        return QModelIndex()
                    destPath = newPath
            else:
                if action == FileConflictAction.REPLACE:
                    os.remove(destPath)

                elif action == FileConflictAction.KEEP:
                    newPath = self._resolve_path_conflict(name, index.parent())
                    if newPath is None:
                        return QModelIndex()
                    destPath = newPath

        os.rename(thisPath, destPath)
        handleInfo.path = handleInfo.path.with_name(name)

        self._sort_and_update_indexes(parentInfo)
        return QModelIndex(pIndex)

    def remove(self, index: QModelIndex | QPersistentModelIndex) -> bool:
        with QReadLocker(self._fsLock):
            parent = index.parent()
            if not parent.isValid():
                return False

            path = self.get_path(index)

        if os.path.isdir(path):
            shutil.rmtree(path)
            return True

        if os.path.exists(path):
            os.remove(path)
            return True

        with QReadLocker(self._fsLock):
            archiveIndex = QPersistentModelIndex(
                self.get_parent_archive(index))
            if not archiveIndex.isValid():
                return False

            archivePath = self.get_path(archiveIndex)
            archive = self._archives[archivePath]

            if not archive.path_exists(path):
                return False

        archive.remove_path(path)
        return True

    def import_paths(self, data: QMimeData, destinationParent: QModelIndex | QPersistentModelIndex, action: FileConflictAction | None = None) -> bool:
        if not destinationParent.isValid():
            return False

        dropEffect = data.data("Preferred DropEffect")
        dropEffectStream = QDataStream(dropEffect, QIODevice.ReadOnly)
        dropEffectStream.setByteOrder(QDataStream.LittleEndian)
        isCutAction = dropEffectStream.readInt32() == 2

        successful = True

        if data.hasFormat(JSystemFSModel.ArchiveMimeType):
            importData = data.data(JSystemFSModel.ArchiveMimeType)
            completeStream = QDataStream(importData, QDataStream.ReadOnly)

            pathCount = completeStream.readInt32()

            byteData = QByteArray()
            completeStream >> byteData
            dataStream = QDataStream(byteData, QDataStream.ReadOnly)

            for _ in range(pathCount):
                successful &= self._import_virtual_path(
                    dataStream, destinationParent, action)

        if data.hasUrls():  # We can save on resources here because the path exists on the filesystem
            for url in data.urls():
                successful &= self._import_fs_path(
                    Path(url.toLocalFile()), destinationParent, action, cutSource=isCutAction)

        self.set_conflict_action(None)
        return successful

    def export_paths(self, data: QMimeData, pathIndexes: list[QModelIndex | QPersistentModelIndex]) -> bool:
        successful = True

        length = 0
        for pathIndex in pathIndexes:
            if not pathIndex.isValid():
                print("WARNING: Invalid index found when exporting")
                continue

            byteData = QByteArray()
            dataStream = QDataStream(byteData, QIODevice.WriteOnly)

            parentArchiveIndex = self.get_parent_archive(pathIndex)

            isVirtual = parentArchiveIndex.isValid()

            if isVirtual:  # Within an archive
                serialSuccessful = self._export_virtual_path(
                    dataStream, pathIndex, parentArchiveIndex)

                if serialSuccessful:
                    length += 1
                else:
                    successful = False
            else:
                path = self.get_path(pathIndex)
                data.setUrls([*data.urls(), QUrl.fromLocalFile(path)])

        if length > 0:
            completeData = QByteArray()
            completeStream = QDataStream(completeData, QIODevice.WriteOnly)

            completeStream.writeInt32(length)
            completeStream << byteData

            data.setData(JSystemFSModel.ArchiveMimeType, completeData)

        return successful

    def mkfile(self, name: str, initialData: bytes | bytearray, parent: QModelIndex | QPersistentModelIndex) -> QModelIndex:
        with QWriteLocker(self._fsLock):
            if not parent.isValid():
                return QModelIndex()

            parentPath = self.get_path(parent)
            parentInfo: JSystemFSModel._HandleInfo = parent.internalPointer()

            row = len(parentInfo.children)
            column = 0

            if not os.path.isdir(parentPath):
                return QModelIndex()

            if self.is_archive(parent):
                archive = self._archives[parentPath]
                fileHandle = archive.new_file(name, initialData)
                if fileHandle is None:
                    return QModelIndex()

            elif self.is_child_of_archive(parent):
                archiveIndex = self.get_parent_archive(parent)
                if not archiveIndex.isValid():
                    return QModelIndex()

                archivePath = self.get_path(archiveIndex)
                archive = self._archives[archivePath]

                virtualPath = parentPath.relative_to(archivePath)
                parentHandle = archive.get_handle(virtualPath)
                if parentHandle is None:
                    return QModelIndex()

                fileHandle = parentHandle.new_file(name, initialData)
                if fileHandle is None:
                    return QModelIndex()

            else:  # File
                with open(parentPath / name, "wb") as f:
                    f.write(initialData)

            handleInfo = JSystemFSModel._HandleInfo(
                row=row,
                path=parentPath / name,
                parent=parentInfo,
                children=[],
                fsKind=JSystemFSModel._FsKind.FILE,
                size=len(initialData)
            )

            parentInfo.children.append(handleInfo)
            parentInfo.children.sort()

            return self.createIndex(row, column, handleInfo)

    def mkdir(self, name: str, parent: QModelIndex | QPersistentModelIndex) -> QModelIndex:
        if not parent.isValid():
            return QModelIndex()

        parentPath = self.get_path(parent)
        thisPath = parentPath / name

        archiveIndex = self.get_parent_archive(parent)
        # Virtual FS
        if archiveIndex.isValid():
            archivePath = self.get_path(archiveIndex)
            with QWriteLocker(self._fsLock):
                archive = self._archives[archivePath]

                virtualPath = parentPath.relative_to(archivePath)
                parentHandle = archive.get_handle(virtualPath)
                if parentHandle is None:
                    return QModelIndex()

                dirHandle = parentHandle.new_directory(name)
                if dirHandle is None:
                    return QModelIndex()

                parentInfo: JSystemFSModel._HandleInfo = parent.internalPointer()
                handleInfo = JSystemFSModel._HandleInfo(
                    row=-1,
                    path=parentPath / name,
                    parent=parentInfo,
                    children=[],
                    fsKind=JSystemFSModel._FsKind.DIRECTORY,
                    size=0,
                    archive=archiveIndex
                )

            # Manual sorted insertion to maintain persistent indexes and do correct signals
            row = 0
            with QReadLocker(self._fsLock):
                for child in parentInfo.children:
                    if not child < handleInfo:
                        break
                    row += 1

            self.beginInsertRows(parent, row, row)
            with QWriteLocker(self._fsLock):
                handleInfo.row = row
                parentInfo.children.insert(row, handleInfo)
                for i, child in enumerate(parentInfo.children[row:]):
                    child.row = row + i
            self.endInsertRows()

            return self.createIndex(row, 0, handleInfo)

        # Physical FS
        if os.path.isdir(parentPath):
            if os.path.exists(thisPath):
                return QModelIndex()

            with QWriteLocker(self._fsLock):
                self._skipRecache = True
                os.mkdir(thisPath)

                parentInfo: JSystemFSModel._HandleInfo = parent.internalPointer()
                handleInfo = JSystemFSModel._HandleInfo(
                    row=-1,
                    path=parentPath / name,
                    parent=parentInfo,
                    children=[],
                    fsKind=JSystemFSModel._FsKind.DIRECTORY,
                    size=0,
                    archive=archiveIndex
                )

            # Manual sorted insertion to maintain persistent indexes and do correct signals
            row = 0
            with QReadLocker(self._fsLock):
                for child in parentInfo.children:
                    if not child < handleInfo:
                        break
                    row += 1

            self.beginInsertRows(parent, row, row)
            with QWriteLocker(self._fsLock):
                parentInfo.children.insert(row, handleInfo)
                for i, child in enumerate(parentInfo.children[row:]):
                    child.row = row + i
            self.endInsertRows()

            return self.createIndex(row, 0, handleInfo)

        return QModelIndex()

    def rmdir(self, index: QModelIndex | QPersistentModelIndex) -> bool:
        if not index.isValid():
            return False

        parentIndex = index.parent()

        path = self.get_path(index)
        if os.path.isdir(path):
            self.beginRemoveRows(parentIndex, index.row(), index.row())
            self._skipRecache = True
            shutil.rmtree(path)
            self.endRemoveRows()
            return True

        if os.path.exists(path):
            return False

        archiveIndex = self.get_parent_archive(index)
        if not archiveIndex.isValid():
            return False

        archivePath = self.get_path(archiveIndex)
        archive = self._archives[archivePath]

        self.beginRemoveRows(parentIndex, index.row(), index.row())
        pathRemoved = archive.remove_path(path)
        self.endRemoveRows()

        return pathRemoved

    def flags(self, index: QModelIndex | QPersistentModelIndex) -> Qt.ItemFlags:
        with QReadLocker(self._fsLock):
            if not index.isValid():
                return Qt.ItemIsDropEnabled
            itemFlags = Qt.ItemIsDragEnabled | Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable
            if self.is_dir(index):
                itemFlags |= Qt.ItemIsDragEnabled
            return itemFlags

    def data(self, index: QModelIndex | QPersistentModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return -1

        with QReadLocker(self._fsLock):
            handleInfo: JSystemFSModel._HandleInfo = index.internalPointer()

            if role == self.FileNameRole:
                return handleInfo.path.stem

            if role == self.FilePathRole:
                return handleInfo.path

            if role == Qt.DisplayRole:
                return handleInfo.path.name

            if role == Qt.SizeHintRole:
                return QSize(80, 20)

            if role == Qt.DecorationRole:
                if handleInfo.icon is None:
                    extension = handleInfo.path.suffix
                    if handleInfo.fsKind == JSystemFSModel._FsKind.DIRECTORY:
                        handleInfo.icon = self._icons["folder"]
                    elif extension in self._icons:
                        handleInfo.icon = self._icons[extension]
                    else:
                        handleInfo.icon = self._icons["file"]
                return handleInfo.icon

            if role == Qt.EditRole:
                return handleInfo.path.name

            if role == Qt.ToolTipRole:
                extension = handleInfo.path.suffix
                if handleInfo.fsKind == JSystemFSModel._FsKind.DIRECTORY:
                    return "Folder"
                if extension in self.ExtensionToTypeMap:
                    return self.ExtensionToTypeMap[extension]
                return "UNKNOWN"

            if role == Qt.WhatsThisRole:
                extension = handleInfo.path.suffix
                if handleInfo.fsKind == JSystemFSModel._FsKind.DIRECTORY:
                    return "Folder"
                if extension in self.ExtensionToTypeMap:
                    return self.ExtensionToTypeMap[extension]
                return "UNKNOWN"

    def setData(self, index: QModelIndex | QPersistentModelIndex, value: Any, role: int = Qt.DisplayRole) -> bool:
        if not index.isValid():
            return False

        changed = False
        if role == Qt.DisplayRole:
            changed = self.rename(index, value)

        if role == Qt.EditRole:
            changed = self.rename(index, value)

        if role == self.FileNameRole:
            changed = self.rename(index, value)

        if role == self.FilePathRole:
            changed = self.rename(index, value)

        if changed:
            with QWriteLocker(self._fsLock):
                handleInfo: JSystemFSModel._HandleInfo = index.internalPointer()
                handleInfo.icon = None
            return True

        return False

    def canFetchMore(self, parent: QModelIndex | QPersistentModelIndex) -> bool:
        if not parent.isValid():
            return False

        with QReadLocker(self._fsLock):
            handleInfo: JSystemFSModel._HandleInfo = parent.internalPointer()
            return handleInfo.loaded is False

    def fetchMore(self, parent: QModelIndex | QPersistentModelIndex) -> None:
        if not self._rootPathExists:
            return

        self.cache_index(parent)

    def hasChildren(self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> bool:
        if not parent.isValid():
            return True

        return self.is_populated(parent)

    def hasIndex(self, row: int, column: int, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> bool:
        return self.index(row, column, parent).isValid()

    def index(self, row: int, column: int, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> QModelIndex:
        if not self._rootPathExists:
            return QModelIndex()

        if self._fileSystemCache is None:
            return QModelIndex()

        if row < 0 or column != 0:
            return QModelIndex()

        with QReadLocker(self._fsLock):
            if not parent.isValid():
                return self.createIndex(row, column, self._fileSystemCache)

            if not self.hasChildren(parent):
                return QModelIndex()

            handleInfo: JSystemFSModel._HandleInfo = parent.internalPointer()  # type: ignore
            if row >= len(handleInfo.children):
                return QModelIndex()
            return self.createIndex(row, column, handleInfo.children[row])

    @overload
    def parent(self) -> QObject: ...

    @overload
    def parent(self, child: QModelIndex | QPersistentModelIndex): ...

    def parent(self, child: QModelIndex | QPersistentModelIndex | None = None) -> QModelIndex:  # type: ignore
        if child is None:
            return super().parent()

        if not self._rootPathExists:
            return QModelIndex()

        if self._fileSystemCache is None:
            return QModelIndex()

        with QReadLocker(self._fsLock):
            if not child.isValid():
                return QModelIndex()

            handleInfo: JSystemFSModel._HandleInfo = child.internalPointer()

            parentInfo = handleInfo.parent
            if parentInfo is None:
                return QModelIndex()  # Already top level

            pParentInfo = parentInfo.parent
            if pParentInfo is None:
                return self.createIndex(0, 0, self._fileSystemCache)  # Root

            return self.createIndex(parentInfo.row, 0, parentInfo)

    def mimeData(self, indexes: list[QModelIndex | QPersistentModelIndex]) -> QMimeData:
        urls: list[QUrl] = []
        with QReadLocker(self._fsLock):
            for index in indexes:
                urls.append(
                    QUrl(
                        str(self.get_path(index))
                    )
                )
        mimeData = QMimeData()
        mimeData.setUrls(urls)
        return mimeData

    def dropMimeData(self, data: QMimeData, action: Qt.DropAction, row: int, column: int, parent: QModelIndex | QPersistentModelIndex) -> bool:
        folder = self.get_path(parent)
        for url in data.urls():
            urlPath = PurePath(url.toLocalFile())
            dstPath = folder / urlPath.name
            if os.path.exists(dstPath):
                continue
            os.rename(urlPath, dstPath)
        return True

    def canDropMimeData(self, data: QMimeData, action: Qt.DropAction, row: int, column: int, parent: QModelIndex | QPersistentModelIndex) -> bool:
        if not data.hasUrls() and not data.hasFormat(JSystemFSModel.ArchiveMimeType):
            return False

        targetIndex = self.index(row, column, parent)
        if not targetIndex.isValid():  # Dropping in parent index?
            return False

        # Should only allow drops when it is a directory (or archive)
        return self.is_dir(targetIndex) or self.is_archive(targetIndex)

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> int:
        if not self._rootPathExists:
            return 0

        if self._fileSystemCache is None:
            return 0

        if not parent.isValid():
            return 1

        with QReadLocker(self._fsLock):
            handleInfo: JSystemFSModel._HandleInfo = parent.internalPointer()
            return len(handleInfo.children)

    def columnCount(self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> int:
        return 1

    def supportedDragActions(self) -> Qt.DropActions:
        return Qt.MoveAction

    def supportedDropActions(self) -> Qt.DropActions:
        return Qt.MoveAction | Qt.CopyAction

    @Slot()
    def reset_cache(self) -> bool:
        if not self._rootPathExists:
            return False

        self.cache_index(self.index(0, 0))
        return True

    @Slot(str)
    def file_changed(self, path: str) -> None:
        if path not in self._fileSystemWatcher.files():
            self._fileSystemWatcher.addPath(path)

        if self._skipRecache:
            self._skipRecache = False
            return

        index = QPersistentModelIndex(self.get_path_index(PurePath(path)))

        with QWriteLocker(self._fsLock):
            handleInfo: JSystemFSModel._HandleInfo = index.internalPointer()
            handleInfo.path = PurePath(path)

        self._indexesToRecache.add(index)

        self._cacheTimer = QTimer()
        self._cacheTimer.timeout.connect(self._recache_indexes)
        self._cacheTimer.setSingleShot(True)
        self._cacheTimer.start(100)  # Reset timer

    @Slot(str)
    def directory_changed(self, path: str) -> None:
        if path not in self._fileSystemWatcher.directories():
            self._fileSystemWatcher.addPath(path)

        if self._skipRecache:
            self._skipRecache = False
            return

        index = QPersistentModelIndex(self.get_path_index(PurePath(path)))

        with QWriteLocker(self._fsLock):
            handleInfo: JSystemFSModel._HandleInfo = index.internalPointer()
            handleInfo.path = PurePath(path)

        self._indexesToRecache.add(index)

        self._cacheTimer = QTimer()
        self._cacheTimer.timeout.connect(self._recache_indexes)
        self._cacheTimer.setSingleShot(True)
        self._cacheTimer.start(100)  # Reset timer

    def _apply_rarc_updates(self, archiveIndex: QModelIndex | QPersistentModelIndex) -> None:
        if not self.is_archive(archiveIndex):  # Abort early, not an archive
            return

        thisArchiveIndex = archiveIndex
        thisArchivePath = self.get_path(thisArchiveIndex)
        thisArchive = self._archives[thisArchivePath]

        while True:
            parentArchiveIndex = self.get_parent_archive(thisArchiveIndex)
            if not parentArchiveIndex.isValid():
                break

            parentArchivePath = self.get_path(parentArchiveIndex)
            parentArchive = self._archives[parentArchivePath]

            virtualThisPath = thisArchivePath.relative_to(parentArchivePath)
            thisArchiveHandle: ResourceFile | None = parentArchive.get_handle(
                virtualThisPath)
            if thisArchiveHandle is None or not thisArchiveHandle.is_file():
                print("Archive doesn't have a file handle owned by another archive")
                continue

            thisArchiveHandle = ResourceFile(
                virtualThisPath.name,
                thisArchive.get_data()
            )

            parentHandle: A_ResourceHandle | None
            if len(virtualThisPath.parts) == 1:
                parentHandle = parentArchive
            else:
                parentHandle = parentArchive.get_handle(virtualThisPath)
                if parentHandle is None:
                    raise RuntimeError(
                        "Failed to track the parent handle during FS update")

            # We update the raw data of the archive handle
            parentHandle.add_handle(
                thisArchiveHandle, action=FileConflictAction.REPLACE)

            thisArchiveIndex = parentArchiveIndex
            thisArchivePath = parentArchivePath
            thisArchive = parentArchive

        # Simple function to run on thread
        def _update_f() -> None:
            with open(thisArchivePath, "wb") as f:
                f.write(thisArchive.to_bytes())

        # At this point we have the topmost archive which is guaranteed to be physical
        # By writing the topmost archive to the file, we update the FS and recache
        t = threading.Thread(target=_update_f)
        t.start()

    def _sort_and_update_indexes(self, infoToSort: _HandleInfo) -> bool:
        # Update each persistent index
        infoToSort.children.sort()
        for i, childInfo in enumerate(infoToSort.children):
            childInfo.row = i

        changed = False

        for pIndex in self.persistentIndexList():
            if not pIndex.isValid():
                continue

            pHandleInfo: JSystemFSModel._HandleInfo = pIndex.internalPointer()
            if str(pHandleInfo.path.parent) != str(infoToSort.path):
                continue

            for childInfo in infoToSort.children:
                if childInfo.path.name == pHandleInfo.path.name:
                    changed |= pIndex.row() != childInfo.row
                    self.changePersistentIndex(
                        pIndex,
                        self.createIndex(i, 0, childInfo)
                    )
                    break
            else:  # No entry matched, assume deleted
                changed = True
                self.changePersistentIndex(
                    pIndex,
                    QModelIndex()
                )

        return changed

    def _recache_indexes(self) -> None:
        # self.layoutAboutToBeChanged.emit()
        for index in self._indexesToRecache:
            with QWriteLocker(self._fsLock):
                handleInfo: JSystemFSModel._HandleInfo = index.internalPointer()
                handleInfo.loaded = False  # Mark dirty
            self.cache_index(index)
        self.layoutChanged.emit()

    def cache_index(self, index: QModelIndex | QPersistentModelIndex) -> None:
        if not self.canFetchMore(index):
            return

        # We update the file system watcher to check this path
        basePath = self.get_path(index)
        if basePath not in self._fileSystemWatcher.files() and basePath not in self._fileSystemWatcher.directories():
            self._fileSystemWatcher.addPath(str(basePath))

        # We always assume the index exists on the real filesystem because
        # virtual filesystem indexes (archive handles) get a complete
        # recursive caching rather than a lazy approach

        if basePath.suffix == ".arc":
            # Treat as archive
            self._cache_archive(index)
        elif not os.path.isdir(basePath):
            # Treat as file
            with QWriteLocker(self._fsLock):
                handleInfo: JSystemFSModel._HandleInfo = index.internalPointer()
                handleInfo.fsKind = JSystemFSModel._FsKind.FILE
                handleInfo.size = os.stat(basePath).st_size
                handleInfo.loaded = True
            return
        else:
            # Treat as directory
            self._cache_directory(index)

    def _cache_directory(self, index: QModelIndex | QPersistentModelIndex) -> None:
        if not index.isValid():
            return

        # Go ahead and let views know we are caching a folder
        # self.layoutAboutToBeChanged.emit()

        with QWriteLocker(self._fsLock):
            handleInfo: JSystemFSModel._HandleInfo = index.internalPointer()
            handleMap: dict[str, JSystemFSModel._HandleInfo] = {
                info.path.name: info for info in handleInfo.children}
            handleInfo.children.clear()
            handleInfo.size = 0

            basePath = handleInfo.path

            # Treat as dir
            for subEntry in os.listdir(basePath):
                subPath = basePath / subEntry

                # Check for parent archive
                if handleInfo.archive is None:
                    archiveIndex = None
                elif handleInfo.fsKind == JSystemFSModel._FsKind.ARCHIVE:
                    archiveIndex = index
                else:
                    archiveIndex = QModelIndex(handleInfo.archive)

                if subEntry in handleMap:
                    childInfo = handleMap[subEntry]
                elif os.path.isdir(subPath):  # Pre-cache as dir
                    # Check for subdirectories (used for smart listing)
                    hasSubDir = False
                    for subSubEntry in os.listdir(subPath):
                        if os.path.isdir(subSubEntry) or subSubEntry.endswith(".arc"):
                            hasSubDir = True
                            break

                    # Create cache
                    childInfo = JSystemFSModel._HandleInfo(
                        row=handleInfo.size,
                        path=subPath,
                        parent=handleInfo,
                        children=[],
                        fsKind=JSystemFSModel._FsKind.DIRECTORY,
                        size=0,
                        loaded=False,
                        hasSubDir=hasSubDir,
                        archive=archiveIndex
                    )
                elif subEntry.endswith(".arc"):
                    with open(subPath, "rb") as rs:
                        hasSubDir = ResourceArchive.get_directory_count(rs) > 1

                    # Create cache
                    childInfo = JSystemFSModel._HandleInfo(
                        row=handleInfo.size,
                        path=subPath,
                        parent=handleInfo,
                        children=[],
                        fsKind=JSystemFSModel._FsKind.ARCHIVE,
                        size=0,
                        loaded=False,
                        hasSubDir=hasSubDir,
                        archive=archiveIndex
                    )
                else:
                    # Create cache
                    childInfo = JSystemFSModel._HandleInfo(
                        row=handleInfo.size,
                        path=subPath,
                        parent=handleInfo,
                        children=[],
                        fsKind=JSystemFSModel._FsKind.FILE,
                        size=0,
                        loaded=False,
                        hasSubDir=False,
                        archive=archiveIndex
                    )

                handleInfo.children.append(childInfo)
                handleInfo.size += 1

            # Sort the entries by directory, then archive, then file, in alphabetical order
            handleInfo.loaded = True

        self._sort_and_update_indexes(handleInfo)

    def _cache_archive(self, index: QModelIndex | QPersistentModelIndex) -> None:

        def _recursive_cache(handle: A_ResourceHandle, archivePath: PurePath, subHandleInfo: "JSystemFSModel._HandleInfo") -> None:
            subHandleMap: dict[str, JSystemFSModel._HandleInfo] = {
                info.path.name: info for info in subHandleInfo.children}
            subHandleInfo.children.clear()
            subHandleInfo.size = 0

            for i, p in enumerate(handle.get_handles()):
                if p.get_name() in subHandleMap:
                    childHandleInfo = subHandleMap[p.get_name()]
                elif p.is_file():
                    if p.get_extension() == ".arc":
                        fsKind = JSystemFSModel._FsKind.ARCHIVE
                    else:
                        fsKind = JSystemFSModel._FsKind.FILE

                    childHandleInfo = JSystemFSModel._HandleInfo(
                        row=subHandleInfo.size,
                        path=archivePath / p.get_path(),
                        parent=subHandleInfo,
                        children=[],
                        fsKind=fsKind,
                        size=p.get_size()
                    )
                else:
                    childHandleInfo = JSystemFSModel._HandleInfo(
                        row=subHandleInfo.size,
                        path=archivePath / p.get_path(),
                        parent=subHandleInfo,
                        children=[],
                        fsKind=JSystemFSModel._FsKind.DIRECTORY,
                        size=p.get_size()
                    )
                subHandleInfo.children.append(childHandleInfo)
                subHandleInfo.hasSubDir = True
                _recursive_cache(p, archivePath, childHandleInfo)
                subHandleInfo.size = i

            subHandleInfo.loaded = True
            self._sort_and_update_indexes(subHandleInfo)

        if not index.isValid():
            return

        # Go ahead and let views know we are caching a folder
        # self.layoutAboutToBeChanged.emit()

        basePath = self.get_path(index)

        if self.is_child_of_archive(index):
            parentArchiveIndex = self.get_parent_archive(index)
            parentArchivePath = self.get_path(parentArchiveIndex)
            parentArchive = self._archives[parentArchivePath]

            if not basePath.is_relative_to(parentArchivePath):
                return

            virtualPath = basePath.relative_to(parentArchivePath)
            handle = parentArchive.get_handle(virtualPath)
            if handle is None:
                return

            archive = ResourceArchive.from_bytes(
                BytesIO(handle.get_data())
            )
        else:
            with open(basePath, "rb") as f:
                archive = ResourceArchive.from_bytes(f)

        if archive is None:
            return

        with QWriteLocker(self._fsLock):
            handleInfo: JSystemFSModel._HandleInfo = index.internalPointer()
            self._archives[basePath] = archive
            _recursive_cache(archive, basePath, handleInfo)

    def _initialize_icons(self):
        for extension in self.ExtensionToTypeMap:
            icon = get_icon(extension.lstrip(".") + ".png")
            if icon is None:
                continue
            self._icons[extension] = icon
        self._icons["file"] = get_icon("generic_file.png")
        self._icons["folder"] = get_icon("generic_folder.png")

    def _resolve_path_conflict(self, name: str, parent: QModelIndex | QPersistentModelIndex) -> PurePath | None:
        if not parent.isValid():
            return None

        with QReadLocker(self._fsLock):
            handleInfo: JSystemFSModel._HandleInfo = parent.internalPointer()
            if len(handleInfo.children) == 0:
                return handleInfo.path / name

            parts = name.rsplit(".", 1)
            copyName = f"{parts[0]} - Copy"

            renameContext = 1
            ogName = copyName

            possibleNames = []
            for subHandleInfo in handleInfo.children:
                subName = subHandleInfo.path.name
                if renameContext > 100:
                    raise FileExistsError(
                        "Name exists beyond 100 unique iterations!")
                if subName.startswith(name):
                    possibleNames.append(subName.rsplit(".", 1)[0])

            if len(possibleNames) == 0:
                return handleInfo.path / name

            i = 0
            while True:
                if i >= len(possibleNames):
                    break
                if renameContext > 100:
                    raise FileExistsError(
                        "Name exists beyond 100 unique iterations!")
                if possibleNames[i] == copyName:
                    copyName = f"{ogName} ({renameContext})"
                    renameContext += 1
                    i = 0
                else:
                    i += 1
            if len(parts) == 2:
                copyName += f".{parts[1]}"
            return handleInfo.path / copyName

    def _import_fs_path(
        self,
        thisPath: Path,
        destinationParent: QModelIndex | QPersistentModelIndex,
        action: FileConflictAction | None = None,
        cutSource: bool = False
    ) -> bool:
        with QReadLocker(self._fsLock):
            destFolder = self.get_path(destinationParent)
            destParentInfo: JSystemFSModel._HandleInfo = destinationParent.internalPointer()  # type: ignore
            destPath = destFolder / thisPath.name

        if destPath == thisPath:
            newPath = self._resolve_path_conflict(
                destPath.name, destinationParent
            )
            if newPath is None:
                return False
            destPath = newPath

        elif destPath.is_relative_to(thisPath):
            print("Source can't be parent of dest")
            return False

        if action:
            self.set_conflict_action(action)

        if thisPath.is_dir():
            destIndex = self.get_path_index(destPath)
            if destIndex.isValid():  # Conflict found
                action = self._capture_conflict_resolution(
                    thisPath, destPath, os.path.isdir(destPath)
                )

                if action == FileConflictAction.SKIP:
                    return False

                elif action == FileConflictAction.KEEP:
                    newPath = self._resolve_path_conflict(
                        thisPath.name, destinationParent
                    )
                    if newPath is None:
                        return False
                    destPath = newPath

            subDir = self.mkdir(destPath.name, destinationParent)

            successful = True
            for subPath in thisPath.iterdir():
                successful &= self._import_fs_path(
                    subPath, subDir, action, cutSource)
            return successful

        # Check if the destination is part of an archive
        destArchive: Optional[ResourceArchive] = None
        destArchiveIndex = self.get_parent_archive(destinationParent)

        # Source exists in filesystem
        if destArchiveIndex.isValid():  # Destination exists in an archive
            destArchivePath = self.get_path(destArchiveIndex)
            destArchive = self._archives[destArchivePath]
            virtualDestPath = destFolder.relative_to(destArchivePath)
            destHandle = destArchive.get_handle(virtualDestPath)
            if destHandle:  # Destination move exists
                self.conflictFound.emit(
                    thisPath, destFolder, destHandle.is_directory())
                while (action := self.get_conflict_action()) is None:
                    time.sleep(0.1)

                if action == FileConflictAction.REPLACE:
                    for i, handleInfo in enumerate(destParentInfo.children):
                        if handleInfo.path.name == destHandle.get_name():
                            self.removeRow(i, destinationParent)
                            break

                elif action == FileConflictAction.KEEP:
                    newPath = self._resolve_path_conflict(
                        thisPath.name, destinationParent)
                    if newPath is None:
                        return False
                    destPath = newPath
                    virtualDestPath = destPath.relative_to(destArchivePath)

                else:  # Skip
                    return True

            # Move from filesystem to archive
            if (isSrcDir := os.path.isdir(thisPath)):
                sourceHandle = ResourceDirectory.import_from(
                    Path(thisPath))
            else:
                sourceHandle = ResourceFile.import_from(Path(thisPath))

            if sourceHandle is None:
                return False

            destParentHandle = destArchive.get_handle(
                virtualDestPath.parent)
            if destParentHandle is None:
                destParentHandle = destArchive

            if not destParentHandle.add_handle(sourceHandle, action=FileConflictAction.REPLACE):
                return False

            if not cutSource:
                return True

            # Remove old path
            if isSrcDir:
                shutil.rmtree(thisPath)
            else:
                os.remove(thisPath)

            return True

        # Filesystem to filesystem
        if os.path.exists(destPath):
            self.conflictFound.emit(
                thisPath, destPath, os.path.isdir(thisPath))
            while (action := self.get_conflict_action()) is None:
                time.sleep(0.1)

            if action == FileConflictAction.REPLACE:
                for i, handleInfo in enumerate(destParentInfo.children):
                    if handleInfo.path.name == destPath.name:
                        self.removeRow(i, destinationParent)
                        break

            elif action == FileConflictAction.KEEP:
                newPath = self._resolve_path_conflict(
                    thisPath.name, destinationParent)
                if newPath is None:
                    return False
                destPath = newPath

            else:  # Skip
                return True

        if cutSource:
            shutil.move(thisPath, destPath)
        else:
            shutil.copy(thisPath, destPath)

        return True

    def _import_virtual_path(
        self,
        inputStream: QDataStream,
        destinationParent: QModelIndex | QPersistentModelIndex,
        action: FileConflictAction | None = None
    ) -> bool:
        """
        This function handles importing filesystem nodes from
        an archive or archive subdirectory to the real filesystem
        """
        thisPath = Path(inputStream.readString())
        thisName = thisPath.name

        with QReadLocker(self._fsLock):
            destParentInfo: JSystemFSModel._HandleInfo = destinationParent.internalPointer()  # type: ignore
            destFolder = self.get_path(destinationParent)
            destPath = destFolder / thisName

        handleType = JSystemFSModel._FsKind(inputStream.readInt8())

        if action:
            self.set_conflict_action(action)

        if self.is_archive(destinationParent):
            destArchiveIndex = destinationParent
        else:
            destArchiveIndex = QPersistentModelIndex(
                self.get_parent_archive(destinationParent))

        if not destArchiveIndex.isValid():  # To filesystem
            # If a file, we simply copy the data to a file of the same name in this dir
            if handleType == JSystemFSModel._FsKind.FILE:
                fileData = QByteArray()
                inputStream >> fileData

                with open(destPath, "wb") as f:
                    f.write(fileData.data())

                return True

            # If a dir, we create a sub dir of this name and iterate over the next items within this dir
            elif handleType == JSystemFSModel._FsKind.DIRECTORY:
                childrenCount = inputStream.readUInt32()

                folderIndex = QPersistentModelIndex(
                    self.mkdir(thisPath.name, destinationParent))

                successful = True
                for _ in range(childrenCount):
                    successful &= self._import_virtual_path(
                        inputStream, folderIndex, action)

                return successful

            # If an archive, we can create the archive in the cache and import future items into it
            # TODO: For now we simply copy an unextracted form of the archive
            elif handleType == JSystemFSModel._FsKind.ARCHIVE:
                fileData = QByteArray()
                inputStream >> fileData

                with open(destPath, "wb") as f:
                    f.write(fileData.data())

                # self._archives[destPath] = ResourceArchive.from_bytes(fileData.data())
                return True

            raise ValueError(
                f"Encountered invalid type ID ({handleType}) while deserializing archive info")

        with QReadLocker(self._fsLock):
            destArchivePath = self.get_path(destArchiveIndex)
            destArchive = self._archives[destArchivePath]

        virtualPath = destPath.relative_to(destArchivePath)
        destHandle = destArchive.get_handle(virtualPath)
        if destHandle:
            action = self._capture_conflict_resolution(
                thisPath, destPath, destHandle.is_directory()
            )

            if action == FileConflictAction.SKIP:
                return False

            elif action == FileConflictAction.KEEP:
                newPath = self._resolve_path_conflict(
                    thisPath.name, destinationParent)
                if newPath is None:
                    return False
                destPath = newPath
                virtualPath = destPath.relative_to(destArchivePath)

        destParentHandle: A_ResourceHandle | None
        if len(virtualPath.parts) == 1:
            destParentHandle = destArchive
        else:
            destParentHandle = destArchive.get_handle(
                virtualPath.parent)
            if destParentHandle is None:
                destParentHandle = destArchive

        # If a file, we simply copy the data to a file of the same name in this dir
        if handleType == JSystemFSModel._FsKind.FILE:
            fileData = QByteArray()
            inputStream >> fileData

            newHandle = ResourceFile(
                destPath.name,
                initialData=fileData.data()
            )
            destParentHandle.add_handle(
                newHandle, action=FileConflictAction.REPLACE)

            successful = True

        # If a dir, we create a sub dir of this name and iterate over the next items within this dir
        elif handleType == JSystemFSModel._FsKind.DIRECTORY:
            childrenCount = inputStream.readUInt32()

            folderIndex = self.mkdir(thisPath.name, destinationParent)

            successful = True
            for _ in range(childrenCount):
                successful &= self._import_virtual_path(
                    inputStream, folderIndex, action)

        # If an archive, we can create the archive in the cache and import future items into it
        # TODO: For now we simply copy an unextracted form of the archive
        elif handleType == JSystemFSModel._FsKind.ARCHIVE:
            fileData = QByteArray()
            inputStream >> fileData

            newHandle = ResourceFile(
                thisName,
                initialData=fileData.data()
            )
            destParentHandle.add_handle(
                newHandle, action=FileConflictAction.REPLACE)

            successful = True

        # We update the archive hierarchy now (fs update)
        self._apply_rarc_updates(destArchiveIndex)

        return successful

    def _export_fs_path(
        self,
        outputStream: QDataStream,
        srcIndex: QModelIndex | QPersistentModelIndex
    ) -> bool:
        with QReadLocker(self._fsLock):
            srcPath = Path(self.get_path(srcIndex))
            srcParentInfo: JSystemFSModel._HandleInfo = srcIndex.internalPointer()  # type: ignore

            outputStream.writeString(str(srcPath))

            if not srcPath.is_dir():
                return True

            if srcParentInfo.size > 0:  # Number of children already cached
                outputStream.writeUInt32(srcParentInfo.size)

                successful = True
                for i in range(srcParentInfo.size):
                    successful &= self._export_fs_path(
                        outputStream, self.index(i, 0, srcIndex))
                return successful
            else:
                paths = [p for p in srcPath.iterdir()]
                outputStream.writeUInt32(len(paths))

                successful = True
                for i, _ in enumerate(paths):
                    successful &= self._export_fs_path(
                        outputStream, self.index(i, 0, srcIndex))
                return successful

    def _export_virtual_path(
        self,
        outputStream: QDataStream,
        srcIndex: QModelIndex | QPersistentModelIndex,
        srcArchiveIndex: QModelIndex | QPersistentModelIndex
    ) -> bool:
        """
        This function handles exporting filesystem nodes from
        an archive or archive subdirectory to the real filesystem
        """
        with QReadLocker(self._fsLock):
            srcPath = self.get_path(srcIndex)
            srcParentInfo: JSystemFSModel._HandleInfo = srcIndex.internalPointer()  # type: ignore

            if not srcArchiveIndex.isValid():  # To filesystem
                return False

            srcArchivePath = self.get_path(srcArchiveIndex)
            srcArchive = self._archives[srcArchivePath]

            virtualPath = srcPath.relative_to(srcArchivePath)
            srcHandle = srcArchive.get_handle(virtualPath)
            if srcHandle is None:
                return False

            outputStream.writeString(str(srcPath))

            if srcHandle.is_file():
                outputStream.writeInt8(JSystemFSModel._FsKind.FILE)
                outputStream << srcHandle.get_raw_data()
                return True

            if srcHandle.is_directory():
                outputStream.writeInt8(JSystemFSModel._FsKind.DIRECTORY)
                if srcParentInfo.size > 0:  # Size is cached already
                    outputStream.writeUInt32(srcParentInfo.size)

                    successful = True
                    for i in range(srcParentInfo.size):
                        successful &= self._export_virtual_path(
                            outputStream, self.index(
                                i, 0, srcIndex), srcArchiveIndex
                        )
                    return successful
                else:
                    paths = [p for p in srcHandle.get_handles()]
                    outputStream.writeUInt32(len(paths))

                    successful = True
                    for i, _ in enumerate(paths):
                        successful &= self._export_virtual_path(
                            outputStream, self.index(
                                i, 0, srcIndex), srcArchiveIndex
                        )
                    return successful

            if srcHandle.is_archive():
                outputStream.writeInt8(JSystemFSModel._FsKind.ARCHIVE)
                outputStream << srcHandle.get_raw_data()
                return True

            raise NotImplementedError(
                "Handle encountered is not a supported handle type")

    def _capture_conflict_resolution(self, src: PurePath, dst: PurePath, isDir: bool) -> FileConflictAction:
        """
        Will hang unless a handler is connected to the `conflictFound` slot
        """
        self.conflictFound.emit(src, dst, isDir)
        while (conflictAction := self.get_conflict_action()) is None:
            time.sleep(0.1)
        return conflictAction


class JSystemFSTreeProxyModel(QSortFilterProxyModel):
    def data(self, index: QModelIndex | QPersistentModelIndex, role: int = Qt.DisplayRole) -> Any:
        if role == Qt.SizeHintRole:
            return QSize(40, 20)

        return super().data(index, role)

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex | QPersistentModelIndex) -> bool:
        sourceModel: JSystemFSModel = self.sourceModel()
        sourceIndex = sourceModel.index(source_row, 0, source_parent)
        return True

    # def hasChildren(self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> bool:
    #     if not parent.isValid():
    #         return True

    #     sourceParent = self.mapToSource(parent)
    #     sourceParentHandle: JSystemFSModel._HandleInfo = sourceParent.internalPointer()

    #     return sourceParentHandle.hasSubDir
