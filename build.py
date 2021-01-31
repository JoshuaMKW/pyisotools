import os
import sys
from cx_Freeze import setup, Executable
from pyisotools import __author__, __version__

include_files = []
excludes = [ "tkinter" ]
packages = []

options = {
    "build_exe": {
        "optimize": 4,
        "excludes": excludes,
        "packages": packages,
        "include_files": include_files
    }
}

executable = Executable(
    script=os.path.join("pyisotools", "__main__.py"),
    targetName="pyisotools",
    icon=os.path.join("pyisotools", "gui", "icons", "pyisotools.ico")
)

setup(name = "pyisotools",
      version = __version__,
      description = "DOL Patcher for extending the codespace of Wii/GC games",
      executables = [executable],
      author = __author__,
      author_email = "joshuamkw2002@gmail.com",
      options = options
      )