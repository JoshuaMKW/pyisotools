# pylint: skip-file

# -*- coding: utf-8 -*-

################################################################################
# Form generated from reading UI file 'designerStRbZO.ui'
##
# Created by: Qt User Interface Compiler version 5.14.1
##
# WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from typing import Optional
from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, QRegularExpression, Qt
from PySide6.QtGui import QRegularExpressionValidator, QIntValidator
from PySide6.QtWidgets import QLabel, QWidget, QDialog, QDialogButtonBox, QComboBox, QMessageBox, QSizePolicy

from pyisotools.gui.customwidgets import FilteredPlainTextEdit, DialogLineEdit


class NodeFieldAlignmentDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None, f: Qt.WindowFlags = 0):
        super().__init__(parent, f)
        self.setFixedSize(201, 80)
        self.setModal(True)

        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setGeometry(QRect(10, 40, 181, 32))
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(
            QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.label = QLabel(self)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(10, 10, 61, 21))
        self.label.setText("Alignment:")

        self.alignmentComboBox = QComboBox(self)
        self.alignmentComboBox.addItems(
            ["4", "8", "16", "32", "64", "128", "256", "512",
             "1024", "2048", "4096", "8192", "16384", "32768"]
        )
        self.alignmentComboBox.setGeometry(QRect(80, 10, 111, 21))


class NodeFieldPositionDialog(QDialog):
    def __init__(self, minimum: int, maximum: int, parent: Optional[QWidget] = None, f: Qt.WindowFlags = 0):
        super().__init__(parent, f)
        self.setFixedSize(221, 94)
        self.setModal(True)

        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setGeometry(QRect(10, 44, 201, 46))
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(
            QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.sanitize)
        self.buttonBox.rejected.connect(self.reject)

        self.label = QLabel(self)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(10, 10, 81, 21))
        self.label.setText("Position:")

        self.hexLabel = QLabel("0x", self)
        self.hexLabel.setGeometry(QRect(68, 11, 79, 22))

        self.lineEdit = DialogLineEdit(self)
        self.lineEdit.setObjectName(u"plainTextEdit")
        self.lineEdit.setGeometry(QRect(80, 10, 131, 21))
        self.lineEdit.setValidator(QRegularExpressionValidator(
            "[0-9A-Fa-f]*"
        ))
        self.lineEdit.setMaxLength(8)
        self.lineEdit.accepted.connect(self.sanitize)

        self.rangeLabel = QLabel(self)
        font = self.rangeLabel.font()
        font.setPointSize(7)
        font.setItalic(True)
        self.rangeLabel.setFont(font)
        self.rangeLabel.setGeometry(QRect(78, 22, 140, 36))
        self.rangeLabel.setText(
            f"Min: 0x{minimum:X} - Max: 0x{maximum:X}"
        )

        self._minimum = minimum
        self._maximum = maximum

    def sanitize(self):
        if self.lineEdit.text().strip() == "":
            return

        address = int(self.lineEdit.text(), 16)
        if self._minimum <= address < self._maximum:
            self.accept()
            return

        error = QMessageBox()
        error.setIcon(QMessageBox.Critical)
        error.setText("Reposition failed!")
        error.setInformativeText(
            f"Positional address provided is out of range! (0x{self._minimum:X} <= 0x{address:X} < 0x{self._maximum:X} is false!)")
        error.setWindowTitle("Error")
        error.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        error.exec()
