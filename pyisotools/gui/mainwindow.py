# pylint: skip-file

# -*- coding: utf-8 -*-

################################################################################
# Form generated from reading UI file 'pyisotools_maindUOHCd.ui'
##
# Created by: Qt User Interface Compiler version 5.14.1
##
# WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, QSize, Qt
from PySide6.QtGui import QFont, QIcon, QAction
from PySide6.QtWidgets import *

from pyisotools.gui.fsviewer import ProjectTreeViewWidget
from pyisotools.gui.models.rarcfs import JSystemFSModel

from . import icons_rc
from .customwidgets import FilteredPlainTextEdit


class Ui_MainWindow():
    def setupUi(self, MainWindow):
        if MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(841, 561)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        MainWindow.setMinimumSize(QSize(841, 561))
        MainWindow.setMaximumSize(QSize(841, 561))
        icon = QIcon()
        icon.addFile(u":/icons/Logo", QSize(), QIcon.Normal, QIcon.Off)
        MainWindow.setWindowIcon(icon)
        MainWindow.setWindowOpacity(1.000000000000000)
        MainWindow.setAutoFillBackground(False)
        MainWindow.setStyleSheet(u"")
        MainWindow.setAnimated(True)
        MainWindow.setTabShape(QTabWidget.Rounded)
        self.actionOpenRoot = QAction(MainWindow)
        self.actionOpenRoot.setObjectName(u"actionOpenRoot")
        self.actionOpenRoot.setEnabled(True)
        self.actionClose = QAction(MainWindow)
        self.actionClose.setObjectName(u"actionClose")
        self.actionClose.setEnabled(False)
        self.actionRebuild = QAction(MainWindow)
        self.actionRebuild.setObjectName(u"actionRebuild")
        self.actionRebuild.setEnabled(False)
        self.actionFile_Alignment = QAction(MainWindow)
        self.actionFile_Alignment.setObjectName(u"actionFile_Alignment")
        self.actionFile_Position = QAction(MainWindow)
        self.actionFile_Position.setObjectName(u"actionFile_Position")
        self.actionFile_Exclusion = QAction(MainWindow)
        self.actionFile_Exclusion.setObjectName(u"actionFile_Exclusion")
        self.actionAbout = QAction(MainWindow)
        self.actionAbout.setObjectName(u"actionAbout")
        self.actionExtract = QAction(MainWindow)
        self.actionExtract.setObjectName(u"actionExtract")
        self.actionExtract.setEnabled(False)
        self.actionOpenISO = QAction(MainWindow)
        self.actionOpenISO.setObjectName(u"actionOpenISO")
        self.actionOpenISO.setEnabled(True)
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName(u"actionSave")
        self.actionSave.setEnabled(False)
        self.actionDarkTheme = QAction(MainWindow)
        self.actionDarkTheme.setObjectName(u"actionDarkTheme")
        self.actionDarkTheme.setCheckable(True)
        self.actionCheckUpdates = QAction(MainWindow)
        self.actionCheckUpdates.setObjectName(u"actionCheckUpdates")
        self.actionCheckUpdates.setCheckable(True)
        self.actionCheckUpdates.setChecked(True)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.fileSystemGroupBox = QGroupBox(self.centralwidget)
        self.fileSystemGroupBox.setObjectName(u"fileSystemGroupBox")
        self.fileSystemGroupBox.setEnabled(False)
        self.fileSystemGroupBox.setGeometry(QRect(470, 10, 361, 491))
        font = QFont()
        font.setPointSize(10)
        self.fileSystemGroupBox.setFont(font)
        self.fileSystemTreeWidget = ProjectTreeViewWidget(
            self.fileSystemGroupBox)
        self.fileSystemTreeWidget.setModel(JSystemFSModel(None))
        self.fileSystemTreeWidget.setObjectName(u"fileSystemTreeWidget")
        self.fileSystemTreeWidget.setGeometry(QRect(10, 20, 341, 431))
        font1 = QFont()
        font1.setPointSize(8)
        self.fileSystemTreeWidget.setFont(font1)
        self.fileSystemTreeWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.fileSystemTreeWidget.setFrameShadow(QFrame.Sunken)
        self.fileSystemTreeWidget.setAlternatingRowColors(False)
        self.fileSystemTreeWidget.setRootIsDecorated(True)
        self.fileSystemTreeWidget.setHeaderHidden(True)
        self.fileSystemStartInfoLabel = QLabel(self.fileSystemGroupBox)
        self.fileSystemStartInfoLabel.setObjectName(
            u"fileSystemStartInfoLabel")
        self.fileSystemStartInfoLabel.setGeometry(QRect(10, 460, 71, 20))
        self.fileSystemStartInfoLabel.setFont(font1)
        self.fileSystemStartInfoLabel.setFrameShape(QFrame.NoFrame)
        self.fileSystemStartInfoLabel.setFrameShadow(QFrame.Plain)
        self.fileSystemStartInfoLabel.setTextFormat(Qt.PlainText)
        self.fileSystemStartInfoLabel.setAlignment(
            Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)
        self.fileSystemStartInfoTextBox = FilteredPlainTextEdit(
            self.fileSystemGroupBox)
        self.fileSystemStartInfoTextBox.setObjectName(
            u"fileSystemStartInfoTextBox")
        self.fileSystemStartInfoTextBox.setGeometry(QRect(90, 460, 81, 22))
        self.fileSystemStartInfoTextBox.setFont(font1)
        self.fileSystemStartInfoTextBox.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff)
        self.fileSystemStartInfoTextBox.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff)
        self.fileSystemStartInfoTextBox.setReadOnly(True)
        self.fileSystemStartInfoTextBox.setTabStopDistance(40)
        self.fileSystemSizeInfoTextBox = FilteredPlainTextEdit(
            self.fileSystemGroupBox)
        self.fileSystemSizeInfoTextBox.setObjectName(
            u"fileSystemSizeInfoTextBox")
        self.fileSystemSizeInfoTextBox.setGeometry(QRect(270, 460, 81, 22))
        self.fileSystemSizeInfoTextBox.setFont(font1)
        self.fileSystemSizeInfoTextBox.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff)
        self.fileSystemSizeInfoTextBox.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff)
        self.fileSystemSizeInfoTextBox.setReadOnly(True)
        self.fileSystemSizeInfoTextBox.setTabStopDistance(40)
        self.fileSystemSizeInfoLabel = QLabel(self.fileSystemGroupBox)
        self.fileSystemSizeInfoLabel.setObjectName(u"fileSystemSizeInfoLabel")
        self.fileSystemSizeInfoLabel.setGeometry(QRect(190, 460, 71, 20))
        self.fileSystemSizeInfoLabel.setFont(font1)
        self.fileSystemSizeInfoLabel.setLayoutDirection(Qt.LeftToRight)
        self.fileSystemSizeInfoLabel.setFrameShape(QFrame.NoFrame)
        self.fileSystemSizeInfoLabel.setFrameShadow(QFrame.Plain)
        self.fileSystemSizeInfoLabel.setTextFormat(Qt.PlainText)
        self.fileSystemSizeInfoLabel.setAlignment(
            Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)
        self.isoDetailsGroupBox = QGroupBox(self.centralwidget)
        self.isoDetailsGroupBox.setObjectName(u"isoDetailsGroupBox")
        self.isoDetailsGroupBox.setEnabled(False)
        self.isoDetailsGroupBox.setGeometry(QRect(10, 10, 451, 141))
        self.isoDetailsGroupBox.setFont(font)
        self.isoMakerCodeLabel = QLabel(self.isoDetailsGroupBox)
        self.isoMakerCodeLabel.setObjectName(u"isoMakerCodeLabel")
        self.isoMakerCodeLabel.setGeometry(QRect(10, 80, 71, 21))
        self.isoMakerCodeLabel.setFont(font1)
        self.isoGameCodeTextBox = FilteredPlainTextEdit(
            self.isoDetailsGroupBox)
        self.isoGameCodeTextBox.setObjectName(u"isoGameCodeTextBox")
        self.isoGameCodeTextBox.setGeometry(QRect(90, 50, 111, 22))
        self.isoGameCodeTextBox.setFont(font1)
        self.isoGameCodeTextBox.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff)
        self.isoGameCodeTextBox.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff)
        self.isoGameCodeTextBox.setTabStopDistance(40)
        self.isoNameTextBox = FilteredPlainTextEdit(self.isoDetailsGroupBox)
        self.isoNameTextBox.setObjectName(u"isoNameTextBox")
        self.isoNameTextBox.setEnabled(False)
        self.isoNameTextBox.setGeometry(QRect(90, 20, 351, 22))
        self.isoNameTextBox.setFont(font1)
        self.isoNameTextBox.setMouseTracking(False)
        self.isoNameTextBox.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.isoNameTextBox.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.isoNameTextBox.setTabStopDistance(40)
        self.isoGameCodeLabel = QLabel(self.isoDetailsGroupBox)
        self.isoGameCodeLabel.setObjectName(u"isoGameCodeLabel")
        self.isoGameCodeLabel.setGeometry(QRect(10, 50, 71, 21))
        self.isoGameCodeLabel.setFont(font1)
        self.isoNameLabel = QLabel(self.isoDetailsGroupBox)
        self.isoNameLabel.setObjectName(u"isoNameLabel")
        self.isoNameLabel.setGeometry(QRect(10, 20, 71, 21))
        self.isoNameLabel.setFont(font1)
        self.isoMakerCodeTextBox = FilteredPlainTextEdit(
            self.isoDetailsGroupBox)
        self.isoMakerCodeTextBox.setObjectName(u"isoMakerCodeTextBox")
        self.isoMakerCodeTextBox.setGeometry(QRect(90, 80, 111, 22))
        self.isoMakerCodeTextBox.setFont(font1)
        self.isoMakerCodeTextBox.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff)
        self.isoMakerCodeTextBox.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff)
        self.isoMakerCodeTextBox.setTabStopDistance(40)
        self.isoMakerCodeTextBox.setScrollPolicy(
            FilteredPlainTextEdit.ScrollHorizontal)
        self.isoMakerCodeTextBox.setMaxLength(2)
        self.isoDiskIDLabel = QLabel(self.isoDetailsGroupBox)
        self.isoDiskIDLabel.setObjectName(u"isoDiskIDLabel")
        self.isoDiskIDLabel.setGeometry(QRect(230, 110, 61, 21))
        self.isoDiskIDLabel.setFont(font1)
        self.isoDiskIDTextBox = FilteredPlainTextEdit(self.isoDetailsGroupBox)
        self.isoDiskIDTextBox.setObjectName(u"isoDiskIDTextBox")
        self.isoDiskIDTextBox.setGeometry(QRect(300, 110, 141, 22))
        self.isoDiskIDTextBox.setFont(font1)
        self.isoDiskIDTextBox.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.isoDiskIDTextBox.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff)
        self.isoDiskIDTextBox.setTabStopDistance(40)
        self.isoDiskIDTextBox.setScrollPolicy(
            FilteredPlainTextEdit.ScrollHorizontal)
        self.isoDiskIDTextBox.setMaxLength(4)
        self.isoRegionLabel = QLabel(self.isoDetailsGroupBox)
        self.isoRegionLabel.setObjectName(u"isoRegionLabel")
        self.isoRegionLabel.setGeometry(QRect(230, 50, 61, 21))
        self.isoRegionLabel.setFont(font1)
        self.isoBuildDateLabel = QLabel(self.isoDetailsGroupBox)
        self.isoBuildDateLabel.setObjectName(u"isoBuildDateLabel")
        self.isoBuildDateLabel.setGeometry(QRect(230, 80, 61, 21))
        self.isoBuildDateLabel.setFont(font1)
        self.isoBuildDateTextBox = FilteredPlainTextEdit(
            self.isoDetailsGroupBox)
        self.isoBuildDateTextBox.setObjectName(u"isoBuildDateTextBox")
        self.isoBuildDateTextBox.setGeometry(QRect(300, 80, 141, 22))
        self.isoBuildDateTextBox.setFont(font1)
        self.isoBuildDateTextBox.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff)
        self.isoBuildDateTextBox.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff)
        self.isoBuildDateTextBox.setTabStopDistance(40)
        self.isoBuildDateTextBox.setScrollPolicy(
            FilteredPlainTextEdit.ScrollHorizontal)
        self.isoBuildDateTextBox.setMaxLength(10)
        self.isoVersionLabel = QLabel(self.isoDetailsGroupBox)
        self.isoVersionLabel.setObjectName(u"isoVersionLabel")
        self.isoVersionLabel.setGeometry(QRect(10, 110, 71, 21))
        self.isoVersionLabel.setFont(font1)
        self.isoVersionTextBox = FilteredPlainTextEdit(self.isoDetailsGroupBox)
        self.isoVersionTextBox.setObjectName(u"isoVersionTextBox")
        self.isoVersionTextBox.setGeometry(QRect(90, 110, 111, 22))
        self.isoVersionTextBox.setFont(font1)
        self.isoVersionTextBox.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff)
        self.isoVersionTextBox.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff)
        self.isoVersionTextBox.setTabStopDistance(40)
        self.isoVersionTextBox.setScrollPolicy(
            FilteredPlainTextEdit.ScrollHorizontal)
        self.isoVersionTextBox.setMaxLength(4)
        self.isoRegionComboBox = QComboBox(self.isoDetailsGroupBox)
        self.isoRegionComboBox.addItem("")
        self.isoRegionComboBox.addItem("")
        self.isoRegionComboBox.addItem("")
        self.isoRegionComboBox.addItem("")
        self.isoRegionComboBox.setObjectName(u"isoRegionComboBox")
        self.isoRegionComboBox.setGeometry(QRect(300, 50, 141, 22))
        self.isoRegionComboBox.setFont(font1)
        self.bannerGroupBox = QGroupBox(self.centralwidget)
        self.bannerGroupBox.setObjectName(u"bannerGroupBox")
        self.bannerGroupBox.setEnabled(False)
        self.bannerGroupBox.setGeometry(QRect(10, 150, 451, 351))
        self.bannerGroupBox.setFont(font)
        self.bannerGroupBox.setAutoFillBackground(True)
        self.bannerShortNameTextBox = FilteredPlainTextEdit(
            self.bannerGroupBox)
        self.bannerShortNameTextBox.setObjectName(u"bannerShortNameTextBox")
        self.bannerShortNameTextBox.setGeometry(QRect(90, 180, 351, 22))
        self.bannerShortNameTextBox.setFont(font1)
        self.bannerShortNameTextBox.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff)
        self.bannerShortNameTextBox.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff)
        self.bannerShortNameTextBox.setTabStopDistance(40)
        self.bannerShortNameTextBox.setScrollPolicy(
            FilteredPlainTextEdit.ScrollHorizontal)
        self.bannerShortNameTextBox.setMaxLength(32)
        self.bannerShortMakerTextBox = FilteredPlainTextEdit(
            self.bannerGroupBox)
        self.bannerShortMakerTextBox.setObjectName(u"bannerShortMakerTextBox")
        self.bannerShortMakerTextBox.setGeometry(QRect(90, 210, 351, 22))
        self.bannerShortMakerTextBox.setFont(font1)
        self.bannerShortMakerTextBox.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff)
        self.bannerShortMakerTextBox.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff)
        self.bannerShortMakerTextBox.setTabStopDistance(40)
        self.bannerShortMakerTextBox.setScrollPolicy(
            FilteredPlainTextEdit.ScrollHorizontal)
        self.bannerShortMakerTextBox.setMaxLength(32)
        self.bannerLongNameTextBox = FilteredPlainTextEdit(self.bannerGroupBox)
        self.bannerLongNameTextBox.setObjectName(u"bannerLongNameTextBox")
        self.bannerLongNameTextBox.setGeometry(QRect(90, 240, 351, 22))
        self.bannerLongNameTextBox.setFont(font1)
        self.bannerLongNameTextBox.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff)
        self.bannerLongNameTextBox.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff)
        self.bannerLongNameTextBox.setTabStopDistance(40)
        self.bannerLongNameTextBox.setScrollPolicy(
            FilteredPlainTextEdit.ScrollHorizontal)
        self.bannerLongNameTextBox.setMaxLength(64)
        self.bannerLongMakerTextBox = FilteredPlainTextEdit(
            self.bannerGroupBox)
        self.bannerLongMakerTextBox.setObjectName(u"bannerLongMakerTextBox")
        self.bannerLongMakerTextBox.setGeometry(QRect(90, 270, 351, 22))
        self.bannerLongMakerTextBox.setFont(font1)
        self.bannerLongMakerTextBox.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff)
        self.bannerLongMakerTextBox.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff)
        self.bannerLongMakerTextBox.setTabStopDistance(40)
        self.bannerLongMakerTextBox.setScrollPolicy(
            FilteredPlainTextEdit.ScrollHorizontal)
        self.bannerLongMakerTextBox.setMaxLength(64)
        self.bannerDescTextBox = FilteredPlainTextEdit(self.bannerGroupBox)
        self.bannerDescTextBox.setObjectName(u"bannerDescTextBox")
        self.bannerDescTextBox.setGeometry(QRect(90, 300, 351, 41))
        self.bannerDescTextBox.setFont(font1)
        self.bannerDescTextBox.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff)
        self.bannerDescTextBox.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff)
        self.bannerDescTextBox.setTabStopDistance(40)
        self.bannerDescTextBox.setScrollPolicy(
            FilteredPlainTextEdit.ScrollHorizontal | FilteredPlainTextEdit.ScrollVertical)
        self.bannerDescTextBox.setMaxLength(128)
        self.bannerShortNameLabel = QLabel(self.bannerGroupBox)
        self.bannerShortNameLabel.setObjectName(u"bannerShortNameLabel")
        self.bannerShortNameLabel.setGeometry(QRect(10, 180, 71, 21))
        self.bannerShortNameLabel.setFont(font1)
        self.bannerShortMakerLabel = QLabel(self.bannerGroupBox)
        self.bannerShortMakerLabel.setObjectName(u"bannerShortMakerLabel")
        self.bannerShortMakerLabel.setGeometry(QRect(10, 210, 71, 21))
        self.bannerShortMakerLabel.setFont(font1)
        self.bannerLongNameLabel = QLabel(self.bannerGroupBox)
        self.bannerLongNameLabel.setObjectName(u"bannerLongNameLabel")
        self.bannerLongNameLabel.setGeometry(QRect(10, 240, 71, 21))
        self.bannerLongNameLabel.setFont(font1)
        self.bannerLongMakerLabel = QLabel(self.bannerGroupBox)
        self.bannerLongMakerLabel.setObjectName(u"bannerLongMakerLabel")
        self.bannerLongMakerLabel.setGeometry(QRect(10, 270, 71, 21))
        self.bannerLongMakerLabel.setFont(font1)
        self.bannerDescLabel = QLabel(self.bannerGroupBox)
        self.bannerDescLabel.setObjectName(u"bannerDescLabel")
        self.bannerDescLabel.setGeometry(QRect(10, 300, 71, 21))
        self.bannerDescLabel.setFont(font1)
        self.bannerVersionLabel = QLabel(self.bannerGroupBox)
        self.bannerVersionLabel.setObjectName(u"bannerVersionLabel")
        self.bannerVersionLabel.setGeometry(QRect(230, 50, 61, 21))
        self.bannerVersionLabel.setFont(font1)
        self.bannerVersionLabel.setAlignment(
            Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)
        self.bannerHFrameLine = QFrame(self.bannerGroupBox)
        self.bannerHFrameLine.setObjectName(u"bannerHFrameLine")
        self.bannerHFrameLine.setEnabled(False)
        self.bannerHFrameLine.setGeometry(QRect(10, 160, 432, 2))
        self.bannerHFrameLine.setStyleSheet(u"")
        self.bannerHFrameLine.setFrameShape(QFrame.HLine)
        self.bannerHFrameLine.setFrameShadow(QFrame.Raised)
        self.bannerHFrameLine.setLineWidth(1)
        self.bannerHFrameLine.setMidLineWidth(0)
        self.bannerVersionTextBox = FilteredPlainTextEdit(self.bannerGroupBox)
        self.bannerVersionTextBox.setObjectName(u"bannerVersionTextBox")
        self.bannerVersionTextBox.setGeometry(QRect(300, 50, 141, 22))
        self.bannerVersionTextBox.setFont(font1)
        self.bannerVersionTextBox.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff)
        self.bannerVersionTextBox.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff)
        self.bannerVersionTextBox.setTabStopDistance(40)
        self.bannerVersionTextBox.setScrollPolicy(
            FilteredPlainTextEdit.ScrollHorizontal)
        self.bannerVersionTextBox.setMaxLength(4)
        self.bannerLanguageLabel = QLabel(self.bannerGroupBox)
        self.bannerLanguageLabel.setObjectName(u"bannerLanguageLabel")
        self.bannerLanguageLabel.setGeometry(QRect(230, 20, 61, 21))
        self.bannerLanguageLabel.setFont(font1)
        self.bannerLanguageLabel.setAlignment(
            Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)
        self.bannerLanguageComboBox = QComboBox(self.bannerGroupBox)
        self.bannerLanguageComboBox.addItem("")
        self.bannerLanguageComboBox.addItem("")
        self.bannerLanguageComboBox.addItem("")
        self.bannerLanguageComboBox.addItem("")
        self.bannerLanguageComboBox.addItem("")
        self.bannerLanguageComboBox.addItem("")
        self.bannerLanguageComboBox.setObjectName(u"bannerLanguageComboBox")
        self.bannerLanguageComboBox.setGeometry(QRect(300, 20, 141, 22))
        self.bannerLanguageComboBox.setFont(font1)
        self.bannerImportButton = QPushButton(self.bannerGroupBox)
        self.bannerImportButton.setObjectName(u"bannerImportButton")
        self.bannerImportButton.setGeometry(QRect(10, 20, 91, 23))
        self.bannerImportButton.setFont(font1)
        self.bannerExportButton = QPushButton(self.bannerGroupBox)
        self.bannerExportButton.setObjectName(u"bannerExportButton")
        self.bannerExportButton.setGeometry(QRect(110, 20, 91, 23))
        self.bannerExportButton.setFont(font1)
        self.bannerSaveButton = QPushButton(self.bannerGroupBox)
        self.bannerSaveButton.setObjectName(u"bannerSaveButton")
        self.bannerSaveButton.setGeometry(QRect(230, 92, 211, 51))
        self.bannerSaveButton.setFont(font1)
        self.bannerImageView = QLabel(self.bannerGroupBox)
        self.bannerImageView.setObjectName(u"bannerImageView")
        self.bannerImageView.setEnabled(False)
        self.bannerImageView.setGeometry(QRect(10, 50, 190, 63))
        self.bannerImageView.setMinimumSize(QSize(190, 63))
        self.bannerImageView.setMaximumSize(QSize(190, 63))
        self.bannerImageView.setToolTipDuration(-1)
        self.bannerImageView.setAutoFillBackground(True)
        self.bannerImageView.setFrameShape(QFrame.Box)
        self.bannerImageView.setFrameShadow(QFrame.Plain)
        self.bannerImageView.setLineWidth(1)
        self.bannerImageView.setMidLineWidth(0)
        self.bannerImageView.setAlignment(Qt.AlignCenter)
        self.bannerComboBox = QComboBox(self.bannerGroupBox)
        self.bannerComboBox.setObjectName(u"bannerComboBox")
        self.bannerComboBox.setGeometry(QRect(10, 120, 190, 22))
        self.bannerComboBox.setFont(font1)
        self.operationProgressBar = QProgressBar(self.centralwidget)
        self.operationProgressBar.setObjectName(u"operationProgressBar")
        self.operationProgressBar.setGeometry(QRect(10, 510, 821, 21))
        self.operationProgressBar.setAutoFillBackground(False)
        self.operationProgressBar.setMaximum(100)
        self.operationProgressBar.setValue(0)
        self.operationProgressBar.setAlignment(Qt.AlignCenter)
        self.operationProgressBar.setTextVisible(False)
        self.operationProgressBar.setInvertedAppearance(False)
        self.operationProgressBar.setTextDirection(QProgressBar.TopToBottom)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 841, 21))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setObjectName(u"menuHelp")
        self.menuSettings = QMenu(self.menubar)
        self.menuSettings.setObjectName(u"menuSettings")
        MainWindow.setMenuBar(self.menubar)
        QWidget.setTabOrder(self.isoNameTextBox, self.isoGameCodeTextBox)
        QWidget.setTabOrder(self.isoGameCodeTextBox, self.isoMakerCodeTextBox)
        QWidget.setTabOrder(self.isoMakerCodeTextBox, self.isoVersionTextBox)
        QWidget.setTabOrder(self.isoVersionTextBox, self.isoRegionComboBox)
        QWidget.setTabOrder(self.isoRegionComboBox, self.isoBuildDateTextBox)
        QWidget.setTabOrder(self.isoBuildDateTextBox, self.isoDiskIDTextBox)
        QWidget.setTabOrder(self.isoDiskIDTextBox, self.bannerImportButton)
        QWidget.setTabOrder(self.bannerImportButton, self.bannerExportButton)
        QWidget.setTabOrder(self.bannerExportButton,
                            self.bannerLanguageComboBox)
        QWidget.setTabOrder(self.bannerLanguageComboBox,
                            self.bannerVersionTextBox)
        QWidget.setTabOrder(self.bannerVersionTextBox, self.bannerSaveButton)
        QWidget.setTabOrder(self.bannerSaveButton, self.bannerShortNameTextBox)
        QWidget.setTabOrder(self.bannerShortNameTextBox,
                            self.bannerShortMakerTextBox)
        QWidget.setTabOrder(self.bannerShortMakerTextBox,
                            self.bannerLongNameTextBox)
        QWidget.setTabOrder(self.bannerLongNameTextBox,
                            self.bannerLongMakerTextBox)
        QWidget.setTabOrder(self.bannerLongMakerTextBox,
                            self.bannerDescTextBox)
        QWidget.setTabOrder(self.bannerDescTextBox, self.fileSystemTreeWidget)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuSettings.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())
        self.menuFile.addAction(self.actionOpenISO)
        self.menuFile.addAction(self.actionOpenRoot)
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addAction(self.actionClose)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionRebuild)
        self.menuFile.addAction(self.actionExtract)
        self.menuHelp.addAction(self.actionFile_Alignment)
        self.menuHelp.addAction(self.actionFile_Position)
        self.menuHelp.addAction(self.actionFile_Exclusion)
        self.menuHelp.addSeparator()
        self.menuHelp.addAction(self.actionAbout)
        self.menuSettings.addAction(self.actionDarkTheme)
        self.menuSettings.addAction(self.actionCheckUpdates)

        self.retranslateUi(MainWindow)
        self.bannerImportButton.released.connect(MainWindow.bnr_load_dialog)
        self.bannerExportButton.released.connect(MainWindow.bnr_save_dialog)
        self.bannerLanguageComboBox.currentTextChanged.connect(
            MainWindow.bnr_update_info)
        self.bannerComboBox.currentTextChanged.connect(
            MainWindow.bnr_update_info)
        self.bannerSaveButton.clicked.connect(MainWindow.bnr_save_info_wrapped)
        self.actionOpenRoot.triggered.connect(MainWindow.iso_load_root_dialog)
        self.actionClose.triggered.connect(MainWindow.reset_all)
        self.actionRebuild.triggered.connect(MainWindow.iso_build_dialog)
        self.actionExtract.triggered.connect(MainWindow.iso_extract_dialog)
        self.actionAbout.triggered.connect(MainWindow.help_about)
        self.actionFile_Alignment.triggered.connect(
            MainWindow.help_file_alignment)
        self.actionFile_Position.triggered.connect(
            MainWindow.help_file_position)
        self.actionFile_Exclusion.triggered.connect(
            MainWindow.help_file_exclusion)
        self.actionOpenISO.triggered.connect(MainWindow.iso_load_iso_dialog)
        self.fileSystemTreeWidget.customContextMenuRequested.connect(
            MainWindow.file_system_context_menu)
        # self.fileSystemTreeWidget.itemClicked.connect(
        #     MainWindow.file_system_set_fields)
        self.actionSave.triggered.connect(MainWindow.save_all_wrapped)
        self.actionDarkTheme.toggled.connect(MainWindow.update_dark)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate(
            "MainWindow", u"pyisotools", None))
        self.actionOpenRoot.setText(
            QCoreApplication.translate("MainWindow", u"Open Root", None))
