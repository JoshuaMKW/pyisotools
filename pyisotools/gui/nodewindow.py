# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'designerStRbZO.ui'
##
## Created by: Qt User Interface Compiler version 5.14.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import QCoreApplication, QMetaObject, QRect, QRegExp, Qt
from PySide2.QtGui import QRegExpValidator
from PySide2.QtWidgets import *

from .customwidgets import FilteredPlainTextEdit


class Ui_NodeFieldWindow(object):
    def setupUi(self, Dialog):
        if Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(201, 80)
        Dialog.setMinimumSize(201, 80)
        Dialog.setMaximumSize(201, 80)
        Dialog.setModal(True)
        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setGeometry(QRect(10, 40, 181, 32))
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        self.label = QLabel(Dialog)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(10, 10, 61, 21))
        self.plainTextEdit = FilteredPlainTextEdit(Dialog)
        self.plainTextEdit.setObjectName(u"plainTextEdit")
        self.plainTextEdit.setGeometry(QRect(80, 10, 111, 21))
        self.plainTextEdit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.plainTextEdit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.plainTextEdit.setScrollPolicy(FilteredPlainTextEdit.NoScroll)
        self.plainTextEdit.setExitOnReturn(True)
        self.plainTextEdit.setMaxLength(16)
        self.plainTextEdit.setValidator(QRegExpValidator(QRegExp(r"[0-9A-Fa-fx\-]*"), self.plainTextEdit))

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Node info", u"Node info", None))
        self.label.setText(QCoreApplication.translate("Node info", u"Field:", None))
    # retranslateUi

