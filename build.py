import os
import subprocess
import sys
from pyisotools import __author__, __version__

if len(sys.argv) == 1 or sys.argv[1].lower() == "p":
    subprocess.Popen('pyinstaller --noconfirm --onefile --console --icon "pyisotools/gui/icons/pyisotools.ico" --name "pyisotools" --clean --add-data "pyisotools/gui/themes;themes/"  "pyisotools/__main__.py"')
elif sys.argv[1].lower() == "build":
    from cx_Freeze import setup, Executable

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
else:
    raise ValueError(f"Invalid arg {sys.argv[1]} is not `p' or `build'")