from pathlib import Path
from typing import Optional
from PySide6.QtCore import QThread, QObject, Signal, Slot
from pyisotools.iso import GamecubeISO


class ISOWatcher(QObject):
    onPhysicalJobStart = Signal(str, int)
    onPhysicalTaskStart = Signal(str, int)
    onPhysicalTaskComplete = Signal()
    onPhysicalJobEnd = Signal()
    onVirtualJobStart = Signal(str, int)
    onVirtualTaskStart = Signal(str, int)
    onVirtualTaskComplete = Signal()
    onVirtualJobEnd = Signal()


class ISOBuilder(ISOWatcher):
    finished = Signal()

    def __init__(self, rootPath: Path, destPath: Path, genNewInfo: bool, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.rootPath = rootPath
        self.destPath = destPath
        self.genNewInfo = genNewInfo

    def process(self) -> None:
        iso = GamecubeISO.from_root(self.rootPath, self.genNewInfo)
        iso.onVirtualJobStart = lambda name, size: self.onVirtualJobStart.emit(
            name, size)
        iso.onVirtualTaskStart = lambda name, size: self.onVirtualTaskStart.emit(
            name, size)
        iso.onVirtualTaskComplete = lambda: self.onVirtualTaskComplete.emit()
        iso.onVirtualJobEnd = lambda: self.onVirtualJobEnd.emit()
        iso.build(self.destPath)
        self.finished.emit()


class ISOExtracter(ISOWatcher):
    finished = Signal()

    def __init__(self, isoPath: Path, destPath: Path, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.isoPath = isoPath
        self.destPath = destPath

    def process(self) -> None:
        iso = GamecubeISO.from_iso(self.isoPath)
        iso.onPhysicalJobStart = lambda name, size: self.onPhysicalJobStart.emit(
            name, size)
        iso.onPhysicalTaskStart = lambda name, size: self.onPhysicalTaskStart.emit(
            name, size)
        iso.onPhysicalTaskComplete = lambda: self.onPhysicalTaskComplete.emit()
        iso.onPhysicalJobEnd = lambda: self.onPhysicalJobEnd.emit()
        iso.extract(self.destPath)
        self.finished.emit()
