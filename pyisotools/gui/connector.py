from __future__ import annotations

import functools
import pickle
import subprocess
import sys
import threading
import time
import traceback
import webbrowser
from pathlib import Path

from PIL import Image, ImageQt
from PySide2.QtCore import QEvent, QFile, Qt, QTextStream, QThread, Signal
from PySide2.QtGui import QColor, QIcon
from PySide2.QtWidgets import (QAction, QDialog, QDialogButtonBox, QFileDialog,
                               QFrame, QLineEdit, QMainWindow, QMenu,
                               QMessageBox, QPlainTextEdit, QTextEdit,
                               QTreeWidgetItem, QVBoxLayout)
from sortedcontainers import SortedDict, SortedList

from .. import __version__
from ..apploader import Apploader
from ..bi2 import BI2
from ..bnrparser import BNR
from ..iso import FSTNode, GamecubeISO, ISOBase
from .customwidgets import FSTTreeWidget
from .nodewindow import Ui_NodeFieldWindow
from .updater import GitReleaseUpdateScraper, ReleaseData
from .updatewindow import Ui_UpdateDialog
from .workpathing import get_program_folder, resource_path

__GLOBAL_STATE = [True, ""]

def excepthook(args: tuple):

    __GLOBAL_STATE[0] = False
    __GLOBAL_STATE[1] = "".join(traceback.format_exception(args[0], args[1], args[2]))

    args[3]._zombie = True

threading.excepthook = excepthook

