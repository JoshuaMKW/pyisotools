# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'pyisotools_settingsDBnypr.ui'
##
## Created by: Qt User Interface Compiler version 5.14.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import (QCoreApplication, QMetaObject, QObject, QPoint,
    QRect, QSize, QUrl, Qt)
from PySide2.QtGui import (QBrush, QColor, QConicalGradient, QCursor, QFont,
    QFontDatabase, QIcon, QLinearGradient, QPalette, QPainter, QPixmap,
    QRadialGradient)
from PySide2.QtWidgets import *


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.setWindowModality(Qt.ApplicationModal)
        Dialog.resize(191, 90)
        Dialog.setMinimumSize(QSize(191, 90))
        Dialog.setMaximumSize(QSize(191, 90))
        icon = QIcon()
        icon.addFile(u"../Pictures/Saved Pictures/pyisotools.png", QSize(), QIcon.Normal, QIcon.Off)
        Dialog.setWindowIcon(icon)
        Dialog.setSizeGripEnabled(False)
        Dialog.setModal(False)
        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setGeometry(QRect(20, 50, 151, 32))
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        self.darkThemeCheckBox = QCheckBox(Dialog)
        self.darkThemeCheckBox.setObjectName(u"darkThemeCheckBox")
        self.darkThemeCheckBox.setGeometry(QRect(20, 10, 91, 17))
        self.updateCheckBox = QCheckBox(Dialog)
        self.updateCheckBox.setObjectName(u"updateCheckBox")
        self.updateCheckBox.setGeometry(QRect(20, 30, 111, 17))

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        self.darkThemeCheckBox.stateChanged.connect(Dialog.switch_theme)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Settings", None))
        self.darkThemeCheckBox.setText(QCoreApplication.translate("Dialog", u"Dark Theme", None))
        self.updateCheckBox.setText(QCoreApplication.translate("Dialog", u"Check for Updates", None))
    # retranslateUi

