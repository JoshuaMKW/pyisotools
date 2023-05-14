# pylint: skip-file

# -*- coding: utf-8 -*-

################################################################################
# Form generated from reading UI file 'pyisotools_updatecycAOF.ui'
##
# Created by: Qt User Interface Compiler version 5.14.1
##
# WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, QSize, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QPushButton, QTextEdit, QLabel


class Ui_UpdateDialog:
    def setupUi(self, Dialog):
        if Dialog.objectName():
            Dialog.setObjectName("Dialog")
        Dialog.resize(361, 491)
        Dialog.setMinimumSize(QSize(361, 491))
        Dialog.setMaximumSize(QSize(361, 491))
        self.changelogTextEdit = QTextEdit(Dialog)
        self.changelogTextEdit.setObjectName("changelogTextEdit")
        self.changelogTextEdit.setGeometry(QRect(10, 70, 341, 361))
        self.changelogTextEdit.setLineWidth(1)
        self.changelogTextEdit.setReadOnly(True)
        self.changelogTextEdit.setTabStopWidth(40)
        self.delayButton = QPushButton(Dialog)
        self.delayButton.setObjectName("delayButton")
        self.delayButton.setGeometry(QRect(190, 440, 161, 41))
        self.updateButton = QPushButton(Dialog)
        self.updateButton.setObjectName("updateButton")
        self.updateButton.setGeometry(QRect(10, 440, 171, 41))
        self.updateLabel = QLabel(Dialog)
        self.updateLabel.setObjectName("updateLabel")
        self.updateLabel.setGeometry(QRect(10, 10, 341, 51))
        font = QFont()
        font.setFamily("MS Shell Dlg 2")
        font.setPointSize(20)
        font.setBold(False)
        font.setUnderline(False)
        font.setWeight(50)
        self.updateLabel.setFont(font)
        self.updateLabel.setScaledContents(False)
        self.updateLabel.setAlignment(Qt.AlignCenter)

        self.retranslateUi(Dialog)
        self.updateButton.released.connect(Dialog.accept)
        self.delayButton.released.connect(Dialog.reject)

        QMetaObject.connectSlotsByName(Dialog)

    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", "Dialog", None))
        self.delayButton.setText(
            QCoreApplication.translate("Dialog", "Remind Me Later", None)
        )
        self.updateButton.setText(
            QCoreApplication.translate("Dialog", "Open GitHub", None)
        )
        self.updateLabel.setText(
            QCoreApplication.translate("Dialog", "New Update Available!", None)
        )

    # retranslateUi
