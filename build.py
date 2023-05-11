import sys
import PyInstaller.__main__

from pyisotools import __author__, __version__


if sys.platform == "win32":
    callArgs = (
        "--noconfirm",
        "--onefile",
        "--console",
        "--icon",
        "pyisotools/gui/icons/pyisotools.ico",
        "--name",
        "pyisotools",
        "--clean",
        "--add-data",
        "pyisotools/gui/themes;themes/",
        "pyisotools/__main__.py" "--windowed",
    )
else:
    callArgs = (
        "--noconfirm",
        "--onefile",
        "--console",
        "--icon",
        "pyisotools/gui/icons/pyisotools.ico",
        "--name",
        "pyisotools",
        "--clean",
        "--add-data",
        "pyisotools/gui/themes:themes/",
        "pyisotools/__main__.py",
    )

PyInstaller.__main__.run(callArgs)
