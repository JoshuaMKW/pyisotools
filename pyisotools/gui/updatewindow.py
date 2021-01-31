# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'pyisotools_updatecycAOF.ui'
##
## Created by: Qt User Interface Compiler version 5.14.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import (QCoreApplication, QMetaObject, QObject, QPoint,
                            QRect, QSize, Qt, QUrl)
from PySide2.QtGui import (QBrush, QColor, QConicalGradient, QCursor, QFont,
                           QFontDatabase, QIcon, QLinearGradient, QPainter,
                           QPalette, QPixmap, QRadialGradient)
from PySide2.QtWidgets import *


class Ui_UpdateDialog(object):
    def setupUi(self, Dialog):
        if Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(361, 491)
        Dialog.setMinimumSize(QSize(361, 491))
        Dialog.setMaximumSize(QSize(361, 491))
        self.changelogTextEdit = QTextEdit(Dialog)
        self.changelogTextEdit.setObjectName(u"changelogTextEdit")
        self.changelogTextEdit.setGeometry(QRect(10, 70, 341, 361))
        self.changelogTextEdit.setLineWidth(1)
        self.changelogTextEdit.setReadOnly(True)
        self.changelogTextEdit.setTabStopWidth(40)
        self.delayButton = QPushButton(Dialog)
        self.delayButton.setObjectName(u"delayButton")
        self.delayButton.setGeometry(QRect(190, 440, 161, 41))
        self.updateButton = QPushButton(Dialog)
        self.updateButton.setObjectName(u"updateButton")
        self.updateButton.setGeometry(QRect(10, 440, 171, 41))
        self.updateLabel = QLabel(Dialog)
        self.updateLabel.setObjectName(u"updateLabel")
        self.updateLabel.setGeometry(QRect(10, 10, 341, 51))
        font = QFont()
        font.setFamily(u"MS Shell Dlg 2")
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
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))
        self.delayButton.setText(QCoreApplication.translate("Dialog", u"Remind Me Later", None))
        self.updateButton.setText(QCoreApplication.translate("Dialog", u"Open GitHub", None))
        self.updateLabel.setText(QCoreApplication.translate("Dialog", u"New Update Available!", None))
    # retranslateUi
