from __future__ import annotations

from PySide2.QtCore import Qt
from PySide2.QtGui import (QKeyEvent, QKeySequence, QRegExpValidator,
                           QTextOption)
from PySide2.QtWidgets import *

from ..fst import FSTNode


class FilteredPlainTextEdit(QPlainTextEdit):

    class ScrollPolicy:
        NoScroll = 0
        ScrollVertical = 1
        ScrollHorizontal = 2

    NoScroll = 0
    ScrollVertical = 1
    ScrollHorizontal = 2

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._scrollPolicy = FilteredPlainTextEdit.ScrollVertical | FilteredPlainTextEdit.ScrollHorizontal
        self._exitOnReturn = False
        self._maxlength = 32767
        self._validator = None

        self.installEventFilter(self)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.context_menu)

    def setScrollPolicy(self, policy: ScrollPolicy):
        self._scrollPolicy = policy

    def setExitOnReturn(self, _exit: bool):
        self._exitOnReturn = _exit

    def setMaxLength(self, length: int):
        self._maxlength = length

    def setValidator(self, validator: QRegExpValidator):
        self._validator = validator

    def keyPressEvent(self, e: QKeyEvent):
        textCursor = self.textCursor()

        if (e.key() == Qt.Key_Return or e.key() == Qt.Key_Enter) and self._exitOnReturn:
            self.parent().accept()
        elif len(self.toPlainText()) - (textCursor.selectionEnd() - textCursor.selectionStart()) < self._maxlength:
            if not self._validator or self._validator.regExp().exactMatch(e.text()):
                super().keyPressEvent(e)
            elif not e.text().isprintable():
                if e.matches(QKeySequence.Paste):
                    self.paste(QApplication.clipboard().text())
                    e.ignore()
                else:
                    super().keyPressEvent(e)
            else:
                e.ignore()

        elif not e.text().isprintable() and not e.matches(QKeySequence.Paste):
            super().keyPressEvent(e)
        else:
            e.ignore()

    def eventFilter(self, obj, event) -> bool:
        if not self._scrollPolicy & FilteredPlainTextEdit.ScrollVertical:
            self.setWordWrapMode(QTextOption.NoWrap)
        else:
            self.setWordWrapMode(QTextOption.WordWrap)

        state = super().eventFilter(obj, event)

        if not self._scrollPolicy & FilteredPlainTextEdit.ScrollVertical:
            vbar = self.verticalScrollBar()
            vbar.setValue(vbar.minimum())
        if not self._scrollPolicy & FilteredPlainTextEdit.ScrollHorizontal:
            hbar = self.horizontalScrollBar()
            hbar.setValue(hbar.minimum())
        return state

    def context_menu(self, point):
        menu = self.createStandardContextMenu(self.mapToGlobal(point))
        menu.actions()[5].triggered.disconnect()
        menu.actions()[5].triggered.connect(lambda ignore=None,
                                            x=QApplication.clipboard().text(): self.paste(x))
        menu.exec_(self.mapToGlobal(point))

    def paste(self, text: str):
        if self._validator and not self._validator.regExp().exactMatch(text):
            return

        currentText = self.toPlainText()
        textCursor = self.textCursor()

        head, tail = currentText[:textCursor.selectionStart(
        )], currentText[textCursor.selectionEnd():]

        pasteLen = max(self._maxlength - len(head), 0)
        croppedPaste = text[:pasteLen]

        body = head + croppedPaste
        whole = head + croppedPaste + tail[:max(self._maxlength - len(body), 0)]

        self.setPlainText(whole)
        textCursor.setPosition(len(whole), textCursor.MoveMode.MoveAnchor)
        self.setTextCursor(textCursor)


class FSTTreeItem(QTreeWidgetItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fstNode = None

    @property
    def node(self) -> FSTNode:
        return self._fstNode

    @node.setter
    def node(self, node: FSTNode):
        self._fstNode = node

    @property
    def alignment(self) -> int:
        return self.node._alignment

    @alignment.setter
    def alignment(self, align: int):
        self.node._alignment = align

    @property
    def position(self) -> int:
        self.node._fileoffset

    @position.setter
    def position(self, pos: int):
        self.node._fileoffset = pos

    @property
    def excluded(self) -> int:
        return self.node._exclude

    @excluded.setter
    def excluded(self, exclude: bool):
        self.node._exclude = exclude

    def __lt__(self, other: FSTTreeItem):
        if self.node.is_root() and not other.node.is_root():
            return True
        elif self.node.is_dir() and other.node.is_file():
            return True
        elif self.node.is_file() and other.node.is_dir():
            return False
        else:
            return self.node._id < other.node._id
