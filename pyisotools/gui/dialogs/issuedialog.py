from pathlib import Path
from typing import Optional, Tuple
from PySide6.QtCore import (QAbstractItemModel, QDataStream, QEvent, QIODevice,
                            QLine, QMimeData, QModelIndex, QObject, QPoint,
                            QSize, Qt, QThread, QTimer, QUrl, Signal, QUrl,
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
from PySide6.QtWebEngineWidgets import QWebEngineView

from enum import IntEnum


class GithubIssueDialog(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedSize(600, 800)
        self.setWindowTitle("Submit Bug Report")
        self.setWindowModality(Qt.ApplicationModal)

        self.mainLayout = QGridLayout()

        self._webView = QWebEngineView()
        self.mainLayout.addWidget(self._webView, 0, 0, 1, 1)

        self.setLayout(self.mainLayout)
        
    @Slot()
    def open_issue_page(self):
        self._webView.load(
            QUrl(
                "https://github.com/JoshuaMKW/Juniors-Toolbox/issues/new?assignees=JoshuaMKW&labels=bug&template=bug_report.md&title=%5BBUG%5D+Short+Description"
            )
        )
        self.show()