# if QT_CONFIG(shortcut)
        self.actionOpenRoot.setShortcut(
            QCoreApplication.translate("MainWindow", u"Ctrl+Shift+O", None))
#endif // QT_CONFIG(shortcut)
        self.actionClose.setText(
            QCoreApplication.translate("MainWindow", u"Close", None))
# if QT_CONFIG(shortcut)
        self.actionClose.setShortcut(QCoreApplication.translate(
            "MainWindow", u"Ctrl+Shift+C", None))
#endif // QT_CONFIG(shortcut)
        self.actionRebuild.setText(
            QCoreApplication.translate("MainWindow", u"Build", None))
# if QT_CONFIG(shortcut)
        self.actionRebuild.setShortcut(
            QCoreApplication.translate("MainWindow", u"Ctrl+B", None))
#endif // QT_CONFIG(shortcut)
        self.actionFile_Alignment.setText(
            QCoreApplication.translate("MainWindow", u"File Alignment", None))
        self.actionFile_Position.setText(
            QCoreApplication.translate("MainWindow", u"File Position", None))
        self.actionFile_Exclusion.setText(
            QCoreApplication.translate("MainWindow", u"File Exclusion", None))
        self.actionAbout.setText(
            QCoreApplication.translate("MainWindow", u"About", None))
        self.actionExtract.setText(
            QCoreApplication.translate("MainWindow", u"Extract", None))
