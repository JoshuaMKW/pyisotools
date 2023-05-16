from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout

class ListInterfaceWidget(QWidget):
    addRequested = Signal()
    removeRequested = Signal()
    copyRequested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setMinimumWidth(180)
        self.setFixedHeight(45)

        addButton = QPushButton("New", self)
        addButton.clicked.connect(self.addRequested.emit)
        self.__addButton = addButton

        removeButton = QPushButton("Remove", self)
        removeButton.clicked.connect(self.removeRequested.emit)
        self.__removeButton = removeButton

        copyButton = QPushButton("Copy", self)
        copyButton.clicked.connect(self.copyRequested.emit)
        self.__copyButton = copyButton

        layout = QHBoxLayout(self)
        layout.addWidget(self.__addButton)
        layout.addWidget(self.__removeButton)
        layout.addWidget(self.__copyButton)

        self.setLayout(layout)