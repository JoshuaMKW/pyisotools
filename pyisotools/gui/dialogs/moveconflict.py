from pathlib import Path, PurePath
from typing import Optional, Tuple
from PySide6.QtCore import (QAbstractItemModel, QDataStream, QEvent, QIODevice,
                            QLine, QMimeData, QModelIndex, QObject, QPoint,
                            QSize, Qt, QThread, QTimer, QUrl, Signal,
                            SignalInstance, Slot)
from PySide6.QtGui import (QAction, QColor, QCursor, QDrag, QDragEnterEvent,
                           QDragLeaveEvent, QDragMoveEvent, QDropEvent, QIcon,
                           QImage, QKeyEvent, QMouseEvent, QPaintDevice,
                           QPainter, QPaintEvent, QPalette, QPixmap,
                           QUndoCommand, QUndoStack)
from PySide6.QtWidgets import (QBoxLayout, QComboBox, QFormLayout, QFrame,
                               QGridLayout, QGroupBox, QHBoxLayout, QLabel,
                               QLayout, QLineEdit, QListView, QListWidget,
                               QListWidgetItem, QMenu, QMenuBar, QPushButton,
                               QScrollArea, QSizePolicy, QSpacerItem,
                               QSplitter, QStyle, QStyleOptionComboBox,
                               QStylePainter, QTableWidget, QTableWidgetItem,
                               QToolBar, QTreeWidget, QTreeWidgetItem, QDialog, QDialogButtonBox, QCheckBox,
                               QVBoxLayout, QWidget)
from enum import IntEnum

from pyisotools.utils.rarc import FileConflictAction


class MoveConflictDialog(QDialog):
    def __init__(self, isMulti: bool = False, parent: Optional[QWidget] = None):
        super().__init__(parent)
        if isMulti:
            self.setFixedSize(400, 190)
        else:
            self.setFixedSize(400, 160)

        layout = QVBoxLayout()

        conflictMessage = QLabel()
        conflictMessage.setWordWrap(True)

        allCheckBox = QCheckBox("Apply to all")
        allCheckBox.setCheckable(True)

        replaceButton = QPushButton()
        skipButton = QPushButton()
        keepButton = QPushButton("Keep both (rename)")
        replaceButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        skipButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        keepButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        replaceButton.clicked.connect(
            lambda: self.__accept_role(FileConflictAction.REPLACE))
        skipButton.clicked.connect(
            lambda: self.__accept_role(FileConflictAction.SKIP))
        keepButton.clicked.connect(
            lambda: self.__accept_role(FileConflictAction.KEEP))

        choicesBox = QDialogButtonBox(Qt.Vertical)
        choicesBox.addButton(
            replaceButton, QDialogButtonBox.ButtonRole.AcceptRole)
        choicesBox.addButton(
            skipButton, QDialogButtonBox.ButtonRole.AcceptRole)
        choicesBox.addButton(
            keepButton, QDialogButtonBox.ButtonRole.AcceptRole)
        choicesBox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        self.conflictMessage = conflictMessage
        self.allCheckBox = allCheckBox
        self.replaceButton = replaceButton
        self.skipButton = skipButton
        self.keepButton = keepButton
        self.choicesBox = choicesBox

        frame = QFrame()
        frame.setFrameShape(QFrame.HLine)
        layout.addWidget(self.conflictMessage)
        if isMulti:
            layout.addWidget(self.allCheckBox)
            layout.addWidget(frame)
        layout.addWidget(self.choicesBox)

        self.setLayout(layout)

        self._actionRole = FileConflictAction.REPLACE
        self._blocked = False

    def apply_to_all(self) -> bool:
        return self.allCheckBox.isChecked()

    def set_paths(self, src: PurePath, dst: PurePath, isDir: bool):
        if src.parent == dst.parent:
            self.setWindowTitle(
                f"Renaming \"{src.name}\" to \"{dst.name}\""
            )
        else:
            self.setWindowTitle(
                f"Moving \"{src.name}\" from \"./{src.parent.name}\" to \"./{dst.parent.name}\""
            )

        srcType = "folder" if isDir else "file"
        dstType = "folder" if isDir else "file"

        self.conflictMessage.setText(
            f"The destination specified already has a {dstType} named \"{dst.name}\""
        )
        self.replaceButton.setText(f"Replace the {dstType}")
        self.skipButton.setText(f"Skip this {srcType}")

    def __accept_role(self, role: FileConflictAction):
        self._actionRole = role
        self.accept()