# if QT_CONFIG(shortcut)
        self.actionExtract.setShortcut(
            QCoreApplication.translate("MainWindow", u"Ctrl+E", None))
#endif // QT_CONFIG(shortcut)
        self.actionOpenISO.setText(
            QCoreApplication.translate("MainWindow", u"Open ISO", None))
# if QT_CONFIG(shortcut)
        self.actionOpenISO.setShortcut(
            QCoreApplication.translate("MainWindow", u"Ctrl+O", None))
#endif // QT_CONFIG(shortcut)
        self.actionSave.setText(
            QCoreApplication.translate("MainWindow", u"Save", None))
# if QT_CONFIG(shortcut)
        self.actionSave.setShortcut(
            QCoreApplication.translate("MainWindow", u"Ctrl+S", None))
#endif // QT_CONFIG(shortcut)
        self.actionDarkTheme.setText(
            QCoreApplication.translate("MainWindow", u"Dark Theme", None))
        self.actionCheckUpdates.setText(
            QCoreApplication.translate("MainWindow", u"Check Updates", None))
        self.fileSystemGroupBox.setTitle(
            QCoreApplication.translate("MainWindow", u"File System", None))
        self.fileSystemStartInfoLabel.setText(
            QCoreApplication.translate("MainWindow", u"File Location: ", None))
        self.fileSystemSizeInfoLabel.setText(
            QCoreApplication.translate("MainWindow", u"File Size: ", None))
        self.isoDetailsGroupBox.setTitle(
            QCoreApplication.translate("MainWindow", u"ISO Details", None))
        self.isoMakerCodeLabel.setText(
            QCoreApplication.translate("MainWindow", u"Maker Code: ", None))
        self.isoGameCodeLabel.setText(
            QCoreApplication.translate("MainWindow", u"Game Code: ", None))
        self.isoNameLabel.setText(
            QCoreApplication.translate("MainWindow", u"Name: ", None))
        self.isoDiskIDLabel.setText(
            QCoreApplication.translate("MainWindow", u"Disk ID:", None))
        self.isoRegionLabel.setText(
            QCoreApplication.translate("MainWindow", u"Region:", None))
        self.isoBuildDateLabel.setText(
            QCoreApplication.translate("MainWindow", u"Build Date: ", None))
        self.isoVersionLabel.setText(
            QCoreApplication.translate("MainWindow", u"Version: ", None))
        self.isoRegionComboBox.setItemText(
            0, QCoreApplication.translate("MainWindow", u"NTSC-U", None))
        self.isoRegionComboBox.setItemText(
            1, QCoreApplication.translate("MainWindow", u"PAL", None))
        self.isoRegionComboBox.setItemText(
            2, QCoreApplication.translate("MainWindow", u"NTSC-J", None))
        self.isoRegionComboBox.setItemText(
            3, QCoreApplication.translate("MainWindow", u"NTSC-K", None))

        self.bannerGroupBox.setTitle(QCoreApplication.translate(
            "MainWindow", u"Banner Details", None))
        self.bannerLongMakerTextBox.setPlainText("")
        self.bannerDescTextBox.setPlainText("")
        self.bannerShortNameLabel.setText(
            QCoreApplication.translate("MainWindow", u"Short Name:", None))
        self.bannerShortMakerLabel.setText(
            QCoreApplication.translate("MainWindow", u"Short Maker:", None))
        self.bannerLongNameLabel.setText(
            QCoreApplication.translate("MainWindow", u"Long Name:", None))
        self.bannerLongMakerLabel.setText(
            QCoreApplication.translate("MainWindow", u"Long Maker:", None))
        self.bannerDescLabel.setText(QCoreApplication.translate(
            "MainWindow", u"Description:", None))
        self.bannerVersionLabel.setText(
            QCoreApplication.translate("MainWindow", u"Version: ", None))
        self.bannerLanguageLabel.setText(
            QCoreApplication.translate("MainWindow", u"Language:", None))
        self.bannerLanguageComboBox.setItemText(
            0, QCoreApplication.translate("MainWindow", u"English", None))
        self.bannerLanguageComboBox.setItemText(
            1, QCoreApplication.translate("MainWindow", u"German", None))
        self.bannerLanguageComboBox.setItemText(
            2, QCoreApplication.translate("MainWindow", u"French", None))
        self.bannerLanguageComboBox.setItemText(
            3, QCoreApplication.translate("MainWindow", u"Spanish", None))
        self.bannerLanguageComboBox.setItemText(
            4, QCoreApplication.translate("MainWindow", u"Italian", None))
        self.bannerLanguageComboBox.setItemText(
            5, QCoreApplication.translate("MainWindow", u"Dutch", None))

        self.bannerImportButton.setText(
            QCoreApplication.translate("MainWindow", u"Import", None))
        self.bannerExportButton.setText(
            QCoreApplication.translate("MainWindow", u"Export", None))
        self.bannerSaveButton.setText(QCoreApplication.translate(
            "MainWindow", u"Save Changes", None))
        self.bannerImageView.setText("")
        self.operationProgressBar.setFormat(QCoreApplication.translate(
            "MainWindow", u"Please wait... %p%", None))
        self.menuFile.setTitle(
            QCoreApplication.translate("MainWindow", u"File", None))
        self.menuHelp.setTitle(
            QCoreApplication.translate("MainWindow", u"Help", None))
        self.menuSettings.setTitle(
            QCoreApplication.translate("MainWindow", u"Settings", None))
    # retranslateUi
