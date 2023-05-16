"""Module allowing for `python -m qdarktheme.widget_gallery`."""
import sys

from pyisotools.gui.qdarktheme import load_stylesheet
from pyisotools.gui.qdarktheme.qtpy.QtCore import Qt
from pyisotools.gui.qdarktheme.qtpy.QtWidgets import QApplication
from pyisotools.gui.qdarktheme.widget_gallery.mainwindow import WidgetGallery

if __name__ == "__main__":
    app = QApplication(sys.argv)
    if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):  # Enable High DPI display with Qt5
        # type: ignore
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
    win = WidgetGallery()
    win.menuBar().setNativeMenuBar(False)
    app.setStyleSheet(qdarktheme.load_stylesheet())
    win.show()
    app.exec()
