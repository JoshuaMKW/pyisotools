from cx_Freeze import setup, Executable

import os
import subprocess
import sys
from pyisotools import __author__, __version__


# import PyInstaller.__main__

# if (sys.platform == "win32"):
#     callArgs = (
#         "--debug=imports",
#         "--noconfirm",
#         "--onefile",
#         "--console",
#         "--icon",
#         "pyisotools/gui/icons/pyisotools.ico",
#         "--name",
#         "pyisotools",
#         "--clean",
#         "--add-data",
#         "pyisotools/gui/themes;themes/",
#         "pyisotools/__main__.py"
#         # "--windowed"
#     )
# else:
#     callArgs = (
#         "pyinstaller",
#         "--noconfirm",
#         "--onefile",
#         "--console",
#         "--icon",
#         '"pyisotools/gui/icons/pyisotools.ico"',
#         "--name",
#         '"pyisotools"',
#         "--clean",
#         "--add-data",
#         '"pyisotools/gui/themes:themes/"',
#         '"pyisotools/__main__.py"'
#     )

# PyInstaller.__main__.run(callArgs)


include_files = []
excludes = ["tkinter"]
packages = []

options = {
    "build_exe": {
        "optimize": 2,
        "excludes": excludes,
        "packages": packages,
        "include_files": include_files
    }
}

# base="Win32GUI" should be used only for Windows GUI app
base = None
if sys.platform == "win32":
    base = "Win32GUI"

executable = Executable(
    script=os.path.join("pyisotools", "__main__.py"),
    targetName="pyisotools",
    icon=os.path.join("pyisotools", "gui", "icons", "pyisotools.ico"),
    base=base
)

setup(name="pyisotools",
      version=__version__,
      description="DOL Patcher for extending the codespace of Wii/GC games",
      executables=[executable],
      author=__author__,
      author_email="joshuamkw2002@gmail.com",
      options=options
      )
