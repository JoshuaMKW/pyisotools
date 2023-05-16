from abc import abstractmethod
import shutil
import sys
import time
from cmath import exp
from enum import Enum, IntEnum, auto
from pathlib import Path, PurePath
from typing import Any, BinaryIO, Callable, Dict, List, Optional, Tuple, Union

from pyisotools.gui.dialogs.moveconflict import MoveConflictDialog

from pyisotools.gui.images import get_icon, get_image
from pyisotools.gui.models.rarcfs import JSystemFSTreeProxyModel, JSystemFSModel
from pyisotools.gui.tools import clear_layout, walk_layout
from pyisotools.gui.widgets.interactivestructs import InteractiveListView, InteractiveTreeView, InteractiveListWidget, InteractiveListWidgetItem, InteractiveTreeWidget
from pyisotools.utils import A_Serializable, VariadicArgs, VariadicKwargs
from pyisotools.utils.filesystem import open_path_in_explorer, open_path_in_terminal
from pyisotools.utils.initializer import FileInitializer
from PySide6.QtCore import (QAbstractItemModel, QDataStream, QEvent, QIODevice, QByteArray, QThread, QRunnable,
                            QLine, QMimeData, QModelIndex, QObject, QPoint,
                            QSize, Qt, QThread, QTimer, QUrl, Signal, QItemSelectionModel, QPersistentModelIndex,
                            SignalInstance, Slot)
from PySide6.QtGui import (QAction, QColor, QCursor, QDrag, QDragEnterEvent, QClipboard,
                           QDragLeaveEvent, QDragMoveEvent, QDropEvent, QIcon,
                           QImage, QKeyEvent, QMouseEvent, QPaintDevice, QContextMenuEvent,
                           QPainter, QPaintEvent, QPalette, QPixmap, QPen,
                           QUndoCommand, QUndoStack)
from PySide6.QtTest import QAbstractItemModelTester
from PySide6.QtWidgets import (QBoxLayout, QComboBox, QFormLayout, QFrame,
                               QGridLayout, QGroupBox, QHBoxLayout, QLabel,
                               QLayout, QLineEdit, QListView, QListWidget,
                               QListWidgetItem, QMenu, QMenuBar, QPushButton,
                               QScrollArea, QSizePolicy, QSpacerItem,
                               QSplitter, QStyle, QStyleOptionComboBox,
                               QStylePainter, QTableWidget, QTableWidgetItem,
                               QToolBar, QTreeWidget, QTreeWidgetItem, QDialog, QDialogButtonBox, QApplication, QTreeView,
                               QVBoxLayout, QWidget)


class ProjectCacheUpdater(QObject, QRunnable):
    cacheUpdated = Signal()

    def __init__(self, model: JSystemFSModel, indexToCache: QModelIndex | QPersistentModelIndex, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.model = model
        self.indexToCache = indexToCache

    def run(self) -> None:
        self.model.cache_index(self.indexToCache)


class ProjectTreeViewWidget(InteractiveTreeView):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QTreeView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setEditTriggers(QTreeView.NoEditTriggers)
        self.setContentsMargins(0, 0, 0, 0)

    def get_source_model(self) -> QAbstractItemModel:
        proxy: JSystemFSTreeProxyModel = self.model()
        return proxy.sourceModel()

    def set_source_model(self, model: QAbstractItemModel) -> None:
        proxy: JSystemFSTreeProxyModel = self.model()
        proxy.setSourceModel(model)

    def get_context_menu(self, point: QPoint) -> Optional[QMenu]:
        menu = QMenu(self)

        # Infos about the node selected.
        selectedIndex = self.indexAt(point)
        selectedIndexValid = selectedIndex.isValid()

        newFolderAction = QAction("New Folder", self)

        explorerAction = QAction("Open in Explorer", self)
        terminalAction = QAction("Open in Terminal", self)
        copyPathAction = QAction("Copy Path", self)

        if selectedIndexValid:
            cutAction = QAction("Cut", self)
            copyAction = QAction("Copy", self)
            copyRelativePathAction = QAction("Copy Relative Path", self)
            renameAction = QAction("Rename", self)
            deleteAction = QAction("Delete", self)

        menu.addAction(newFolderAction)
        menu.addAction(explorerAction)
        menu.addAction(terminalAction)
        menu.addSeparator()

        if selectedIndexValid:
            menu.addAction(cutAction)
            menu.addAction(copyAction)
            menu.addSeparator()

        menu.addAction(copyPathAction)

        if selectedIndexValid:
            menu.addAction(copyRelativePathAction)
            menu.addSeparator()
            menu.addAction(renameAction)
            menu.addAction(deleteAction)

        return menu