def notify_status(context: JobDialogState):
    """ Wrapped function must return a (Controller, bool, str) tuple to indicate a status, and show message """
    def decorater_inner(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                value = func(*args, **kwargs)
            except Exception:
                dialog = JobFailedDialog(args[0], info="".join(traceback.format_exc()))
                dialog.exec_()
                args[0].ui.operationProgressBar.setTextVisible(False)
                args[0].ui.operationProgressBar.setValue(0)
                return None

            dialog = None
            if __GLOBAL_STATE[0] is False:
                dialog = JobFailedDialog(args[0], info=__GLOBAL_STATE[1])
                dialog.exec_()
                args[0].ui.operationProgressBar.setTextVisible(False)
                args[0].ui.operationProgressBar.setValue(0)
                __GLOBAL_STATE[0] = True
                __GLOBAL_STATE[1] = ""
            elif issubclass(type(value[1]), QDialog):
                if value[0] is False and (context & JobDialogState.SHOW_FAILURE):
                    value[1].exec_()
                if value[0] is True and (context & JobDialogState.SHOW_COMPLETE):
                    value[1].exec_()
                if value[0] is False and (context & JobDialogState.SHOW_FAILURE_WHEN_MESSAGE):
                    value[1].exec_()
                if value[0] is True and (context & JobDialogState.SHOW_COMPLETE_WHEN_MESSAGE):
                    value[1].exec_()
                if value[0] is True and (context & JobDialogState.SHOW_WARNING_WHEN_MESSAGE):
                    value[1].exec_()
                if context & JobDialogState.RESET_PROGRESS_AFTER:
                    args[0].ui.operationProgressBar.setTextVisible(False)
                    args[0].ui.operationProgressBar.setValue(0)
            else:
                if value[0] is False and (context & JobDialogState.SHOW_FAILURE):
                    dialog = JobFailedDialog(args[0], info=value[1])
                    dialog.exec_()
                if value[0] is True and (context & JobDialogState.SHOW_COMPLETE):
                    dialog = JobCompleteDialog(args[0], info=value[1])
                    dialog.exec_()
                if value[0] is False and (context & JobDialogState.SHOW_FAILURE_WHEN_MESSAGE):
                    if value[1]:
                        dialog = JobFailedDialog(args[0], info=value[1])
                        dialog.exec_()
                if value[0] is True and (context & JobDialogState.SHOW_COMPLETE_WHEN_MESSAGE):
                    if value[1]:
                        dialog = JobCompleteDialog(args[0], info=value[1])
                        dialog.exec_()
                if value[0] is True and (context & JobDialogState.SHOW_WARNING_WHEN_MESSAGE):
                    if value[1]:
                        dialog = JobWarningDialog(value[1], args[0])
                        dialog.exec_()
                if context & JobDialogState.RESET_PROGRESS_AFTER:
                    args[0].ui.operationProgressBar.setTextVisible(False)
                    args[0].ui.operationProgressBar.setValue(0)

            return value
        return wrapper
    return decorater_inner


class StoppableThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._zombie = False

    def is_zombie(self) -> bool:
        return self._zombie


class JobDialogState:
    SHOW_NONE = 0
    SHOW_COMPLETE = 1
    SHOW_FAILURE = 2
    SHOW_COMPLETE_WHEN_MESSAGE = 4
    SHOW_FAILURE_WHEN_MESSAGE = 8
    SHOW_WARNING_WHEN_MESSAGE = 16
    RESET_PROGRESS_AFTER = 32


class JobFailedDialog(QMessageBox):
    def __init__(self, *args, info=None, **kwargs):
        super().__init__(*args, **kwargs)

        if not info:
            info = ""

        self.setIcon(QMessageBox.Critical)
        self.setText("Job failed!")
        self.setInformativeText(info)
        self.setWindowTitle("Error")


class JobCompleteDialog(QMessageBox):
    def __init__(self, *args, info=None, **kwargs):
        super().__init__(*args, **kwargs)

        if not info:
            info = ""

        self.setIcon(QMessageBox.Information)
        self.setText("Job complete!")
        self.setInformativeText(info)
        self.setWindowTitle("Info")

class JobWarningDialog(QMessageBox):
    def __init__(self, info, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setIcon(QMessageBox.Warning)
        self.setText(info)
        self.setWindowTitle("Warning")

class NodeFieldDialog(QDialog):
    def __init__(self, ui, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = ui

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress and obj is self.ui.plainTextEdit:
            if event.key() == Qt.Key_Return and self.ui.plainTextEdit.hasFocus():
                self.accept()
                return False
        return super().eventFilter(obj, event)        


class Controller(QMainWindow):
    class Themes:
        DARK = resource_path(Path("themes", "dark.qss"))
        LIGHT = resource_path(Path("themes", "light.qss"))

    def __init__(self, ui, *args, **kwargs):
        super().__init__(*args, **kwargs)
        __CACHED_GUI = self

        self.iso = None

        self.ui = ui
        self.theme = Controller.Themes.LIGHT

        self.bnrImagePath = None
        self.buildPath = None
        self.extractPath = None
        self.rootPath = None
        self.genericPath = None

        self._fromIso = False
        self._viewPath = None

        self.updater = GitReleaseUpdateScraper("JoshuaMKW", "pyisotools")
        self.updater.updateFound.connect(self.notify_update)
        self.updater.start()

    @property
    def programConfig(self):
        versionStub = __version__.replace(".", "-")
        return get_program_folder(f"pyisotools v{versionStub}") / "program.cfg"

    def closeEvent(self, event):
        self.update_program_config()
        self.updater.exit(0)
        event.accept()

    def notify_update(self, releaseInfo: ReleaseData):
        self.updater.skipCount = 60
        
        dialog = QDialog(self, Qt.WindowSystemMenuHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        updateWindow = Ui_UpdateDialog()
        updateWindow.setupUi(dialog)
        dialog.setModal(True)

        updateWindow.updateLabel.setText(f"pyisotools {releaseInfo.version} available!")
        updateWindow.changelogTextEdit.setHtml(str(releaseInfo.info))

        if dialog.exec_() == QDialog.Accepted:
            webbrowser.open_new_tab(releaseInfo.parentURL)


    def is_from_iso(self) -> bool:
        return self._fromIso

    @notify_status(JobDialogState.SHOW_FAILURE_WHEN_MESSAGE | JobDialogState.RESET_PROGRESS_AFTER)
    def iso_load_iso_dialog(self) -> (bool, str):
        dialog = QFileDialog(parent=self,
                             caption="Open Gamecube ISO",
                             directory=str(
                                 self.rootPath.parent if self.rootPath else Path.home()),
                             filter="Gamecube Image (*.iso *.gcm);;All files (*)")

        dialog.setFileMode(QFileDialog.ExistingFile)

        if dialog.exec_() != QFileDialog.Accepted:
            return False, None

        selected = Path(dialog.selectedFiles()[0]).resolve()

        if not selected.exists():
            return False, "The path does not exist!"

        self.rootPath = selected

        if self.rootPath.is_file():
            self.iso = GamecubeISO.from_iso(self.rootPath)
            self._fromIso = True
            self.update_all()
            self.ui.actionClose.setEnabled(True)
            self.ui.actionSave.setEnabled(True)
            self.ui.actionRebuild.setEnabled(False)
            self.ui.actionExtract.setEnabled(True)
        else:
            return False, "The file does not exist!"

        self.setWindowTitle(f"pyisotools v{__version__} - {self.iso.bootheader.gameName} (iso)")

        return True, None

    @notify_status(JobDialogState.SHOW_FAILURE_WHEN_MESSAGE | JobDialogState.RESET_PROGRESS_AFTER)
    def iso_load_root_dialog(self) -> (bool, str):
        dialog = QFileDialog(parent=self,
                             caption="Open Gamecube Root",
                             directory=str(
                                 self.rootPath.parent if self.rootPath else Path.home()),
                             filter="All folders (*)")

        dialog.setFileMode(QFileDialog.DirectoryOnly)

        if dialog.exec_() != QFileDialog.Accepted:
            return False, None

        selected = Path(dialog.selectedFiles()[0]).resolve()

        if not selected.exists():
            return False, "The path does not exist!"

        self.rootPath = selected
        if self.rootPath.is_dir():
            self.iso = GamecubeISO.from_root(self.rootPath)
            self._fromIso = False
            self.update_all()
            self.ui.actionClose.setEnabled(True)
            self.ui.actionSave.setEnabled(True)
            self.ui.actionRebuild.setEnabled(True)
            self.ui.actionExtract.setEnabled(False)
        else:
            return False, "The file does not exist!"

        self.setWindowTitle(f"pyisotools v{__version__} - {self.iso.bootheader.gameName} (root)")

        return True, None

    @notify_status(JobDialogState.SHOW_FAILURE_WHEN_MESSAGE | JobDialogState.SHOW_COMPLETE | JobDialogState.RESET_PROGRESS_AFTER)
    def iso_build_dialog(self) -> (bool, str):
        dialog = QFileDialog(parent=self,
                             caption="Build Root To...",
                             directory=str(
                                 self.buildPath.parent if self.buildPath else Path.home()),
                             filter="Gamecube Image (*.iso *.gcm);;All files (*)")

        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setFileMode(QFileDialog.AnyFile)

        if dialog.exec_() != QFileDialog.Accepted:
            return False, None

        self.buildPath = Path(dialog.selectedFiles()[0]).resolve()

        self.save_all(False)

        isoProcess = StoppableThread(target=self.iso.build, args=(self.buildPath, False), daemon=True)
        progressBarProcess = ProgressHandler(self, isoProcess, self)

        isoProcess.start()

        while not self.iso.progress.is_ready() and isoProcess.is_alive():
            pass

        if isoProcess.is_alive():
            progressBarProcess.run()

        return True, None

    @notify_status(JobDialogState.SHOW_FAILURE_WHEN_MESSAGE | JobDialogState.SHOW_COMPLETE | JobDialogState.RESET_PROGRESS_AFTER)
    def iso_extract_dialog(self) -> (bool, str):
        dialog = QFileDialog(parent=self,
                             caption="Extract ISO To...",
                             directory=str(self.extractPath.parent if self.extractPath else Path.home()))

        dialog.setFileMode(QFileDialog.DirectoryOnly)

        if dialog.exec_() != QFileDialog.Accepted:
            return False, None

        self.extractPath = Path(dialog.selectedFiles()[0]).resolve()

        self.save_all(False)

        isoProcess = StoppableThread(target=self.iso.extract, args=(self.extractPath,), daemon=True)
        progressBarProcess = ProgressHandler(self, isoProcess, self)

        isoProcess.start()

        while not self.iso.progress.is_ready() and isoProcess.is_alive():
            pass

        if isoProcess.is_alive():
            progressBarProcess.run()
            
        return True, None

    @notify_status(JobDialogState.SHOW_FAILURE_WHEN_MESSAGE | JobDialogState.SHOW_COMPLETE | JobDialogState.RESET_PROGRESS_AFTER)
    def iso_extract_system_dialog(self) -> (bool, str):
        dialog = QFileDialog(parent=self,
                             caption="Extract System Data To...",
                             directory=str(self.genericPath.parent if self.genericPath else Path.home()))

        dialog.setFileMode(QFileDialog.DirectoryOnly)

        if dialog.exec_() != QFileDialog.Accepted:
            return False, None

        self.genericPath = Path(dialog.selectedFiles()[0]).resolve()

        isoProcess = StoppableThread(target=self.iso.extract_system_data, args=(self.genericPath,), daemon=True)
        progressBarProcess = ProgressHandler(self, isoProcess, self)

        isoProcess.start()

        while not self.iso.progress.is_ready() and isoProcess.is_alive():
            pass

        if isoProcess.is_alive():
            progressBarProcess.run()

        return True, None

    @notify_status(JobDialogState.SHOW_FAILURE_WHEN_MESSAGE | JobDialogState.RESET_PROGRESS_AFTER)
    def bnr_load_dialog(self) -> (bool, str):
        dialog = QFileDialog(parent=self,
                             caption="Open Image",
                             directory=str(self.bnrImagePath.parent if self.bnrImagePath else Path.home()),
                             filter="PNG Image (*.png);;JPEG Image (*.jpg *.jpeg);;Nintendo BNR Image Info (*.bnr);;All files (*)")

        dialog.setFileMode(QFileDialog.ExistingFile)

        if dialog.exec_() != QFileDialog.Accepted:
            return False, None

        self.bnrImagePath = Path(dialog.selectedFiles()[0]).resolve()

        if self.bnrImagePath.is_file():
            if self.bnrImagePath.suffix == ".bnr":
                self.iso.bnr.rawImage = BNR(self.bnrImagePath).rawImage
            else:
                with Image.open(self.bnrImagePath) as image:
                    if image.size != (96, 32):
                        dialog = JobWarningDialog(f"Resizing image of size {image.size} to match BNR size (96, 32)", self)
                        dialog.exec_()
                    self.iso.bnr.rawImage = image

            self.bnr_update_info()
            return True, None
        else:
            return False, "The file does not exist!"

    @notify_status(JobDialogState.SHOW_FAILURE_WHEN_MESSAGE | JobDialogState.RESET_PROGRESS_AFTER)
    def bnr_save_dialog(self) -> (bool, str):
        dialog = QFileDialog(parent=self,
                             caption="Save Image To...",
                             directory=str(self.bnrImagePath.parent if self.bnrImagePath else Path.home()),
                             filter="PNG Image (*.png);;All files (*)")

        dialog.setFileMode(QFileDialog.AnyFile)
        dialog.setAcceptMode(QFileDialog.AcceptSave)

        if dialog.exec_() != QFileDialog.Accepted:
            return False, None

        self.bnrImagePath = Path(dialog.selectedFiles()[0]).resolve()

        image = self.iso.bnr.getImage()
        image.save(self.bnrImagePath)

        return True, None

    def bnr_reset_info(self):
        self.ui.bannerLanguageComboBox.setCurrentIndex(0)
        self.bnr_update_info()

    def bnr_update_info(self):
        pixmap = ImageQt.toqpixmap(self.iso.bnr.getImage())
        pixmap = pixmap.scaled(self.ui.bannerImageView.geometry().width(
        ) - 1, self.ui.bannerImageView.geometry().height() - 1, Qt.KeepAspectRatio)
        self.ui.bannerImageView.setPixmap(pixmap)
        self.ui.bannerImageView.setFrameShape(QFrame.NoFrame)

        self.ui.bannerVersionTextBox.setPlainText(self.iso.bnr.magic)
        if self.iso.bnr.region == "NTSC-J":
            self.ui.bannerLanguageComboBox.setItemText(0, "Japanese")
            self.ui.bannerLanguageComboBox.setCurrentIndex(0)
            self.ui.bannerLanguageComboBox.setEnabled(False)
        elif self.iso.bnr.region == "NTSC-U":
            self.ui.bannerLanguageComboBox.setItemText(0, "English")
            self.ui.bannerLanguageComboBox.setCurrentIndex(0)
            self.ui.bannerLanguageComboBox.setEnabled(False)
        else:
            self.iso.bnr.index = self.ui.bannerLanguageComboBox.currentIndex()
            self.ui.bannerLanguageComboBox.setEnabled(True)
        
        self.ui.bannerVersionTextBox.setEnabled(False)

        self.ui.bannerShortNameTextBox.setPlainText(self.iso.bnr.gameName)
        self.ui.bannerLongNameTextBox.setPlainText(self.iso.bnr.gameTitle)
        self.ui.bannerShortMakerTextBox.setPlainText(
            self.iso.bnr.developerName)
        self.ui.bannerLongMakerTextBox.setPlainText(
            self.iso.bnr.developerTitle)
        self.ui.bannerDescTextBox.setPlainText(
            self.iso.bnr.gameDescription)

    def bnr_save_info(self):
        self.iso.bnr.index = self.ui.bannerLanguageComboBox.currentIndex()
        self.iso.bnr.gameName = self.ui.bannerShortNameTextBox.toPlainText()
        self.iso.bnr.gameTitle = self.ui.bannerLongNameTextBox.toPlainText()
        self.iso.bnr.developerName = self.ui.bannerShortMakerTextBox.toPlainText()
        self.iso.bnr.developerTitle = self.ui.bannerLongMakerTextBox.toPlainText()
        self.iso.bnr.gameDescription = self.ui.bannerDescTextBox.toPlainText()

    def help_about(self):
        desc = "".join(["pyisotools is a tool for extracting and building Gamecube ISOs.\n",
                        "This tools serves as the successor to GCR, and supports new features\n",
                        "as well as many bug fixes.",
                        "\n\n",
                        "Please see the readme for more details.",
                        "\n\n",
                        "Copyright © 2021; All rights reserved.",
                        "\n\n",
                        "JoshuaMK <joshuamkw2002@gmail.com>",
                        "\n\n",
                        f"Running version: {__version__}"])

        QMessageBox.about(self, "About pyisotools", desc)

    def help_file_alignment(self):
        info = "".join(["When an extracted root is opened, you can right click on each node\n",
                        "to set the alignment of that node.\n",
                        "If the node is a file, the file obtains the new alignment.\n",
                        "If the node is a folder, all children will recursively update ",
                        "to the new alignment.",
                        "\n\n",
                        "Default alignment: 4",
                        "\n\n",
                        "Valid alignments:\n",
                        "4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768"])

        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Question)
        dialog.setText(info)
        dialog.setWindowTitle("File Alignment")
        dialog.exec_()

    def help_file_position(self):
        info = "".join(["When an extracted root is opened, you can right click on each file\n",
                        "to set the internal ISO position of that node.",
                        "\n\n",
                        "Default position: -1"])

        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Question)
        dialog.setText(info)
        dialog.setWindowTitle("File Position")
        dialog.exec_()

    def help_file_exclusion(self):
        info = "".join(["When an extracted root is opened, you can right click on each node\n",
                        "to set if it (and all children) is excluded from the build process."])

        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Question)
        dialog.setText(info)
        dialog.setWindowTitle("File Exclusion")
        dialog.exec_()

    def update_program_config(self):
        _data = {}
        _data["darktheme"] = self.ui.actionDarkTheme.isChecked()
        _data["updates"] = self.ui.actionCheckUpdates.isChecked()

        self.programConfig.parent.mkdir(parents=True, exist_ok=True)
        with self.programConfig.open("wb") as config:
            pickle.dump(_data, config)

    def load_program_config(self):
        if not self.programConfig.exists():
            self.theme = Controller.Themes.LIGHT
            self.ui.actionDarkTheme.setChecked(False)
            self.ui.actionCheckUpdates.setChecked(True)
            return

        with self.programConfig.open("rb") as config:
            _data = pickle.load(config)

        self.ui.actionDarkTheme.setChecked(_data["darktheme"])
        self.ui.actionCheckUpdates.setChecked(_data["updates"])

        if _data["darktheme"] is True:
            self.theme = Controller.Themes.DARK
        else:
            self.theme = Controller.Themes.LIGHT

        self._manage_settings_text()

    def update_theme(self, checked: bool):
        if checked:
            self.theme = Controller.Themes.DARK
        else:
            self.theme = Controller.Themes.LIGHT

        self._manage_settings_text()
        self._load_theme()

    def update_all(self):
        _recursive_enable(self.ui)

        if self.is_from_iso():
            self.ui.actionRebuild.setEnabled(False)
        else:
            self.ui.actionExtract.setEnabled(False)

        self.load_file_system()
        self.bnr_reset_info()

        self.ui.isoNameTextBox.setPlainText(self.iso.bootheader.gameName)
        self.ui.isoGameCodeTextBox.setPlainText(self.iso.bootheader.gameCode)
        self.ui.isoMakerCodeTextBox.setPlainText(self.iso.bootheader.makerCode)
        self.ui.isoVersionTextBox.setPlainText(str(self.iso.bootheader.version))
        self.ui.isoBuildDateTextBox.setPlainText(self.iso.apploader.buildDate)

        if self.iso.bootinfo.countryCode == BI2.Country.AMERICA:
            self.ui.isoRegionComboBox.setCurrentIndex(0)
        elif self.iso.bootinfo.countryCode == BI2.Country.EUROPE:
            self.ui.isoRegionComboBox.setCurrentIndex(1)
        elif self.iso.bootinfo.countryCode == BI2.Country.JAPAN:
            self.ui.isoRegionComboBox.setCurrentIndex(2)
        else:
            self.ui.isoRegionComboBox.setCurrentIndex(3)

        self.ui.isoRegionComboBox.setEnabled(False)
        self.ui.isoDiskIDTextBox.setPlainText(f"0x{self.iso.bootheader.diskID:02X}")

    @notify_status(JobDialogState.SHOW_FAILURE_WHEN_MESSAGE | JobDialogState.SHOW_COMPLETE_WHEN_MESSAGE | JobDialogState.RESET_PROGRESS_AFTER)
    def save_all(self, showjob: bool = True):
        _boot = self.iso.bootheader
        _bi2 = self.iso.bootinfo
        _appldr = self.iso.apploader

        _boot.gameName = self.ui.isoNameTextBox.toPlainText()
        _boot.gameCode = self.ui.isoGameCodeTextBox.toPlainText()
        _boot.makerCode = self.ui.isoMakerCodeTextBox.toPlainText()

        diskID = self.ui.isoDiskIDTextBox.toPlainText()
        version = self.ui.isoVersionTextBox.toPlainText()
        try:
            if diskID.startswith("0x"):
                _boot.diskID = int(diskID, 16)
            else:
                _boot.diskID = int(diskID)
        except ValueError:
            dialog = JobFailedDialog(self)
            dialog.setText(f"Invalid input for `diskID` \"{diskID}\" could not be converted to int")
            return False, dialog

        try:
            if diskID.startswith("0x"):
                _boot.version = int(version, 16)
            else:
                _boot.version = int(version)
        except ValueError:
            dialog = JobFailedDialog(self)
            dialog.setText(f"Invalid input for `version` \"{version}\" could not be converted to int")
            return False, dialog

        _appldr.buildDate = self.ui.isoBuildDateTextBox.toPlainText()
        self.bnr_save_info()

        if not showjob:
            if self.is_from_iso():
                self.iso.save_system_datav()
            else:
                self.iso.save_system_data()
            return True, None
        else:
            if self.is_from_iso():
                isoProcess = StoppableThread(target=self.iso.save_system_datav, daemon=True)
            else:
                isoProcess = StoppableThread(target=self.iso.save_system_data, daemon=True)

            progressBarProcess = ProgressHandler(self, isoProcess, self)

            isoProcess.start()

            while not self.iso.progress.is_ready() and isoProcess.is_alive():
                pass

            if isoProcess.is_alive():
                progressBarProcess.run()

            dialog = JobCompleteDialog(self)
            if self.is_from_iso():
                dialog.setText("ISO metadata saved successfully!")
            else:
                dialog.setText("Root information saved successfully!")

            return True, dialog

    def reset_all(self):
        self.ui.setupUi(self)
        self._load_theme()
        self.setWindowTitle(f"pyisotools v{__version__}")

    def load_file_system(self):
        rootNode = FSTTreeWidget()
        rootNode.setIcon(0, QIcon(u":/icons/Disc"))
        rootNode.setText(0, "root")
        rootNode.node = self.iso
        self._load_fst_tree(rootNode, self.iso)

        self.ui.fileSystemTreeWidget.takeTopLevelItem(0)
        self.ui.fileSystemTreeWidget.addTopLevelItem(rootNode)

        self.ui.fileSystemTreeWidget.sortItems(0, Qt.SortOrder.AscendingOrder)

    def file_system_context_menu(self, point):
        # Infos about the node selected.
        index = self.ui.fileSystemTreeWidget.indexAt(point)

        if not index.isValid():
            return

        item = self.ui.fileSystemTreeWidget.itemAt(point)
        self.file_system_set_fields(item, 0)

        # We build the menu.
        menu = QMenu(self.ui.fileSystemTreeWidget)

        if not self.is_from_iso():
            if item.node.is_root():
                path = self.iso.root
            else:
                path = self.iso.root / self.iso.name / item.node.path

            viewAction = QAction("Open Path in Explorer", self.ui.fileSystemTreeWidget)
            viewAction.triggered.connect(lambda clicked=None, x=path: self._open_path_in_explorer(x))
            alignmentAction = QAction("Set Alignment...", self.ui.fileSystemTreeWidget)
            alignmentAction.triggered.connect(lambda clicked=None, x=item: self._open_alignment_dialog(x))
            positionAction = QAction("Set Position...", self.ui.fileSystemTreeWidget)
            positionAction.triggered.connect(lambda clicked=None, x=item: self._open_position_dialog(x))
            excludeAction = QAction("Include" if item.node._exclude else "Exclude", self.ui.fileSystemTreeWidget)
            excludeAction.triggered.connect(lambda clicked=None, x=item: self._disable_node(x))
            menu.addAction(viewAction)
            menu.addSeparator()
            menu.addAction(alignmentAction)
            if item.node.is_file():
                menu.addAction(positionAction)
            if not item.node.is_root():
                menu.addSeparator()
                menu.addAction(excludeAction)
        else:
            if item.node.is_root():
                extractAction = QAction(f"Extract ISO To...", self.ui.fileSystemTreeWidget)
                extractAction.triggered.connect(self.iso_extract_dialog)
                sysExtractAction = QAction(f"Extract System Data To...", self.ui.fileSystemTreeWidget)
                sysExtractAction.triggered.connect(self.iso_extract_system_dialog)
                menu.addAction(extractAction)
                menu.addAction(sysExtractAction)
            else:
                extractAction = QAction(f"Extract \"{item.text(0)}\" To...", self.ui.fileSystemTreeWidget)
                extractAction.triggered.connect(lambda x=self, y=item.node: self.save_generic_to_folder(parent=x, callback=_extract_path_from_iso, args=(y,)))
                menu.addAction(extractAction)

        menu.exec_(self.ui.fileSystemTreeWidget.mapToGlobal(point))

    def file_system_set_fields(self, item: FSTTreeWidget, column: int):
        if item.node.is_dir():
            self.ui.fileSystemStartInfoLabel.setText("Start Index:")
            self.ui.fileSystemSizeInfoLabel.setText("End Index:")
            self.ui.fileSystemStartInfoTextBox.setPlainText(str(item.node._id))
            self.ui.fileSystemSizeInfoTextBox.setPlainText(str(item.node.size + item.node._id))
        else:
            self.ui.fileSystemStartInfoLabel.setText("File Location:")
            self.ui.fileSystemSizeInfoLabel.setText("File Size:")
            self.ui.fileSystemStartInfoTextBox.setPlainText(f"0x{item.node._fileoffset if not item.node._position else item.node._position:X}")
            self.ui.fileSystemSizeInfoTextBox.setPlainText(f"0x{item.node.size:X}")


    @notify_status(JobDialogState.SHOW_FAILURE_WHEN_MESSAGE | JobDialogState.SHOW_COMPLETE | JobDialogState.RESET_PROGRESS_AFTER)
    def save_generic_to_folder(self, parent=None, caption="Save to folder...", filter=None, callback=None, args=()) -> (bool, str):
        if filter is None:
            filter = "Any folder"

        dialog = QFileDialog(parent=parent,
                             caption=caption,
                             directory=str(self.genericPath.parent if self.genericPath else Path.home()),
                             filter=filter)
                             
        dialog.setAcceptMode(QFileDialog.AcceptOpen)
        dialog.setFileMode(QFileDialog.DirectoryOnly)

        if dialog.exec_() != QFileDialog.Accepted:
            return False, None

        self.genericPath = Path(dialog.selectedFiles()[0])

        if callback:
            isoProcess = StoppableThread(target=callback, args=(self, self.genericPath, *args), daemon=True)
            progressBarProcess = ProgressHandler(self, isoProcess, self)

            isoProcess.start()

            while not self.iso.progress.is_ready() and isoProcess.is_alive():
                pass

            if isoProcess.is_alive():
                progressBarProcess.run()

            return True, None
        else:
            return True, None

    @notify_status(JobDialogState.SHOW_FAILURE_WHEN_MESSAGE)
    def _open_alignment_dialog(self, item: FSTTreeWidget):
        window = Ui_NodeFieldWindow()
        dialog = QDialog(self, Qt.WindowSystemMenuHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)

        window.setupUi(dialog)

        dialog.setWindowTitle(item.text(0))
        dialog.setModal(True)

        window.label.setText("Alignment:")
        if item.node._alignment:
            window.plainTextEdit.setPlainText(str(item.node._alignment))
        else:
            window.plainTextEdit.setPlainText("4")

        dialog.show()
        if dialog.exec_() != QFileDialog.Accepted:
            return False, None

        text = window.plainTextEdit.toPlainText()

        try:
            if text.startswith("0x"):
                alignment = int(text, 16)
            else:
                alignment = int(text)
        except ValueError:
            dialog = JobFailedDialog(self)
            dialog.setText(f"Invalid input \"{text}\" could not be converted to int")
            return False, dialog

        alignment = _round_up_to_power_of_2(max(4, min(alignment, 32768)))
        if item.node._alignment != alignment:
            item.node._alignment = alignment
            self.iso.pre_calc_offsets(self.iso.MaxSize - self.iso.get_auto_blob_size())
            self.ui.fileSystemStartInfoTextBox.setPlainText(f"0x{item.node._fileoffset:X}")
        if item.node.is_dir():
            for child in item.node.children:
                child._alignment = _round_up_to_power_of_2(alignment)

        return True, None

    @notify_status(JobDialogState.SHOW_FAILURE_WHEN_MESSAGE)
    def _open_position_dialog(self, item: FSTTreeWidget):
        window = Ui_NodeFieldWindow()
        dialog = QDialog(self, Qt.WindowSystemMenuHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)

        window.setupUi(dialog)

        dialog.setWindowTitle(item.text(0))
        dialog.setModal(True)

        window.label.setText("Position:")
        if item.node._position:
            window.plainTextEdit.setPlainText(f"0x{item.node._position:X}")
        else:
            window.plainTextEdit.setPlainText("-1")

        dialog.show()
        if dialog.exec_() != QFileDialog.Accepted:
            return False, None

        text = window.plainTextEdit.toPlainText()
        
        try:
            if text.startswith("0x"):
                position = int(text, 16)
            else:
                position = int(text)
        except ValueError:
            dialog = JobFailedDialog(self)
            dialog.setText(f"Invalid input \"{text}\" could not be converted to int")
            return False, dialog

        if position < 0:
            if item.node._position:
                item.node._position = None
                self.iso.pre_calc_offsets(self.iso.MaxSize - self.iso.get_auto_blob_size())
                self.ui.fileSystemStartInfoTextBox.setPlainText(f"0x{item.node._fileoffset:X}")
            return True, None
        else:
            newPos = min(position, self.iso.MaxSize - 4) & -4
            if item.node._position != newPos:
                item.node._position = newPos
                self.iso.pre_calc_offsets(self.iso.MaxSize - self.iso.get_auto_blob_size())

            self.ui.fileSystemStartInfoTextBox.setPlainText(f"0x{item.node._position:X}")
            return True, None

    def _disable_node(self, item: FSTTreeWidget):
        if item.node._exclude:
            item.node._exclude = False
        else:
            item.node._exclude = True

        item.setDisabled(item.node._exclude)
        self.iso.pre_calc_offsets(self.iso.MaxSize - self.iso.get_auto_blob_size())
        self.ui.fileSystemStartInfoTextBox.setPlainText(f"0x{item.node._fileoffset:X}")

    @staticmethod
    def _open_path_in_explorer(path: Path):
        if sys.platform == "win32":
            subprocess.Popen(f"explorer /select,\"{path.resolve()}\"", shell=True)
        elif sys.platform == "linux":
            subprocess.Popen(["xdg-open", path.resolve()])
        elif sys.platform == "darwin":
            subprocess.Popen(['open', '--', path.resolve()])

    def _load_fst_tree(self, parent: FSTTreeWidget, node: FSTNode):
        for child in node.children:
            treeNode = FSTTreeWidget(child.name)
            treeNode.setText(0, child.name)
            treeNode.setDisabled(child._exclude)
            treeNode.node = child

            if child.is_dir():
                treeNode.setIcon(0, QIcon(u":/icons/Folder"))
                self._load_fst_tree(treeNode, child)
            else:
                treeNode.setIcon(0, QIcon(u":/icons/File"))

            parent.addChild(treeNode)

    def _manage_settings_text(self, checked: bool = False):
        if self.ui.actionDarkTheme.isChecked():
            self.ui.actionDarkTheme.setText("✔ Dark Theme")
        else:
            self.ui.actionDarkTheme.setText("Dark Theme")

        if self.ui.actionCheckUpdates.isChecked() is True and self.ui.actionDarkTheme.isChecked() is True:
            self.ui.actionCheckUpdates.setText("✔ Check Updates")
        else:
            self.ui.actionCheckUpdates.setText("Check Updates")

    def _load_theme(self):
        self.setStyleSheet(self.theme.read_text())

        if self.theme == Controller.Themes.LIGHT:
            self.ui.bannerImageView.setStyleSheet("")
            self.ui.bannerHFrameLine.setStyleSheet("")
        else:
            self.ui.bannerImageView.setStyleSheet("QLabel {\n"
                                                  "  background-color: #19232D\n;"
                                                  "  border: 1px solid #32414B\n;"
                                                  "  padding: 2px\n;"
                                                  "  margin: 0px\n;"
                                                  "  color: #F0F0F0\n;"
                                                  "}\n\n"

                                                  "QLabel:disabled {\n"
                                                  "  background-color: #19232D;\n"
                                                  "  border: 1px solid #32414B;\n"
                                                  "  color: #787878;\n"
                                                  "}")
            self.ui.bannerHFrameLine.setStyleSheet(".QFrame {\n"
                                                   "  border-radius: 4px;\n"
                                                   "  border: 1px solid #32414B;\n"
                                                   "}\n\n"

                                                   ".QFrame[frameShape=\"0\"] {\n"
                                                   "  border-radius: 4px;\n"
                                                   "  border: 1px transparent #32414B;\n"
                                                   "}\n\n"

                                                   ".QFrame[frameShape=\"4\"] {\n"
                                                   "  max-height: 2px;\n"
                                                   "  border: none;\n"
                                                   "  background-color: #32414B;\n"
                                                   "}\n\n"

                                                   ".QFrame[frameShape=\"5\"] {\n"
                                                   "  max-width: 2px;\n"
                                                   "  border: none;\n"
                                                   "  background-color: #32414B;\n"
                                                   "}")


class ProgressHandler(QThread):
    def __init__(self, controller: Controller, t: threading.Thread, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.controller = controller
        self.watched = t

    def run(self):
        self.controller.ui.operationProgressBar.setTextVisible(True)
        self.controller.ui.operationProgressBar.setMaximum(self.controller.iso.progress.jobSize)
        self.controller.ui.operationProgressBar.setValue(0)

        while self.controller.iso.progress.jobProgress < self.controller.iso.progress.jobSize and not self.watched.is_zombie():
            self.controller.ui.operationProgressBar.setValue(self.controller.iso.progress.jobProgress)
            time.sleep(0.01)

        self.controller.ui.operationProgressBar.setValue(self.controller.iso.progress.jobProgress)


def _recursive_enable(parent):
    for member in [getattr(parent, attr) for attr in dir(parent) if not callable(getattr(parent, attr)) and not attr.startswith("__")]:
        if hasattr(member, "setEnabled"):
            member.setEnabled(True)
            _recursive_enable(member)

def _extract_path_from_iso(controller: Controller, dest: Path, node: FSTNode):
    controller.iso.extract_path(node.path, dest)

def _round_up_to_power_of_2(n):
    n -= 1
    n |= n >> 1
    n |= n >> 2
    n |= n >> 4
    n |= n >> 8
    n |= n >> 16
    return n + 1
