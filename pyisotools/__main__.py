import sys

from argparse import ArgumentParser
from pathlib import Path

from PySide2.QtCore import QCoreApplication
from PySide2.QtWidgets import QApplication, QMainWindow

from pyisotools import __version__
from pyisotools.gui.mainwindow import Ui_MainWindow
from pyisotools.gui.connector import Controller
from pyisotools.iso import GamecubeISO

if __name__ == "__main__":
    if len(sys.argv) == 1:
        app = QApplication()
        central = Ui_MainWindow()
        mainWindow = Controller(central)
        central.setupUi(mainWindow)
        mainWindow.load_program_config()
        mainWindow._load_theme()
        mainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", f"pyisotools v{__version__}", None))
        mainWindow.show()
        sys.exit(app.exec_())
    else:
        parser = ArgumentParser(f"pyisotools v{__version__}", description="ISO tool for extracting/building Gamecube ISOs", allow_abbrev=False)

        parser.add_argument("src", help="ISO/root to build/extract with")
        parser.add_argument("job",
                            choices=["B", "E"],
                            help="Job to do")
        parser.add_argument("--newinfo",
                            help="Overwrite original information with custom info (build only)",
                            action="store_true")
        parser.add_argument("--dest",
                            help="Directory (extract)/ISO (build) to store data")

        args = parser.parse_args()

        src = Path(args.src).resolve()
        iso = GamecubeISO()
        if args.job == "E":
            iso.extract(src, args.dest)
        elif args.job == "B":
            iso.build(src, args.dest, genNewInfo=args.newinfo)
        else:
            parser.print_help()